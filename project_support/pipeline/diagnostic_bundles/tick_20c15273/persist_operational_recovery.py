"""Persist actual postlaunch protection and preserve every earlier disposition."""
from datetime import datetime, timezone
from pathlib import Path
import copy
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
PIPE = ROOT / "pipeline"
HERE = Path(__file__).resolve().parent
TOKEN = "20c15273b622479495bada469c5f3c99"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CID = "hierarchy-native-variance-decomposition-composition"
SOURCE = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
sys.path.insert(0, str(SKILL))
import pipeline_monitor as mon


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    owner = read(PIPE / "headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(PIPE / "headless/.tick_context.json") == owner["context_sha256"]
    assert sha(PIPE / "headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return {k: owner[k] for k in (
        "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256",
    )}


def write_new(path, value):
    with path.open("x", encoding="utf8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def git(*args):
    return subprocess.check_output(
        ["git", "-C", str(ROOT / "Cluster"), *args], text=True, encoding="utf8",
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
    ).strip()


def preservation():
    index_path = Path(git("rev-parse", "--git-path", "index"))
    if not index_path.is_absolute():
        index_path = ROOT / "Cluster" / index_path
    return {
        "main_head": git("rev-parse", "HEAD"),
        "main_parent": git("rev-parse", "HEAD^"),
        "index_sha256": sha(index_path),
        "git_status_porcelain": git("status", "--porcelain", "--untracked-files=no"),
        "fixed_files": {name: sha(ROOT / name) for name in (
            "SERVERS.yaml", "pipeline/goal.json", "pipeline/queue.json",
            "pipeline/running.json", "pipeline/execution_mode.json",
            "pipeline/authorizations/server4_gpu0_overlay_20261104.json",
            "pipeline/admissions/M230-HVD.json",
        )},
    }


owner = guard()
assert not (HERE / "persist_result.json").exists(), "Do not replay state persistence"
final_path = HERE / "hvd_live_final.json"
observed = read(final_path)["observation"]
start_path = HERE / "guardian_start_result.json"
started = json.loads(read(start_path)["stdout"])
review_path = HERE / "hvd_guardian_actual_independent_review.json"
review = read(review_path)
assert review.get("passed") is True
assert observed["pid"] == 2829477 and observed["starttime"] == "158248846"
assert observed["source_commit"] == SOURCE
assert started["spawn"]["guardian_pid"] == 3024669
assert started["spawn"]["guardian_starttime"] == "158549879"
assert started["live_three_locks_confirmed"] is True
assert len(observed["locks"]) == 3
for lock in observed["locks"]:
    assert len(lock["kernel_entries"]) == 1
    row = lock["kernel_entries"][0].split()
    assert row[1] == "FLOCK" and row[3] == "WRITE" and row[4] == "3024669"
first, second = observed["samples"]
assert first["last_native_phase_progress"][:3] == second["last_native_phase_progress"][:3] == ["Train", "3", "50"]
assert int(second["last_native_phase_progress"][3]) > int(first["last_native_phase_progress"][3])
assert not first["fatal_error_markers"] and not second["fatal_error_markers"]
assert observed["stages"]["m230_12e364dc"]["exists"] is False
assert observed["stages"]["m230_20c15273"]["state.json"]["status"] == "HOLDING"
evidence_paths = [
    HERE / "hvd_live_before.json", HERE / "binding.json",
    HERE / "hvd_guardian_prelaunch_independent_review.json",
    HERE / "guardian_start_request.json", start_path,
    HERE / "hvd_live_after.json", final_path, review_path,
    HERE / "postflight_operational_recovery_audit.json",
    ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/hvd_actual_postlaunch_reconciliation.json",
    ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/hvd_canonical_launch_reconciliation.json",
    ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/hvd_dispatch_v3_independent_review.json",
    ROOT / "pipeline/diagnostic_bundles/tick_12e364dc/hvd_guardian_root_fix/actual_start.json",
    ROOT / "pipeline/tick_receipts/12e364dc14cd4e1195532c7fd295b834.json",
]
evidence = [ref(path) for path in evidence_paths]
now = datetime.now(timezone.utc).isoformat()
lock = mon.acquire_lock(str(ROOT))
assert lock is not None, "No concurrent pipeline state writer allowed"
try:
    owner = guard()
    before = preservation()
    assert before["main_head"] == SOURCE
    assert before["main_parent"] == "07ef534a6e44f22bd7b2d083550ebd7823d1d3d3"
    work_path = PIPE / "research_work.json"
    old_bytes = work_path.read_bytes()
    with (HERE / "research_work_before.json").open("xb") as stream:
        stream.write(old_bytes)
    with (HERE / "codex_memory_before.md").open("xb") as stream:
        stream.write((PIPE / "codex_memory.md").read_bytes())
    work = read(work_path)
    candidates = work["candidates"]
    sequence = list(candidates.values()) if isinstance(candidates, dict) else candidates
    candidate = next(c for c in sequence if c.get("id") == CID)
    untouched = {c["id"]: copy.deepcopy(c) for c in sequence if c["id"] != CID}
    task = next(t for t in read(PIPE / "queue.json")["gpu_queues"]["server-4"] if t["id"] == "M230-HVD")
    assert task["status"] == "running" and task["launch_verified"] is True and task["pid"] == 2829477
    correction_keys = (
        "resources", "full_forward", "implementation_status", "actual_parent",
        "source_version_status", "future_version_parent_scope", "native_execution_blocker",
        "unblock_condition", "training_status", "launch_verified", "launch_protection", "next_action",
    )
    candidate.setdefault("operational_state_correction_history", []).append({
        "recorded_at": now, "owner": owner,
        "previous_fields": {key: copy.deepcopy(candidate.get(key)) for key in correction_keys},
        "reason": "Reconcile stale prelaunch labels with already completed native/resource admission, single real launch, canonical progress reconciliation and current measured postlaunch CPU guardian. Preserve old negatives and no prelaunch-lock assertion.",
    })
    candidate.update({
        "stage": "training", "training_status": "running",
        "launch_verified": True, "launch_verification": "training_progress",
        "resources": "ACTUAL_ORIGINAL_PAIRED_RESOURCES_PASSED",
        "full_forward": "ACTUAL_ORIGINAL_TRAIN2_FULL_FORWARD_BACKWARD_PASSED",
        "implementation_status": "TESTED_SOURCE_DEPLOYED_NATIVE_TRAINING_VERIFIED",
        "actual_parent": before["main_parent"],
        "source_version_status": "TESTED_D20_SOURCE_PROMOTED_AND_DEPLOYED",
        "future_version_parent_scope": "HVD d20 is the tested main/runtime version, parent07ef. Original e38(parent6bc), compatibility evidence and old frozen NULL packets remain historical; no global rebinding.",
        "updated_at": now,
        "native_execution_blocker": None,
        "unblock_condition": "Existing HVD trainer holds the one project GPU0 slot. Observe only until natural terminal; preserve all manually paused tasks. Future new launches require actual direct-Popen lock inheritance proof and fresh resource/owner binding.",
        "next_action": "Read-only monitor this exact HVD PID2829477/start158248846 and CPU guardian3024669/start158549879/three kernel locks, bounded native progress/validations/natural terminal. Never relaunch. PSC0ccc native/resources await natural project-slot release and fresh reviewed execution binding; the Bash-only shim is insufficient for any future direct Popen launch.",
    })
    candidate["native_execution_blocker_history"] = candidate.get("native_execution_blocker_history", [])
    previous_blocker = candidate["operational_state_correction_history"][-1]["previous_fields"].get("native_execution_blocker")
    if previous_blocker:
        candidate["native_execution_blocker_history"].append({
            "superseded_at": now, "previous": previous_blocker,
            "reason": "NEC completed and HVD was admitted/deployed and actually launched; historical observation retained.",
        })
    candidate["launch_protection"] = {
        "status": "ACTUAL_POSTLAUNCH_CPU_GUARDIAN_THREE_LOCKS_HOLDING",
        "guardian_pid": 3024669, "guardian_starttime": "158549879",
        "trainer_pid": 2829477, "trainer_starttime": "158248846",
        "remote_stage": "/data/songcl/Project/Cluster_project/pipeline/cooperative_guards/m230_20c15273",
        "locks_acquired_at": started["state"]["locks_acquired_at"],
        "postlaunch_correction": True, "prelaunch_lock_check_proven": False,
        "training_restarted": False, "signals_sent": False, "GPU_calls": False,
        "lifetime": "Exact trainer natural pidfd exit only; initial owner deadline controls startup only.",
        "evidence": [ref(start_path), ref(final_path), ref(review_path)],
        "remaining_launcher_defect": "Current conda_source Bash function does not intercept closure.safe_launch direct subprocess.Popen(['python',...]) via PATH. Old Bash CPU proof was not proof of actual launch lock inheritance. Require a separately reviewed actual executable-PATH or FD proof before any subsequent new trainer launch.",
    }
    candidate["current_training_observation"] = {
        "observed_at": observed["observed_at"], "pid": 2829477, "starttime": "158248846",
        "native_train_epoch": 3, "native_steps": [357, 362], "steps_per_epoch": 4686,
        "recent_printed_validation_miou": [0.337, 0.383],
        "precision_scope": "Rounded native phase metrics, not exact terminal best.",
        "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "evidence": ref(final_path),
    }
    for item in evidence:
        if item not in candidate["evidence"]:
            candidate["evidence"].append(item)
    if work.get("tick_attempt"):
        work.setdefault("tick_attempt_history", []).append(copy.deepcopy(work["tick_attempt"]))
    work["tick_attempt"] = {
        "tick_started_at": owner["generated_at"], "candidate_id": CID,
        "kind": "resource_check", "result": "passed",
        "command": "python -B -X utf8 pipeline/diagnostic_bundles/tick_20c15273/start_hvd_cooperative_guardian.py; python -B -X utf8 pipeline/diagnostic_bundles/tick_20c15273/observe_hvd.py final",
        "observation": "Actual CPU-only postlaunch repair for the exact already-running HVD trainer: guardian3024669 acquired all three existing-inode FLOCK WRITE locks, then same trainer2829477/start158248846 advanced epoch3 TRAIN357->362/4686 while all locks remained held. No GPU work, signal, new trainer, restart or scientific resource retest. Prelaunch-lock proof remains false; old expired/hash-mismatch evidence retained.",
        "evidence": [ref(start_path), ref(final_path), ref(review_path)],
    }
    work["current_training_protection"] = copy.deepcopy(candidate["launch_protection"])
    work["updated_at"] = now
    for c in sequence:
        if c["id"] != CID:
            assert c == untouched[c["id"]]
    guard()
    temp = work_path.with_name("research_work." + TOKEN[:8] + ".tmp")
    write_new(temp, work)
    os.replace(temp, work_path)
    decision_path = mon.log_decision(
        str(ROOT), "other",
        "HVD已单次真实启动并由canonical核实，但实际direct Popen未继承三协作锁；旧owner的纠正启动在过期断言前拒绝。",
        "当前owner另存审查绑定并只启动一次CPU guardian3024669，为现有trainer2829477补持training/diagnostic/exclusive三FLOCK；原生epoch3步骤357→362已实测。",
        "用户已授权继续与外部共享；保留项目max1。仅保护原进程，不发送信号、重启、迁移或新增GPU任务；prelaunch_lock_check_proven=false。旧12e INCOMPLETE、Bash-only证明局限和字节哈希失配证据全部保留。",
        "; ".join(item["path"] + " SHA" + item["sha256"] for item in (
            ref(start_path), ref(final_path), ref(review_path),
        )),
    )
    after = preservation()
    assert before == after, "User index/main/queue/running/configs must remain unchanged"
    write_new(HERE / "persist_result.json", {
        "recorded_at": now, "owner": owner, "passed": True,
        "before_preservation": before, "after_preservation": after,
        "other_candidate_records_unchanged": len(untouched),
        "new_candidates": 0, "new_admissions": 0, "new_training_launches": 0,
        "CPU_guardian_starts": 1,
        "research_work_before_sha256": hashlib.sha256(old_bytes).hexdigest(),
        "research_work_after_sha256": sha(work_path),
        "decision": ref(Path(decision_path)),
        "evidence": evidence,
    })
finally:
    lock.close()
print(json.dumps({
    "HVD_stage": "training", "resource_check": "actual_postlaunch_cooperative_locks_passed",
    "other_candidates_preserved": len(untouched), "queue_index_main_preserved": True,
    "new_training_launches": 0, "evidence": ref(HERE / "persist_result.json"),
}))
