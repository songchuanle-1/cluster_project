"""Summarize all preregistered branches of the modality intervention."""
from collections import defaultdict
import hashlib
import json
import random
import statistics
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/modality_mean_intervention_20260916.json"
data = json.loads(source.read_text(encoding="utf-8"))
summary = {}
for branch in ("repeat", "three_d", "two_d", "both"):
    deltas, scene_deltas = [], defaultdict(list)
    rescued = harmed = changed = 0
    for batch in data["batches"]:
        control = batch["branches"]["base"]
        tested = batch["branches"][branch]
        assert control["physical"] == tested["physical"]
        assert len(control["rows"]) == len(tested["rows"])
        for a, b in zip(control["rows"], tested["rows"]):
            assert (a["scene"], a["ann_id"]) == (b["scene"], b["ann_id"])
            delta = b["iou"] - a["iou"]
            deltas.append(delta)
            scene_deltas[a["scene"]].append(delta)
            rescued += a["iou"] <= .5 < b["iou"]
            harmed += b["iou"] <= .5 < a["iou"]
            changed += a["query"] != b["query"]
    means = [statistics.mean(v) for v in scene_deltas.values()]
    rng = random.Random(1999)
    boot = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(10000))
    summary[branch] = dict(expressions=len(deltas), scenes=len(means),
        mean=statistics.mean(deltas), scene_mean=statistics.mean(means),
        bootstrap95=[boot[249], boot[9749]], rescues=rescued, harms=harmed,
        query_changes=changed, max_absolute_delta=max(map(abs, deltas)))
out = root / "pipeline/reports/modality_mean_summary_20260916.json"
out.write_text(json.dumps(dict(summary=summary,
    scope="Fixed123TRAIN5branches,GT-based perturbation not efficacy. "
          "Query changes use identical physical support. Scene bootstrap descriptive.",
    evidence=[dict(path=p.relative_to(root).as_posix(),
                   sha256=hashlib.sha256(p.read_bytes()).hexdigest())
              for p in (source, Path(__file__))]), indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
