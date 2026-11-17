"""Opt-in, fail-closed research receipts and non-destructive deployment."""
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

GATES = ("diagnosis", "derivation", "literature", "controls", "native_backward",
         "resources", "independence", "constraints")
STAGES = ("diagnosis", "design", "implementation", "validation", "admission",
          "deployment", "training", "rejected", "blocked")


def read(path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default


def enabled(project):
    return read(Path(project) / "pipeline/closure_policy.json", {}).get("enabled") is True


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def artifact(project, entry):
    path = (Path(project) / entry["path"]).resolve()
    if not path.is_relative_to(Path(project).resolve()) or not path.is_file():
        raise ValueError("Missing or out-of-project artifact")
    if digest(path) != entry["sha256"]:
        raise ValueError("Artifact hash mismatch: " + str(path))
    return path


def pending(project):
    data = read(Path(project) / "pipeline/research_work.json", {"candidates": []})
    return [c for c in data["candidates"] if c.get("stage") not in ("training", "rejected")]


def admission(project, task):
    """Evidence is human/agent-reviewed; hashes prove identity, not scientific truth."""
    if not task.get("admission_receipt"):
        raise ValueError("Missing admission receipt")
    receipt_path = (Path(project) / task["admission_receipt"]).resolve()
    if not receipt_path.is_relative_to(Path(project).resolve()):
        raise ValueError("Admission receipt outside project")
    receipt = read(receipt_path, {})
    if receipt.get("id") != task["id"] or receipt.get("config") != task["config"]:
        raise ValueError("Missing or mismatched admission receipt")
    commit = receipt.get("code_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit != task.get("code_commit"):
        raise ValueError("Admission commit mismatch")
    if receipt.get("goal_sha256") != digest(Path(project) / "pipeline/goal.json"):
        raise ValueError("Goal changed since admission")
    for name in GATES:
        gate = receipt.get("gates", {}).get(name, {})
        if gate.get("passed") is not True or not gate.get("evidence"):
            raise ValueError("Incomplete admission gate: " + name)
        for evidence in gate["evidence"]:
            artifact(project, evidence)
    artifact(project, receipt["decision"])
    return receipt


def git(code, *args):
    return subprocess.check_output(["git", "-C", str(code), *args],
                                   text=True, timeout=120).strip()


def safe_sync(project, code, server, ssh):
    """Never stash, clean, reset, auto-commit, or overwrite a diverged checkout."""
    commit = git(code, "rev-parse", "HEAD")
    root = server["remote_code_root"]
    qroot = shlex.quote(root)
    remote = ssh(server["host"], server["user"], f"git -C {qroot} rev-parse HEAD").strip()
    if remote != commit:
        if not re.fullmatch(r"[0-9a-f]{40}", remote):
            raise ValueError("Remote source identity unavailable")
        ref = "refs/heads/codex-admitted-" + commit[:12]
        target = f'{server["user"]}@{server["host"]}:{root}'
        git(code, "push", target, f"{commit}:{ref}")
        ssh(server["host"], server["user"],
            f"git -C {qroot} -c merge.autoStash=false merge --ff-only {ref}")
    if ssh(server["host"], server["user"], f"git -C {qroot} rev-parse HEAD").strip() != commit:
        raise ValueError("Remote fast-forward verification failed")
    return True


def safe_launch(project, server, task, gpu, ssh):
    """Return PID and unique log; never invoke legacy remote_train.sh."""
    root = server["remote_code_root"]
    config = task["config"]
    if not re.fullmatch(r"[0-9]+", str(gpu)):
        raise ValueError("Only single GPU launch is supported")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = f"{root}/logs/train_{Path(config).stem}_{timestamp}.log"
    # Only this candidate's deployment paths are transformed.
    local = read(Path(project) / "pipeline/closure_policy.json", {})["path_mappings"]
    mappings = [(item["source"], server[item["server_key"]].rstrip("/")) for item in local]
    program = f"""
import json,os,pathlib,subprocess,yaml
root=pathlib.Path({root!r})
cfg={config!r}
p=(root/cfg).resolve()
assert p.is_relative_to(root.resolve()) and p.is_file()
for cmdfile in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
    try: cmd=cmdfile.read_bytes().split(b'\\0')
    except OSError: continue
    if b'tools/train.py' in cmd and cfg.encode() in cmd:
        raise RuntimeError('Candidate already running; reconcile before retry')
def adapt(x):
    if isinstance(x,dict): return {{k:adapt(v) for k,v in x.items()}}
    if isinstance(x,list): return [adapt(v) for v in x]
    if isinstance(x,str):
        for a,b in {mappings!r}: x=x.replace(a,b)
    return x
c=adapt(yaml.safe_load(p.read_text()))
assert pathlib.Path(c['model']['data_root']).is_dir()
assert pathlib.Path(c['train']['pretrain']).is_file()
p.write_text(yaml.safe_dump(c,sort_keys=False))
env=os.environ.copy()
env['PYTHONPATH']=str(root)+':'+str(root/'framework/lib')+':'+env.get('PYTHONPATH','')
env['LD_LIBRARY_PATH']=env['CONDA_PREFIX']+'/lib:'+env['CONDA_PREFIX']+'/lib/python3.10/site-packages/torch/lib:'+env.get('LD_LIBRARY_PATH','')
(root/'logs').mkdir(exist_ok=True)
with open({log!r},'ab',buffering=0) as out:
    proc=subprocess.Popen(['python','tools/train.py',cfg,'--gpu_ids',{str(gpu)!r},'--num_gpus','1'],
        cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
(root/'logs'/('.pid_'+pathlib.Path(cfg).stem)).write_text(str(proc.pid))
print(json.dumps(dict(pid=proc.pid,log={log!r})))
"""
    cmd = (f"source {shlex.quote(server['conda_source'])} && "
           f"conda activate {shlex.quote(server['conda_env'])} && python -c {shlex.quote(program)}")
    result = json.loads(ssh(server["host"], server["user"], cmd))
    if not isinstance(result.get("pid"), int) or result.get("log") != log:
        raise ValueError("Invalid launch response; reconcile remote before retry")
    return result


def steps(text):
    return [(int(e), int(s)) for e, s in re.findall(
        r"Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+", text)]


def verify_progress(server, task, ssh, wait_s=90):
    deadline = time.monotonic() + wait_s
    while True:
        cmd = (f"if kill -0 {int(task['pid'])} 2>/dev/null; then "
               f"tail -c 24000 {shlex.quote(task['log'])}; else echo __DEAD__; fi")
        text = ssh(server["host"], server["user"], cmd)
        if "__DEAD__" in text or any(x in text for x in ("Traceback", "CUDA out of memory", "RuntimeError")):
            return False
        if len(set(steps(text))) >= 2 and max(s for _, s in steps(text)) > 0:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(3)


def postflight(project):
    root = Path(project)
    context = read(root / "pipeline/headless/.tick_context.json")
    if any(context["preflight"].get(k, 1) != 0 for k in ("monitor_rc", "goal_rc")):
        raise ValueError("Preflight failed")
    since = datetime.fromisoformat(context["generated_at"]).timestamp()
    reports = [p for p in (root / "pipeline/reports").glob("summary_*.md")
               if p.stat().st_mtime >= since]
    if not reports:
        raise ValueError("Missing current tick report")
    text = max(reports, key=lambda p: p.stat().st_mtime).read_text(encoding="utf-8")
    if not all(re.search(rf"^##\s+{n}[.\s]", text, re.M) for n in range(6)):
        raise ValueError("Incomplete six-section report")
    queue = read(root / "pipeline/queue.json", {"gpu_queues": {}})
    for tasks in queue["gpu_queues"].values():
        for task in tasks:
            if (task.get("launch_verification") == "pending_progress"
                    and task.get("status") in ("waiting", "claiming", "running")):
                raise ValueError("Training launch still requires progress verification: " + task["id"])
    if context["mode"] == "steady":
        return
    memory = root / "pipeline/codex_memory.md"
    content = memory.read_text(encoding="utf-8")
    required = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                "Closed Or Failed Directions", "Running And Queue", "Open Questions And Risks", "Last Tick")
    if memory.stat().st_mtime < since or len(content.splitlines()) >= 200 or not all(
            "## " + name in content for name in required):
        raise ValueError("Memory snapshot missing/stale/invalid")
    work = read(root / "pipeline/research_work.json", {})
    candidates = work.get("candidates", [])
    if context["mode"] == "design" and not candidates:
        raise ValueError("Design tick has no durable candidate disposition")
    seen = set()
    for candidate in candidates:
        if candidate["id"] in seen or candidate.get("stage") not in STAGES:
            raise ValueError("Duplicate candidate or invalid stage")
        seen.add(candidate["id"])
        if not candidate.get("next_action") or not candidate.get("evidence"):
            raise ValueError("Missing actionable disposition/evidence")
        for evidence in candidate["evidence"]:
            artifact(root, evidence)
        if candidate["stage"] == "blocked" and not all(candidate.get(k) for k in (
                "blocker", "retry_after", "unblock_condition")):
            raise ValueError("Blocked candidate needs retry and unblock condition")
    old = context.get("research_work", {}).get("candidates", [])
    for previous in old:
        current = next((c for c in candidates if c["id"] == previous["id"]), None)
        if current is None:
            raise ValueError("Unfinished candidate silently removed")
        # Timestamp-only edits or reworded next_action do not constitute progress.
        if (current.get("stage") == previous.get("stage")
                and current.get("evidence") == previous.get("evidence")
                and current["stage"] != "blocked"):
            raise ValueError("Unfinished candidate made no durable progress")
    for current in candidates:
        if current["stage"] == "training":
            task_id = (current.get("queue_id") or current.get("experiment_id")
                       or current["id"])
            tasks = [t for group in queue["gpu_queues"].values() for t in group
                     if t.get("id") == task_id]
            if not tasks or not tasks[0].get("launch_verified"):
                raise ValueError("Training disposition lacks verified launch")


if __name__ == "__main__":
    project = Path(os.environ.get("PROJECT_ROOT", "D:/project")) / sys.argv[1]
    if enabled(project):
        try:
            postflight(project)
        except (ValueError, KeyError, OSError, TypeError) as exc:
            print("CLOSURE_INCOMPLETE:", exc)
            sys.exit(1)
        print("CLOSURE_POSTFLIGHT_PASS")
