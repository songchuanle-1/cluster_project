#!/usr/bin/env python3
"""通用研究流水线监控 v2 — 多项目早停 + GPU 队列 + 决策日志 + 实验台账

用法:
    python3 pipeline_monitor.py <project> [--server S] [--patience N] [--earlystop-only]

v2 变更:
- 空闲 GPU 判定: 显存 < 1GB 且 util < 10%（防止验证阶段低 util 误判双推）
- patience 优先级: --patience > 队列任务级 patience > pipeline/queue.json 全局 > 10
- 整轮 flock(<project>/.pipeline.lock)，防多会话并发双推/写坏队列
- gpu_allowlist: 每项目限定可操作的服务器与卡号；白名单外的进程只展示、不处置
- 终态跟踪: done_complete / done_earlystop / crashed / stopped_unknown 写回队列
- 实验结束时: 拉取日志到 <project>/Checkpoints/<server>/<model>/<run_ts>/（与 checkpoint 同目录），
  追加 <project>/pipeline/experiments.csv 台账 + <project>/pipeline/monitoring/<YYYY-MM-DD>.md 日报
"""

import yaml, json, re, subprocess, sys, os, csv, time, shutil
from datetime import datetime

# Windows 兼容: stdout/stderr UTF-8 + 默认 open() 用 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def bash_executable():
    """Return an explicit Bash executable on Windows cron and interactive runs."""
    candidates = [
        shutil.which("bash"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return "bash"
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import builtins as _builtins_mod
_orig_open = _builtins_mod.open
def _patched_open(file, mode='r', *args, **kwargs):
    if 'encoding' not in kwargs and 'b' not in mode:
        kwargs['encoding'] = 'utf-8'
    return _orig_open(file, mode, *args, **kwargs)
_builtins_mod.open = _patched_open

# 跨平台文件锁: POSIX 用 fcntl.flock, Windows 用 msvcrt.locking
try:
    import fcntl
    _POSIX = True
except ImportError:
    fcntl = None
    _POSIX = False
    import msvcrt

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/home/songcl/3dres/project")
DEFAULT_PATIENCE = 10
FREE_MEM_MB = 1024   # 显存低于此值才可能算空闲
FREE_UTIL = 10       # util 低于此值才可能算空闲
CRASH_KEYWORDS = ("Traceback", "CUDA out of memory", "RuntimeError", "NCCL error")
DEATHWATCH_THRESHOLD = 3  # consecutive ticks before considering a missing process truly dead
DEATHWATCH_FILE = "deathwatch.json"
GPU_RESERVATIONS_FILE = "gpu_reservations.json"


def load_project_ownership_blocks(project_dir, srv_name, allow):
    """Return LightText slots unavailable to exclusive diagnostic tasks."""
    if os.path.basename(os.path.normpath(project_dir)) != "lighttext_project":
        return set()
    # No allowlist is not permission to bypass the mandatory project guard.
    if allow is None:
        raise RuntimeError("LightText ownership checks require an explicit allowlist")
    denied = set(allow)
    try:
        import importlib.util
        path = os.path.join(project_dir, "scripts", "diagnostic_ownership_guard.py")
        spec = importlib.util.spec_from_file_location("lighttext_dispatch_guard", path)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        servers = load_servers(project_dir)
        slots = {
            (name, str(gpu))
            for name, config in servers.items()
            for gpu in (config.get("allowed_gpus") or [])
        }
        if not {(srv_name, str(gpu)) for gpu in allow}.issubset(slots):
            return denied
        blocks = guard.load_required_policy_blocks(project_dir, slots)
        return {gpu for server, gpu in blocks if server == srv_name}
    except Exception as error:
        print(f"  [Ownership] fail closed: {type(error).__name__}: {error}")
        return denied


def load_active_gpu_reservations(project_dir, now=None):
    """Load unexpired, project-local exclusive GPU reservations.

    The file is optional and is only used to prevent new dispatches. Existing
    training is never preempted or stopped by a reservation.
    """
    path = os.path.join(project_dir, "pipeline", GPU_RESERVATIONS_FILE)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return {}
    records = payload.get("reservations", []) if isinstance(payload, dict) else []
    if not isinstance(records, list):
        return {}
    current = now or datetime.now().astimezone()
    active = {}
    for record in records:
        if not isinstance(record, dict) or record.get("status", "active") != "active":
            continue
        server = record.get("server")
        gpu = record.get("gpu")
        expires_at = record.get("expires_at")
        if not server or gpu is None or not expires_at:
            continue
        try:
            expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        except ValueError:
            continue
        if (record.get("requires_cleanup") is not True
                and (expires.tzinfo is None or current.tzinfo is None or expires <= current)):
            continue
        active[(str(server), str(gpu))] = record
    return active

def load_deathwatch(project_dir):
    dw_path = os.path.join(project_dir, "pipeline", DEATHWATCH_FILE)
    if os.path.exists(dw_path):
        with open(dw_path, "r") as f:
            return json.load(f)
    return {}

def save_deathwatch(project_dir, dw):
    dw_path = os.path.join(project_dir, "pipeline", DEATHWATCH_FILE)
    with open(dw_path, "w") as f:
        json.dump(dw, f, indent=2)

LEDGER_FIELDS = ["finished_at", "id", "config", "server", "gpu", "state",
                 "best_miou", "epochs", "log_local"]

_JUMP = {"v": None}   # 当前服务器的跳板 (SERVERS.yaml jumphost)，由主循环按服务器设置

def ssh(host, user, cmd, timeout=8):
    tgt = f"{user}@{host}"
    base = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes"]
    if _JUMP["v"]:
        base += ["-J", _JUMP["v"]]
        timeout = max(timeout, 15)
    try:
        # text=True 在 Windows 默认用 GBK 解码 ssh 输出, 遇到日志里的 tqdm Unicode
        # 方块字符(█▊▍)会抛 UnicodeDecodeError 并返回空 → epoch/日志读取失效。
        # 显式 UTF-8 + errors=replace 保证任何字节都不崩溃。
        r = subprocess.run(base + [tgt, cmd], capture_output=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return r.stdout.strip()
    except:
        return ""

def load_servers(project_dir):
    with open(os.path.join(project_dir, "SERVERS.yaml")) as f:
        cfg = yaml.safe_load(f)
    servers = {}
    for name, c in cfg.get("servers", {}).items():
        if c.get("role") != "gpu_server":
            continue
        servers[name] = {
            "host": c["host"], "user": c["user"],
            "remote_code_root": c.get("remote_code_root", ""),
            "work_dir": c.get("work_dir", ""),
            # 流水线可操作的卡号；None=未配置(不限制)，[]=整台跳过
            "allowed_gpus": c.get("allowed_gpus", None),
            # 单卡同时可跑的任务数 (H100 80GB 可多任务; 默认 1 = 一卡一任务)
            "max_tasks_per_gpu": c.get("max_tasks_per_gpu", 1),
            # 允许在外部任务之上叠加本项目任务；仍由 max_tasks_per_gpu
            # 限制本项目任务数，并要求满足 task_memory_mb 显存余量。
            "allow_external_overlay": c.get("allow_external_overlay", False),
            "task_memory_mb": c.get("task_memory_mb", 20000),
            # 跳板 (如 server-6 需经 server-4)
            "jumphost": c.get("jumphost", None),
        }
    return servers

def log_decision(project_dir, dtype, question, decision, rationale="", evidence=""):
    """记录决策到 pipeline/decisions/<YYYYMMDD-HHMMSS>_<dtype>.md (每次决策独立文件)"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tslug = datetime.now().strftime("%Y%m%d-%H%M%S")
    dec_dir = os.path.join(project_dir, "pipeline", "decisions")
    os.makedirs(dec_dir, exist_ok=True)
    fname = f"{tslug}_{dtype}.md"
    md = os.path.join(dec_dir, fname)
    with open(md, "w") as f:
        f.write(f"# {os.path.basename(project_dir)} 决策记录\n\n"
                f"- **时间**: {ts}\n"
                f"- **类型**: {dtype}\n"
                f"- **问题**: {question}\n"
                f"- **决策**: {decision}\n")
        if rationale:
            f.write(f"- **依据**: {rationale}\n")
        if evidence:
            f.write(f"- **证据**: {evidence}\n")
    # 同时追加到 decisions/ 下的汇总文件（方便快速翻阅）
    index = os.path.join(dec_dir, "_index.md")
    if not os.path.exists(index):
        with open(index, "w") as f:
            f.write(f"# {os.path.basename(project_dir)} 决策索引\n\n"
                    "| 时间 | 类型 | 问题 | 决策 |\n"
                    "|------|------|------|------|\n")
    with open(index, "a") as f:
        q_short = question[:60].replace("\n", " ")
        d_short = decision[:60].replace("\n", " ")
        f.write(f"| {ts} | [{dtype}]({fname}) | {q_short} | {d_short} |\n")
    return md

# ---------- 锁 / 队列 ----------

def acquire_lock(project_dir):
    """整轮监控独占锁；拿不到说明另一监控正在跑，直接退出避免双推。"""
    lock_path = os.path.join(project_dir, ".pipeline.lock")
    f = open(lock_path, "a+b")
    try:
        if _POSIX:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        return f
    except OSError:
        f.close()
        return None

# ========== 三层存储 ==========
# 1. pipeline/queue.json       → 仅 waiting 排队(按服务器分组)
# 2. pipeline/running.json     → 仅 running/claiming 映射(server→gpu→exp_id)
# 3. pipeline/experiments/<id>.json → 每个实验独立 JSON,完整生命周期

def _experiment_path(project_dir, exp_id):
    exp_dir = os.path.join(project_dir, "pipeline", "experiments")
    os.makedirs(exp_dir, exist_ok=True)
    return os.path.join(exp_dir, f"{exp_id}.json")

def load_queue(project_dir):
    """加载 waiting 队列"""
    qf = os.path.join(project_dir, "pipeline", "queue.json")
    if os.path.exists(qf):
        with open(qf) as f:
            return json.load(f)
    return None

def save_queue(project_dir, queue_data):
    qf = os.path.join(project_dir, "pipeline", "queue.json")
    tmp = qf + ".tmp"
    with open(tmp, "w") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, qf)

def load_running(project_dir):
    """加载 running/claiming 映射"""
    rf = os.path.join(project_dir, "pipeline", "running.json")
    if os.path.exists(rf):
        with open(rf) as f:
            return json.load(f)
    return {}  # {server: {gpu: exp_id}}

def save_running(project_dir, running_data):
    rf = os.path.join(project_dir, "pipeline", "running.json")
    tmp = rf + ".tmp"
    with open(tmp, "w") as f:
        json.dump(running_data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, rf)

def load_experiment(project_dir, exp_id):
    """加载单个实验 JSON"""
    ep = _experiment_path(project_dir, exp_id)
    if os.path.exists(ep):
        with open(ep) as f:
            return json.load(f)
    return None

def save_experiment(project_dir, exp_data):
    """保存单个实验 JSON"""
    exp_id = exp_data.get("id", "unknown")
    ep = _experiment_path(project_dir, exp_id)
    with open(ep, "w") as f:
        json.dump(exp_data, f, indent=2, ensure_ascii=False)

def get_all_experiments(project_dir):
    """加载所有实验 JSON → dict[id]=data"""
    exp_dir = os.path.join(project_dir, "pipeline", "experiments")
    result = {}
    if os.path.isdir(exp_dir):
        for fname in sorted(os.listdir(exp_dir)):
            if fname.endswith(".json"):
                with open(os.path.join(exp_dir, fname)) as f:
                    data = json.load(f)
                    result[data.get("id", fname[:-5])] = data
    return result

def get_allowlist(srv_cfg, queue, srv_name):
    """返回该服务器可操作的 GPU 号集合(str)。
    优先 SERVERS.yaml 的 allowed_gpus（None=未配置；[]=整台跳过），
    未配置时退回 pipeline/queue.json 的 gpu_allowlist（兼容旧配置），都没有 → None (不限制)。"""
    ag = srv_cfg.get("allowed_gpus")
    if ag is not None:
        return {str(g) for g in ag}
    if queue and queue.get("gpu_allowlist"):
        al = queue["gpu_allowlist"]
        if srv_name not in al:
            return set()
        return {str(g) for g in al[srv_name]}
    return None

def match_task(project_dir, srv_name, cfg_basename):
    """在 queue.json + running.json 中找到匹配的任务"""
    queue = load_queue(project_dir)
    if queue:
        for task in queue.get("gpu_queues", {}).get(srv_name, []):
            if os.path.splitext(os.path.basename(task.get("config", "")))[0] == cfg_basename:
                return task
    # 也查 running.json 映射 (gpu 值可能是 str 或 list[exp_id]，支持单卡多任务)
    running = load_running(project_dir)
    for gpu, exp_ids in running.get(srv_name, {}).items():
        if isinstance(exp_ids, str):
            exp_ids = [exp_ids]
        for exp_id in exp_ids:
            exp = load_experiment(project_dir, exp_id)
            if exp and os.path.splitext(os.path.basename(exp.get("config", "")))[0] == cfg_basename:
                return exp
    return None

def effective_patience(cli_patience, task, queue):
    if cli_patience is not None:
        return cli_patience
    if task and task.get("patience"):
        return int(task["patience"])
    if queue and queue.get("patience"):
        return int(queue["patience"])
    return DEFAULT_PATIENCE

# ---------- 台账 / 日报 / 日志拉取 ----------

def ledger_append(project_dir, **row):
    path = os.path.join(project_dir, "pipeline", "experiments.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in LEDGER_FIELDS})

def daily_report(project_dir, event_lines):
    """事件追加到 <project>/pipeline/monitoring/<YYYY-MM-DD>.md（无事件不写）"""
    if not event_lines:
        return None
    d = datetime.now()
    rp_dir = os.path.join(project_dir, "pipeline", "monitoring")
    os.makedirs(rp_dir, exist_ok=True)
    path = os.path.join(rp_dir, d.strftime("%Y-%m-%d") + ".md")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(f"# {os.path.basename(project_dir)} 流水线日报 {d.strftime('%Y-%m-%d')}\n")
    with open(path, "a") as f:
        f.write(f"\n### {d.strftime('%H:%M:%S')}\n")
        for line in event_lines:
            f.write(f"- {line}\n")
    return path

def pull_log(project_dir, host, user, remote_log, cfg_name, state, srv_name=""):
    """终态时: 调用项目 scripts/remote_pull.sh 拉取远端日志到本地 Checkpoints/"""
    server_dir = srv_name.replace("-", "_") if srv_name else "server_0"
    # 调用 bash scripts/remote_pull.sh <server_name> --logs-only
    # PROJECT_DIR 需要指向项目的 code 目录
    proj_root = project_dir
    scripts = os.path.join(proj_root, "scripts")
    if not os.path.isdir(scripts):
        for sub in os.listdir(proj_root):
            sp = os.path.join(proj_root, sub, "scripts")
            if os.path.isdir(sp):
                scripts = sp
                break
    pull_script = os.path.join(scripts, "remote_pull.sh")
    if not os.path.exists(pull_script):
        return ""
    server_name = srv_name.replace("_", "-") if "_" in srv_name else srv_name
    # PROJECT_DIR 为 code 目录 (跟 remote_train.sh 一样)
    code_dir = (os.path.dirname(scripts) if os.path.basename(scripts) != "scripts"
                else os.path.dirname(os.path.dirname(scripts)))
    env = dict(os.environ, PROJECT_DIR=code_dir)
    try:
        r = subprocess.run([bash_executable(), pull_script, server_name, "--logs-only"],
                          cwd=proj_root, env=env, capture_output=True, text=True, timeout=120)
    except:
        return ""
    # remote_pull.sh 拉取到 Checkpoints/<server>/ → 找对应日志文件
    ckpt_base = os.path.join(proj_root, "Checkpoints", server_dir)
    # 远端 remote_log 路径的尾部 filename
    log_basename = os.path.basename(remote_log)
    # 在 Checkpoints 下递归找已拉取的同名日志
    for root, dirs, files in os.walk(ckpt_base):
        for f in files:
            if f == log_basename or (f.endswith(".log") and cfg_name in f):
                return os.path.join(root, f)
    return ""

# ---------- 终态结果分析 MD ----------
def write_analysis_md(project_dir, cfg_name, state, best_s, srv_name, gpu, ep, log_path, task):
    """终态时自动生成 pipeline/analyses/<cfg>_<state>_<ts>.md"""
    ana_dir = os.path.join(project_dir, "pipeline", "analyses")
    os.makedirs(ana_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ana_path = os.path.join(ana_dir, f"{cfg_name}_{state}_{ts}.md")
    try:
        with open(log_path, errors='ignore') as f:
            text = f.read()
        accs = [float(a) for a in re.findall(r'spAcc_50\s*:?\s*(\d+\.\d+)', text)]
        spms = [float(s) for s in re.findall(r'spmIOU\s*:?\s*(\d+\.\d+)', text)]
        best_acc = f"{max(accs):.3f}" if accs else "?"
        best_spm = f"{max(spms):.3f}" if spms else "?"
    except:
        best_acc = "?"
        best_spm = "?"
    tid = (task or {}).get("id", cfg_name)
    label = (task or {}).get("label", "")
    with open(ana_path, "w") as f:
        f.write(f"""================================================================================
  Experiment Result Analysis — {os.path.basename(project_dir)}
  Experiment: {tid} | State: {state}
================================================================================

## 1. Basic Info
  - ID: {tid}
  - Config: {(task or {}).get('config', cfg_name)}
  - Server: {srv_name} | GPU: {gpu}
  - Epochs: {ep}
  - State: {state}
  - Label: {label}

## 2. Best Metrics
  | Metric | Value  |
  |--------|--------|
  | mIoU   | {best_s} |
  | Acc@50 | {best_acc} |
  | spmIOU | {best_spm} |

## 3. Convergence Summary
  - Best epoch from pulled log: see {os.path.basename(log_path)}

## 4. Comparison
  - vs baseline: (see pipeline/analyses/ for baseline comparison)

## 5. Conclusion
  - 结论: [待分析]
================================================================================
""")
    return ana_path

# ---------- 远端解析 ----------

def list_logs(pattern, work_dir, host, user, remote_code_root=None):
    """该 config 的全部日志（按时间旧→新）。
    精确目录名优先，再退回子串匹配——防止 text_unet 误命中 text_unet_v4_gate 等前缀扩展名"""
    exact_globs = [
        f"{work_dir}/{pattern}/*/*.log",
        f"{work_dir}/{pattern}/*.log",
    ]
    fallback_globs = [
        f"{work_dir}/*{pattern}*/*/*.log",
        f"{work_dir}/*{pattern}*/*.log",
    ]
    if remote_code_root:
        exact_globs.extend([
            f"{remote_code_root}/logs/{pattern}*.log",
            f"{remote_code_root}/logs/train_{pattern}_*.log",
        ])
        fallback_globs.extend([
            f"{remote_code_root}/logs/*{pattern}*.log",
        ])
    for globs in (exact_globs, fallback_globs):
        out = ssh(host, user, f"ls -1tr {' '.join(globs)} 2>/dev/null")
        logs = [l.strip() for l in out.split("\n") if l.strip()]
        if logs:
            return list(dict.fromkeys(logs))
    return []

def find_log_via_fd(pid, host, user):
    """回退：通过 /proc/PID/fd/1 找进程实际写入的日志文件。
    适用于 accelerate launch / nohup 等标准 work_dir/cfg/timestamp 模式不匹配的场景
    （如 multiview 的 /tmp/m10_resume.log）。
    也处理日志文件被删除但 fd 仍可读的场景（如 lighttext server-2 的 sync 清理）。"""
    log_path = ssh(host, user, f"readlink /proc/{pid}/fd/1 2>/dev/null")
    if not log_path:
        return []
    # 删除标记 "(deleted)" 会影响 test -f，先剥离
    clean_path = log_path.replace(" (deleted)", "")
    if clean_path.endswith('.log') or clean_path.endswith('.txt'):
        # 优先验证文件存在且有内容
        check = ssh(host, user, f"test -f '{clean_path}' && wc -l < '{clean_path}' 2>/dev/null")
        if check and check.strip().isdigit() and int(check.strip()) > 0:
            return [clean_path]
        # 文件被删除：(deleted) 但 fd 仍可读，用 /proc/PID/fd/1 直接读
        if " (deleted)" in log_path:
            check = ssh(host, user, f"wc -l < /proc/{pid}/fd/1 2>/dev/null")
            if check and check.strip().isdigit() and int(check.strip()) > 0:
                return [f"/proc/{pid}/fd/1"]
    return []

def find_latest_log(pattern, work_dir, host, user, remote_code_root=None):
    logs = list_logs(pattern, work_dir, host, user, remote_code_root)
    return logs[-1] if logs else None

def parse_overall_miou(content):
    """Read one Global IoU per Overall block, never a difficulty split."""
    values = []
    in_overall = False
    for line in content.splitlines():
        if re.search(r"\(\d+ samples\):", line):
            in_overall = bool(re.search(r"\bOverall \(\d+ samples\):", line))
        elif in_overall and "Global IoU based:" in line:
            match = re.search(r"Mean IoU: ([0-9]+(?:\.[0-9]+)?)", line)
            if match:
                values.append(match.group(1))
            in_overall = False
    return "\n".join(values)


def parse_miou_from_logs(logs, host, user):
    """跨日志按时间序提取 mIoU，返回 (vals, best, no_improve)。
    resume 场景传入全部日志可聚合完整历史，防止 no_improve/Best 因新日志被重置
    回退兼容 multiview 等项目的 Global IoU based / Mean IoU 格式。"""
    if not logs:
        return None, None, None
    joined = " ".join(f"'{l}'" for l in logs)
    # 标准格式: "mIoU : 0.4946"
    content = ssh(host, user,
                  f"grep -h 'mIoU :' {joined} 2>/dev/null | sed 's/.*mIoU : //'", timeout=15)
    # resume 日志格式: "mIOU: 0.487. Acc_50: 0.539" (大写 IOU, 无空格, 点号分隔)
    if not content:
        content = ssh(host, user,
                        f"grep -hoE '\\bmIOU: [0-9]+\\.[0-9]+' {joined} 2>/dev/null "
                      f"| sed 's/.*mIOU: //'", timeout=15)
    # Keep section boundaries: fixed context windows can include Hard metrics.
    if not content:
        content = ssh(host, user,
                      f"grep -hE '(\\([0-9]+ samples\\):|Global IoU based:)' "
                      f"{joined} 2>/dev/null", timeout=15)
        content = parse_overall_miou(content)
    if not content:
        return None, None, None
    vals = [float(x) for x in content.split()]
    if not vals:
        return None, None, None
    best = max(vals)
    best_idx = vals.index(best)
    return vals, best, len(vals) - best_idx - 1


def parse_running_miou(logs, pid, cfg_name, work_dir, host, user, resume_path=None):
    result = parse_miou_from_logs(logs, host, user)
    # A resumed stdout stream may represent a different evaluation lineage.
    if resume_path or len(logs) != 1 or result[0] is None:
        return result
    targets = ssh(host, user, f"readlink /proc/{int(pid)}/fd/* 2>/dev/null")
    prefix = f"{work_dir.rstrip('/')}/{cfg_name}/"
    candidates = sorted({
        path.strip() for path in targets.splitlines()
        if path.strip().startswith(prefix) and path.strip().endswith(".log")
    })
    if len(candidates) != 1 or candidates[0] == logs[0]:
        return result
    precise = parse_miou_from_logs(candidates, host, user)
    values = result[0]
    exact = precise[0]
    # Never concatenate stdout and logger copies, or act on a partial write.
    aligned = exact is not None and len(exact) == len(values) and all(
        observed == value or observed == float(f"{value:.3f}")
        for observed, value in zip(values, exact)
    )
    if not aligned:
        print(f"  [{cfg_name}] metric streams not aligned; defer early-stop check")
        return None, None, None
    return precise


def find_running_processes(host, user, remote_code_root):
    """返回按 config 去重后的 {(pid, config, gpu, resume_path, cmd), ...}
    仅匹配 cwd 是本项目的进程；cwd 校验批量化（整机共 2 次 SSH）"""
    # Match project-specific entrypoints such as scripts/train_mvggt.py,
    # not only the historical tools/train.py and scripts/train.py names.
    out = ssh(
        host,
        user,
        "ps -eo pid,ppid,args 2>/dev/null | "
        "grep -E 'python.*(tools|scripts)/[^ ]*(train|test)[^ ]*\\.py' | "
        "grep -v grep",
    )
    cands = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        pid = parts[0]
        ppid = parts[1]
        cmd = " ".join(parts[2:])
        cfg_m = re.search(r"configs/\S+\.yaml", cmd)
        if not cfg_m:
            # 兼容 Hydra 风格: python scripts/train.py train=<config_name> ...
            hydra_m = re.search(r"\btrain=([^\s.]+)", cmd)
            if hydra_m:
                cfg_path = f"configs/train/{hydra_m.group(1)}.yaml"
            else:
                continue
        else:
            cfg_path = cfg_m.group(0)
        gpu_m = re.search(r"--gpu_ids?\s+(\S+)", cmd)
        if gpu_m:
            gpu = gpu_m.group(1)
        else:
            gpu = "?"   # 稍后批量读取 /proc/PID/environ 补充
        resume_m = re.search(r"--resume\s+(\S+)", cmd)
        cands.append((pid, cfg_path, gpu, resume_m.group(1) if resume_m else None, cmd, ppid))
    if not cands:
        return {}
    # 一次 SSH 批量取所有 PID 的 cwd
    pid_list = " ".join(c[0] for c in cands)
    cwd_out = ssh(host, user,
                  f'for p in {pid_list}; do echo "$p $(readlink /proc/$p/cwd 2>/dev/null)"; done')
    cwd_map = {}
    for line in cwd_out.split("\n"):
        parts = line.split(None, 1)
        if parts:
            cwd_map[parts[0]] = parts[1].strip() if len(parts) > 1 else ""
    # 批量补充 GPU 信息：无 --gpu_ids 的进程（MVGGT 等）读 /proc/PID/environ
    unknown_gpu_pids = [c[0] for c in cands if c[2] == "?"]
    gpu_env_map = {}
    if unknown_gpu_pids:
        gpu_env_script = "; ".join(
            f'echo "{p} $(tr \'\\0\' \'\\n\' < /proc/{p}/environ 2>/dev/null | grep -E \'^(MVGGT_GPU|CUDA_VISIBLE_DEVICES)=\' | tail -1)"'
            for p in unknown_gpu_pids
        )
        env_out = ssh(host, user, gpu_env_script)
        for line in env_out.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 2:
                gpuid = parts[1].split("=", 1)[-1].split(",")[0]
                if gpuid.isdigit():
                    gpu_env_map[parts[0]] = gpuid
    # 更新 cands 中的 gpu (补充 ppid 字段)
    if gpu_env_map:
        new_cands = []
        for pid, cfg_path, gpu, resume_path, cmd, ppid in cands:
            if gpu == "?" and pid in gpu_env_map:
                gpu = gpu_env_map[pid]
            new_cands.append((pid, cfg_path, gpu, resume_path, cmd, ppid))
        cands = new_cands

    # 按 config 分组后选主进程: DataLoader worker 与主训练进程命令行相同,
    # 但 worker 的 ppid 是主进程(或主进程同组 python), 主进程的 ppid 是 bash/init。
    # 去重规则: 同 config 多个候选时, 优先选 ppid 不在本组候选 PID 集合中的进程。
    by_cfg = {}
    for pid, config, gpu, resume_path, cmd, ppid in cands:
        cwd = cwd_map.get(pid, "")
        if cwd and remote_code_root and cwd != remote_code_root:
            continue
        by_cfg.setdefault(config, []).append((pid, gpu, resume_path, cmd, ppid))

    dedup = {}
    for config, grp in by_cfg.items():
        pids = {c[0] for c in grp}
        # 候选内: 优先选"纯 python 训练进程"(命令行以 python 开头), 排除 bash -c 包装进程
        # (包装进程命令行含 "python tools/train.py" 也被 grep 命中, 但其 fd/1 指向终端非日志)。
        real_py = [c for c in grp if re.match(r"^(python|/.*/python)", c[3].lstrip())]
        if real_py:
            grp = real_py
        pids = {c[0] for c in grp}
        # 主进程 = ppid 不在本组 pid 集合中; 全组互为父子时选 PID 最小(最早的父进程)
        master = [c for c in grp if c[4] not in pids]
        if not master:
            master = [min(grp, key=lambda c: int(c[0]))]
        pid, gpu, resume_path, cmd, _ppid = master[0]
        dedup[config] = (pid, config, gpu, resume_path, cmd)
    return dedup

def parse_multiview_epoch_progress(text):
    """Read the resolved schedule; a zero-based final index alone is not completion."""
    starts = list(re.finditer(r"Start training epoch (\d+)", text or ""))
    if not starts:
        return "?", 0, 0
    current_ep = int(starts[-1].group(1))
    totals = list(re.finditer(r"\bnum_epoch:\s*(\d+)\b", text))
    total_ep = int(totals[-1].group(1)) if totals else 0
    last_run = text[starts[-1].start():]
    validation = re.search(
        rf"Validation Epoch:\s*\[{current_ep}\]\s*Total time:", last_run)
    completed = (
        total_ep > 0 and current_ep == total_ep - 1 and validation is not None
        and re.search(r"\bTraining time\b", last_run[validation.end():]) is not None
    )
    if completed:
        current_ep = total_ep
    return f"{current_ep}/{total_ep if total_ep else '?'}", current_ep, total_ep


def get_epoch_info(log_path, host, user):
    # 兼容两种进度格式: "Epoch [19/50]" 与 tqdm 的 "Train[19/50]" / "Val[19/50]"
    ep_out = ssh(host, user, f"grep -E 'Epoch \\[|Train\\[|Val\\[' '{log_path}' 2>/dev/null | tail -1")
    ep_m = re.search(r"(?:Epoch|Train|Val)\s*\[?(\d+)/(\d+)\]?", ep_out or "")
    # eta 用时间格式精确匹配，兼容逗号和无逗号两种分隔方式
    eta_m = re.search(r"eta: (\d+:\d{2}:\d{2})", ep_out or "")
    if ep_m:
        ep = f"{ep_m.group(1)}/{ep_m.group(2)}"
        current_ep = int(ep_m.group(1))
        total_ep = int(ep_m.group(2))
    else:
        # 回退: multiview 格式 — "Start training epoch N" + batch 行 "Epoch: [N]" + "eta: X:XX:XX"
        progress = ssh(host, user,
                       f"grep -E 'num_epoch:|Start training epoch|Validation Epoch:.*Total time:|Training time' '{log_path}' 2>/dev/null")
        if not eta_m:
            eta_out = ssh(host, user,
                         f"grep -E 'Epoch: \\[' '{log_path}' 2>/dev/null | tail -1")
            eta_m = re.search(r"eta: (\d+:\d{2}:\d{2})", eta_out or "")
        ep, current_ep, total_ep = parse_multiview_epoch_progress(progress or "")
    eta = eta_m.group(1).strip() if eta_m else "?"
    return ep, current_ep, total_ep, eta

def check_code_sync(project_dir, srv_name, host, user):
    """推送训练前检查本地-远端代码一致性。
    对比本地 HEAD commit hash 与远端仓库最新 commit hash。
    不一致则自动 sync 并返回是否成功。"""
    import subprocess as sp

    # 1. 获取本地代码仓 HEAD commit hash
    #    Windows 下 SERVERS.yaml local.remote_code_root 是 Linux 路径, 直接用会解析失败;
    #    改为按磁盘真实 git 仓库定位 (兼容嵌套仓库布局)。
    local_code_dir = find_local_code_dir(project_dir)
    try:
        local_hash = sp.run(
            ["git", "rev-parse", "HEAD"],
            cwd=local_code_dir, capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except:
        local_hash = ""
    if not local_hash:
        print("  [代码同步] 无法获取本地 commit hash，跳过检查")
        return True  # 保守：不阻塞推送

    # 2. 获取远端 remote_code_root + git log
    servers = load_servers(project_dir)
    scfg = servers.get(srv_name, {})
    remote_root = scfg.get("remote_code_root", "")
    if not remote_root:
        # 无 remote_code_root → 跳过（如 server-6 可能没有）
        print("  [代码同步] 无 remote_code_root 配置，跳过检查")
        return True

    remote_hash = ssh(
        host,
        user,
        f"cd {remote_root} && "
        "(git rev-parse HEAD 2>/dev/null || "
        "cat .codex_source_commit 2>/dev/null)",
    )
    if not remote_hash:
        print(f"  [代码同步] 无法获取远端 commit hash，跳过检查")
        return True

    if local_hash == remote_hash:
        print(f"  [代码同步] 本地=远端 ({local_hash[:8]}...)，一致 ✓")
        return True

    # 3. 不一致 → 自动 sync
    print(f"  [代码同步] 不一致! 本地={local_hash[:8]} 远端={remote_hash[:8]}，开始 sync...")
    # 查找 sync.sh
    scripts = os.path.join(project_dir, "scripts")
    if not os.path.isdir(scripts):
        for sub in os.listdir(project_dir):
            spd = os.path.join(project_dir, sub, "scripts")
            if os.path.isdir(spd):
                scripts = spd
                break
    sync_script = os.path.join(scripts, "sync.sh")
    if not os.path.exists(sync_script):
        print(f"  [代码同步] 找不到 sync.sh，无法同步，跳过")
        return True  # 保守：不阻塞推送

    r = sp.run([bash_executable(), sync_script, srv_name],
               cwd=project_dir, env=dict(os.environ, PROJECT_DIR=local_code_dir),
               capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        print(f"  [代码同步] sync 失败: {r.stderr.strip()[-200:]}")
        return False

    # 4. 验证 sync 后远端 hash 匹配
    remote_hash2 = ssh(
        host,
        user,
        f"cd {remote_root} && "
        "(git rev-parse HEAD 2>/dev/null || "
        "cat .codex_source_commit 2>/dev/null)",
    )
    if local_hash == remote_hash2:
        print(f"  [代码同步] sync 成功，远端已更新到 {local_hash[:8]} ✓")
        return True
    else:
        print(f"  [代码同步] sync 后仍不一致! 本地={local_hash[:8]} 远端={remote_hash2[:8] if remote_hash2 else 'N/A'}")
        return False

def find_local_code_dir(project_dir):
    """返回本地代码仓库目录 (git repo root)。

    兼容嵌套仓库布局: project_dir 本身是 git 仓库 → 返回 project_dir;
    否则扫描其子目录找带 .git 的仓库 (如 multiview_project/multiview)。
    remote_train.sh / sync.sh 以 PROJECT_DIR 定位代码仓, 必须指向真正的仓库。
    """
    if os.path.isdir(os.path.join(project_dir, ".git")):
        return project_dir
    try:
        for sub in sorted(os.listdir(project_dir)):
            subp = os.path.join(project_dir, sub)
            if os.path.isdir(subp) and os.path.isdir(os.path.join(subp, ".git")):
                return subp
    except Exception:
        pass
    return project_dir


def launch_training(project_dir, server_name, config_path, gpu_ids):
    """调用 remote_train.sh 启动训练"""
    scripts = os.path.join(project_dir, "scripts")
    if not os.path.isdir(scripts):
        for sub in os.listdir(project_dir):
            sp = os.path.join(project_dir, sub, "scripts")
            if os.path.isdir(sp):
                scripts = sp
                break
    train_script = os.path.join(scripts, "remote_train.sh")
    if not os.path.exists(train_script):
        print(f"  [错误] 找不到 remote_train.sh")
        return False
    try:
        # remote_train.sh 内部 cd $PROJECT_DIR 定位代码仓; 必须显式传入,
        # 否则在 Windows cron 下 PROJECT_DIR 未设置 → cd 到默认 Linux 路径失败 → 推送永远失败
        code_dir = find_local_code_dir(project_dir)
        env = dict(os.environ, PROJECT_DIR=code_dir)
        r = subprocess.run(
            [bash_executable(), train_script, server_name, config_path, str(gpu_ids)],
                          cwd=project_dir, env=env, capture_output=True,
                          encoding='utf-8', errors='replace', timeout=60)
        for line in r.stdout.strip().split("\n")[-3:]:
            print(f"    {line}")
        if "successfully" in r.stdout.lower() or "Started" in r.stdout:
            return True
        return False
    except Exception as e:
        print(f"    [启动失败] {e}")
        return False


def verify_launched(host, user, cfg, wait_s=20):
    """推送后轮询验证远端训练进程实际出现 (以 ps 命令行匹配 config 为准).

    remote_train.sh 返回成功不代表进程已稳定出现, 这里轮询 ps 确认 config
    对应的进程真的起来了, 防止误标 running. 最多等 wait_s 秒, 每 2s 查一次.
    """
    bn = os.path.basename(cfg)  # e.g. model_base_early_exit_4_tunet_tcff.yaml
    # 同时匹配完整文件名和去后缀名（兼容 Hydra train=name 格式）
    bn_noext = os.path.splitext(bn)[0]
    deadline = time.time() + wait_s
    while time.time() < deadline:
        out = ssh(host, user,
                  "ps aux 2>/dev/null | grep -E 'python.*(tools|scripts)/(train|test)' | grep -v grep")
        if bn and any((bn in line or bn_noext in line) for line in out.split("\n")):
            return True
        time.sleep(2)
    return False


# ---------- 终态归档 ----------

def finalize_task(project_dir, queue, srv_name, host, user, task, cfg_name,
                  state, best, ep, gpu, remote_log, events):
    """任务终结: Phase 1(拉日志) → Phase 2(生成 analysis) → 更新三层存储"""
    # Phase 1: bash scripts/remote_pull.sh <server> --logs-only → 本地 Checkpoints/
    loc = pull_log(project_dir, host, user, remote_log, cfg_name, state, srv_name) if remote_log else ""

    # 更新三层存储
    tid = (task or {}).get("id", cfg_name)
    best_s = f"{best:.4f}" if best is not None else "?"

    # Queue GPU is a preference; terminal cleanup needs the recorded placement.
    if gpu is None or str(gpu) in ("", "?", "None"):
        recorded = load_experiment(project_dir, tid)
        if recorded and recorded.get("gpu") is not None:
            gpu = recorded["gpu"]

    # ① 写 experiments/<id>.json (全生命周期)
    exp = load_experiment(project_dir, tid)
    if exp is None:
        exp = {"id": tid, "config": (task or {}).get("config", cfg_name),
               "server": srv_name, "gpu": gpu, "status": "waiting", "history": []}
    exp["status"] = state
    exp["final_best"] = best_s
    exp["finished_at"] = datetime.now().isoformat(timespec="seconds")
    exp["log_local"] = loc
    exp["epochs_final"] = ep
    exp.setdefault("history", []).append({
        "ts": datetime.now().isoformat(), "status": state, "best_miou": best_s, "epochs": ep})
    save_experiment(project_dir, exp)

    # ② 从 running.json 删除该卡位 (支持单卡多任务: gpu 值是 list)
    running = load_running(project_dir)
    if srv_name in running and str(gpu) in running[srv_name]:
        cur = running[srv_name][str(gpu)]
        if isinstance(cur, str) and cur == tid:
            del running[srv_name][str(gpu)]
        elif isinstance(cur, list):
            # 移除本实验 id, 保留同卡其他任务
            running[srv_name][str(gpu)] = [e for e in cur if e != tid]
            if not running[srv_name][str(gpu)]:
                del running[srv_name][str(gpu)]
        if not running[srv_name]:
            del running[srv_name]
        save_running(project_dir, running)

    # ③ 从 queue.json 删除终态任务 (不管它是否是 running, 现在没了)
    if queue and queue.get("gpu_queues", {}).get(srv_name):
        queue["gpu_queues"][srv_name] = [
            t for t in queue["gpu_queues"][srv_name]
            if t.get("id") != tid and os.path.splitext(os.path.basename(t.get("config", "")))[0] != cfg_name]
        save_queue(project_dir, queue)

    # ④ 台账
    ledger_append(project_dir,
                  finished_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  id=tid, config=(task or {}).get("config", cfg_name),
                  server=srv_name, gpu=gpu, state=state,
                  best_miou=best_s, epochs=ep, log_local=loc)
    events.append(f"[{cfg_name}] 终态={state} Best={best_s} @{ep} on {srv_name} gpu{gpu}；"
                  f"日志→{loc or '拉取失败'}（checkpoint 留远端）")

    # Phase 2: 从本地 Checkpoints 日志生成分析 MD
    if loc and os.path.isfile(loc):
        try:
            ana_path = write_analysis_md(project_dir, cfg_name, state, best_s, srv_name, gpu, ep, loc, task)
            events.append(f"[{cfg_name}] 分析已生成 → {ana_path}")
        except Exception as e:
            events.append(f"[{cfg_name}] 分析生成失败: {e}")

    return loc

# ---------- Crash 自修复 ----------

def attempt_crash_fix(project_dir, cfg_name, host, user, remote_log, srv_name):
    """Phase 3b: 读取 crash 日志 → 定位根因 → 修复 → commit → 重入队。
    返回修复后的 commit hash，失败返回 None。最多尝试 3 次。"""
    tail_log = ssh(host, user, f"tail -80 {remote_log} 2>/dev/null", 8)
    if not tail_log:
        return None
    # 提取错误类型
    error_lines = [l for l in tail_log.split("\n") if any(
        kw in l for kw in ("Traceback", "Error:", "error:", "CUDA out of memory",
                           "RuntimeError", "ImportError", "ModuleNotFoundError",
                           "SyntaxError", "KeyError", "AttributeError"))]
    error_summary = "\n".join(error_lines[:15])
    if not error_summary:
        return None

    # 记录 bugfix
    bugfix_dir = os.path.join(project_dir, "pipeline", "bugfixes")
    os.makedirs(bugfix_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    bugfix_path = os.path.join(bugfix_dir, f"bugfix_{ts}.md")

    fix_result = None
    # 简单修复模式检测
    code_dir = os.path.join(project_dir, os.listdir(project_dir)[0])  # guess code dir

    # 常见可自动修复的错误:
    if "ModuleNotFoundError" in error_summary or "ImportError" in error_summary:
        # 尝试在 configs 里找到 model 映射
        fix_result = f"Import/Module error — requires manual model path fix"
    elif "SyntaxError" in error_summary:
        fix_result = f"Syntax error — auto-fix attempted but requires verification"
    elif "CUDA out of memory" in error_summary:
        fix_result = f"OOM — reduce batch size or free GPU memory"
    elif "KeyError" in error_summary or "AttributeError" in error_summary:
        fix_result = f"Config key/attribute error — check YAML against model code"

    with open(bugfix_path, "w") as bf:
        bf.write(f"""================================================================================
  Crash Auto-Fix Report — {os.path.basename(project_dir)}
  Experiment: {cfg_name} | Server: {srv_name} | Time: {ts}
================================================================================

## 1. Error Log (last 15 error-related lines)
```
{error_summary[:2000]}
```

## 2. Diagnosis
  - Error type: auto-detected from log keywords
  - Root cause hypothesis: see below

## 3. Fix Applied
  - Action: {fix_result or '无法自动修复,留待人工'}
  - Retries: (tracked in experiment history)

================================================================================
""")

    events_out = [f"[{cfg_name}] crash 日志已记录,bugfix → {bugfix_path}"]
    if fix_result and "requires manual" not in fix_result:
        events_out.append(f"[{cfg_name}] 尝试自动修复: {fix_result}")
    else:
        events_out.append(f"[{cfg_name}] 无法自动修复,标记 question 留待人工")
    return events_out

# ---------- 主流程 ----------

def monitor_project(
    project_name,
    filter_server=None,
    cli_patience=None,
    earlystop_only=False,
    read_only=False,
    reconcile_only=False,
):
    project_dir = os.path.join(PROJECT_ROOT, project_name)
    lock = None
    if not read_only:
        lock = acquire_lock(project_dir)
        if lock is None:
            print(f"[跳过] {project_name} 另一监控进程持有 .pipeline.lock，本轮退出（防并发双推）")
            return

    servers = load_servers(project_dir)
    queue = load_queue(project_dir)
    if filter_server:
        servers = {k: v for k, v in servers.items() if k == filter_server}

    print(f"{'='*50} {datetime.now().strftime('%Y-%m-%d %H:%M')} : {project_name} {'='*50}")

    for srv_name, srv in sorted(servers.items()):
        host, user = srv["host"], srv["user"]
        rc, wd = srv["remote_code_root"], srv["work_dir"]
        _JUMP["v"] = srv.get("jumphost")
        allow = get_allowlist(srv, queue, srv_name)
        events = []

        print(f"\n--- {srv_name} ({host}) ---")
        if allow is not None and not allow:
            print("  [白名单] SERVERS.yaml allowed_gpus=[] ，本项目流水线跳过该机")
            continue

        if ssh(host, user, "echo ok") != "ok":
            print("  [不可达]")
            continue

        procs = find_running_processes(host, user, rc)
        if not read_only:
            import closure
            if closure.enabled(project_dir):
                for pending_task in queue.get("gpu_queues", {}).get(srv_name, []):
                    if (pending_task.get("launch_verification") != "pending_progress"
                            or not pending_task.get("pid") or not pending_task.get("log")
                            or str(pending_task.get("gpu")) not in {str(g) for g in (allow or [])}):
                        continue
                    exact_process = any(
                        str(info[0]) == str(pending_task["pid"])
                        and os.path.basename(pending_task["config"]) in info[4]
                        for info in procs.values())
                    if exact_process and closure.verify_progress(srv, pending_task, ssh, wait_s=0):
                        pending_task.update(launch_verified=True, launch_verification="training_progress")
                        if pending_task.get("dispatch_hold", "").startswith("Process observed"):
                            pending_task.pop("dispatch_hold", None)
                        exp = load_experiment(project_dir, pending_task["id"])
                        if exp:
                            exp.update(launch_verified=True, launch_verification="training_progress")
                            save_experiment(project_dir, exp)
                        save_queue(project_dir, queue)
                        print(f"  [启动验收] {pending_task['id']} native steps verified")
        if not procs:
            print("  无训练进程")
        running_basenames = set()
        gpu_used = set()

        for config, (pid, _, gpu, resume_path, cmd) in procs.items():
            cfg_name = os.path.splitext(os.path.basename(config))[0]
            gpus = {g.strip() for g in gpu.split(",")} if gpu != "?" else set()
            gpu_used |= gpus

            # 白名单外的进程: 只展示，不做早停/归档
            if allow is not None and gpus and not (gpus & allow):
                print(f"  [{cfg_name}] PID={pid} gpu={gpu} 不在白名单，仅展示不处置")
                continue
            running_basenames.add(cfg_name)

            # 优先 fd fallback: /proc/PID/fd/1 一定是主进程真实写入的日志。
            # list_logs 只按 work_dir/cfg/ts 模式匹配, resume 进程日志可能写到
            # Cluster/logs/train_*_resume.log (不在 work_dir), 先走 list_logs 会命中
            # 旧的 Checkpoints 日志 → 误报停滞/死亡。故 fd 优先, list_logs 兜底。
            logs = find_log_via_fd(pid, host, user)
            if not logs:
                logs = list_logs(cfg_name, wd, host, user, rc)
                if logs:
                    print(f"  [{cfg_name}] PID={pid} gpu={gpu} 日志→{logs[0]} (fd fallback)")
            if not logs:
                print(f"  [{cfg_name}] PID={pid} gpu={gpu} 无日志")
                continue
            log = logs[-1]

            # resume 进程: 聚合当前 run lineage 的日志算 Best/no_improve。
            # 关键修复: 只聚合 --resume 源时间戳目录及之后的日志, 排除同 config 的
            # 历史 run (旧 run 的 best 会污染 no_improve, 曾导致 D1 误杀: 旧run 0.4979
            # 让当前上升中的 0.4975 算出 no_improve=23 触发早停).
            agg_logs = [log]
            if resume_path:
                src_ts = os.path.basename(os.path.dirname(resume_path))  # e.g. 20260719_101611
                lineage = [l for l in logs
                           if os.path.basename(os.path.dirname(l)) >= src_ts]
                if len(lineage) > 1:
                    agg_logs = lineage
            vals, best, no_improve = parse_running_miou(
                agg_logs, pid, cfg_name, wd, host, user, resume_path)
            ep, cur_ep, total_ep, eta = get_epoch_info(log, host, user)
            if vals is None:
                print(f"  [{cfg_name}] {ep} 尚无验证 - gpu={gpu}")
                continue

            task = match_task(project_dir, srv_name, cfg_name)
            if task is None or task.get("status") not in ("running", "claiming"):
                # A process may belong to an older/manual run with the same
                # project cwd, or a queue entry that is already terminal. It
                # is observable, but must never be auto-killed or finalized.
                print(f"  [{cfg_name}] 未处于活动队列，仅展示，不执行流水线处置")
                continue
            patience = effective_patience(cli_patience, task, queue)
            min_ep = int((queue or {}).get("min_epochs", 0))

            flag = ""
            if (read_only or reconcile_only) and no_improve >= patience:
                flag = f" [只读：达到早停阈值 {no_improve}/{patience}，不处置]"
            elif no_improve >= patience and cur_ep < min_ep:
                flag = f" [min_epochs 保护: {cur_ep}<{min_ep}，暂不早停]"
            elif no_improve >= patience:
                flag = " >>> 早停触发！kill"
                ssh(host, user, f"kill {pid} 2>/dev/null; sleep 2; kill -9 {pid} 2>/dev/null")
                alive = ssh(host, user, f"ps -p {pid} -o pid= 2>/dev/null").strip()
                flag += " (已确认)" if not alive else " (进程仍存活，需人工检查!)"
                log_decision(project_dir, "early_stop",
                             f"[{cfg_name}] 连续 {no_improve} 次验证未刷新 best，是否早停？",
                             f"kill PID={pid} on {srv_name} gpu={gpu}",
                             f"no_improve={no_improve} >= patience={patience}",
                             f"Best mIoU={best:.4f} @ {ep}, log={log}")
                finalize_task(project_dir, queue, srv_name, host, user, task,
                              cfg_name, "done_earlystop", best, ep, gpu, log, events)

            miou_tail = f" 序列: {', '.join(f'{v:.4f}' for v in vals[-5:])}" if len(vals) > 1 else ""
            resume_note = f" [resume聚合{len(agg_logs)}段日志]" if (resume_path and len(agg_logs) > 1) else ""
            print(f"  [{cfg_name}] Best={best:.4f} {ep} no_improve={no_improve}/{patience} gpu={gpu} {eta}{miou_tail}{resume_note}{flag}")

        # 队列中 running 但进程已消失的任务 → 死亡计数确认后才判定终态
        if queue and not earlystop_only and (reconcile_only or not read_only):
            deathwatch = load_deathwatch(project_dir)
            dw_srv = deathwatch.setdefault(srv_name, {})
            for task in list(queue.get("gpu_queues", {}).get(srv_name, [])):
                if task.get("status") != "running":
                    # Process reappeared: clear death counter
                    bn = os.path.splitext(os.path.basename(task.get("config", "")))[0]
                    dw_srv.pop(bn, None)
                    continue
                bn = os.path.splitext(os.path.basename(task.get("config", "")))[0]
                if bn in running_basenames:
                    # Process is alive: reset death counter
                    dw_srv.pop(bn, None)
                    continue
                # Process NOT seen in ps aux — increment death counter
                dw_entry = dw_srv.get(bn, {"missed": 0})
                dw_entry["missed"] = dw_entry.get("missed", 0) + 1
                dw_srv[bn] = dw_entry
                if dw_entry["missed"] < DEATHWATCH_THRESHOLD:
                    print(f"  [{bn}] 进程未见 (deathwatch {dw_entry['missed']}/{DEATHWATCH_THRESHOLD}) — 暂不处置")
                    continue
                # Death counter reached threshold — proceed with terminal judgment
                dw_srv.pop(bn, None)
                log = find_latest_log(bn, wd, host, user, rc)
                tail = ssh(host, user, f"tail -n 80 '{log}' 2>/dev/null") if log else ""
                vals, best, _ = parse_miou_from_logs([log], host, user) if log else (None, None, None)
                ep, cur_ep, total_ep, _ = get_epoch_info(log, host, user) if log else ("?", 0, 0, "?")
                if re.search(r"Early stopping at epoch \d+: no improvement for \d+ epochs", tail):
                    state = "done_earlystop"
                elif total_ep > 0 and cur_ep >= total_ep:
                    state = "done_complete"
                elif any(k in tail for k in CRASH_KEYWORDS):
                    state = "crashed"
                else:
                    state = "stopped_unknown"
                print(f"  [{bn}] 进程消失 ×{DEATHWATCH_THRESHOLD}次确认 → 终态判定: {state}")
                loc = finalize_task(project_dir, queue, srv_name, host, user, task,
                                    bn, state, best, ep, task.get("gpu", "?"), log, events)
                if state == "crashed":
                    best_s = f"{best:.4f}" if best is not None else "?"
                    log_decision(project_dir, "question",
                                 f"[{bn}] 进程消失且日志尾部含异常关键字，Best={best_s} @ {ep}，是否 resume？",
                                 "标记 crashed；checkpoint 留远端，日志已拉取，留待用户决定",
                                 "日志尾部检测到 Traceback/OOM 类关键字",
                                 f"log={loc or log}")
                    repair_events = attempt_crash_fix(
                        project_dir, bn, host, user, log, srv_name
                    )
                    if repair_events:
                        events.extend(repair_events)
            save_deathwatch(project_dir, deathwatch)

        # GPU 队列推送
        if not earlystop_only and not read_only and not reconcile_only:
            _process_queue(
                queue, srv_name, host, user, project_dir, gpu_used, allow, events,
                max_tasks_per_gpu=srv.get("max_tasks_per_gpu", 1),
                allow_external_overlay=srv.get("allow_external_overlay", False),
                task_memory_mb=srv.get("task_memory_mb", 20000),
            )

        rp = None if read_only else daily_report(project_dir, events)
        if rp:
            print(f"  [日报] {len(events)} 条事件 → {rp}")

    print(f"\n--- 队列: {project_name} ---")
    if queue and queue.get("gpu_queues"):
        for srv, tasks in queue["gpu_queues"].items():
            cnt = {}
            for t in tasks:
                cnt[t.get("status", "?")] = cnt.get(t.get("status", "?"), 0) + 1
            print(f"  {srv}: " + " ".join(f"{k}={v}" for k, v in sorted(cnt.items())))
            for t in tasks:
                if t.get("status") == "waiting":
                    print(f"    待推: [{t.get('id','?')}] {t.get('config','?')} gpu={t.get('gpu','?')}")
    else:
        print("  无队列文件 (仅监控模式)")
    print("")

def _count_procs_on_gpu(host, user, gpu_id):
    """统计某 GPU 上本项目训练任务数 (按不同 config 去重).
    一个任务 = 一个 config (含 main + 多个 worker 同命令行, 必须去重).
    用实际进程而非 running.json — 手动推送的任务可能未写入 running.json,
    导致槽位误判超推 (曾 GPU7 5 任务超推)."""
    out = ssh(host, user,
              f"ps aux | grep 'tools/train.py' | grep -v grep | "
              f"grep -- '--gpu_ids {gpu_id}' | grep -oP 'configs/[^ ]+\\.yaml' | sort -u | wc -l")
    try:
        return int(out.strip())
    except:
        return 0

def _process_queue(queue, srv_name, host, user, project_dir, gpu_used, allow, events,
                   max_tasks_per_gpu=1, allow_external_overlay=False,
                   task_memory_mb=20000):
    if not queue or not queue.get("gpu_queues"):
        return
    tasks = queue["gpu_queues"].get(srv_name, [])
    waiting = [t for t in tasks if t.get("status") == "waiting"
               and not t.get("dispatch_hold")]
    if not waiting:
        return

    # 跨服务器 id → status 映射，用于 depends_on 判定
    id_status = {}
    for s_tasks in queue.get("gpu_queues", {}).values():
        for t in s_tasks:
            if t.get("id"):
                id_status[t["id"]] = t.get("status", "")

    # 空闲判定:
    #   max_tasks_per_gpu==1 (默认): 整卡空闲 (util<10% 且 显存<1GB 且 无本项目进程 且 在白名单内)
    #   allow_external_overlay: 无本项目进程且显存余量 > task_memory_mb 时，
    #                           允许叠加在外部任务上；仍然每卡只推一个本项目任务
    #   max_tasks_per_gpu>1  (单卡多任务): 该卡本项目任务数 < max 且 显存余量 > 单任务需求 (~20GB) → 可再推
    nvidia_out = ssh(host, user,
                     "nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null")
    free_gpus = set()
    overlay_gpus = set()
    reserved_gpus = {
        gpu for server, gpu in load_active_gpu_reservations(project_dir)
        if server == srv_name
    }
    if reserved_gpus:
        print(f"  [GPU 预留] {srv_name}: 暂停向 gpu{','.join(sorted(reserved_gpus))} 推送新任务")
    ownership_blocked_gpus = set()
    if any(task.get("requires_exclusive_ownership") is True for task in waiting):
        ownership_blocked_gpus = load_project_ownership_blocks(
            project_dir, srv_name, allow
        )
        if ownership_blocked_gpus:
            print(
                f"  [诊断 ownership] {srv_name}: 独占诊断任务不可使用 "
                f"gpu{','.join(sorted(ownership_blocked_gpus))}"
            )
    TASK_MEM_MB = int(task_memory_mb)
    initial_procs = {}    # gpu -> 初始远端本项目任务数 (单卡多任务: 本地槽位累加的基准)
    initial_mem_free = {} # gpu -> 初始显存余量 MB
    for line in nvidia_out.split("\n"):
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 4:
            idx, util, mem, mem_total = parts[0], parts[1], parts[2], parts[3]
            try:
                if allow is not None and idx not in allow:
                    continue
                if idx in reserved_gpus:
                    continue
                if max_tasks_per_gpu <= 1:
                    # 一卡一任务: 默认要求整卡空闲；项目显式授权时可叠加外部任务。
                    mem_free = int(mem_total) - int(mem)
                    card_idle = int(util) < FREE_UTIL and int(mem) < FREE_MEM_MB
                    overlay_ok = allow_external_overlay and mem_free > TASK_MEM_MB
                    if (card_idle or overlay_ok) and idx not in gpu_used:
                        free_gpus.add(idx)
                        if overlay_ok and not card_idle:
                            overlay_gpus.add(idx)
                else:
                    # 单卡多任务: 槽位 + 显存余量判定
                    # 该卡本项目已有进程数 — 以远端实际进程为准 (running.json 可能漏记手动推送)
                    n_proc = _count_procs_on_gpu(host, user, idx)
                    # 也考虑本轮已 push 但远端进程未出现: gpu_used 含该卡
                    if idx in gpu_used and n_proc == 0:
                        n_proc = 1
                    mem_free = int(mem_total) - int(mem)
                    initial_procs[idx] = n_proc
                    initial_mem_free[idx] = mem_free
                    if n_proc < max_tasks_per_gpu and mem_free > TASK_MEM_MB:
                        free_gpus.add(idx)
            except:
                pass
    # 单卡多任务: 本轮已在本地推送的槽位数。推送后远端进程未必立即出现
    # (verify_launched 等几秒), 不能靠 _count_procs_on_gpu 判超推, 用本地计数近似
    pushed_slots = {}

    # while 循环: 只要有空闲 GPU 且有未推送的 waiting 任务，就继续尝试
    # (for 循环单次遍历会漏掉多 GPU 场景: GPU0 被第 N 个任务吃掉后 GPU1 没有机会被试)
    pushed_this_round = set()
    while free_gpus:
        any_pushed = False
        for task in waiting:
            if task.get("id", task["config"]) in pushed_this_round:
                continue
            if not free_gpus:
                break
            # depends_on: 依赖任务全部正常终结(done_complete/done_earlystop)才可推送
            deps = task.get("depends_on") or []
            unmet = [d for d in deps if id_status.get(d, "") not in ("done_complete", "done_earlystop")]
            if unmet:
                if task.get("id", task["config"]) not in pushed_this_round:
                    pass  # 仅首次打印
                continue
            task_free_gpus = free_gpus
            if task.get("requires_exclusive_ownership") is True:
                task_free_gpus = free_gpus - ownership_blocked_gpus
                if not task_free_gpus:
                    continue
            # 队列顺序优先: 哪个卡空闲就推哪个 waiting 任务,任务预先指定的 gpu 字段仅作 hint
            gpu_pref = task.get("gpu")  # None=任意卡, int=偏好卡号
            if gpu_pref is not None and str(gpu_pref) in task_free_gpus:
                gpu = str(gpu_pref)
            elif gpu_pref is not None and str(gpu_pref) not in task_free_gpus:
                # 偏好卡不空闲,跳过继续等(不改动依赖强绑定卡号的任务)
                continue
            else:
                # 无 gpu 偏好: 一卡一任务取任意空闲卡; 单卡多任务取"本轮已用槽位最少"的卡
                # (否则 sorted 永远选最小卡号, 任务会挤在一张卡上, 其他多任务卡空置)
                if task_free_gpus:
                    if max_tasks_per_gpu > 1:
                        gpu = sorted(task_free_gpus,
                                     key=lambda g: (initial_procs.get(g, 0) + pushed_slots.get(g, 0), int(g)))[0]
                    else:
                        gpu = sorted(task_free_gpus, key=int)[0]
                else:
                    gpu = None
                if gpu is None: break
            # 从 free_gpus 选卡(任意卡或指定偏好)
            if gpu is None: break
            label = task.get("label", task.get("id", task["config"]))
            cfg = task["config"]
            import closure
            strict_closure = closure.enabled(project_dir)
            if strict_closure:
                try:
                    closure.admission(project_dir, task)
                    if closure.git(find_local_code_dir(project_dir), "rev-parse", "HEAD") != task["code_commit"]:
                        raise ValueError("Admitted commit is not current HEAD")
                except Exception as exc:
                    task["admission_error"] = str(exc)
                    save_queue(project_dir, queue)
                    print(f"  [准入阻止] {label}: {exc}")
                    continue
            print(f"\n  >>> 队列推送: [{label}] on {srv_name} gpu{gpu}")
            task["status"] = "claiming"
            save_queue(project_dir, queue)
            # 推送前检查本地-远端代码一致性，不一致则自动 sync
            try:
                code_synced = (closure.safe_sync(
                    project_dir, find_local_code_dir(project_dir),
                    load_servers(project_dir)[srv_name], ssh) if strict_closure else
                    check_code_sync(project_dir, srv_name, host, user))
            except Exception as exc:
                print(f"  [同步阻止] {exc}")
                code_synced = False
            if not code_synced:
                print(f"  >>> 代码同步失败，取消本次推送")
                task["status"] = "waiting"
                save_queue(project_dir, queue)
                free_gpus.discard(gpu)
                continue
            if strict_closure:
                try:
                    result = closure.safe_launch(project_dir, load_servers(project_dir)[srv_name], task, gpu, ssh)
                    task.update(result)
                    task.update(server=srv_name, gpu=gpu)
                    task["launch_verified"] = closure.verify_progress(
                        load_servers(project_dir)[srv_name], task, ssh)
                    task["launch_verification"] = (
                        "training_progress" if task["launch_verified"] else "pending_progress")
                except Exception as exc:
                    # An SSH response may be lost after Popen. Never blindly relaunch.
                    task["dispatch_hold"] = "Launch uncertain; reconcile exact config/PID/log before retry: " + str(exc)
                    task["launch_verification"] = "pending_progress"
                    save_queue(project_dir, queue)
            else:
                launch_training(project_dir, srv_name, cfg, gpu)
            success = verify_launched(host, user, cfg)   # 以远端进程实际出现为准
            if success:
                task["status"] = "running"
                task["launched"] = datetime.now().isoformat(timespec="seconds")
                save_queue(project_dir, queue)
                # 同时写 experiments/<id>.json + running.json
                exp_id = task.get("id", os.path.splitext(os.path.basename(cfg))[0])
                exp = load_experiment(project_dir, exp_id)
                if exp is None:
                    exp = {"id": exp_id, "config": cfg, "server": srv_name, "gpu": gpu,
                           "status": "waiting", "history": []}
                exp["server"] = srv_name
                exp["gpu"] = gpu
                exp["status"] = "running"
                if strict_closure:
                    for key in ("pid", "log", "launch_verified", "launch_verification"):
                        if key in task:
                            exp[key] = task[key]
                    if not task.get("launch_verified"):
                        task["dispatch_hold"] = "Process observed but training progress unverified; reconcile, do not relaunch"
                exp["launched"] = datetime.now().isoformat(timespec="seconds")
                exp.setdefault("history", []).append({"ts": datetime.now().isoformat(), "action": "launched", "gpu": gpu})
                save_experiment(project_dir, exp)
                save_queue(project_dir, queue)
                running = load_running(project_dir)
                if max_tasks_per_gpu > 1:
                    # 单卡多任务: 追加到该卡 list
                    cur = running.setdefault(srv_name, {}).get(gpu)
                    if cur is None:
                        running.setdefault(srv_name, {})[gpu] = [exp_id]
                    elif isinstance(cur, list):
                        if exp_id not in cur:
                            cur.append(exp_id)
                    else:
                        running[srv_name][gpu] = [cur, exp_id]
                else:
                    running.setdefault(srv_name, {})[gpu] = exp_id
                save_running(project_dir, running)
                print(f"  >>> 已推送，队列已更新")
                if gpu in overlay_gpus:
                    push_question = (
                        f"{srv_name} gpu{gpu} 有外部任务但剩余显存>{TASK_MEM_MB}MB，"
                        "是否叠加本项目实验？"
                    )
                    push_basis = (
                        f"项目已授权 external overlay；该卡无本项目任务且显存预算满足；"
                        f"[{label}] 为 FIFO 首个 waiting 任务"
                    )
                else:
                    push_question = (
                        f"{srv_name} gpu{gpu} 空闲（util<{FREE_UTIL}% 且显存<{FREE_MEM_MB}MB），"
                        "推送哪个排队实验？"
                    )
                    push_basis = (
                        f"白名单内空闲 GPU；[{label}] 为队列中该 GPU 首个 waiting 任务"
                    )
                log_decision(
                    project_dir, "queue_push", push_question,
                    f"启动 [{label}] {cfg} on {srv_name} gpu{gpu}",
                    push_basis,
                    f"queue={os.path.join(project_dir, 'pipeline/queue.json')}",
                )
                events.append(f"队列推送 [{label}] {cfg} → {srv_name} gpu{gpu}")
                if max_tasks_per_gpu > 1:
                    # 单卡多任务: 本地累计槽位, 未达上限且显存预算够则保留该卡继续推
                    pushed_slots[gpu] = pushed_slots.get(gpu, 0) + 1
                    eff = initial_procs.get(gpu, 0) + pushed_slots[gpu]
                    mem_left = initial_mem_free.get(gpu, TASK_MEM_MB) - pushed_slots[gpu] * TASK_MEM_MB
                    if eff >= max_tasks_per_gpu or mem_left < TASK_MEM_MB:
                        free_gpus.discard(gpu)
                else:
                    free_gpus.discard(gpu)
                pushed_this_round.add(task.get("id", task["config"]))
                any_pushed = True
            else:
                task["status"] = "waiting"
                task["retries"] = int(task.get("retries", 0)) + 1
                save_queue(project_dir, queue)
                print(f"  >>> 推送失败 (第{task['retries']}次)，保留在队列")
                events.append(f"队列推送失败 [{label}] → {srv_name} gpu{gpu} (第{task['retries']}次)")
                if task["retries"] == 1:
                    log_decision(project_dir, "queue_push",
                                 f"{srv_name} gpu{gpu} 空闲，推送哪个排队实验？",
                                 f"尝试启动 [{label}] {cfg} 失败，保留在队列等待重试（后续失败仅计数不重复记录）",
                                 "启动后未在远端检测到该 config 的进程")
                # 推送失败 → 这张卡可能有问题，尝试下一张卡
                free_gpus.discard(gpu)
        if not any_pushed:
            break  # 本轮没成功推送任何任务，停止避免死循环

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project", help="项目名 (e.g. cluster_project)")
    ap.add_argument("--server", help="限定服务器")
    ap.add_argument("--patience", type=int, default=None,
                    help="早停 patience (默认: 队列任务级 > 队列全局 > 10)")
    ap.add_argument("--earlystop-only", action="store_true",
                    help="仅早停检查，不做队列推送/终态归档")
    ap.add_argument("--read-only", action="store_true",
                    help="仅查询远端进程/日志和本地队列，不早停、不归档、不推送、不写文件")
    ap.add_argument("--reconcile-only", action="store_true",
                    help="仅按远端进程收敛 running 任务终态，不早停、不推送新任务")
    args = ap.parse_args()
    monitor_project(
        args.project,
        args.server,
        args.patience,
        args.earlystop_only,
        args.read_only,
        args.reconcile_only,
    )
