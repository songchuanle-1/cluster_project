"""Finalize current hashed facts, notes and an honest deadline disposition."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "pipeline/reports"
TOKEN = "66fa1e81aec94d5eb10265ea533669ac"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def reference(path):
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
deadline = datetime.fromisoformat(owner["deadline_at"])
remaining = (deadline - datetime.now(deadline.tzinfo)).total_seconds()
prefixes = ("between_pair_inventory", "between_pair_typed_inventory", "between_pair_controls",
            "between_pair_native", "between_support_excess", "between_parameter_readout")
paths = {name: P / (name + "_" + TOKEN + ".json") for name in prefixes}
data = {name: read(path) for name, path in paths.items()}
native = data["between_pair_native"]
excess = data["between_support_excess"]
parameters = data["between_parameter_readout"]
expected = {row["selection"]["group"]: row["input_sha256"] for row in native["rows"]}
assert all(row["input_sha256"] == expected[row["selection"]["group"]]
           for result in (excess, parameters) for row in result["rows"])
summary = {
    "tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
    "snapshot_at": "2026-10-13T18:09:42.565182+00:00",
    "deadline_at": deadline.isoformat(), "remaining_seconds_at_summary": remaining,
    "remote_cpu_runs": 3, "successful_gpu_runs": 3,
    "gpu_completed_group_readouts": sum(len(result["rows"]) for result in (native, excess, parameters)),
    "unique_gpu_groups": len(expected),
    "unique_gpu_expressions": sum(len(row["selection"]["ann_ids"]) for row in native["rows"]),
    "source_train_denominator": 36665,
    "metadata_counts": data["between_pair_inventory"]["counts"],
    "typed_geometry_controls": data["between_pair_controls"]["cohorts"]["typed"]["counts"],
    "center_nonzero_query_gradient_groups": sum(row["between_readout"]["final_query_gradient_norm"] > 0
                                               for row in native["rows"]),
    "support_nonzero_query_gradient_groups": sum(row["between_readout"]["final_query_gradient_norm"] > 0
                                                for row in excess["rows"]),
    "gt_self_excess_max": max(case.get("gt_mask_proxy_loss", 0) for row in excess["rows"]
                             for case in row["between_readout"]["cases"]),
    "parameter_nonzero_groups": sum(row["between_readout"]["parameter_readout"]["original_nonzero_tensors"] > 0
                                    for row in parameters["rows"]),
    "original_trainable_tensors": parameters["rows"][0]["between_readout"]["parameter_readout"]["original_trainable_tensor_count"],
    "maximum_original_finite_nonzero_tensors": max(row["between_readout"]["parameter_readout"]["original_nonzero_tensors"]
                                                 for row in parameters["rows"]),
    "same_capture_parameter_repeat_max_delta": max(row["between_readout"]["parameter_readout"]["same_capture_original_parameter_repeat_max_delta"]
                                                  for row in parameters["rows"]),
    "maximum_allocator_allocated_mib": max(result["allocator_peak_allocated_mib"] for result in (native, excess, parameters)),
    "maximum_allocator_reserved_mib": max(result["allocator_peak_reserved_mib"] for result in (native, excess, parameters)),
    "optimizer_steps": 0, "new_model_variants": 0, "training_admissions": 0,
    "historical_strict_full_forward_failures_retained": True,
    "scope": "Original checkpoint diagnostics; same-capture parameter repeat is not independent/full-model backward, exclusive efficiency, efficacy or novelty certification.",
    "evidence": [reference(path) for path in paths.values()]
}
resource_command = (
    "date -Iseconds; nvidia-smi -i 7 --query-gpu=uuid,memory.used,memory.free,memory.total,utilization.gpu "
    "--format=csv,noheader,nounits; nvidia-smi -i 7 --query-compute-apps=pid,process_name,used_memory "
    "--format=csv,noheader,nounits; flock -n /tmp/cluster_project_gpu7_diagnostic.lock true; "
    "flock -n /tmp/cluster_project_gpu7_slot2_diagnostic.lock true")
probe = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "songcl@100.64.3.28", resource_command],
                       capture_output=True, text=True, timeout=30)
summary["post_probe"] = {"local_verified_at": datetime.now(timezone.utc).astimezone().isoformat(),
                         "exit": probe.returncode, "remote_output": probe.stdout.strip(),
                         "error": probe.stderr.strip(),
                         "meaning": "Both project diagnostic locks reacquirable only if exit0; foreign resident preserved."}
output = P / "between_tick_summary_20261014_0209.json"
with output.open("x") as stream:
    json.dump(summary, stream, indent=2)
    stream.write("\n")
refs = summary["evidence"] + [
    reference(output),
    reference(ROOT / "pipeline/reviews/motivation_review_20261014_0209.md"),
    reference(ROOT / "pipeline/designs/between_pair_history_addendum_20261014_0220.md"),
    reference(ROOT / "pipeline/designs/between_native_prereg_20261014_0235.md"),
    reference(ROOT / "pipeline/designs/between_support_excess_addendum_20261014_0246.md"),
    reference(ROOT / "pipeline/designs/between_parameter_addendum_20261014_0258.md"),
    reference(ROOT / "pipeline/references/relation_primary_20261014_0209/manifest.json")]
update = {
    "stage": "validation",
    "execution_status": "Current tick diagnostics completed; actual postflight not yet run",
    "scientific_scope": "Centroid realization no-op retained; coherent support-excess active on4nativegroups and362originaltensors, GTself0. Unknown events/true witness IDs, whole-method novelty and historical full-forward failures retained.",
    "next_action": "Implement independent model/config for coherent-pair support-excess using verified TRAIN event/physical-category metadata; preserve original inference and frozen schedule. Then full native batch1/batch2 repeated forward/backward, GT/identity/fragmented/disjoint/radial/bypass controls, same-protocol baseline/champion efficiency and six admission gates. No scalar repair, fake anchor labels, unverified novelty, fabricated cooldown or automatic training.",
    "gates": {
        "diagnosis": {"passed": False, "status": "task_relevant_physical_support_path_observed; true_witness_identity_and_production_metadata_coverage_unverified"},
        "controls": {"passed": False, "status": "native_prototype_GT_identity_fragmented_disjoint_radial_controls_executed; independent_model_controls_pending"},
        "native_backward": {"passed": False, "status": "362original_parameter_tensors_nonzero_finite4groups; no_independent_full_model_repeated_backward"},
        "resources": {"passed": False, "status": "shared_diagnostic_peak3684.29MiB_reserved3974; uniform_candidate_efficiency_pending"},
        "independence": {"passed": False, "status": "no_independent_model/config; known_ternary_and_alignment_primitives_not_claimed_new"},
        "constraints": {"passed": False, "status": "frozen_goal_bans_schedule_preserved; no_admission_receipt"}
    },
    "evidence": refs}
with (P / "between_work_update_20261014_0209.json").open("x") as stream:
    json.dump(update, stream, indent=2)
    stream.write("\n")
notes = {
    "actions": [
        "科学状态validation：本轮先续做3个来源候选的AST信息流检查，再新建1个BETWEEN诊断候选。3次远端CPU诊断、3次GPU原生诊断，24组完成读数，去重8组32表达；无优化器步、新模型、准入或训练。",
        "全TRAIN36665表达：literal BETWEEN2157、root BETWEEN1511、双直接节点675。初始宽松节点枚举混入非BETWEEN节点，归属已撤回；typed样本另行冻结，不用缺失类别或未知身份当作负证据。",
        "typed物理控制100个不同ID候选对：80正间隙、20重叠未知；5组连续读数分离、3组成员状态分离。对照通过不表示真实参照物已标注。",
        "中心间隙原型8组全部零损失/零query梯度。支持质量分布原型4组梯度有限非零，6条可解释GT自损失0；2条事件不可用。362个原始参数张量在4组非零有限，同次捕获重复最大差0；不替代独立模型或历史全forward严格失败。",
        "已核对原始NS3D/EDA并归档原文哈希；三元关系/文本解耦不是创新声明。与碎片化参照、非参照物配对和GT径向形状控制的原生梯度不同，仍不证明训练收益或整体新颖性。",
        f"最新资源核验本地{summary['post_probe']['local_verified_at']}，远端时钟单列：{summary['post_probe']['remote_output']}; 退出{probe.returncode}。峰值allocator3684.29MiB/reserved3974，不是独占效率或进程峰值。",
        "执行状态以finish/abort及租约释放验证为准，本报告尚未postflight。收据尚未生成，用量窗口/统计未知；收尾后只在任务内补充，不重复相加缓存，不当账单。"
    ],
    "decisions": [
        "保留旧严格双锚路线拒绝状态及3条来源角色假设；新候选保持validation，六项准入未完整通过，不填槽训练。",
        "下一步实现独立包/config与完整元数据覆盖，再做原生完整重复、匹配控制和统一效率；不能把本轮原始checkpoint参数读数直接当作候选准入。",
        "真实截止未修改。当前接近截止时保留具体可执行下一步，不伪造资源阻塞/全局穷尽/无信息增益冷却。不操作其他项目或调度，下一计划时间未知。"
    ]}
with (P / "between_notes_20261014_0209.json").open("x", encoding="utf-8") as stream:
    json.dump(notes, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"summary": str(output), "remaining_seconds": remaining,
                  "native_group_readouts": summary["gpu_completed_group_readouts"],
                  "support_active_groups": summary["support_nonzero_query_gradient_groups"],
                  "parameter_nonzero_groups": summary["parameter_nonzero_groups"],
                  "post_probe": summary["post_probe"]}, indent=2))
