"""Scene-balanced message intervention and matched regression subsets."""
import hashlib
import json
import random
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
source = root / "cluster_message_causal_20260916.json"
data = json.loads(source.read_text())
paired = json.loads((root / "baseline_matched_summary_20260916.json").read_text())
groups = {(r["scene"], r["ann_id"]): r["transition"] for r in paired["rows"]}
results = {}
for branch in ("repeat", "zero", "shift"):
    rows = []
    for batch in data["batches"]:
        assert batch["support_equal"]
        for base, changed in zip(batch["branches"]["base"], batch["branches"][branch]):
            identity = (base["scene"], base["ann_id"])
            assert identity == (changed["scene"], changed["ann_id"])
            a, b = base["layers"][-1]["selected"], changed["layers"][-1]["selected"]
            rows.append(dict(scene=identity[0], ann_id=identity[1], group=groups[identity],
                             before=a, after=b, delta=b-a))
    scene_means = [statistics.mean(r["delta"] for r in rows if r["scene"] == scene)
                   for scene in sorted({r["scene"] for r in rows})]
    rng = random.Random(1999)
    boot = sorted(statistics.mean(rng.choices(scene_means, k=len(scene_means)))
                  for _ in range(10000))
    results[branch] = dict(rows=rows, expression_mean=statistics.mean(r["delta"] for r in rows),
        scene_mean=statistics.mean(scene_means), scene_ci95=[boot[249], boot[9749]],
        rescues=sum(r["before"] <= .5 < r["after"] for r in rows),
        losses=sum(r["after"] <= .5 < r["before"] for r in rows),
        regression_rescues=sum(r["group"] == "regressed" and r["after"] > .5 for r in rows))
report = dict(results=results, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    limitations="Same-weight forward intervention,not removal of training history. "
    "Regression subset selected from prior paired capture. No rerouting/readback "
    "candidate or new efficacy/admission claim.")
(root / "cluster_message_summary_20260916.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: {s: v for s, v in r.items() if s != "rows"}
                  for k, r in results.items()}, indent=2))
