"""Scene-level coordinate intervention summary."""
import hashlib
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
path = root / "frame_intervention_20260916.json"
data = json.loads(path.read_text())
rows = []
for batch in data["batches"]:
    branches = batch["branches"]
    for i, before in enumerate(branches["base"]["rows"]):
        row = dict(scene=before["scene"], ann_id=before["ann_id"],
                   before=before["layers"][-1]["selected"])
        for mode in ("repeat", "inverse", "mismatch"):
            after = branches[mode]["rows"][i]
            assert (after["scene"], after["ann_id"]) == (before["scene"], before["ann_id"])
            row[mode] = after["layers"][-1]["selected"] - row["before"]
            row[mode + "_sampling_changed"] = branches[mode]["seeds"][i] != branches["base"]["seeds"][i]
        rows.append(row)
summary = {}
for mode in ("repeat", "inverse", "mismatch"):
    scenes = defaultdict(list)
    for row in rows:
        scenes[row["scene"]].append(row[mode])
    means = [statistics.mean(v) for v in scenes.values()]
    rng = random.Random(1999)
    boot = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(10000))
    summary[mode] = dict(expressions=len(rows), scenes=len(scenes),
        expression_mean=statistics.mean(r[mode] for r in rows),
        scene_mean=statistics.mean(means), descriptive_ci=[boot[249], boot[9749]],
        positive=sum(r[mode] > 0 for r in rows), negative=sum(r[mode] < 0 for r in rows),
        sampling_changed=sum(r[mode+"_sampling_changed"] for r in rows))
report = dict(summary=summary, rows=rows,
              source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              scope="Decoder coordinate intervention only;not rotation-label correctness, "
                    "grounded relations,training efficacy or novel mechanism admission.")
(root / "frame_summary_20260916.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary, indent=2))
