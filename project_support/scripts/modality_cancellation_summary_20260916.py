"""Scene-balanced descriptive analysis of native fusion capture."""
from collections import defaultdict
import hashlib
import json
import random
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/modality_cancellation_20260916.json"
data = json.loads(source.read_text(encoding="utf-8"))
rows = data["rows"]
assert len({(r["scene"], r["ann_id"]) for r in rows}) == len(rows) == 123
groups = defaultdict(list)
for row in rows:
    if row["missing"] or row["cancellation_ratio"] is None:
        groups["missing"].append(row)
    elif row["original_iou"] > .5:
        groups["success"].append(row)
    elif row["original_winner_overlap"] > .5 and row["original_winner"] != row["target"]:
        groups["confident_wrong"].append(row)
    else:
        groups["remaining_failure"].append(row)
summary = {}
for name, members in groups.items():
    summary[name] = dict(expressions=len(members), scenes=len({r["scene"] for r in members}))
    if name != "missing":
        ratios = [r["cancellation_ratio"] for r in members]
        summary[name].update(mean=statistics.mean(ratios), median=statistics.median(ratios),
                             negative=sum(x < 0 for x in ratios))
paired = []
for scene in sorted({r["scene"] for r in rows}):
    scene_values = {}
    for name in ("success", "confident_wrong"):
        unique = {r["target"]: r for r in groups[name] if r["scene"] == scene}
        scene_values[name] = [r["cancellation_ratio"] for r in unique.values()]
    if all(scene_values.values()):
        paired.append(dict(scene=scene, difference=statistics.mean(scene_values["confident_wrong"])
                           - statistics.mean(scene_values["success"])))
diffs = [r["difference"] for r in paired]
rng = random.Random(1999)
boot = sorted(statistics.mean(rng.choices(diffs, k=len(diffs))) for _ in range(10000)) if diffs else []
summary["paired_scenes"] = dict(rows=paired, count=len(diffs),
    mean=statistics.mean(diffs) if diffs else None, bootstrap95=[boot[249], boot[9749]] if boot else None)
summary["replay"] = dict(
    max_iou_delta=max(abs(r["native_iou"] - r["original_iou"]) for r in rows),
    success_flips=sum((r["native_iou"] > .5) != (r["original_iou"] > .5) for r in rows))
result = dict(summary=summary, limitations=[
    "Centroid difference cancellation is descriptive,not task-information or causal loss.",
    "Nearest raw2D neighbor is outcome-independent,but strata are outcome-defined.",
    "Paired scene averaging deduplicates targets per stratum;one target may appear in both.",
    "TRAIN fixed sample only;no population-random sample or VAL efficacy claim.",
    "Neither summed feature distance nor cosine specifies a semantic grounding metric.",
], evidence=[dict(path=p.relative_to(root).as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in (source, Path(__file__))])
out = root / "pipeline/reports/modality_cancellation_summary_20260916.json"
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
