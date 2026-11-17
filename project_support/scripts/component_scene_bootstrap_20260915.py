"""Recover scene identity from hashed native incidence capture; diagnostic CI."""
import json
import random
from pathlib import Path
from statistics import mean

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
incidence = json.loads((root / "boundary_components_20260915-1607.json").read_text())
data = json.loads((root / "component_four_batch_summary_20260915.json").read_text())
lookup = {(r["step"], r["ann_id"]): r["scene"] for r in incidence["rows"]}
assert len(lookup) == len(incidence["rows"])
groups = {}
for row in data["rows"]:
    batch = row["batch"] + (2 if "extra" in row["source"] else 0)
    scene = lookup[(batch, row["ann_id"])]
    assert scene in row["scenes"]
    if row["components"] > 1:
        groups.setdefault(scene, {}).setdefault(row["ann_id"], []).append(row["delta"])
scene_means = {s: mean(mean(v) for v in expressions.values()) for s, expressions in groups.items()}
values = list(scene_means.values())
rng = random.Random(1999)
samples = sorted(mean(rng.choices(values, k=len(values))) for _ in range(10000))
report = dict(scenes=scene_means, scene_count=len(values),
              scene_balanced_mean=mean(values), interval95=[samples[249], samples[9749]],
              scope="Four sequential TRAIN batches;disconnected subset;query means within expression then scene. "
                    "Only a few scenes;bootstrap descriptive,not confirmatory efficacy.")
(root / "component_scene_bootstrap_20260915.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report))
