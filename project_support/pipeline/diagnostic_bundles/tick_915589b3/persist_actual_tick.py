"""Persist measured current-tick RVE outcomes without admission or source changes."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
TOKEN = "915589b3154c4c3c99b1db658f610a1f"
CID = "fine-leaf-receiver-conditioned-vector-exchange"
assert sys.dont_write_bytecode and os.environ.get("GIT_OPTIONAL_LOCKS") == "0"
owner_raw = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
owner = {k: owner_raw[k] for k in (
    "token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256"
)}
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def evidence(path):
    path = Path(path)
    assert path.is_file() and path.resolve().is_relative_to(ROOT.resolve())
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}


for name, key in ((".tick_context.json", "context_sha256"), (".tick_context_state.next.json", "pending_sha256")):
    assert sha(ROOT / "pipeline/headless" / name) == owner[key]
actual_path = HERE / "rvec_native_execution_v2/run_smoke_candidate_actual.json"
actual = read(actual_path)
result = actual["observation"]["result"]
common = result["original_common_initialization_comparison"]
assert actual["owner"] == result["owner"] == owner
assert actual["observation"]["certainty"] == "terminal"
assert actual["observation"]["returncode"] == 1
assert common["passed"] is False and all(common[k] for k in ("same_names", "same_shapes", "same_dtypes"))
assert common["candidate_tensor_count"] == common["reference_tensor_count"] == 841
assert len(common["different_parameter_names"]) == 252
assert result["optimizer_steps"] == result["native_loss_forwards"] == result["native_criterion_backwards"] == 0
assert common["copied_common_weights"] is False and common["post_reference_rng_substituted"] is False
release_path = HERE / "stage_release_rvec_915589b3b_gpu0.json"
release = read(release_path)
first, second = release["observations"]
assert not first["stage_processes_or_native_trainers"] and not second["additional_project_stage_processes"]
assert all(item["original_inode_matches"] and item["nonblocking_available"] for item in first["original_locks"])
probe = read(HERE / "environment_lineage_prepare/probe_actual.json")
assert [arm["observation"]["import_passed"] for arm in probe["arms"]] == [False, True, False]
files = [
    "previous_native_reconciliation_actual.json",
    "operational_review/previous_native_reconciliation_independent_review.json",
    "current_source/source_version.json",
    "common_init_review/common_init_static_review.json",
    "environment_lineage_prepare/FROZEN.json",
    "environment_lineage_prepare/probe_actual.json",
    "operational_review/environment_lineage_probe_independent_review.json",
    "operational_review/environment_lineage_actual_independent_review.json",
    "rvec_native_prepare/FROZEN.json",
    "operational_review/rvec_native_source_transport_independent_review.json",
    "rvec_native_execution/run_smoke_candidate_actual.json",
    "operational_review/rvec_native_actual_independent_review.json",
    "stage_release_rvec_915589b3_gpu0.json",
    "harness_registry_review/loss_module_alias_assessment.json",
    "rvec_native_prepare_v2/FROZEN.json",
    "operational_review/rvec_native_source_transport_independent_review_v2.json",
    "rvec_native_execution_v2/run_smoke_candidate_actual.json",
    "operational_review/rvec_native_actual_independent_review_v2.json",
    "stage_release_rvec_915589b3b_gpu0.json",
    "revision_plan/conditional_rng_guard_plan.json",
]
refs = [evidence(HERE / name) for name in files]
now = datetime.now(timezone.utc).isoformat()
summary = {
    "schema_version": 1, "owner": owner, "recorded_at": now,
    "candidate_id": CID, "experiment_id": "M234-RVE",
    "source_commit": "0f8cc0f978b38c24e159d3a2d37344f59cc9a0be",
    "runtime_HEAD": "0747f6acec1c61018ec99acf2efa5329c9b3523c",
    "import_contrast": {"direct_isolated": False, "activated_native": True, "activated_isolated": False},
    "first_native_attempt": "HARNESS_DUPLICATE_CRITERION_REGISTRATION_BEFORE_REFERENCE",
    "second_native_attempt": "ACTUAL_COMMON_INITIALIZATION_VALUE_MISMATCH_BEFORE_TRAIN",
    "common": {k: common[k] for k in (
        "passed", "same_names", "same_shapes", "same_dtypes", "candidate_tensor_count",
        "reference_tensor_count", "candidate_sha256", "reference_sha256",
        "candidate_source_initialization_untouched", "copied_common_weights", "post_reference_rng_substituted"
    )},
    "different_common_parameter_count": 252,
    "TRAIN_steps": 0, "loss_forwards": 0, "backwards": 0, "optimizer_updates": 0,
    "resources": "NOT_RUN", "model_source_revision": "NOT_IMPLEMENTED",
    "prelaunch_free_mib": result["before"]["memory_free_mib"],
    "original_three_locks_available_after": True, "stage_processes_and_trainers_after": 0,
    "foreign_contexts_preserved": second["gpu0_contexts"],
    "remaining_time_disposition": "Measured final failure at 02:03:25Z; no further safe reviewed native attempt before original 02:12:12Z deadline. Preserve bounded revision plan for next current-owner tick.",
    "failure_scope": "implementation", "scientific_admission": False,
    "queued": False, "deployed": False, "training_started": False,
    "efficacy": "UNKNOWN", "novelty": "UNKNOWN", "evidence": refs,
}
summary_path = HERE / "current_tick_actual_summary.json"
save(summary_path, summary)
refs.append(evidence(summary_path))
work_path = ROOT / "pipeline/research_work.json"
work_sha_before = sha(work_path)
work = read(work_path)
candidate = next(item for item in work["candidates"] if item["id"] == CID)
assert candidate["stage"] == "validation" and candidate["code_commit"] == summary["source_commit"]
assert not candidate["queued"] and not candidate["training_started"]
assert len(candidate.get("implementation_revisions", [])) == 0
for item in refs:
    if item not in candidate["evidence"]:
        candidate["evidence"].append(item)
candidate.update(
    updated_at=now, failure_scope="implementation",
    common_init="FAILED_ACTUAL_VALUE_COMPARISON_841_COMMON_252_DIFFERENT",
    native="CONSTRUCTED_COMMON_INIT_FAILED_BEFORE_TRAIN",
    latest_native_attempt={
        "owner": owner, "result": "failed", "failure_scope": "implementation",
        "observation": "Actual common names/shapes/dtypes match at841;252 values differ. Reference entry RNG restored; no copied weights/reseed/substitution. Native task loss/TRAIN/backward/update0;resources NOT_RUN.",
        "evidence": [evidence(actual_path), evidence(release_path), evidence(summary_path)],
    },
    next_action="Preserve r0 and all actual failures. Pre-register one bounded constructor RNG-isolation implementation revision under this stable ID before changing source; independently review and save its exact retained version. Use a new current-owner source/environment/runtime/stage/lease binding, then remeasure original common841 values, two natural TRAIN batches/original task loss/all-five-core updates and original resources. Do not reuse consumed intents or broaden exclusions/copy common weights/reseed.",
)
candidate["known_limitations"] = [
    "Native r0 model constructed; actual common initialization failed:841 names/shapes/dtypes match,252 parameter values differ. It is not a mechanism rejection.",
    "Original task loss/two natural TRAIN steps/finite backward/all-five-core updates and resources remain NOT_RUN.",
    *[item for item in candidate.get("known_limitations", []) if not item.startswith(
        ("The nine-file integration", "Toy operator backward"))],
]
previous_attempt = work.get("tick_attempt")
if previous_attempt and previous_attempt not in work.setdefault("tick_attempt_history", []):
    work["tick_attempt_history"].append(previous_attempt)
work["tick_attempt"] = {
    "tick_started_at": owner["generated_at"], "candidate_id": CID,
    "kind": "native_smoke", "result": "failed",
    "command": "python -B -X utf8 pipeline/diagnostic_bundles/tick_915589b3/rvec_native_prepare_v2/run_native_once.py --execute-root --mode smoke --target candidate --source-version current_source/source_version.json --source-version-sha256 475d1b2261d9aad995379e63903bbaf327937c115561f6b7a38996d24b5089c5 --review operational_review/rvec_native_source_transport_independent_review_v2.json --review-sha256 8bc47df31f414e8218da3bd9dc6e5605848e5488f4c85a130adfd033b2806666",
    "observation": "Actual r0 common initialization failed at841 matched names/shapes/dtypes with252 different parameter values, before TRAIN. Import contrast and constructor-only loss alias independently reviewed; all original source/model/training numbers unchanged. Task loss/backward/updates0;resources NOT_RUN;both worker stages terminal and all3 original locks available.",
    "evidence": refs,
}
work["updated_at"] = now
temporary = work_path.with_name("research_work.915589b3.tmp")
assert not temporary.exists()
save(temporary, work)
os.replace(temporary, work_path)
save(HERE / "research_work_update_audit.json", {
    "owner": owner, "recorded_at": now, "before_sha256": work_sha_before,
    "after_sha256": sha(work_path), "only_candidate_id_modified": CID,
    "source_or_protocol_or_queue_or_admission_mutated": False,
})
memory_path = ROOT / "pipeline/codex_memory.md"
memory = memory_path.read_text(encoding="utf-8")
memory = memory.replace(
    "- RVE实际CPU8cases输出/全部可微输入与参数梯度等价、donorcut/跨leaf/并列与padding控制及一次完整孤立operator toy更新通过；RNG恢复/CUDA未初始化。原生模型/两TRAIN步/common-init/原loss整core更新/全部资源尚未测，不借用旧门槛PASS。",
    "- RVE原CPU8cases保持有效。当前r0原生构造已到达，common-init实测841个公共参数名称/形状/dtype一致但252个值不同，原比较门失败；未复制权重/重设seed/放宽排除。TRAIN/loss/backward/update0，资源未测，效力/novelty UNKNOWN。",
)
memory = memory.split("## Last Tick", 1)[0] + """## Last Tick
- 915589b3154c4c3c99b1db658f610a1f；快照2026-11-09T01:12:12Z，原deadline02:12:12Z，按canonical report/finish收尾，不延长。
- 先独立reconcile前轮stage：无项目trainer/残余worker，三原锁dev66308/inodes92537152/53/54可用，runtimeHEAD0747，外部任务保留。
- 三臂真实导入：direct-isolated失败/activated-native通过/activated-isolated失败；普通Python加载用户目录兼容扩展ef0daa5c，隔离模式误选旧egg。只恢复已认证历史激活环境，未安装/改包。
- 新owner源码实核475d1b22…绑定原retained0f8cc0f9；九文件/HEAD/index保持。两次native使用独立stage/lease/intent，未重放旧执行。
- 首次native因baseline Criterion重复注册失败，common-init未测。v2仅按同SHA复用loss模块避免重复装饰，独审通过；没有registry force/clear或模型/数值/RNG修改。
- v2实际common841/252值不同，hash候选c26cf150…/原M9545fb14bd…；reference entry RNG恢复且未复制/重seed。02:03:25Z真实失败在TRAIN前，未准入/入队/部署/训练。
- v2实际fff18fe7…、两次终态/三原锁可用核验995bbd9e…；外部PID1184577/1320411保持。全部资源未测，不把技术结果当效力/novelty。
- 条件RNG guard修订计划800a6b52…仅准备，尚未预注册/实现/提交，revision仍0。下轮先预注册有证据的同ID局部修订，再独审/保存版本/新owner绑定/common-init/TRAIN2/整core/资源；不自动重启历史失败/人工暂停项。
"""
assert len(memory.splitlines()) < 120
memory_path.write_text(memory, encoding="utf-8", newline="\n")
save(HERE / "report_notes.json", {
    "actions": [
        "核验前轮终态和三原锁释放；本轮真实三臂导入识别隔离模式扩展搜索路径差异，恢复已认证历史普通Python环境，不安装或修改包。",
        "两次独立stage执行RVE原生检查：首次检查程序重复注册Criterion；v2经独审仅复用同SHA损失模块。随后实测841公共参数名称/形状/dtype一致但252值不同，按原门在TRAIN前停止。原源码与所有失败保留。",
        "原生task-loss/backward/optimizer/TRAIN步均0，资源未测；尚未准入、入队、部署或训练，不声称效力/新颖性。两stage进程终态，原三锁与外部任务核验保持。",
    ],
    "decisions": [
        "保持M234-RVE validation，失败范围implementation，不作机制否定。截止02:03:25Z实测后保留有证据的条件修订计划；未预注册/实施模型修订，不能在原deadline前安全完成新一轮源码/独审/原生实测。",
        "下轮先预注册同ID局部构造RNG隔离修订，再保存受审版本并使用全新owner绑定测common-init、原两自然TRAIN步和整core/原资源。server4GPU0/20GB/项目max1/三锁及M206/M227独立人工暂停保持。",
    ],
})
print(json.dumps({"status": "ACTUAL_FAILURE_PERSISTED_NO_ADMISSION", "summary_sha256": sha(summary_path),
                  "research_work_sha256": sha(work_path), "memory_lines": len(memory.splitlines())}))
