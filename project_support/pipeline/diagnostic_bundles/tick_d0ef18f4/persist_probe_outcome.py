"""Archive the completed fault-localization probe without resource/admission claims."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys

R = Path("D:/project/cluster_project")
D = Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {"path": p.relative_to(R).as_posix(), "sha256": sha(p)}
def put(p, value):
    with p.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")

owner = read(R / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == "d0ef18f480384c67a1e74e5e2b1b93f6"
assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
assert sha(R / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
assert sha(R / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
baseline = read(D / "protected_assets_before.json")
git = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks", "-c",
       "core.fsmonitor=false", "-C", str(R / "Cluster")]
def query(*args): return subprocess.check_output(git + list(args))
index = Path(query("rev-parse", "--git-path", "index").decode().strip())
if not index.is_absolute(): index = R / "Cluster" / index
assert query("rev-parse", "HEAD").decode().strip() == baseline["head"]
assert sha(index) == baseline["index_sha256"]
assert query("status", "--porcelain=v1", "--untracked-files=all", "-z").hex() == baseline["status_hex"]
for name, expected in baseline["files"].items():
    assert sha(R / "Cluster" / name) == expected, name
for name, expected in baseline["protected_ledgers"].items():
    assert sha(R / "pipeline" / name) == expected, name
execution_path = D / "nde_crash_probe_execution/crash_probe_execution.json"
execution = read(execution_path)
assert execution["certainty"] == "terminal" and execution["returncode"] == 0
review_path = D / "nde_fault_probe_actual_independent_review.json"
review = read(review_path)
assert review["passed"] and review["classification"] == "NOT_REPRODUCED_UNDER_INSTRUMENTATION_ONLY"
assert review["repair_established"] is False and review["root_cause_localized"] is False
assert review["comparable_resource_or_latency_evidence"] is False
raw_path = D / "fault_probe_evidence/resources_candidate_result.json"
raw = read(raw_path)
assert raw["execution_completed"] and raw["native_predict_calls"] == 121
assert raw["optimizer_steps"] == raw["native_loss_forwards"] == 0
assert not (D / "nde_execution/resources_champion_request.json").exists()
assert not (D / "nde_execution/resources_candidate_request.json").exists()
now = datetime.now(timezone.utc).isoformat()
put(D / "final_integrity.json", {
    "recorded_at": now, "owner_token": owner["token"], "passed": True,
    "main_HEAD": baseline["head"], "main_index_sha256": sha(index),
    "protected_user_files": len(baseline["files"]),
    "protected_ledgers": len(baseline["protected_ledgers"]),
    "probe_terminal": True, "probe_returncode": 0,
    "ordinary_resource_requests_created": False,
    "new_admissions": 0, "new_training": 0})
paths = [execution_path, review_path, raw_path, D / "final_integrity.json",
         D / "crash_probe_capture.json", D / "fault_probe_evidence/collection.json",
         D / "fault_probe_evidence/crash_probe_started.json",
         D / "fault_probe_evidence/crash_probe_completed.json",
         D / "fault_probe_evidence/crash_probe_stdout.log",
         D / "fault_probe_evidence/crash_probe_stderr.log",
         D / "fault_probe_evidence/fault_localization_markers.jsonl",
         D / "nde_crash_actual_binding_independent_review.json",
         D / "nde_crash_metadata_delta_independent_review.json",
         D / "nde_crash_bootstrap_current_owner_review.json",
         D / "nde_execution/execution_binding.json",
         D / "nde_execution/execution_lease.json",
         D / "nde_execution/native_manifest.json",
         D / "nde_execution/stage_execution.json",
         D / "champion_resource_control_preregistration.json"]
evidence = [ref(path) for path in paths]
wp = R / "pipeline/research_work.json"
work = read(wp)
candidate = next(c for c in work["candidates"] if c["id"] ==
                 "hierarchy-native-distribution-embedding-composition")
assert candidate["revision_history"][0]["result"] == "pending"
known = {(entry["path"], entry["sha256"]) for entry in candidate["evidence"]}
candidate["evidence"].extend(entry for entry in evidence if (entry["path"], entry["sha256"]) not in known)
old_attempt = work.get("tick_attempt")
if old_attempt and not any(x.get("tick_started_at") == old_attempt.get("tick_started_at")
                          for x in work.setdefault("tick_attempt_history", [])):
    work["tick_attempt_history"].append(old_attempt)
work["tick_attempt"] = {
    "tick_started_at": owner["generated_at"], "candidate_id": candidate["id"],
    "kind": "implementation_test", "result": "passed",
    "command": [sys.executable, "-B", "-X", "utf8", str(D / "capture_fault_probe.py")],
    "observation": "唯一受审有界定位探针PID1698516终态rc0；原worker资源函数完成121predict，19有序marker以resources_return/entry_after/hooks_restored结束，无fatal stack。仅仪器化条件下未重现SIGSEGV，不证明修复/根因，不作为可比资源/延迟或准入；普通资源/EQ未执行。",
    "evidence": [ref(path) for path in (execution_path, review_path,
                 D / "fault_probe_evidence/collection.json",
                 D / "fault_probe_evidence/fault_localization_markers.jsonl")]}
candidate.setdefault("diagnostic_fault_localization_history", []).append(candidate.get("diagnostic_fault_localization"))
candidate["diagnostic_fault_localization"] = {
    "owner_token": owner["token"], "status": review["classification"],
    "actual_execution": ref(execution_path), "actual_independent_review": ref(review_path),
    "pid": execution["pid"], "returncode": 0, "marker_count": review["marker_count"],
    "complete_worker_result": ref(raw_path), "worker_predict_calls": 121,
    "instrumented": True, "repair_established": False, "root_cause_localized": False,
    "admission_evidence": False, "comparable_resources_or_latency_evidence": False,
    "single_instrumented_probe_consumed": True, "ordinary_control_not_executed": True}
candidate["current_owner_activation"]["actual_chain_review_pending"] = False
candidate["current_owner_activation"]["actual_binding_review"] = ref(D / "nde_crash_actual_binding_independent_review.json")
candidate["current_owner_activation"]["diagnostic_execution_terminal"] = True
candidate["current_owner_activation"]["instrumented_probe_executed"] = True
candidate["current_owner_activation"]["training_started"] = False
candidate["next_action"] = (
    "仪器化故障定位已真实rc0、原资源函数返回，f653 SIGSEGV在本探针条件下未重现；不是修复/根因或可比资源准入。"
    "单次instrumented max1已消费，不重放。下一优先补从未执行的原无插桩champion resources控制，"
    "需另存匹配实际owner/source/runtime/root/UUID/producer的ordinary-resource capability/scope绑定并独审，"
    "不可复用仅one-crash-probe授权；保持_no_replay/_previous_complete/1020/20k/max1/三锁/外部共享。"
    "随后按适用范围补候选无插桩资源和独立等价；复用已通过TRAIN2/common835及旧champion71/source46，不重复旧检查。"
    "保持原46超10G/f653 SIGSEGV与全部负结果；revision1 pending，未准入/入队/完整训练。")
candidate["updated_at"] = work["updated_at"] = now
wp.write_text(json.dumps(work, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
mp = R / "pipeline/codex_memory.md"
memory = mp.read_text(encoding="utf-8")
memory = memory[:memory.index("## Last Tick")] + """## Last Tick
- 当前d0ef18f480384c67a1e74e5e2b1b93f6 generated2026-11-08T09:10:48.129203Z/deadline10:10:48.129203Z；前2b已FINALIZED/PASS/context_committed/released。无项目完整训练/ready队列，两人工暂停保持。
- 本轮早复用冻结4d3d bootstrap/16文件/特殊operation，仅新owner/2940协议及metadata/hash。原14文件及special remote/root字节、adapter方法不改；新owner审、metadata/actualchain审完成，prepare09:20:09/stage09:20:13 verified，实际free32003MiB/三锁available。
- 唯一探针09:29:24启动，PID1698516/start_ticks174671018，09:30:07终态rc0。原worker完成resources函数/121predict，无训练optimizer或loss步。19有序markers最后resources_return→original_entry_after→hooks_restored，未观察到fatal stack。
- 原started/completed/stdout103B/stderr43723B/markers4123B/worker result12205B完整按SHA保全；独立actual审d728c8…通过，分类NOT_REPRODUCED_UNDER_INSTRUMENTATION_ONLY。原SIGSEGV根因UNKNOWN、未证明修复或未来稳定；仪器化改变计时/可复现性，任何该输出的FLOPs/latency/peak不代签正式资源/准入。
- 单次instrumented max1已消费，不再探针重放。原无插桩champion资源控制虽从未执行，当前actualbinding仅授权one crash-localization request；scope复核明确需另受审ordinary-resource capability，原_previous_complete空检查不构成授权转换。本轮未执行普通资源/EQ、未准入/入队/完整训练。
- 下一轮优先另存ordinary-resource scope/capability的新owner实际链，复用原资源函数、14原文件及历史实测，不再制造探针；先缺champion资源，再按适用范围候选资源与等价。保持_no_replay/priorfailed/1020/20k/max1/三锁/overlay；不盲重放f653失败请求/消费旧probe。
- revision1仍pending，已通过TRAIN2/common835/旧champion71/source46及原46超10G/f653 SIGSEGV全部保留。main/index/28用户文件/40ledger末核保持，所有证据tick_d0ef18f4；report/finish真实收据核释放，释放后不改记录。
"""
memory = memory.replace("资源SIGSEGV无指标，等价未执行，revision pending。", "正式资源仍缺，仪器化探针未重现SIGSEGV但不代签资源；等价未执行，revision pending。")
assert len(memory.splitlines()) < 120
mp.write_text(memory, encoding="utf-8")
put(D / "tick_notes.json", {
    "actions": [
        "复用冻结诊断方法，仅新owner数据重绑定并独审，提前完成实际prepare/stage及原资源/三锁检查。",
        "唯一受审故障探针PID1698516终态rc0，原资源函数完成121predict；19有序markers结束于resources_return/entry_after/hooks_restored，无fatal stack。原六文件按SHA完整保全并独审。",
        "原SIGSEGV在仪器化条件下未重现，根因/修复未确定；输出不作为可比资源/latency或准入。",
        "普通champion资源拟定scope复核发现当前能力仅one crash probe，故未越过能力范围执行。原普通资源/EQ/训练未启动，末核main/index/28用户文件/40ledger保持。"],
    "decisions": [
        "本轮完成有界定位即收尾，instrumented max1已消费；不重放或把诊断成功转成正式资源/准入PASS。",
        "后续优先补缺的无插桩champion资源，但须另受审ordinary-resource capability及新owner实际链；保留原守护、已通过TRAIN2、全部原负结果/人工暂停/数据seed协议。"]})
print(json.dumps({"status": "ACTUAL_INSTRUMENTED_PROBE_OUTCOME_PERSISTED",
                  "classification": review["classification"],
                  "new_admissions": 0, "ordinary_resources_executed": False,
                  "notes": str(D / "tick_notes.json")}))
