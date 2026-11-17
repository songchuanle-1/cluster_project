"""Freeze a diagnosis before reviewing other routes."""
from datetime import datetime, timezone
from ops import *

guard()
protocol = {
    "candidate_id": CID,
    "preregistered_at": datetime.now(timezone.utc).isoformat(),
    "hypothesis": "Fine-cell mean aggregation can erase feature-position cross moments. Establish whether actual M95 is blind to a within-cell feature permutation changing those moments, then measure task relevance with the same native TRAIN prefix and criterion. A mathematical nullspace alone is not a task deficit or attention admission.",
    "matched_control": "Identity and within-fine-cell permutation preserve memberships, feature multisets, means and counts; only correspondence to positions changes. Freeze original query/criterion inputs for paired suffix tests. No label-based repartitioning, routing or instance identity proposal.",
    "first_test": "Execute actual aggregate_cluster on CPU with an analytic moment-changing permutation.",
    "next_test": "Capture original M95 TRAIN features, coordinates, hierarchy and loss once; compare actual pooled/refined tokens, feature-position moments and paired native suffix task responses under within-fine-cell permutations.",
    "frozen_assets_source": "pipeline/diagnostic_bundles/tick_819a58d8/task_suffix/native_manifest.json",
    "checkpoint_scope": "Available M95 epoch16, not verified historical champion weights",
    "sampling": "Two previously frozen TRAIN scenes / eight expressions; descriptive, no population CI",
    "rejection_rules": ["If actual mean-token computation already encodes altered moments, reject the blind-spot premise", "Task-path compensation or unresolved relevance cannot establish a task deficit", "Single normalization/scale/residual/gate or closed mechanism is not a new model", "No validation selection, production edits, optimizer/scheduler steps, or extra GPU authorization"],
    "tolerance": 1e-6,
    "scientific_admission": False
}
save("protocol.json", protocol)
work_path = ROOT / "pipeline/research_work.json"
work = tick.load(work_path)
assert not any(c["id"] == CID for c in work["candidates"]), "Reuse existing stable ID instead"
work["candidates"].append({"id": CID, "stage": "diagnosis", "hypothesis": protocol["hypothesis"], "matched_control": protocol["matched_control"], "next_action": protocol["first_test"], "evidence": [evidence(OUT / "protocol.json")], "scientific_status": "Unrun diagnostic; no admission or efficacy claim", "created_at": protocol["preregistered_at"]})
guard()
tick.save(work_path, work)
print(json.dumps({"candidate_id": CID, "stage": "diagnosis", "protocol_frozen": True}))
