"""Preserve the completed champion control and the actual prelaunch refusal."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "5287cf71a0424b018f3d0c77db4950ff"
CID = "hierarchy-native-distribution-embedding-composition"


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


def put(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
baseline = read(HERE / "protected_assets_before.json")
git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks",
       "-c", "core.fsmonitor=false", "-C", str(ROOT / "Cluster")]
def query(*args):
    return subprocess.check_output(git + list(args))
index = Path(query("rev-parse", "--git-path", "index").decode().strip())
if not index.is_absolute():
    index = ROOT / "Cluster" / index
assert query("rev-parse", "HEAD").decode().strip() == baseline["head"]
assert sha(index) == baseline["index_sha256"]
assert query("status", "--porcelain=v1", "--untracked-files=all", "-z").hex() == baseline["status_hex"]
for name, expected in baseline["files"].items():
    assert sha(ROOT / "Cluster" / name) == expected, name
for name, expected in baseline["protected_ledgers"].items():
    assert sha(ROOT / "pipeline" / name) == expected, name

execution_path = HERE / "nde_execution/resources_champion_execution.json"
execution = read(execution_path)
raw = execution["result"]
assert execution["certainty"] == "terminal" and execution["returncode"] == 0
assert raw["execution_completed"] and raw["target"] == "champion"
assert raw["native_predict_calls"] == 121
assert raw["optimizer_steps"] == raw["native_loss_forwards"] == 0
assert len(raw["measurements_ms"]) == 100 and all(math.isfinite(x) and x > 0 for x in raw["measurements_ms"])
review_path = HERE / "ordinary_resource_actual_result_independent_review.json"
review = read(review_path)
assert review["passed"]
blocked = read(HERE / "run_resources_candidate_capture.json")
assert blocked["returncode"] != 0 and "Insufficient unchanged owner deadline" in blocked["stderr_tail"]
for name in ("nde_root_run_resources_candidate_intent.json",
             "nde_execution/resources_candidate_request.json",
             "nde_execution/resources_candidate_execution.json",
             "nde_root_revision1_equivalence_intent.json",
             "nde_equivalence_execution",
             "nde_equivalence_active/operation_release.json"):
    assert not (HERE / name).exists(), name
remote = read(HERE / "final_remote_release_observation.json")
assert all(item["state"] == "available" for item in remote["observation"]["locks"].values())
assert not remote["observation"]["remote_candidate_request_exists"]
now = datetime.now(timezone.utc).isoformat()
put(HERE / "final_integrity.json", {
    "recorded_at": now, "owner_token": TOKEN, "passed": True,
    "main_HEAD": baseline["head"], "main_index_sha256": sha(index),
    "protected_user_files": len(baseline["files"]),
    "protected_ledgers": len(baseline["protected_ledgers"]),
    "champion_terminal_rc0": True, "candidate_refused_before_root_intent_and_request": True,
    "EQ_not_released_or_executed": True, "new_admissions": 0, "new_training": 0,
    "remote_cooperative_locks_available": ref(HERE / "final_remote_release_observation.json")})
paths = [
    execution_path, review_path, HERE / "ordinary_resource_capability.json",
    HERE / "ordinary_resource_capability_independent_review.json",
    HERE / "ordinary_resource_actual_binding_independent_review.json",
    HERE / "candidate_resource_followup_preregistration.json",
    HERE / "candidate_resource_followup_independent_review.json",
    HERE / "run_resources_candidate_capture.json",
    HERE / "run_resources_candidate_capture.stderr.txt",
    HERE / "resource_evidence_champion/collection.json",
    HERE / "nde_execution/execution_binding.json",
    HERE / "nde_execution/execution_lease.json",
    HERE / "nde_execution/native_manifest.json",
    HERE / "nde_execution/stage_execution.json",
    HERE / "nde_equivalence_active/FROZEN.json",
    HERE / "nde_equivalence_active/preparation.json",
    HERE / "final_remote_release_observation.json",
    HERE / "final_integrity.json"]
paths.extend(sorted((HERE / "resource_evidence_champion").glob("*")))
evidence = []
for path in paths:
    entry = ref(path)
    if entry not in evidence:
        evidence.append(entry)
work_path = ROOT / "pipeline/research_work.json"
work = read(work_path)
candidate = next(c for c in work["candidates"] if c["id"] == CID)
frozen_revision = json.dumps(candidate["revision_history"], sort_keys=True)
assert candidate["revision_history"][0]["result"] == "pending"
candidate["evidence"].extend(entry for entry in evidence if entry not in candidate["evidence"])
previous = work.get("tick_attempt")
if previous and not any(x.get("tick_started_at") == previous.get("tick_started_at")
                        for x in work.setdefault("tick_attempt_history", [])):
    work["tick_attempt_history"].append(previous)
work["tick_attempt"] = {
    "tick_started_at": owner["generated_at"], "candidate_id": CID,
    "kind": "resource_check", "result": "passed",
    "command": [sys.executable, "-B", "-X", "utf8", str(HERE / "capture_resources.py"),
                "run", "--mode", "resources", "--target", "champion"],
    "observation": "原口径无插桩champion资源控制真实121predict/rc0；只完成对照臂，不是候选资源配对PASS。candidate在11:49:01Z被原>1020秒守护于root intent/request之前拒绝，未启动；EQ未释放/执行。保留原SIGSEGV/10G失败与pending revision，不延期或绕过守护。",
    "evidence": [ref(execution_path), ref(review_path),
                 ref(HERE / "resource_evidence_champion/collection.json"),
                 ref(HERE / "run_resources_candidate_capture.json")]}
candidate["ordinary_champion_resource_control"] = {
    "owner_token": TOKEN, "status": "ACTUAL_COMPLETE_CHAMPION_ONLY_NOT_PAIRED_ADMISSION",
    "execution": ref(execution_path), "independent_review": ref(review_path),
    "raw_collection": ref(HERE / "resource_evidence_champion/collection.json"),
    "pid": execution["pid"], "returncode": 0,
    "flops_g": raw["profile"]["flops_g"], "median_ms": raw["median_ms"],
    "p90_ms": raw["p90_ms"], "peak_allocated_bytes": raw["peak_allocated_bytes"],
    "instrumented": False, "native_predict_calls": 121,
    "full_optimizer_training_memory": "UNKNOWN",
    "original_no_cluster_resource_delta": "UNKNOWN",
    "next_tick_reuse": "Keep exact original owner/source/runtime/protocol/hash evidence; do not re-sign or rerun this control unless inputs change."}
candidate.setdefault("current_owner_activation_history", []).append(candidate["current_owner_activation"])
candidate["current_owner_activation"] = {
    "owner_token": TOKEN, "actual_binding": ref(HERE / "nde_execution/execution_binding.json"),
    "stage_execution": ref(HERE / "nde_execution/stage_execution.json"),
    "actual_binding_review": ref(HERE / "ordinary_resource_actual_binding_independent_review.json"),
    "diagnostic_only": True, "champion_resource_executed": True,
    "candidate_resource_executed": False, "candidate_deadline_guard_prelaunch": True,
    "native_smoke_repeated": False, "EQ_executed": False, "training_started": False}
candidate["resources"] = "ACTUAL_UNINSTRUMENTED_CHAMPION_COMPLETE_CANDIDATE_PENDING_PRELAUNCH_DEADLINE_REFUSAL"
candidate["next_action"] = (
    "复用5287真实无插桩champion资源控制及原owner/source/runtime/hash，不重测/补签；"
    "原候选资源11:49:01Z因>1020秒守护在root intent/request前拒绝，未启动无未知launch。"
    "下一真实快照尽早另存新owner实际资源capability/binding/lease/stage并独审，复用已审冻结普通14文件/方法，"
    "补ONE未执行的候选无插桩资源；原f653 SIGSEGV与46超10G保持，单次instrumented探针已消费不得重放。"
    "原同口径资源完成并独审后，使用已冻结standalone EQ另存新owner实际链/独审scope，"
    "复用TRAIN2/common835/整core更新与旧champion71/source46，不重复有效检查。"
    "revision1仍pending，无资源配对/等价/准入/入队/训练；守护/20k/max1/三锁/overlay/数据seed协议及人工暂停不变。")
assert json.dumps(candidate["revision_history"], sort_keys=True) == frozen_revision
candidate["updated_at"] = work["updated_at"] = now
work_path.write_text(json.dumps(work, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
memory_path = ROOT / "pipeline/codex_memory.md"
memory = memory_path.read_text(encoding="utf-8")
memory = memory[:memory.index("## Last Tick")] + """## Last Tick
- 5287cf71a0424b018f3d0c77db4950ff generated2026-11-08T11:05:50.038753Z/deadline12:05:50.038753Z；前d0ef已FINALIZED/PASS/context_committed/released。preflight健康，项目完整训练0/ready0，两人工暂停保持。
- 复用普通f653 operational与4fa原14文件，未带crash bootstrap。新owner独立资源capability/静态scope审/实际binding审通过；原worker/resources方法/remote字节保持，prepare11:29:37/stage11:29:49真实核验，free28620MiB/三锁可用且允许外部context。
- 原无插桩champion资源11:45:03→11:45:35真实完成，PID2301732/rc0/121predict，0loss/optimizer步。计数9.762532428G，median70.42729842942208ms/P90 73.84670877363533ms，peak_alloc936763392B。按原bs1/warmup20/repeat100与原计数器；overlay条件记录，不是完整TRAIN显存或no-cluster增量。
- 6份原始文件完整收齐并核hash，stdout102B/stderr44168B/result11931B；独审核实际终态。此champion控制可跨轮按原owner/source/hash复用，不能补签为新owner或重复测量。
- 独立candidate新有界请求scope通过后，wrapper11:49:01Z被原>1020秒remaining保护拒绝（阈值11:48:50Z），在projectlock/root intent/request/远端进程之前，候选未启动无unknown。不延期/放宽/重试；资源配对与EQ仍缺。
- standalone EQ新metadata实际绑定另存nde_equivalence_active，源仅原已审locator适配；尚无operation release/intent/request/执行。不要当作等价PASS。下一轮优先原未执行candidate资源再EQ，复用有效TRAIN2/common835与本轮champion，不再重做。
- 原46超10G/f653 SIGSEGV/仪器化非复现及pending revision1全保留，未新修订/准入/入队/训练。末核main/index/28用户文件/40ledger保持；只读核三锁dev66308/inodes92537152/53/54可用。按真实report/finish收据核释放，释放后不写。
"""
memory = memory.replace(
    "正式资源仍缺，仪器化探针未重现SIGSEGV但不代签资源；等价未执行，revision pending。",
    "5287原无插桩champion资源已完成；候选资源仍缺，仪器化探针不代签；等价未执行，revision pending。")
assert len(memory.splitlines()) < 120
memory_path.write_text(memory, encoding="utf-8")
put(HERE / "tick_notes.json", {
    "actions": [
        "复用原普通14文件与方法，仅新owner资源capability/实际链另存并独审，原原生TRAIN2/common835不重复。",
        "原无插桩champion资源控制PID2301732终态rc0/121predict，计数9.762532428G、median70.4273ms/P9073.8467ms、peak_alloc936763392B。六份原始文件完整保全并独审；仅对照臂完成，资源配对待补。",
        "candidate新请求在11:49:01Z被原>1020秒保护于root intent/request之前拒绝，未启动；EQ未释放或执行。未准入/入队/完整训练，三协作锁和受保护资产末核保持。"],
    "decisions": [
        "不改deadline或放宽原守护，不重放消费探针、旧失败请求或原生TRAIN2。保持全部负结果与pending revision1。",
        "下一轮复用本轮champion真实证据及冻结普通/EQ代码，尽早补候选原口径资源与独立等价；按新快照另存owner实际绑定，不补签或续写旧lease。"]})
print(json.dumps({"status": "CHAMPION_CONTROL_AND_PRELAUNCH_BLOCK_PERSISTED",
                  "new_admissions": 0, "new_training": 0, "candidate_spawned": False}))
