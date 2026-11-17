"""Outcome-stratified layer geometry, descriptive only."""
import hashlib
import json
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
source = root / "language_layer_20260916.json"
outcomes = root / "anchor_instance_names_20260916.json"
rows = json.loads(source.read_text())["rows"]
labels = {(r["scene"], r["ann_id"]): r for r in json.loads(outcomes.read_text())["rows"]}
assert len(rows) == 861
assert len({(r["scene"], r["ann_id"], r["layer"]) for r in rows}) == 861
result = []
for layer in ["input"] + [f"encoder{i}" for i in range(6)]:
    for group in ["all", "success", "wrong", "remaining"]:
        selected = []
        for row in rows:
            if row["layer"] != layer:
                continue
            label = labels[(row["scene"], row["ann_id"])]
            actual = "success" if label["before"] > .5 else (
                "wrong" if label["winner_overlap"] > .5 and not label["winner_is_target"]
                else "remaining")
            if group == "all" or group == actual:
                selected.append(row)
        result.append(dict(layer=layer, group=group, expressions=len(selected),
            scenes=len({r["scene"] for r in selected}),
            metrics={key: statistics.mean(r[key] for r in selected)
                     for key in ["mean_pair_cosine", "centered_energy",
                                 "centered_effective_rank", "leading_fraction"]}))
report = dict(rows=result, sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in (source, outcomes)},
    limitations="TRAIN outcome-defined groups. Layer rank is descriptive, not causal "
    "oversmoothing or a mandate for rank regularization. Different token counts affect "
    "effective rank. Excludes BOS/finaltwo null tokens,not all punctuation/suffix. "
    "No novelty, efficacy or admission;do not launch norm/scaling/rank-loss sweep.")
(root / "language_layer_summary_20260916.json").write_text(json.dumps(report, indent=2))
for row in result:
    if row["layer"] in ("input", "encoder5"):
        print(json.dumps(row))
