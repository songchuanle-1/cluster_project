"""Persist actual diagnostics, narrowly reconcile stale metadata and scope holds."""
from datetime import datetime, timezone, timedelta
import json
from tick_ops import guard, save, evidence, tick, ROOT, OUT, PRIOR, CID, run

guard()
result=tick.load(OUT/"scale_result.json")
analysis=tick.load(OUT/"scale_analysis.json")
post=tick.load(OUT/"postcheck_resources.json")
assert result["passed_controls"] and post["source_hashes_match"] and not post["contexts"]
assert not post["own_diagnostic_pids"] and all(v=="acquired_and_released" for v in post["locks"].values())
assert tick.load(ROOT/"pipeline/tick_receipts/21500d1a24a149c4bc63ba867beea115.json")["status"]=="FINALIZED"
exp_path=ROOT/"pipeline/experiments/M202-HDS.json"
exp=tick.load(exp_path)
assert exp["status"]=="done_earlystop" and exp["server"]=="server-4" and str(exp["gpu"])=="0"
meta=tick.load(PRIOR/"checkpoint_metadata.json")["checkpoints"]["best.pth"]
assert post["checkpoint_sha256"]==meta["sha256"]==result["checkpoint_sha256"]
best=meta["meta"]["best_miou"]
assert meta["meta"]["epoch"]==19 and best==0.4946560263633728
old=exp["best_miou_exact"]
assert old==0.47346487641334534, "Do not overwrite an unexpected concurrent metadata change"
reconciliation={"observed_at":datetime.now(timezone.utc).isoformat(),"experiment":"M202-HDS",
    "field":"best_miou_exact","before":old,"after":best,"best_epoch_exact":19,
    "reason":"Top-level exact field retained previous crashed-run value after normal terminal finalization; preserve old value as historical provenance, not current best.",
    "proof":[evidence(PRIOR/"checkpoint_metadata.json"),evidence(OUT/"postcheck_resources.json")],
    "unchanged":["done_earlystop","epochs_final29/50","rounded final_best0.4947","historical champion0.5020","CSV historical metrics","all failure logs"]}
save("terminal_metric_reconciliation.json",reconciliation)
exp.setdefault("best_miou_exact_history",[]).append({"value":old,"scope":"previous target crashed-run cached field",
    "preserved_at":reconciliation["observed_at"],"reconciliation":evidence(OUT/"terminal_metric_reconciliation.json")})
exp.update(best_miou_exact=best,best_epoch_exact=19,best_metric_provenance=evidence(OUT/"terminal_metric_reconciliation.json"))
guard();tick.save(exp_path,exp)

work=tick.load(ROOT/"pipeline/research_work.json")
candidate=next(c for c in work["candidates"] if c["id"]==CID)
assert candidate["stage"]=="validation"
candidate.update(stage="complete",failure_scope="hypothesis",hypothesis_scope="Only the local all-scales-nonnegative-on-every-fixed-TRAIN-scene premise; not the whole HDS/hierarchy family.",
    gate_result="Measurement controls PASS; local all-scales-beneficial premise FALSE; no training/admission evidence or population causal claim.",
    next_action="Keep all signed8subset TRAIN results and bias-retained/true-zero distinction. Pre-register disjoint TRAIN replication and matched content/magnitude negative controls before a distinct structural mechanism; do not tune/drop scales/restart/revise HDS.")
candidate["measurement_protocol_history"][0]["result"]="passed_native_controls_unchanged_tolerance"
files=("scale_execution.json","scale_fetch.json","live_resource_precheck.json","scale_result.json","scale_analysis.json",
       "postcheck_resources.json","server3_resource_observation.json","terminal_metric_reconciliation.json",
       "tick_ops.py","prepare_revision1.py","postcheck_and_analyze.py")
candidate["evidence"].extend(evidence(OUT/name) for name in files)
candidate["evidence"].append(evidence(ROOT/"pipeline/analyses/M202-HDS_TRAIN_scale_attribution_20261017_796c44e9.md"))
now=datetime.now(timezone.utc)
holds=[c for c in work["candidates"] if c["stage"]=="blocked"]
expected={"m95-native-relation-other-sign-conflict","m95-native-main-role-weight-precedence","m95-native-secondary-positive-mass","m95-native-between-pair-support"}
assert {c["id"] for c in holds}==expected
scope={"observed_at":now.isoformat(),"goal_sha256":tick.digest(ROOT/"pipeline/goal.json"),
    "roadmap_sha256":tick.digest(ROOT/"docs/research_mainline_correction_20261015.md"),
    "review":"Due human_authorization holds rechecked once against unchanged goal/latest user instructions. No priority-restoring authorization or mechanism-matched auxiliary requirement. Timer/GPU opening is not authorization.",
    "ids":sorted(expected),"training_launches":0,"scientific_gate_changes":0,"scientific_rejections":0,
    "before":[{"id":c["id"],"retry_after":c["retry_after"],"blocker_kind":c["blocker_kind"]} for c in holds],
    "retry_after":(now+timedelta(hours=4)).isoformat()}
assert all(c["blocker_kind"]=="human_authorization" and datetime.fromisoformat(c["retry_after"])<=now for c in holds)
save("auxiliary_scope_recheck.json",scope)
for held in holds:
    held["retry_after"]=scope["retry_after"]
    held["evidence"].append(evidence(OUT/"auxiliary_scope_recheck.json"))
guard();tick.save(ROOT/"pipeline/research_work.json",work)
counts={stage:sum(c["stage"]==stage for c in work["candidates"]) for stage in ("complete","rejected","blocked","training")}
assert counts=={"complete":10,"rejected":91,"blocked":4,"training":0}
decision=run(["C:/Program Files (x86)/Git/bin/bash.exe",
    "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline/log_decision.sh","cluster_project","other",
    "HDS各尺度是否都有益，先前零消息对照能否隔离层级内容收益？",
    "固定4TRAIN场景8子集原生诊断完成；保留偏置空层级与真零分开：full-empty=-0.003351，full-zero=+0.023922。拒绝仅局部全尺度均有益假设，不删尺度或调权，不作模型修订3；四辅助授权hold维持。",
    "16表达细中粗Shapley均值+0.007568/-0.004528/-0.006391，控制误差0。首轮表达轴测量失败保留；源码及权重未变。下一步独立TRAIN复核及匹配内容/幅度负对照；未证明总体提升、全局尺度有害或VAL差因。另保留旧精确字段并更正当前epoch19best元数据，不改champion。",
    "pipeline/analyses/M202-HDS_TRAIN_scale_attribution_20261017_796c44e9.md;pipeline/diagnostic_bundles/tick_796c44e9/scale_analysis.json;pipeline/diagnostic_bundles/tick_796c44e9/postcheck_resources.json"],45)
save("decision_log_result.json",{"returncode":decision.returncode,"stdout":decision.stdout,"stderr":decision.stderr})
assert decision.returncode==0,decision.stderr
save("persistence_outcome.json",{"observed_at":datetime.now(timezone.utc).isoformat(),"candidate_id":CID,"stage":"complete",
    "candidate_counts":counts,"records":len(work["candidates"]),"metadata_corrected":True,"hold_rechecks":4,
    "training_launches":0,"admissions":0,"model_revisions":0,"postflight":"pending_actual_finish"})
print(json.dumps({"counts":counts,"corrected_exact_best":best,"held_auxiliary_ids":4,"decision":decision.stdout},ensure_ascii=False,indent=2))
