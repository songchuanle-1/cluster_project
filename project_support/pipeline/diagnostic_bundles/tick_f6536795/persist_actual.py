from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys

R = Path("D:/project/cluster_project")
D = Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {"path": p.relative_to(R).as_posix(), "sha256": sha(p)}
def put(p, v):
    with p.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(v, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")

o = read(R / "pipeline/headless/.foreground.lockdir/owner.json")
assert o["token"] == "f653679598744de7ac2fafb23a96c1ea"
assert o["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(o["deadline_at"])
assert sha(R / "pipeline/headless/.tick_context.json") == o["context_sha256"]
assert sha(R / "pipeline/headless/.tick_context_state.next.json") == o["pending_sha256"]
b = read(D / "protected_assets_before.json")
g = ["C:/Program Files (x86)/Git/cmd/git.exe", "--no-optional-locks", "-c",
     "core.fsmonitor=false", "-C", str(R / "Cluster")]
def q(*a): return subprocess.check_output(g + list(a))
index = Path(q("rev-parse", "--git-path", "index").decode().strip())
if not index.is_absolute(): index = R / "Cluster" / index
assert q("rev-parse", "HEAD").decode().strip() == b["head"]
assert sha(index) == b["index_sha256"]
assert q("status", "--porcelain=v1", "--untracked-files=all", "-z").hex() == b["status_hex"]
for n, h in b["files"].items(): assert sha(R / "Cluster" / n) == h, n
for n, h in b["protected_ledgers"].items(): assert sha(R / "pipeline" / n) == h, n
npath = D / "nde_execution/smoke_candidate_execution.json"
fpath = D / "nde_execution/resources_candidate_execution.json"
n, f = read(npath), read(fpath)
assert n["certainty"] == "terminal" and n["returncode"] == 0
assert n["result"]["optimizer_steps"] == 2 and n["result"]["native_smoke_checks_passed"]
assert f["certainty"] == "terminal" and f["returncode"] == -11 and not f.get("result")
review = D / "nde_partial_actual_independent_review.json"
assert read(review)["review_record_passed"]
partial = next((D / "nde_result_active").glob("results_*/partial_actual_results.json"))
assert read(partial)["PASS_artifacts_written"] is False
assert not (D / "nde_execution/resources_champion_request.json").exists()
now = datetime.now(timezone.utc).isoformat()
put(D / "final_integrity.json", {
    "recorded_at": now, "owner_token": o["token"], "passed": True,
    "main_HEAD": b["head"], "main_index_sha256": sha(index),
    "user_files": len(b["files"]), "protected_ledgers": len(b["protected_ledgers"]),
    "native_smoke_terminal": True, "resource_candidate_terminal_returncode": -11,
    "new_admissions": 0, "new_training": 0})
paths = [npath, fpath, review, partial, D / "final_integrity.json",
         D / "resource_crash_evidence/collection.json",
         D / "resource_crash_evidence/resources_candidate_started.json",
         D / "resource_crash_evidence/resources_candidate_completed.json",
         D / "resource_crash_evidence/resources_candidate_stdout.log",
         D / "resource_crash_evidence/resources_candidate_stderr.log",
         D / "run_smoke_candidate_capture.json",
         D / "run_resources_candidate_capture.json",
         D / "run_resources_champion_capture.json",
         D / "nde_normalizer_independent_review.json"]
evidence = [ref(p) for p in paths]
wp = R / "pipeline/research_work.json"
w = read(wp)
c = next(x for x in w["candidates"] if x["id"] == "hierarchy-native-distribution-embedding-composition")
old = w.get("tick_attempt")
if old and not any(x.get("tick_started_at") == old.get("tick_started_at") for x in w.setdefault("tick_attempt_history", [])):
    w["tick_attempt_history"].append(old)
known = {(e["path"], e["sha256"]) for e in c["evidence"]}
c["evidence"] += [e for e in evidence if (e["path"], e["sha256"]) not in known]
revision = c["revision_history"][0]
assert revision["result"] == "pending" and revision["revision"] == 1
outputs = [ref(p) for p in (npath, fpath, review, partial)]
revision["evidence"] += outputs
revision["result_evidence"] = outputs
revision["partial_observation"] = "TRAIN2/core update passed; resource SIGSEGV/-11 with no raw result. Pair and equivalence incomplete; revision pending."
c["native"] = "ACTUAL_PAIRED_TRAIN2_PASSED_NOT_CANONICAL_ADMISSION"
c["resources"] = "ACTUAL_RESOURCE_PROCESS_SIGSEGV_NO_METRICS_CHAMPION_BLOCKED"
c["Torch_autograd"] = "ACTUAL_ORIGINAL_FINITE_LOSS_BACKWARD_WHOLE_CORE_UPDATE"
c["full_forward"] = "ACTUAL_TWO_NATURAL_TRAIN_BATCHES"
c["scientific_admission"] = "NOT_ADMITTED"
c["queued"] = c["deployed"] = c["training_started"] = False
c.setdefault("actual_validation_history", []).append(c["latest_actual_validation"])
c["latest_actual_validation"] = {
    "owner_token": o["token"], "source_commit": c["code_commit"], "revision": 1,
    "smoke_candidate_losses": n["result"]["losses"], "optimizer_steps": 2,
    "paired_common835_and_two_batches_matched": True, "native_review": ref(review),
    "resource_pid": f["pid"], "resource_terminal_returncode": -11,
    "resource_raw_result": None, "flops_g": None, "median_ms": None, "peak_allocated_bytes": None,
    "failure_scope": "implementation/inconclusive; not a new FLOPs budget or mechanism result",
    "champion_resource_executed": False, "champion_resource_remote_request_created": False,
    "champion_resource_blocker": "Original prior-failed guard; local intent exists",
    "equivalence_executed": False, "paired_resources_complete": False,
    "technical_admission_passed": False, "partial_normalization": ref(partial)}
c["current_owner_activation"]["native_execution_started"] = True
c["current_owner_activation"]["terminal_diagnostic_requests"] = ["smoke_candidate", "resources_candidate"]
c["next_action"] = "保留0747本轮原生TRAIN2/common835/整core更新通过及资源PID202438终态SIGSEGV/-11无指标；原priorfailed守护已阻止champion新臂，无远端request/PID。资源/等价未完成、revision1 pending、未准入训练。后续先另存新owner受审的有界崩溃定位方案，查故障前阶段/原样栈；不盲重跑未改失败臂或绕过守护。原46超10G失败、旧champion71/source46 provenance及全部原门保持。"
c["updated_at"] = w["updated_at"] = now
w["tick_attempt"] = {
    "tick_started_at": o["generated_at"], "candidate_id": c["id"],
    "kind": "resource_check", "result": "failed",
    "command": [sys.executable, "-B", "-X", "utf8", str(D / "capture_operation.py"),
                "run", "--mode", "resources", "--target", "candidate"],
    "observation": "原生TRAIN2及匹配对照/整core更新通过；资源进程终态-11/SIGSEGV，无raw指标。champion被priorfailed门拒绝，EQ未执行，normalizer仅partial；不准入或训练。",
    "evidence": [ref(p) for p in (fpath, D / "resource_crash_evidence/collection.json", review, partial)]}
wp.write_text(json.dumps(w, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
mp = R / "pipeline/codex_memory.md"
memory = mp.read_text(encoding="utf-8")
memory = memory[:memory.index("## Last Tick")] + """## Last Tick
- 当前f653679598744de7ac2fafb23a96c1ea generated2026-11-08T03:07:06.793723Z/deadline04:07:06.793723Z；前4fa INCOMPLETE/context未提交/lease released已核。
- 复用0747/b37fe5/active348024冻结native，另存freshowner执行链；软件20及actual stage32独审通过。runtime仍NSD根/f625，candidate为stage overlay，不是部署。
- 03:25:28Z candidate smoke PID191497终态rc0，原两自然TRAIN losses9.142848014831543/13.907115936279297；原loss有限backward/整core weight-module更新通过。独审21证据/192路径谓词与旧champion common835及两批精确匹配；旧champion仍71owner/source46，不重跑/改签。
- 03:28:07Z resourcecandidate PID202438终态-11/SIGSEGV，无raw result，FLOPs/延迟/显存全UNKNOWN；不是新10G超限。原stdout0B/stderr347B仅pynvml警告，无Python traceback；原started/completed/log哈希完整保全，根因UNKNOWN。
- 03:36:53Z reconcile0活worker，原PID/proc不存在。03:37:06Z冠军新资源臂被原priorfailed守护拒绝；本地intent有，远端request/PID无。守护保持，未继续GPU/EQ、不盲重放。
- normalizer软件29项独审通过，实际只保存partial（缺resources_champion_execution.json，PASS_artifacts_written=false）；无完整准入/入队/部署/训练。revision1保持pending、资源/等价NOT_COMPLETE，效力novelty UNKNOWN。
- 下一轮优先受审有界故障定位（阶段/原样崩溃栈），不盲重跑未改资源或绕过priorfailed；不改变三锁/20k/max1/overlay/原协议/精度/原资源计数。原46的10.036472908G失败及全部旧holds/bans/人工暂停保持。
- 本轮末核main/index/28用户文件/40ledger不变；所有实际证据tick_f6536795。以report/finish真实收据核释放，释放后不改记录。
"""
memory = memory.replace("revision1 Torch/数值反向等价/native/resources全部NOT_RUN，revision result保持pending。", "revision1本轮TRAIN2/整core更新通过；资源SIGSEGV无指标，等价未执行，revision pending。")
memory = memory.replace("本轮无已登记项目训练或ready waiting；只两个人工暂停。无remote stage/新native lease/request/PID、无准入/部署/训练。", "无完整训练或ready waiting；两人工暂停保持。本轮f653另存诊断stage/lease，两执行臂已终态；未准入训练。")
memory = memory.replace("native active只是runtime DRAFT单flag变更的本地软件副本；未创建adapter_release/实际native binding/lease/stage，不能称已启用运行。", "本轮复用native active，另存freshowner实际诊断链并执行两臂；未准入完整训练。")
assert len(memory.splitlines()) < 120
mp.write_text(memory, encoding="utf-8")
put(D / "tick_notes.json", {
    "actions": ["复用冻结NDE r1，freshowner binding/stage独审后实际candidate TRAIN2通过；与旧champion common835及两自然批精确匹配，有限原loss backward/整core真实更新成立。",
                "候选资源进程SIGSEGV/-11，无raw资源指标；原stdout0B/stderr347B警告及started/completed/hash保全，根因UNKNOWN。reconcile无活worker。",
                "冠军新臂被原priorfailed门前拒绝；有本地intent，无远端request/PID，EQ未执行。normalizer只partial，不签PASS。",
                "main/index/28用户文件/40ledger末核保持，准备提前report/finish。"],
    "decisions": ["revision1 pending；资源/等价不完整，未准入入队部署训练，不把SIGSEGV解释为机制失败或新10G超限。",
                  "后续先受审有界故障定位，保留原守护、负结果和全部协议/资源/暂停；不盲重跑或绕过priorfailed。"]})
print(json.dumps({"status": "ACTUAL_FAILURE_PERSISTED", "native_steps": 2,
                  "resource_returncode": -11, "new_admissions": 0,
                  "notes": str(D / "tick_notes.json")}))
