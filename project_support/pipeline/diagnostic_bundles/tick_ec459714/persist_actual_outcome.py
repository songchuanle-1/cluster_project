"""Archive matched resources and the failed standalone harness honestly."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "ec4597142e314aa7a0478bac13e26402"
CID = "hierarchy-native-distribution-embedding-composition"
def read(p):
    return json.loads(p.read_bytes())
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)}
def put(p, value):
    with p.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")

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

resource_path = HERE / "nde_execution/resources_candidate_execution.json"
resource = read(resource_path)
raw = resource["result"]
assert resource["certainty"] == "terminal" and resource["returncode"] == 0
assert raw["execution_completed"] and raw["native_predict_calls"] == 121
assert raw["optimizer_steps"] == raw["native_loss_forwards"] == 0
resource_review = HERE / "ordinary_resource_actual_result_independent_review.json"
assert read(resource_review)["passed"]
eq_path = HERE / "nde_equivalence_execution/equivalence_execution.json"
eq = read(eq_path)
assert eq["certainty"] == "terminal" and eq["returncode"] == 1
assert eq["result"]["execution_completed"] is False
assert eq["result"]["error_type"] == "AttributeError"
assert "text_encoder" in eq["result"]["error"]
eq_review = HERE / "nde_equivalence_actual_independent_review.json"
assert eq_review.exists()
assert not list((HERE / "nde_result_active").glob("results_*"))
assert not (ROOT / "pipeline/admissions/M233-NDE.json").exists()
now = datetime.now(timezone.utc).isoformat()
put(HERE / "final_integrity.json", {
    "recorded_at": now, "owner_token": TOKEN, "passed": True,
    "main_HEAD": baseline["head"], "main_index_sha256": sha(index),
    "protected_user_files": len(baseline["files"]),
    "protected_ledgers": len(baseline["protected_ledgers"]),
    "resource_candidate_terminal_rc0": True, "EQ_terminal_rc1": True,
    "normalizer_not_executed": True, "new_admissions": 0, "new_training": 0,
    "SERVERS_and_goal_unchanged": True})
paths = [
    resource_path, resource_review, eq_path, eq_review,
    HERE / "ordinary_resource_capability.json",
    HERE / "candidate_resource_followup_preregistration.json",
    HERE / "ordinary_resource_capability_independent_review.json",
    HERE / "ordinary_resource_actual_binding_independent_review.json",
    HERE / "nde_equivalence_root_scope_independent_review.json",
    HERE / "harness_fix_source_independent_review.json",
    HERE / "nde_execution/execution_binding.json",
    HERE / "nde_execution/execution_lease.json",
    HERE / "nde_execution/native_manifest.json",
    HERE / "nde_execution/stage_execution.json",
    HERE / "nde_equivalence_active/FROZEN.json",
    HERE / "equivalence_capture.json",
    HERE / "equivalence_capture.stderr.txt",
    HERE / "nde_normalizer_source_independent_review.json",
    HERE / "nde_result_provenance_prepare/FROZEN.json",
    HERE / "nde_result_active/FROZEN.json",
    HERE / "nde_path_production_prepare/FROZEN.json",
    HERE / "nde_path_production_transport/FROZEN.json",
    HERE / "nde_pointer_prepare/FROZEN.json",
    HERE / "final_integrity.json"]
for folder in ("resource_evidence_candidate", "equivalence_evidence",
               "eq_harness_failure_evidence", "nde_equivalence_harness_fix_prepare"):
    if (HERE / folder).exists():
        paths.extend(sorted(p for p in (HERE / folder).rglob("*") if p.is_file()))
if (HERE / "final_remote_release_observation.json").exists():
    paths.append(HERE / "final_remote_release_observation.json")
evidence = []
for p in paths:
    entry = ref(p)
    if entry not in evidence:
        evidence.append(entry)
wp = ROOT / "pipeline/research_work.json"
work = read(wp)
c = next(c for c in work["candidates"] if c["id"] == CID)
revision_before = json.dumps(c["revision_history"], sort_keys=True)
assert c["revision_history"][0]["result"] == "pending"
for entry in evidence:
    if entry not in c["evidence"]:
        c["evidence"].append(entry)
prior = work.get("tick_attempt")
if prior and not any(x.get("tick_started_at") == prior.get("tick_started_at")
                     for x in work.setdefault("tick_attempt_history", [])):
    work["tick_attempt_history"].append(prior)
work["tick_attempt"] = {
    "tick_started_at": owner["generated_at"], "candidate_id": CID,
    "kind": "implementation_test", "result": "failed",
    "command": [sys.executable, "-B", "-X", "utf8",
                str(HERE / "nde_equivalence_active/run_equivalence_operation.py"),
                "--execute-root", "--operation", "run"],
    "observation": "候选原资源真实rc0且配对10G/15%显存门槛独审通过；随后独立EQ进程真实rc1，原生YAML优化器的全模型paramwise接口访问私有core缺少text_encoder。首fixture前向/反向已发生，但比较结果未持久化、无完成case，等价UNKNOWN；诊断harness错误，不是机制证伪或已证明修复。未normalization/准入/入队/训练。",
    "evidence": [ref(resource_path), ref(resource_review), ref(eq_path), ref(eq_review),
                 ref(HERE / "equivalence_evidence/collection.json")]}
c.setdefault("actual_validation_history", []).append(c.get("latest_actual_validation"))
c["latest_actual_validation"] = {
    "owner_token": TOKEN, "source_commit": c["source_commit"], "revision": 1,
    "native_TRAIN2": "REUSE_VALID_F653_AND_HISTORICAL71_EXPLICIT_ORIGINAL_OWNERS",
    "native_review": {
        "path": "pipeline/diagnostic_bundles/tick_f6536795/nde_partial_actual_independent_review.json",
        "sha256": "c1a1287b19c3cfc6397e58db68279a357915c0585e67364df23869a9d58bb5cc"},
    "resource_candidate": ref(resource_path), "resource_independent_review": ref(resource_review),
    "champion_resource_original_owner": "5287cf71a0424b018f3d0c77db4950ff",
    "paired_original_resources_complete": True, "original_10G_and_15percent_memory_gates_passed": True,
    "candidate_flops_g": raw["profile"]["flops_g"],
    "candidate_peak_allocated_bytes": raw["peak_allocated_bytes"],
    "candidate_median_ms": raw["median_ms"], "candidate_p90_ms": raw["p90_ms"],
    "latency_interpretation": "Observed slower than historical champion under different external GPU contexts; no causal attribution or speedup claim.",
    "full_optimizer_training_memory_and_no_cluster_delta": "UNKNOWN",
    "EQ_execution": ref(eq_path), "EQ_independent_review": ref(eq_review),
    "EQ_returncode": 1, "equivalence_passed": None, "equivalence_conclusion": "UNKNOWN_HARNESS_INTERFACE_FAILURE",
    "model_revision_falsified": False, "technical_admission_passed": False,
    "normalizer_executed": False, "training_started": False}
c.setdefault("current_owner_activation_history", []).append(c["current_owner_activation"])
c["current_owner_activation"] = {
    "owner_token": TOKEN, "actual_binding": ref(HERE / "nde_execution/execution_binding.json"),
    "stage_execution": ref(HERE / "nde_execution/stage_execution.json"),
    "actual_binding_review": ref(HERE / "ordinary_resource_actual_binding_independent_review.json"),
    "diagnostic_only": True, "candidate_resource_executed": True,
    "EQ_executed": True, "EQ_terminal_rc1": True,
    "native_smoke_repeated": False, "training_started": False}
c["resources"] = "ACTUAL_ORIGINAL_PAIRED_RESOURCE_GATES_PASSED_EXPLICIT_CROSS_OWNER_PROVENANCE"
c["partial_revision_observation"] = "TRAIN2/common835/core update retained; uninstrumented resources passed original gates. Standalone EQ failed at full-model optimizer grouping interface; core equivalence UNKNOWN, revision remains pending."
c["equivalence_harness_repair"] = {
    "scope": "DIAGNOSTIC_HARNESS_ONLY_NOT_MODEL_REVISION2",
    "preparation": ref(HERE / "nde_equivalence_harness_fix_prepare/FROZEN.json"),
    "independent_software_review": ref(HERE / "harness_fix_source_independent_review.json"),
    "new_entry_sha256": "ed2c1bb56d5a27040ae6557c061bbeb64d5e9c0c76646bc25caa09584e00febc",
    "software_and_stdlib_mock_passed": True, "actual_fixed_EQ": "NOT_RUN",
    "requires_fresh_owner_capability_stage_manifest_lease": True}
c["next_action"] = (
    "复用ec候选和5287冠军原资源实测/独审以及f653+71原TRAIN2/common835/整core证据，不重测/补签。"
    "EQ实际PID2840900/rc1，full-model paramwise optimizer对private core访问text_encoder失败；"
    "首fixture已做前向/反向但无完成case/持久比较，不能称core等价失败或通过。"
    "原EQcapmax1已消费，不重放旧intent/lease/stage，不再本ownerGPU。"
    "仅修诊断harness：按原YAML五组native builder将core放dec组，另四组为空carrier，"
    "不改原模型0747/数值/tolerance/fixture/negative control/RNG；已采实际gorilla源b0ceec0b供审。"
    "下一真实快照复用新harness冻结修复包，另存新owner/source/runtime/root/UUID/producer/entrySHA的stage/lease/cap并独审，"
    "实际EQ全通过后再用已备provenance normalizer/独审、passed revision摘要与receipt准入/队列/安全同步/新生产shim及原dispatcher核步数。"
    "原46超10G/f653 SIGSEGV/d0ef非复现全保留；revision1 pending，未新增模型修订/准入/入队/训练，人工暂停及20k/max1/三锁/overlay保持。")
assert json.dumps(c["revision_history"], sort_keys=True) == revision_before
c["updated_at"] = work["updated_at"] = now
wp.write_text(json.dumps(work, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
mp = ROOT / "pipeline/codex_memory.md"
memory = mp.read_text(encoding="utf-8")
memory = memory[:memory.index("## Last Tick")] + """## Last Tick
- ec4597142e314aa7a0478bac13e26402 generated2026-11-08T13:10:13.081564Z/deadline14:10:13.081564Z；前5287已FINALIZED/PASS/context_committed/released。preflight健康，无项目完整训练/ready，M206/M227人工暂停保持。
- 原普通14文件/workerb37/runtime348/模型0747/原资源方法复用，另存新owner资源cap/实际链并独审；prepare13:21:48/stage13:23:13真实，free25451MiB/三锁available，外部context允许且未触碰。
- 候选原无插桩资源13:32:04→13:32:55，PID2774468/rc0/121predict、0loss/optimizer步；原计数9.930828876G<=10G、peak_alloc932033536B比5287champ936763392B低0.5049%，+15%条件不触发，7dc56b…独审通过。
- candidate median196.9578533899039ms/P90203.52482080925256ms，比旧champ70.4273/73.8467慢；两次外部context不同，保留真实观察不因果归因/不称加速。Full optimizer训练显存/no-cluster增量仍UNKNOWN。6份原始文件完整收齐/核hash。
- ONE standalone EQ新scope及实际链由root独审、资源先独审通过后，13:47:15→13:47:27执行PID2840900/终态rc1。原entry82b3在native gorilla paramwise optimizer对privatecore getattr(text_encoder)报AttributeError。首fixture前向/反向发生，但无完成case/持久比较，等价UNKNOWN，不是模型机制证伪或修复。
- EQ六原始文件完整收齐；08e23e…独审核失败。原EQmax1已消费，不再本ownerGPU/重放。保持revision1 pending，修的是诊断harness而非模型revision2；采实际gorilla/solver/build.py SHA b0ceec0b…与YAML五组优化器，供新冻结修复/独审。
- 后续只修core carrier：text_encoder/input_conv/unet/output_layer为空，dec=原core，完整原五组YAML native builder/默认AdamW/参数顺序；不改model0747/fixture/默认容差/negativecontrol/RNG。新harness实际通过后才normalizer/准入/队列/部署训练；复用所有有效原生/资源证据不重测/补签。
- harness修复新entry ed2c1bb…已另存FROZEN d675efd…；独立软件/mock审2022e7…通过，复现旧缺属性并验证五组身份/顺序/过滤/原options。仅准备，不是实际数值等价PASS，下一快照需新owner/cap/stage/manifest/lease/entrySHA。
- provenance normalizer新准备/源独审通过但未执行，无PASS/draft receipt；新生产core/factory复用/传输pointer包prospective disabled，无安装/发布/改SERVERS/主干/调度。原46超10G/f653 SIGSEGV/d0ef非复现全保留。
- mainf625/index/28用户文件/40ledger末核保持，无新准入/入队/训练。按真实report/finish收据核释放；释放后不写。
"""
memory = memory.replace("本轮先于新实现01:23:19Z预注册revision1", "2026-11-08 01:23:19Z先于新实现预注册revision1")
memory = memory.replace("champion资源未执行，normalizer只partial", "该原46测试当时champion资源未执行，normalizer只partial")
memory = memory.replace("5287原无插桩champion资源已完成；候选资源仍缺，仪器化探针不代签；等价未执行，revision pending。",
                        "ec与5287原资源配对门槛通过；独立EQ因harness优化器接口错误未完成，等价UNKNOWN/revision pending。")
assert len(memory.splitlines()) < 120
mp.write_text(memory, encoding="utf-8")
put(HERE / "tick_notes.json", {
    "actions": [
        "复用原普通14文件和有效TRAIN2/common835，另存新owner资源实际绑定/lease/stage并独审；候选原无插桩资源PID2774468终态rc0。",
        "原资源配对门槛独审通过：候选9.930828876G<=10G，peak_alloc相对champ低0.5049%。候选实测median/P90较旧champ慢且外部context不同，不作因果归因或加速声称；六份原始资源文件完整保全。",
        "独立EQ新实际链与scope审后真实执行PID2840900/rc1；native paramwise optimizer期待全模型text_encoder，而输入是私有core，诊断harness中断。无完成case/等价结论，六原始文件完整保全并独审。",
        "仅准备harness修复及复用provenance normalizer/生产core元数据；未执行normalizer、准入、入队、同步部署或训练；main/index/28用户文件/40ledger保持。"],
    "decisions": [
        "保留原模型revision1 pending和全部原负结果；EQ接口失败不等于核心等价被证伪。旧EQmax1消费，不再本ownerGPU、不改守护或重放。",
        "下一快照优先完成独立harness修复审查及新entrySHA/实际owner链的EQ；复用全部有效原生/资源证据，通过后继续normalizer/独审/准入/派发。"]})
print(json.dumps({"status": "RESOURCE_PASS_AND_EQ_HARNESS_FAILURE_PERSISTED",
                  "revision": "pending", "new_admissions": 0, "new_training": 0}))
