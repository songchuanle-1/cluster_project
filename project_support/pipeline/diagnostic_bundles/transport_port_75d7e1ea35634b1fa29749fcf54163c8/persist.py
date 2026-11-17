"""Persist real preparation and the occupied single-slot disposition."""

from datetime import datetime, timedelta
import json
from pathlib import Path
import subprocess
import sys

import stage

stage.guard(180)
project = stage.PROJECT
bundle = stage.BUNDLE
prepared = stage.tick.load(bundle / "preparation.json")
manifest = stage.tick.load(bundle / "frozen_manifest.json")
guard = stage.tick.load(bundle / ("launch_guard_" + stage.TOKEN + ".json"))
assert json.loads(guard["stdout"])["status"] == "BLOCKED"
assert prepared["status"] == "PASS" and prepared["native_getter_calls"] == 8
assert prepared["gpu_forwards"] == prepared["parameter_gradient_calls"] == prepared["optimizer_steps"] == 0
assert prepared["gpu_slot"]["status"] == "occupied" and prepared["training_lease"] == "held"
observation = stage.tick.load(bundle / "exact_training_observation.json")
assert observation["native_progress_verified"] and observation["pid"] == 2634704
assert stage.tick.load(bundle / "registered_probe_live.json")["status"] == "PASS"
dirty = project / "Cluster/scripts/validate_pdc_20261009.py"
assert stage.tick.digest(dirty) == "00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26"
tests = []
for args, cwd, count in (
    ([sys.executable, "-B", str(project / "scripts/test_registered_cluster_probe_20261014.py")], str(project), 6),
    ([sys.executable, "-B", "-m", "unittest", "test_foreground_tick", "test_closure",
      "test_tick_context", "test_closure_multiview"], "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline", 69),
):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, encoding="utf-8", timeout=45)
    tests.append({"returncode": result.returncode, "stdout": result.stdout,
                  "stderr": result.stderr, "expected_tests": count})
    assert result.returncode == 0 and f"Ran {count} tests" in result.stderr
stage.save("monitor_validation", {
    "tests": tests, "monitor_sha256": stage.tick.digest(Path(stage.monitor.__file__)),
    "scoped_test_sha256": stage.tick.digest(project / "scripts/test_registered_cluster_probe_20261014.py"),
    "scope": "Cluster/server4 opt-in exact-PID probe only. Other project/host paths retain legacy discovery. Unknown/malformed observations skip deathwatch instead of declaring absence.",
    "repairs": ["Initial missing shlex import repaired before tests.",
                "Live test discovered configuration loader omitted opt-in field; fixed and regression added.",
                "Live opt-in probe matched actual PID2634704/config/GPU0; increasing native Train12 steps751->756 confirmed."],
})


def ref(path):
    return {"path": path.relative_to(project).as_posix(), "sha256": stage.tick.digest(path)}


files = sorted(path for path in bundle.iterdir() if path.is_file())
files += [project / "scripts/test_registered_cluster_probe_20261014.py"]
references = [ref(path) for path in files]
work_path = project / "pipeline/research_work.json"
work = stage.tick.load(work_path)
ids = ["m95-native-main-role-weight-precedence", "m95-native-relation-other-sign-conflict",
       "m95-native-secondary-positive-mass"]
retry = (datetime.now().astimezone() + timedelta(hours=1)).isoformat()
for cid in ids:
    candidate = next(row for row in work["candidates"] if row["id"] == cid)
    assert candidate["stage"] == "validation"
    assert len(candidate["gates"]) == 6 and all(not value["passed"] for value in candidate["gates"].values())
    for entry in references:
        if entry not in candidate["evidence"]:
            candidate["evidence"].append(entry)
    candidate.update(
        stage="blocked", blocker_kind="exclusive_gpu_slot", required_server="server-4",
        blocker="Non-GPU preparation complete and frozen. Only authorized GPU0/max_tasks1 is occupied by live M201-BPS PID2634704 and its training flock is held; exclusive native parameter-gradient diagnostic cannot run.",
        retry_after=retry,
        unblock_condition="Queue opening on authorized server4 GPU0 plus fresh pinned host/UUID/no-other-compute-process check and exclusive training/diagnostic flocks acquired; >=720 seconds in the current immutable foreground deadline.",
        attempted_alternatives=manifest["attempted_alternatives"],
        frozen_manifest=ref(bundle / "frozen_manifest.json"),
        non_gpu_preparation=ref(bundle / "preparation.json"),
        occupation_evidence=ref(bundle / "exact_training_observation.json"),
        next_action="After actual exclusive GPU0 availability, execute frozen launch_native.py --token <current_owned_token>. Preserve epoch4 SHA, groups0/60/101/124, companions, seed1999, original parameter autograd.grad and absolute1e-6 repeats. Persist actual identity/gradient-repeat/subset/task-dot results; do not infer harm, native repeat repair, independent core or efficacy from preparation.",
        execution_status="Current75d7 event:11 assets/source/epoch4 strict CPU state/identical constant buffers PASS;4 actual native groups x2 getters exact, CUDA uninitialized. AST preserves original scientific functions. Future launcher check-only correctly blocked;0 native/GPU forwards/parameter gradients/optimizer/admissions/new launches. Original source facts/FD/full-forward FAILs and six false gates retained.",
    )
bps = next(row for row in work["candidates"] if row["id"] == "m95-native-between-pair-support")
assert bps["stage"] == "training"
for name in ("exact_training_observation.json", "registered_probe_live.json", "deathwatch_reconciliation.json", "monitor_validation.json"):
    entry = ref(bundle / name)
    if entry not in bps["evidence"]:
        bps["evidence"].append(entry)
bps["execution_status"] = (
    "Current75d7 exact registered PID2634704 on server4 GPU0 matched cwd/config/resume; Train12 steps751->756. "
    "Completed epoch11 best0.47720658779144287/no_improve0. Scoped monitor repair live-verified; false miss1 removed under lock. "
    "Separate GPU process3148713/1656MiB observed, attribution unknown and untouched. No restart/duplicate/scientific admission/efficacy claim."
)
stage.tick.save(work_path, work)
decision = stage.monitor.log_decision(
    str(project), "other", "冻结原生参数梯度实验是否已完成非GPU准备，迁移监控能否可靠识别现有训练？",
    "完成server4资产/AST/检查点/真实输入准备；三条原ID转为真实exclusive_gpu_slot阻塞，保留六门槛false。继续同一训练，修复仅cluster/server4启用的精确PID监控。",
    "11资产SHA通过；epoch4严格CPU加载与四组双读取一致、CUDA未初始化；GPU0训练2634704占单槽且flock持有，启动器check-only拒绝。6专项+69回归测试通过，实机Train12步751->756。所有历史FAIL与实际传输/配置问题保留。",
    str(bundle / "frozen_manifest.json"),
)
notes = {
    "actions": [
        "本轮event固定快照17:09:15+08，截止18:09:15；复用章节0-3，不重复begin/preflight。所有权/19约束/11禁令/server4 GPU0单槽/后台Disabled已核实。",
        "资产传输超时保留；核验部分检查点SHA后sftp续传60938308字节成功。后续全量核验发现十项小资产缺失，逐项补齐；11项资产全哈希与冻结epoch4检查点SHA通过，无源服务器诊断执行。",
        "原科学函数AST一致；仅主机/路径/装载/独占锁适配。server4 CPU真实准备PASS：epoch4严格state加载、两项非持久常量完全一致；原生组0/60/101/124各读取两次，共8次getter，输入重复一致、CUDA未初始化。0 GPU/原生前向、0模型参数梯度、0优化器更新。",
        "冻结manifest及后续租约绑定启动器已落盘；实际check-only返回BLOCKED/GPU launches0。唯一授权GPU0仍由训练2634704占用、训练flock持有，三原ID转blocked/exclusive_gpu_slot，retry_after=" + retry + "；队列开槽与实时无其他进程/独占锁核验会解除阻塞，不等于训练准入。",
        "17:52:11+08精确PID/cwd/config/resume与原生Train12/50步751->756核验；已完成epoch11，Best0.47720658779144287、no_improve0。GPU总32607MiB/使用21751/剩10351/util86%；进程2634704占19998MiB、另3148713占1656MiB归属未知且未处置。未收敛/未达baseline或champion。",
        "修复整机进程枚举挂起造成的假死亡：仅cluster/server4显式启用精确已登记PID探测；未知响应不当缺失。初次shlex缺失及配置loader丢开关问题真实保留、分别修复；6专项+69回归通过、实机探测通过，按锁只清本训练deathwatch1。其他项目默认逻辑、调度、阈值未改。",
        "同一准备支撑三角色子集，不冒称三个独立机制；六科学门槛均false，旧source事实/FD/完整原生重复失败保留。新候选/准入/训练启动均0；真实模型参数梯度实验待独占槽，不宣称全研究路线耗尽。",
        "PDC用户文件SHA保持00d58e60d96a61272d4c8719fbca85fab449252ea84311ee3af09be015b26c26。finish尚未执行，执行状态待postflight；收据用量为begin到收据局部窗口，不含最终回复，未知不填零、缓存属于输入/推理属于输出、不当账单。",
    ],
    "decisions": [
        "继续server4上的同一M201-BPS训练，不重启、不挤占单槽、不处理归属未知GPU进程，不恢复后台。",
        "非GPU准备完成后停止重复研究；等待真实队列开槽，再以新当前租约执行冻结四组原生参数实验。不得改checkpoint/cohort/seed/1e-6门槛或把CPU准备PASS写成科学PASS；下一调度时间未知。",
    ],
}
notes_path = project / "pipeline/reports" / ("notes_" + stage.TOKEN + ".json")
stage.tick.save(notes_path, notes)
print(json.dumps({"ids": ids, "stage": "blocked", "retry_after": retry,
                  "decision": decision, "notes": str(notes_path)}))
