"""Paired native interchange outcomes and scene-balanced uncertainty."""
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/scene_interchange_20260916.json"
raw = json.loads(source.read_text())
results = {}
for name in ("repeat", "same", "different", "shuffle"):
    deltas, scenes, rescue, harm, cases = [], [], 0, 0, []
    for batch in raw["batches"]:
        local = []
        for a, b in zip(batch["branches"]["base"]["rows"], batch["branches"][name]["rows"]):
            assert (a["scene"], a["ann_id"]) == (b["scene"], b["ann_id"])
            d = b["before"] - a["before"]
            local.append(d)
            rescue += a["before"] <= .5 < b["before"]
            harm += b["before"] <= .5 < a["before"]
            if (a["before"] > .5) != (b["before"] > .5):
                cases.append(dict(scene=a["scene"], ann_id=a["ann_id"],
                                  before=a["before"], after=b["before"]))
        deltas.extend(local)
        scenes.append(float(np.mean(local)))
    rng = np.random.default_rng(1999)
    means = np.asarray(scenes)[rng.integers(len(scenes), size=(10000, len(scenes)))].mean(1)
    results[name] = dict(expressions=len(deltas), scenes=len(scenes),
        mean_delta=float(np.mean(deltas)), scene_mean=float(np.mean(scenes)),
        scene_bootstrap95=np.quantile(means, [.025, .975]).tolist(),
        rescues=int(rescue), harms=int(harm), changed_cases=cases)
noise = max(abs(x-y) for b in raw["batches"]
            for a, c in zip(b["branches"]["base"]["logits"], b["branches"]["repeat"]["logits"])
            for x, y in zip(a, c))
result = dict(results=results, repeat_logit_noise=noise,
    evidence=[dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
              for p in (source, Path(__file__))],
    limitations="TRAIN fixed32scenes;bootstrap descriptive,not independent population inference. "
    "Pretrained state exchange not a learned intervention or new mechanism efficacy test.")
(root / "pipeline/reports/scene_interchange_summary_20260916.json").write_text(
    json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result["results"]))
