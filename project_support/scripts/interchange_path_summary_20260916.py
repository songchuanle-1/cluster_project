"""Summarize isolated scene interchange pathways on matched native inputs."""
import hashlib
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
source = root / "pipeline/reports/interchange_path_control_20260916.json"
raw = json.loads(source.read_text())
results = {}
for name in ("repeat", "read_same", "read_different", "mask_same", "mask_different"):
    scene_deltas, cases = [], []
    rescues = harms = score_changes = 0
    max_score_error = 0.
    for batch in raw["batches"]:
        a, b = batch["branches"]["base"], batch["branches"][name]
        deltas = []
        for x, y, lx, ly in zip(a["rows"], b["rows"], a["logits"], b["logits"]):
            assert (x["scene"], x["ann_id"]) == (y["scene"], y["ann_id"])
            deltas.append(y["before"] - x["before"])
            score_changes += int(np.argmax(lx) != np.argmax(ly))
            max_score_error = max(max_score_error, max(abs(u-v) for u, v in zip(lx, ly)))
            rescued = x["before"] <= .5 < y["before"]
            harmed = y["before"] <= .5 < x["before"]
            rescues += rescued
            harms += harmed
            if rescued or harmed:
                cases.append(dict(scene=x["scene"], ann_id=x["ann_id"],
                                  before=x["before"], after=y["before"]))
        scene_deltas.append(float(np.mean(deltas)))
    rng = np.random.default_rng(1999)
    means = np.asarray(scene_deltas)[rng.integers(len(scene_deltas),
        size=(10000, len(scene_deltas)))].mean(1)
    results[name] = dict(mean_delta=float(np.mean(scene_deltas)),
        scene_bootstrap95=np.quantile(means, [.025, .975]).tolist(),
        rescues=int(rescues), harms=int(harms), selected_query_changes=score_changes,
        max_logit_error=max_score_error, changed_cases=cases)
output = root / "pipeline/reports/interchange_path_summary_20260916.json"
output.write_text(json.dumps(dict(results=results,
    evidence=[dict(path=str(p.relative_to(root)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
              for p in (source, Path(__file__))],
    limitations="128TRAIN32scenes,fixedphysicalsupport;queryindexcomparison only within "
    "matched runs. No evidence of learned efficacy or core novelty."), indent=2))
print(json.dumps({k: {a: b for a, b in v.items() if a != "changed_cases"}
                  for k, v in results.items()}))
