"""Persist bounded static event evidence, never mutate the runtime queue."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "pipeline/research_work.json"
work = json.loads(path.read_text(encoding="utf-8"))
paths = ["pipeline/reports/evaluation_contract_20260916-1310.json",
         "scripts/evaluation_contract_20260916.py",
         "pipeline/decisions/20260916-131124_route_change.md"]
evidence = [{"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
            for p in paths]
actions = {
    "referent-causality-audit": "Scope B supersedes question101512. Compare terminal PIRS outputs on paired scenes; baseline scene-balanced=.6875, pooled=.6910569. Preserve pre-registered thresholds; oracle restriction is not relabelling efficacy.",
    "referent-discrimination": "Scope B permits supervision research.123 membership rows lack capture_id,ann_id and physical support. Capture native per-query seed/mask/score contingency with exact axes before linking PIRS results.",
    "modality-identity-preservation": "Implement shared native capture with capture_id,scene,ann_id,expression_slot,original_superpoint_ids,sample_inverse and raw/projected/fused/final features. Apply tested physical_join before same-class comparisons;no modality candidate admitted.",
    "instance-identity-representation": "28 archived instance rows lack ann_id and physical support. Capture exact same-forward axes before relating wrong-instance ranks to acceptable-mask ranks;do not infer feature insufficiency.",
    "referent-query-selection": "Use best rank over ALL masks with IoU>.5,not maximum-IoU query rank;report no-acceptable separately. Capture exact query/support axes and check deployment tie convention before using tested helper.",
    "input-modality-distinguishability": "Indexing validity does not establish cross-capture identity. Capture paired row vectors,original_superpoint_ids,sample_inverse and producer identity;test rejection of reordered support.",
    "same-target-description-grounding": "Bind seven enumerated connected mention IDs in evaluation_contract report to native physical endpoints;retain12 disconnected controls. Text IDs alone fail tested physical_join. Native binding remains pending.",
    "same-forward-coverage-diagnosis": "Emit exact axes and all-acceptable ranks in shared native capture;do not join123 intervention and123 membership rows by position since neither archive has ann_id or capture_id. No repeated cluster audit.",
}
for candidate in work["candidates"]:
    cid = candidate["id"]
    if cid in actions:
        candidate["next_action"] = actions[cid]
        candidate["evaluation_contract_progress"] = {
            "timestamp": "2026-09-16T13:11:00+08:00",
            "finding": actions[cid], "scope": "Executed static audit, not native capture."}
    if cid == "referent-supervision-axis":
        candidate["experiment_id"] = "M197-PIRS"
        candidate["evaluation_contract_progress"] = {
            "native_log_observation": "Train[2/50] steps154->168/4686 at13:09.",
            "tests_passed": 14,
            "risks": "Soft-IoU can reverse hard-IoU ranks;soft>0 is not hard overlap."}
    if cid in actions or cid == "referent-supervision-axis":
        existing = {item["path"] for item in candidate["evidence"]}
        candidate["evidence"].extend(e for e in evidence if e["path"] not in existing)
path.write_text(json.dumps(work, indent=2, ensure_ascii=True) + "\n", encoding="ascii")
print("Eight due records updated; active mapping recorded; queue untouched.")
