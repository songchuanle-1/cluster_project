"""Full predeclared support accounting; no cherry-picked native batches."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
files = ["component_free_sampling_aligned_20260915.json",
         "component_free_sampling_extra_aligned_20260915.json",
         "component_remaining_aligned_20260915.json"]
batches = [b for f in files for b in json.loads((root / f).read_text())["results"]]
assert len(batches) == 16
summary = {}
for subset in ("all", "connected", "disconnected"):
    parts = [b["full_support_hard_iou_bounds"][subset] for b in batches]
    total = sum(p["total"] for p in parts)
    observed = sum(p["observed"] for p in parts)
    lower_sum = sum((p["lower"] or 0) * p["total"] for p in parts)
    upper_sum = sum((p["upper"] or 0) * p["total"] for p in parts)
    observed_sum = (lower_sum + upper_sum) / 2
    summary[subset] = dict(
        total=total, observed=observed, missing=total-observed,
        observed_query_mean=observed_sum/observed if observed else None,
        full_support_bounds=[lower_sum/total, upper_sum/total] if total else None)
report = dict(summary=summary, batches=16,
              sources={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files},
              interpretation="One-step native free-sampling diagnostic only. Full-support bounds cross zero. "
              "No aggregate positive efficacy conclusion or application-novelty admission.")
(root / "component_complete_summary_20260915.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report))
