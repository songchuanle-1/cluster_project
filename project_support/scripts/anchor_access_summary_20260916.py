"""Summarize every eligible expression with explicit sampling exclusions."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
source = root / "anchor_access_20260916.json"
report = json.loads(source.read_text())
rows = []
for item in report["eligibility"]:
    batch = report["batches"][str(item["batch"])]
    b = item["expression"]
    original = batch["base"]["rows"][b]
    row = dict(item, scene=original["scene"],
               before=original["layers"][-1]["selected"])
    for branch in ("repeat", "anchor", "control"):
        variant = batch[branch]["rows"][b]
        assert variant["ann_id"] == original["ann_id"] and variant["scene"] == original["scene"]
        row[branch + "_same_sampling"] = batch[branch]["same_physical_sampling"][b]
        row[branch + "_delta"] = variant["layers"][-1]["selected"] - row["before"]
    row["all_same_sampling"] = all(row[b + "_same_sampling"] for b in ("repeat", "anchor", "control"))
    rows.append(row)
eligible = [r for r in rows if r["eligible"]]
included = [r for r in eligible if r["all_same_sampling"]]
summary = dict(total=len(rows), eligible=len(eligible), included=len(included),
               excluded_sampling=len(eligible) - len(included))
for branch in ("repeat", "anchor", "control"):
    scenes = defaultdict(list)
    for r in included:
        scenes[r["scene"]].append(r[branch + "_delta"])
    means = [statistics.mean(v) for v in scenes.values()]
    rng = random.Random(1999)
    boot = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(10000)) if means else []
    observed_sum = sum(r[branch + "_delta"] for r in included)
    missing = len(eligible) - len(included)
    summary[branch] = dict(scenes=len(means),
        expression_mean=statistics.mean(r[branch + "_delta"] for r in included) if included else None,
        scene_mean=statistics.mean(means) if means else None,
        descriptive_scene_bootstrap=[boot[249], boot[9749]] if boot else None,
        eligible_support_bounds=[(observed_sum-missing)/len(eligible),
                                 (observed_sum+missing)/len(eligible)] if eligible else None,
        positive=sum(r[branch + "_delta"] > 0 for r in included),
        negative=sum(r[branch + "_delta"] < 0 for r in included))
paired = [r["anchor_delta"] - r["control_delta"] for r in included]
summary["anchor_minus_control_expression_mean"] = statistics.mean(paired) if paired else None
output = dict(summary=summary, rows=rows,
              sources={source.name: hashlib.sha256(source.read_bytes()).hexdigest()},
              scope="Existing TRAIN fixed16 diagnostic;bootstrap descriptive,not efficacy. "
                    "Eligibility requires enough countmatched neutral tokens. "
                    "Only all-branch physical-sampling identity included;missing bounds explicit. "
                    "QLA deletion leaves indirect encoder anchor paths active.")
(root / "anchor_access_summary_20260916.json").write_text(json.dumps(output, indent=2))
print(json.dumps(summary, indent=2))
