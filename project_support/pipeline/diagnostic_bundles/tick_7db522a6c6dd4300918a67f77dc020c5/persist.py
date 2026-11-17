"""Reconcile only this falsely finalized experiment and genuine GPU runtime block."""

import csv
from datetime import datetime, timedelta
import io
import json
import os
from pathlib import Path
import shutil

from audit_terminal import BUNDLE, PROJECT, TOKEN, guard, save, tick, monitor

guard(180)
audit = tick.load(BUNDLE / "resource_diagnosis.json")
recovery = tick.load(BUNDLE / "recovery_validation.json")
assert recovery["status"] == "PASS" and recovery["optimizer_state_count"] == 642
assert recovery["meta"]["epoch"] == 26 and recovery["meta"]["epochs_no_improve"] == 8
assert recovery["cuda_initialized"] is False and recovery["native_forwards"] == recovery["optimizer_steps"] == 0
assert recovery["compute"] == "2634704, 20016"
assert recovery["locks"]["/tmp/cluster_project_gpu0_m201_migration.lock"] == "held"
native_log = BUNDLE / "20261014_154431.log"
assert tick.digest(native_log) == audit["native_log_sha256"]
precise = monitor.parse_native_lineage(native_log.read_text(encoding="utf-8"), resumed=True)
rounded = audit["stdout_rounded_values"]
old_missed = len(rounded) - rounded.index(max(rounded)) - 1
assert precise[1:] == (recovery["meta"]["best_miou"], 8) and old_missed == 11
assert not monitor.should_early_stop({}, {"patience": 10}, precise[2], 26, 50)
assert tick.digest(PROJECT / "Cluster/scripts/validate_pdc_20261009.py") == "00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26"
save("monitor_fix_validation", {
    "status": "PASS", "native_exact_best": precise[1], "native_no_improve": precise[2],
    "old_rounded_no_improve": old_missed, "patience": 10,
    "test_results_observed_in_tools": {"native_lineage_tests": 7, "registered_pid_tests": 6, "closure_regression_tests": 69},
    "monitor_sha256": tick.digest(Path(monitor.__file__)),
    "test_files": [
        {"path": "scripts/test_registered_cluster_metrics_20261015.py",
         "sha256": tick.digest(PROJECT / "scripts/test_registered_cluster_metrics_20261015.py")},
        {"path": "scripts/test_registered_cluster_probe_20261014.py",
         "sha256": tick.digest(PROJECT / "scripts/test_registered_cluster_probe_20261014.py")},
    ],
    "scope": "Actual native logger replay plus mocked discovery/precision alignment; no fresh live training metric probe after the process disappeared. Only explicit cluster/server4 native precision path changed.",
})
save("recovery_plan", {
    "experiment_id": "M201-BPS", "same_experiment_only": True,
    "checkpoint": recovery["checkpoint"], "checkpoint_sha256": recovery["checkpoint_sha256"],
    "meta": recovery["meta"], "code_commit": "f8457d3b657e66306a7fce1afb3d81d8ab874669",
    "seed": 1999, "epochs": 50, "scheduler_max_iters": 70, "native_patience": 10,
    "optimizer_state_exact": True, "scheduler_state_exact": True, "next_epoch": 27,
    "minimum_current_deadline_margin_seconds": 720,
    "unblock_condition": "Pinned server4/GPU0 UUID; no NVML compute process; idle-equivalent >=30000MiB; original training and diagnostic flocks actually available; fresh code/checkpoint/current foreground lease checks.",
    "launch_executed": False, "optimizer_steps": 0,
    "scope": "No cold restart or new admission. Full native state recovery only; interrupted epoch27 replays, no mid-epoch/RNG/bitwise trajectory claim.",
})


def ref(path):
    return {"path": path.relative_to(PROJECT).as_posix(), "sha256": tick.digest(path)}


work_path = PROJECT / "pipeline/research_work.json"
work = tick.load(work_path)
assert not any(entry["path"].replace("\\", "/") in (
    "pipeline/experiments/M201-BPS.json", "pipeline/experiments.csv")
    for candidate in work["candidates"] for entry in candidate.get("evidence", []))
lock = monitor.acquire_lock(str(PROJECT))
assert lock is not None
try:
    experiment = monitor.load_experiment(str(PROJECT), "M201-BPS")
    assert experiment["status"] == "done_earlystop" and experiment["pid"] == 2634704
    save("monitor_terminal_experiment_initial", {"experiment": experiment})
    ledger_path = PROJECT / "pipeline/experiments.csv"
    before_hash = tick.digest(ledger_path)
    shutil.copyfile(ledger_path, BUNDLE / "experiments_before_reconciliation.csv")
    with ledger_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = list(reader)
    current = [row for row in rows if row["id"] == "M201-BPS"]
    assert len(current) == 1 and current[0]["state"] == "done_earlystop"
    previous_row = dict(current[0])
    current[0].update(state="stopped_unknown", best_miou=str(recovery["meta"]["best_miou"]),
                      epochs="26/50", log_local=str(native_log))
    assert tick.digest(ledger_path) == before_hash
    temporary = ledger_path.with_suffix(".csv.reconcile.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, ledger_path)
    experiment.update(
        status="stopped_unknown", final_best=recovery["meta"]["best_miou"],
        epochs_final="26/50", best_epoch=18, native_epochs_no_improve=8,
        log_local=str(native_log), screen_status="interrupted_by_false_monitor_patience",
        recovery_checkpoint=recovery["checkpoint"], recovery_sha256=recovery["checkpoint_sha256"],
        recovery_meta=recovery["meta"], recovery_launch_verified=False,
        monitor_terminal_initial={"status": "done_earlystop", "rounded_best": "0.4900",
                                  "reported_epoch": "27/50", "reported_no_improve": 11},
    )
    experiment["history"].append({
        "ts": datetime.now().astimezone().isoformat(), "action": "terminal_precision_reconciliation",
        "status": "stopped_unknown", "best_miou": recovery["meta"]["best_miou"],
        "best_epoch": 18, "completed_epoch": 26, "native_no_improve": 8,
        "reason": "Rounded resumed stdout omitted sub-rounding best updates; monitor killed during unfinished epoch27.",
        "gpu_recovery_not_launched": True,
    })
    monitor.save_experiment(str(PROJECT), experiment)
    save("terminal_reconciliation", {
        "original_ledger_row": previous_row, "corrected_ledger_row": current[0],
        "ledger_before_sha256": before_hash, "ledger_after_sha256": tick.digest(ledger_path),
        "experiment_before": ref(BUNDLE / "monitor_terminal_experiment_initial.json"),
        "scope": "One existing M201 row corrected, not duplicated. Initial monitor record/history archived; queue/running unchanged; no signals or new dispatch.",
    })
finally:
    lock.close()

analysis = PROJECT / "pipeline/analyses/M201-BPS_interrupted_monitor_20261015.md"
launch_attempt = PROJECT / "pipeline/diagnostic_bundles/transport_port_75d7e1ea35634b1fa29749fcf54163c8" / ("native_execution_" + TOKEN + ".json")
assert json.loads(tick.load(launch_attempt)["stdout"])["status"] == "BLOCKED"
files = sorted(path for path in BUNDLE.iterdir() if path.is_file()) + [analysis, launch_attempt,
    PROJECT / "scripts/test_registered_cluster_metrics_20261015.py"]
references = [ref(path) for path in files]
scalar_ids = ["m95-native-main-role-weight-precedence", "m95-native-relation-other-sign-conflict",
              "m95-native-secondary-positive-mass"]
retry = (datetime.now().astimezone() + timedelta(minutes=40)).isoformat()
condition = (
    "Fresh pinned server4/GPU0 observation with no NVML compute process and >=30000MiB idle-equivalent free memory; "
    "all original training/diagnostic flocks truly available. Do not reset GPU, delete locks, kill unknown owners or assume sudo."
)
for cid in scalar_ids:
    candidate = next(row for row in work["candidates"] if row["id"] == cid)
    assert candidate["stage"] == "blocked" and all(not gate["passed"] for gate in candidate["gates"].values())
    for entry in references:
        if entry not in candidate["evidence"]:
            candidate["evidence"].append(entry)
    candidate.update(
        blocker_kind="gpu_context_or_lock_not_released", required_server="server-4",
        blocker="Queue opening is real, but exact parent disappeared while NVML still lists PID2634704/20016MiB and original training flock remains held. Kernel flock holder2634697 also absent; cause/authority for cleanup unknown. Frozen GPU diagnostic was actually denied, zero GPU launches.",
        retry_after=retry, unblock_condition=condition,
        occupation_evidence=ref(BUNDLE / "recovery_validation.json"),
        attempted_alternatives=[
            "Previous11 immutable assets/AST/epoch4 strict-constant audit/four native CPU groups x2 completed; preserve frozen manifest, do not repeat.",
            "This tick ran frozen launcher: actual GPU slot refusal,0 native GPU launches.",
            "This tick exact parent/kernel-lock/native logger/best+last metadata audited; no broad process scan/reset/signal.",
            "This tick completed same M201 full CPU resume preparation and native full-precision replay; no native role parameter-gradient execution.",
        ],
        execution_status="Current7db5: original frozen parameter diagnostic denied; no GPU/native forward, parameter gradient, optimizer, core or gate PASS. Same evidence supports3role subsets, not3independent mechanisms. Original source/FD/full-forward FAILs retained.",
        next_action="When actual GPU0 context+training flock clear, under fresh current foreground lease execute the unchanged epoch4/groups0,60,101,124 parameter-gradient instrument; preserve seed1999, companions and absolute1e-6 controls. Do not equate this tick's CPU recovery/monitor tests with native role transport or independent-core admission.",
    )
bps = next(row for row in work["candidates"] if row["id"] == "m95-native-between-pair-support")
assert bps["stage"] == "training"
for entry in references:
    if entry not in bps["evidence"]:
        bps["evidence"].append(entry)
bps.update(
    stage="blocked", blocker_kind="gpu_context_or_lock_not_released", required_server="server-4",
    blocker="Same M201 was prematurely interrupted by rounded monitor patience, not native convergence. Full CPU recovery ready, but original GPU context and training flock remain unavailable after exact parent disappeared.",
    retry_after=retry, unblock_condition=condition,
    occupation_evidence=ref(BUNDLE / "recovery_validation.json"),
    recovery_plan=ref(BUNDLE / "recovery_plan.json"),
    attempted_alternatives=["Actual native logger/best+last state audit; initial false monitor row retained and corrected.",
                            "7native-lineage+6PID+69closure tests passed; exact restored patience replay8, not rounded11.",
                            "CPU strict model load after identical constant audit,642optimizer states/scheduler/best/no_improve8 exactly restored; failures retained.",
                            "Actual NVML residue/flock remained unavailable; no safe visible owning PID for cleanup. No GPU reset/sudo/foreign signal."],
    execution_status="Same experiment interrupted during epoch27 step3656/4686. Best0.489848792552948@18, completed26/no_improve8. Screen incomplete, not native patience10 stop or efficacy rejection.0 new optimizer steps/GPU forwards/recovery launches; full native last checkpoint preserved.",
    next_action="After actual GPU0/lease release and fresh code/checkpoint/current foreground checks, recover SAME M201-BPS from validated epoch26 full native state (SHAf2f6fb53bd3a6388e1bf05e8d7c5099bacf94e5f81f06d4584d2a1707426d8df) using native --resume; retain642optimizer states/scheduler/best/no_improve8/seed1999/epochs50/max_iters70/patience10. Replay unfinished27, verify increasing native steps, no new candidate/admission/cold restart or bitwise trajectory claim.",
)
attempted = scalar_ids + [bps["id"]]
work["design_cycle"] = {
    "stop_reason": "external_resource_blocked", "attempted_ids": attempted,
    "evidence": [ref(BUNDLE / "recovery_validation.json"), ref(BUNDLE / "resource_diagnosis.json"),
                 ref(BUNDLE / "monitor_fix_validation.json"), ref(analysis), ref(launch_attempt)],
    "resume_condition": condition, "retry_after": retry,
    "scope": "Only actual authorized GPU runtime/lock unavailability after executable non-GPU preparation; not global route exhaustion or two independent scientific hypotheses.",
}
tick.save(work_path, work)
decision = monitor.log_decision(
    str(PROJECT), "other", "M201监控早停是否符合原生patience，队列开槽是否等于显存与独占锁释放？",
    "纠正同一M201记录为stopped_unknown/协议中断；只修cluster/server4原生精度与续训计数；四原ID真实资源阻塞，原门槛不变。",
    "真实日志与best/last检查点一致：best0.48984879@18、完成26/no_improve8，而三位小数旧计数11；训练27仅3656步，无原生早停。CPU完整恢复642状态通过；NVML仍20016MiB/训练flock持有，原PID/锁PID不可见，不做未经核实的cleanup。7+6+69测试通过，0GPU/恢复启动。",
    str(analysis),
)
notes = {
    "actions": [
        "本轮design快照2026-10-15 03:09:49+08，截止04:09:49不可变；任务ID/最新goalSHA24083b8d/19约束11禁令/server4 GPU0单槽/后台Disabled核实。begin仅一次，章节0-3保留原监控快照；后续纠正不篡改该快照。",
        "begin按三位小数旧计数11/10终止同一M201 PID2634704，并记done_earlystop/27轮。实机审计发现原生完整精度日志18次验证和best/last均为best0.489848792552948@18、完成epoch26/no_improve8；epoch27仅3656/4686，无原生Early stopping消息。本次为监控误停，非完整收敛或合法patience10筛选。",
        "原记录/台账已字节归档；只纠正同一M201行与实验为stopped_unknown、Best精确值、完成26轮，未重复终态入账或创建新实验。Acc50约0.541/spmIOU约0.454@18为三位小数日志；对Baseline约+0.000449，对Champion约-0.012151，未达目标、效益不确定。",
        "只在cluster/server4显式精确PID模式使用真实logger full-precision和resume初始best/patience；精度/谱系缺失则不做早停。真实日志回放7项、进程6项及公共闭环69项均通过；其他项目默认路径、patience10、科学门槛/调度不变。未来恢复训练仍需实机验证计数路径。",
        "冻结四组参数诊断实际执行启动器，返回BLOCKED/GPU launches0。03:13/03:17/03:29的资源证据：GPU0总32607MiB/使用20107/剩11994/util0%；NVML仍PID2634704占20016MiB，原进程不可见；训练flock持有、内核锁PID2634697亦不可见，原因未知。其他两诊断锁可用；低util和队列开槽不是GPU空闲。",
        "同一M201 epoch26完整CPU恢复准备PASS：源模型严格加载前核验两项非持久常量完全相同；642优化器状态、scheduler、best/no_improve8精确恢复，checkpointSHAf2f6fb53bd3a6388e1bf05e8d7c5099bacf94e5f81f06d4584d2a1707426d8df。第一次未审计常量键与第二次numpy float32收据序列化失败均保留；第三次通过。CUDA未初始化，0原生/GPU前向/参数梯度/优化器更新/训练恢复启动。",
        "先续三旧ID再完成误停恢复准备；四原ID均blocked/gpu_context_or_lock_not_released，retry_after=" + retry + "，真实GPU/锁释放才恢复。三scalar六门槛仍false、旧source/FD/full-forward FAIL全部保留；BPS训练协议未完成，不改名/冷启动/扫参/判机制失败。同一仪器不冒称3独立机制；设计以真实external_resource_blocked收尾，未声称路线耗尽。",
        "未执行sudo/GPU reset/删除锁/外部进程信号或全机进程扫描；无法核实可安全清理的活进程，需要服务器侧排查残留。PDC用户文件原SHA不变。本轮postflight尚未执行，执行状态待finish；收据仅begin到收据局部用量窗口，未知不填零、缓存属于输入/推理属于输出、不是账单；实际产出不等于科学收益。",
    ],
    "decisions": [
        "恢复优先保持同一M201完整原生状态及patience10；在GPU上下文/训练flock真释放前不启动任何GPU实验，不以低util或队列空槽越过独占保护。",
        "四原ID均保留可续动作和实际阻塞证据；短期资源冷却须finish通过后才生效，下一自动调度时间未知。没有合格新机制就保留空槽，不放宽目标、科学准入或制造变体。",
    ],
}
notes_path = PROJECT / "pipeline/reports" / ("notes_" + TOKEN + ".json")
tick.save(notes_path, notes)
print(json.dumps({"experiment_status": "stopped_unknown", "native_best": precise[1],
                  "native_no_improve": precise[2], "blocked_ids": attempted,
                  "retry_after": retry, "decision": decision, "notes": str(notes_path)}))
