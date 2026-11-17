"""Descriptive feature ambiguity controls, no outcome-trained decision rule."""
import hashlib
import json
import statistics
import random
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
source = root / "instance_feature_audit_20260916.json"
data = json.loads(source.read_text())
rows = data["rows"]
assert len(rows) == 123
assert len({(r["scene"], r["ann_id"]) for r in rows}) == 123
assert not any(r["missing"] for r in rows)
groups = {
    "success": [r for r in rows if r["before"] > .5],
    "confident_wrong": [r for r in rows if r["before"] <= .5
                        and r["winner_overlap"] > .5 and r["winner"] != r["target"]],
    "remaining_failure": [r for r in rows if r["before"] <= .5
                          and not (r["winner_overlap"] > .5 and r["winner"] != r["target"])],
}
summary = {}
for name, items in groups.items():
    nearest = [r["nearest_clip"][0][1] for r in items if r["nearest_clip"]]
    unique = {(r["scene"], r["target"]): r for r in items}
    target_nearest = [r["nearest_clip"][0][1] for r in unique.values() if r["nearest_clip"]]
    summary[name] = dict(expressions=len(items), scenes=len({r["scene"] for r in items}),
        unique_targets=len(unique), nearest_missing=len(items)-len(nearest),
        nearest_mean=statistics.mean(nearest),
        nearest_median=statistics.median(nearest),
        target_balanced_nearest_mean=statistics.mean(target_nearest))
wrong = groups["confident_wrong"]
summary["wrong_pair"] = dict(
    cosine_mean=statistics.mean(r["target_winner_clip_cosine"] for r in wrong),
    rank1=sum(r["winner_clip_rank"] == 1 for r in wrong),
    rank3=sum(r["winner_clip_rank"] <= 3 for r in wrong),
    total=len(wrong))
scene_rows = []
for scene in sorted({r["scene"] for r in rows}):
    values = {}
    for group in ("success", "confident_wrong"):
        unique = {r["target"]: r for r in groups[group] if r["scene"] == scene}
        values[group] = [r["nearest_clip"][0][1] for r in unique.values()
                         if r["nearest_clip"]]
    if all(values.values()):
        scene_rows.append(dict(scene=scene, success_targets=len(values["success"]),
            wrong_targets=len(values["confident_wrong"]),
            difference=statistics.mean(values["confident_wrong"])
                       - statistics.mean(values["success"])))
deltas = [r["difference"] for r in scene_rows]
rng = random.Random(1999)
samples = sorted(statistics.mean(rng.choices(deltas, k=len(deltas)))
                 for _ in range(10000)) if deltas else []
summary["within_scene"] = dict(
    paired_scenes=len(deltas), excluded_scenes=32-len(deltas),
    equal_scene_mean=statistics.mean(deltas) if deltas else None,
    bootstrap95=[samples[249], samples[9749]] if samples else None,
    positive=sum(x > 0 for x in deltas), negative=sum(x < 0 for x in deltas),
    rows=scene_rows,
    limitation="Outcome-defined descriptive strata, not causal. A target can appear "
               "in both groups through different expressions. No independent test set.")
report = dict(summary=summary, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    scope="Descriptive native cached2D uniform-SP pooled features,all123fixedTRAIN identities."
          "Successful targets also have similar neighbors;not evidence of model feature collapse."
          "No lexical predicate truth,causal feature attribution,threshold selection or admission.")
(root / "instance_feature_summary_20260916.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary, indent=2))
