"""Record genuine instrument validation while preserving all scientific gaps."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["PROJECT_ROOT"] = "D:/project"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick as tick
import pipeline_monitor as monitor

TOKEN = "6e56a11f72b04b37b9595704b8cec930"
PROJECT = Path("D:/project/cluster_project")
BUNDLE = Path(__file__).resolve().parent
owner = tick.load(PROJECT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.fromisoformat(owner["deadline_at"]) > datetime.now(timezone.utc)
assert not (BUNDLE / "metrics_audit.json").exists()
exp = monitor.load_experiment(str(PROJECT), "M201-BPS")
servers = monitor.load_servers(str(PROJECT))
program = f"""
import datetime,json,pathlib,subprocess,torch
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
base=pathlib.Path({servers['server-4']['work_dir']!r})/{Path(exp['config']).stem!r}
paths=[p for p in base.glob('*/last.pth') if p.parent.name>='20261014_154428']
assert paths
path=max(paths,key=lambda p:p.stat().st_mtime_ns)
before=path.stat()
saved=torch.load(path,map_location='cpu',weights_only=False,mmap=True)
meta=saved['meta']
after=path.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
assert meta['epoch']>=9
log=pathlib.Path({exp['log']!r})
with log.open('rb') as stream:
    stream.seek(max(0,log.stat().st_size-1048576))
    lines=stream.read().decode(errors='replace').replace('\\r','\\n').splitlines()
metrics=[s for s in lines if s.startswith(('mIOU:','spmIOU:'))][-4:]
print(json.dumps({{'observed_at':datetime.datetime.now().astimezone().isoformat(),
                  'checkpoint':str(path),'checkpoint_meta':meta,'log_metrics':metrics,
                  'scope':'Completed native validation metadata; not converged efficacy or subgroup harm evaluation.'}},
                 default=lambda x:x.item()))
"""
remote = subprocess.run(
    ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=12",
     "server-4", "/home/songcl/.conda/envs/project_cluster/bin/python", "-B", "-"],
    input=program, text=True, encoding="utf-8", capture_output=True, timeout=30,
)
assert remote.returncode == 0, remote.stderr
metrics = json.loads(remote.stdout)
tick.save(BUNDLE / "metrics_audit.json", metrics)
result = tick.load(BUNDLE / "result.json")
assert result["status"] == "PASS" and result["gpu_forwards"] == 0
assert result["function_calls"] == 4 and result["parameter_gradient_requests"] == 28
assert all(row["analytic_max_delta"] <= 1e-6 for row in result["fixtures"])
prereg = PROJECT / "pipeline/designs/parameter_transport_cpu_prereg_20261014_1620.md"
native_plan = PROJECT / "pipeline/designs/bps_parameter_transport_prereg_20261014_1434.md"
files = sorted(p for p in BUNDLE.iterdir() if p.is_file()) + [prereg, native_plan]


def ref(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}


work_path = PROJECT / "pipeline/research_work.json"
work = tick.load(work_path)
roles = {
    "m95-native-main-role-weight-precedence": "main_secondary",
    "m95-native-relation-other-sign-conflict": "relation_other",
    "m95-native-secondary-positive-mass": "fractional_secondary",
}
for cid, condition in roles.items():
    candidate = next(c for c in work["candidates"] if c["id"] == cid)
    assert candidate["stage"] == "validation"
    assert all(not g["passed"] for g in candidate["gates"].values())
    known = {(e["path"], e["sha256"]) for e in candidate["evidence"]}
    for path in files:
        entry = ref(path)
        if (entry["path"], entry["sha256"]) not in known:
            candidate["evidence"].append(entry)
    candidate["parameter_gradient_instrument"] = {
        "stage": "CPU_method_validated_native_adapter_not_yet_ported",
        "condition": condition, "result": ref(BUNDLE / "result.json"),
        "native_forwards": 0, "optimizer_steps": 0,
        "scope": "One common instrument test for three role subsets, not three independent mechanisms or native scene gradients.",
    }
    candidate["required_server"] = "server-4"
    candidate["next_action"] = (
        "Adapt and stage the already-preregistered epoch4/first-four-group native parameter-gradient adapter "
        "for verified server4, preserving frozen source/checkpoint/cohort/seed/tolerance and auditing only "
        "host/path/nonpersistent-buffer runtime compatibility. This deployment preparation is still executable "
        "non-GPU work, not a fabricated GPU-only block. Then execute the native diagnostic only when the "
        "single authorized GPU0 slot is available and its lease is acquired. CPU fixture PASS is not native "
        "parameter transport, an independent core, source falsification, FD repair, new admission or efficacy."
    )
    candidate["execution_status"] = (
        "Current6e56 event: unchanged parameter_transport function tested on server4 CPU; "
        "two synthetic Jacobian fixtures/two repeats, four calls/28 VJPs, six-condition analytic checks/identity/"
        "unused-tensor/.grad nonaccumulation/repeat controls PASS. Output dot+1 versus parameter dot-7 "
        "counterexample rules out direct direction extrapolation only. Zero native cohort forwards/GPU jobs/"
        "optimizer updates/new gates. Old source and native/FD FAILs preserved."
    )
bps = next(c for c in work["candidates"] if c["id"] == "m95-native-between-pair-support")
assert bps["stage"] == "training"
for name in ("exact_training_observation.json", "deathwatch_reconciliation.json", "metrics_audit.json", "run.py", "persist.py"):
    entry = ref(BUNDLE / name)
    if entry not in bps["evidence"]:
        bps["evidence"].append(entry)
bps["execution_status"] = (
    "Current6e56 event exact registered server4 PID2634704/config/cwd verified; native Train10 steps419->439, "
    "false deathwatch missed1 cleared under project lock. Native completed checkpoint metrics observed; "
    "no restart/duplicate/new admission or efficacy claim."
)
tick.save(work_path, work)
decision = monitor.log_decision(
    str(PROJECT), "other", "局部角色方向是否能直接外推参数方向，且迁移后进程枚举缺失是否意味着死亡？",
    "核验既有参数梯度仪器，保留三条原有ID及六门槛false；用精确PID/原生日志纠正本实验一次误记，不重启训练。",
    "未改函数的CPU双fixture双重复/28VJP分析对照通过；输出点积+1与参数点积-7受控反例。原生Train10步419->439且同一PID；参数级原生实验仍未执行，未完成部署准备不伪造资源block。",
    str(BUNDLE / "result.json"),
)
notes = {
    "actions": [
        "本轮event快照2026-10-14 16:11:35+08，截止17:11:35不可变；实际任务ID核实，19约束/11禁令/server4 GPU0单槽/后台Disabled。begin只执行一次，章节0-3保持脚本快照。",
        "begin未枚举到训练进程并记deathwatch1/3；精确核验已登记PID2634704/cwd/config/--resume，16:23:33原生Train10/50步419到439/4686、日志大小增长。实测GPU20089MiB/剩12012MiB/util81%，只有本训练GPU进程19998MiB；只清除该实验误记，不改监控基础设施/调度/外部任务。",
        "三条到期scalar均沿用ID/假设/原FAIL/六门槛false；实际执行原参数梯度仪器CPU验证：两个受控Jacobian、两次重复、4调用/28梯度请求、6条件分析对照、身份、unused参数、梯度不积累和重复通过。错误恒等Jacobian对照被检出；输出点积+1/参数点积-7反例说明必须测真实传递。",
        "CPU测试明确是合成二次目标，不是原生语义loss或真实场景模型参数梯度；0GPU前向/0原生cohort前向/0优化器更新/0新增候选或准入。未清除旧1e-6有限差分或完整原生重复失败。三ID仍validation；同一仪器用于三子集，不冒称三项独立机制。",
        "后续固定epoch4/四组原生参数实验仍未执行。server4的路径/缓冲区兼容和资产部署尚需完成，属于可执行非GPU准备，不标成GPU-only block、不声称研究耗尽或冷却。原生GPU测试须在唯一授权槽释放且真实租约核实后进行；不并发挤占当前训练。",
        "最新完成验证的检查点：epoch" + str(metrics["checkpoint_meta"]["epoch"]) +
        "，Best=" + str(metrics["checkpoint_meta"]["best_miou"]) +
        "，no_improve=" + str(metrics["checkpoint_meta"]["epochs_no_improve"]) +
        "；精确观察时间" + metrics["observed_at"] + "。不等于收敛、泛化或子群安全。",
        "上一8eea轮实际abort1/INCOMPLETE/context未提交/租约与pending不存在已核实；本轮postflight尚未执行，结果与租约释放在任务报告补充。收据只含begin到收据的可见用量，晚到与最终回复不含，未知不填零，缓存属于输入/推理属于输出，不当账单。",
    ],
    "decisions": [
        "继续唯一server4原生训练，精确进程证据优先于不完整枚举；不重复启动，不碰源GPU7外部任务。",
        "完成本event三条候选的共同仪器验证，不以该PASS冒充原生参数验证或新结构准入。下一动作是移植冻结原生适配器并核验资产；不为容量生成变体或凭局部方向推出训练伤害。下一调度时间未知。",
    ],
}
notes_path = PROJECT / "pipeline/reports" / ("notes_" + TOKEN + ".json")
tick.save(notes_path, notes)
print(json.dumps({"metrics": metrics, "decision": decision, "notes": str(notes_path)}))
