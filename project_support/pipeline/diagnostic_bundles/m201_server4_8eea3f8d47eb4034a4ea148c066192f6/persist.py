"""Persist verified migration facts, not a new scientific admission."""

from datetime import datetime
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate as m

m.guard()
assert not (m.BUNDLE / "migration_summary.json").exists()
progress = m.tick.load(m.BUNDLE / "progress.json")
checkpoint = m.tick.load(m.BUNDLE / "checkpoint.json")
probe = m.tick.load(m.BUNDLE / "native_probe_compat.json")
assert progress["native_progress_verified"]
assert m.monitor.load_experiment(str(m.PROJECT), "M201-BPS")["launch_verified"]
audit = json.loads(m.remote(m.TARGET, f"""
import fcntl,hashlib,json,pathlib,subprocess
assert not pathlib.Path('/proc/2591725').exists()
assert not pathlib.Path('/proc/2617502').exists()
lease=open('/tmp/cluster_project_gpu0_exclusive.lock','a+')
fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
state=subprocess.check_output(['git','-C',{m.OLD!r},'status','--porcelain'])
assert hashlib.sha256(state).hexdigest()=='124e3dbd67d93d64b4fbb66189bb2f84c51828459a1a75c577fa280ba88ec478'
print(json.dumps({{'original_checkout_status_unchanged':True,'precheck_absent':True,
                  'failed_launch_absent':True,'old_diagnostic_lease_free':True}}))
""", timeout=25))
source = json.loads(m.remote(m.SOURCE, """
import json,pathlib,subprocess
assert not pathlib.Path('/proc/2867534').exists()
print(json.dumps({'source_pid_absent':True,
                  'gpu7_compute':subprocess.check_output(['nvidia-smi','-i','7','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()}))
""", timeout=20))
assert source["gpu7_compute"] == "262355, 928"
summary = {
    "token": m.TOKEN, "recorded_at": datetime.now().astimezone().isoformat(),
    "experiment": "M201-BPS", "migration_status": "VERIFIED_RESUME",
    "server": "server-4", "gpu": 0, "pid": progress["pid"],
    "checkpoint_sha256": checkpoint["source"]["sha256"],
    "checkpoint_meta": checkpoint["source"]["meta"],
    "optimizer_step_at_checkpoint": checkpoint["source"]["optimizer_step_max"],
    "native_progress": {key: progress[key] for key in ("first_step", "second_step", "gpu", "compute")},
    "dataset_files_exact": 2226, "dataset_bytes_exact": 17894540419,
    "native_backward": {"batch_size": 2, "finite_gradient_tensors": probe["finite_gradient_tensors"],
                        "optimizer_steps": 0, "peak_allocated_mib": probe["peak_allocated_mib"],
                        "optimizer_tensors_restored_exact": True, "scheduler_restored": True},
    "target_audit": audit, "source_audit": source,
    "new_experiments": 0, "new_admissions": 0, "resume_attempts": 2,
    "verified_resumes": 1, "native_readiness_attempts": 2,
    "retained_failures": ["strict-load nonpersistent buffers", "read-only all-proc timeout",
                          "long TMPDIR torch_shm_manager Invalid argument"],
    "constraints": "Same native config/code/seed1999/epochs50/max_iters70/batch2/workers4/patience10. Immutable admission preserved. Host/runtime compatibility only; not scientific gain.",
    "known_limits": "Incomplete epoch9 is replayed; mid-epoch/RNG/bitwise trajectory is not preserved. Readiness sample has zero between_support_loss, not a new BPS activity gate. Trained efficacy/VAL harm remains unknown.",
    "tick_status": "Postflight not yet executed; immutable begin capacity2/server6 differs from current user-authorized capacity1/server4.",
}
m.record("migration_summary", summary)
from pipeline_monitor import log_decision
decision = log_decision(
    str(m.PROJECT), "manual", "用户要求移动到server4上训练",
    "M201-BPS保留原科学准入并从epoch8完整检查点在server4唯一GPU0续训，精确停源，更新队列/运行映射/实验历史。原生第9轮180到199验证通过。",
    "身份与GPU UUID核实；2226文件/17894540419字节SHA逐项一致；9源码文件与冻结catalog一致；642优化器状态逐tensor/调度器恢复。仅修序列化常量审计及短TMPDIR，不改变配置、模型、种子或schedule。",
    str(m.BUNDLE / "migration_summary.json"),
)
work_path = m.PROJECT / "pipeline/research_work.json"
work = m.tick.load(work_path)
candidate = next(c for c in work["candidates"] if c["id"] == "m95-native-between-pair-support")
assert candidate["stage"] == "training"
files = sorted(p for p in m.BUNDLE.iterdir() if p.is_file() and p.suffix in (".py", ".json", ".log")) + [Path(decision)]
known = {(e["path"], e["sha256"]) for e in candidate["evidence"]}
for path in files:
    entry = {"path": path.relative_to(m.PROJECT).as_posix(), "sha256": m.tick.digest(path)}
    if (entry["path"], entry["sha256"]) not in known:
        candidate["evidence"].append(entry)
candidate["migration_20261014"] = {
    "status": "verified_resume", "server": "server-4", "gpu": 0,
    "summary": {"path": (m.BUNDLE / "migration_summary.json").relative_to(m.PROJECT).as_posix(),
                "sha256": m.tick.digest(m.BUNDLE / "migration_summary.json")},
}
candidate["execution_status"] = "M201 migrated from source GPU7 to server4 GPU0; checkpoint epoch8/best.466449975967/optimizer37488/scheduler restored; native Train9 steps180->199 verified. First strict-load/runtime failures retained; TMPDIR-only repair. No new scientific admission or scalar gate change."
candidate["next_action"] = "Monitor the exact server4 resumed PID/log without relaunch. Preserve all prior scalar/source/FD failures; evaluate converged original ScanRefer VAL and preregistered subgroups under the unchanged plan. No claim of bitwise cross-device resume or trained benefit."
m.tick.save(work_path, work)
notes = {
    "actions": [
        "快照2026-10-14 15:12:13+08，模式design，原截止16:12:13不可变；章节0-3复用begin事实，不代表迁移后的实时状态。此前2bbb轮实际finish0/PASS/COMPLETE且租约不存在已核实。",
        "按用户明确迁移授权，server4身份dl04-MS-7E06/历史SSH pin核实，实际只有GPU0 RTX5090，当前容量1；server6新派发关闭，其他项目/调度/外部进程不操作。SERVERS及goal只记录最新主机授权，科学目标与禁令不变。",
        "同项目隔离训练目录保留server4旧脏配置；冻结代码f8457d3b与9文件哈希/catalog核实。2226相关数据资产逐文件SHA全部一致，共17894540419字节。epoch8完整检查点三端SHA12af607876e9c669ac47e1d11c3a1e4335ae9b9701a78de508fb6a56edb200eb一致。",
        "原strict-load FAIL保留；只核实两个非持久常量缓冲区逐值一致，无缺权重。642优化器状态逐tensor一致、调度器准确恢复，batch2原生前向/反向梯度有限，诊断0optimizer。两批原生多进程数据加载PASS（4workers）。所选就绪样本BPS loss为0，不冒充新科学门槛。",
        "只读预检/proc卡住已精确处理自己的PID2591725，后核实不存在/旧诊断锁可获取；不触碰外部PID3172。首次续训long TMPDIR共享内存错误保留，精确停其自身树，短TMPDIR修复后恢复相同检查点，不改科学代码/worker/batch/schedule。",
        "15:46左右验证M201在server4 GPU0/PID2634704，Train9/50从180到199/4686递增；GPU使用14299MiB/剩17802MiB/util62%。源PID2867534确已不存在，GPU7只余外部PID262355/928MiB未触碰；唯一原生续训实例已验证。",
        "科学状态M201=training，保留Best0.466449975967/早停0/optimizer37488检查点状态；未完成轮次和RNG不做逐步无损声明。0新候选/0新准入/0新实验，2续训尝试/1验证成功，原失败不覆盖；三scalar六门槛false保持，本轮未做新scalar测试。",
        "研究tick尚待postflight：begin旧容量2/server6与用户迁移后的实际容量1/server4不同，不改快照、补假候选或等待凑截止。用量收据只覆盖begin到收据可见本地记录，缺失未知，缓存属于输入/推理属于输出，不重复相加、不当账单。实际验收/释放在任务报告补充。",
    ],
    "decisions": [
        "执行用户迁移优先，parameter_transport计划未执行。不冷启动、不扩展GPU1、不改变历史科学准入/FD失败/目标0.51，也不驱逐外部任务。",
        "训练迁移成功与研究tick验收分开：若原不可变资源快照导致postflight容量缺口拒绝，保留证据并精确abort核实释放，不伪造研究完成或修改checker。下一tick用新配置监控；下一调度时间未查询，记未知。",
    ],
}
notes_path = m.PROJECT / "pipeline/reports" / ("notes_" + m.TOKEN + ".json")
m.tick.save(notes_path, notes)
print(json.dumps({"summary": str(m.BUNDLE / "migration_summary.json"), "decision": decision,
                  "notes": str(notes_path), "new_evidence": len(files)}))
