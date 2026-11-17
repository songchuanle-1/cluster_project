"""Expression-level full-update effects; no cross-forward query correspondence."""
import hashlib
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "pipeline/reports"
path = root / "role_parameter_step_20260916.json"
data = json.loads(path.read_text())
rows = []
for batch in data["batches"]:
    for i, identity in enumerate(batch["identities"]):
        branches = {k: v["rows"][i] for k, v in batch["branches"].items()}
        native, neutral, repeat = [branches[k] for k in ("native", "neutral", "native_repeat")]
        rows.append(dict(identity, batch=batch["batch"],
            delta=neutral["selected"]-native["selected"],
            repeat_delta=repeat["selected"]-native["selected"],
            native=native["selected"], neutral=neutral["selected"],
            sampling_changed=neutral["physical_seeds"] != native["physical_seeds"],
            repeat_sampling_changed=repeat["physical_seeds"] != native["physical_seeds"]))
summary = {}
for group in ("all", "repeated", "other"):
    take = [r for r in rows if group == "all" or r["repeated"] == (group == "repeated")]
    scenes = defaultdict(list)
    for r in take:
        scenes[r["scene"]].append(r["delta"])
    means = [statistics.mean(v) for v in scenes.values()]
    rng = random.Random(1999)
    boot = sorted(statistics.mean(rng.choices(means, k=len(means))) for _ in range(10000))
    summary[group] = dict(expressions=len(take), scenes=len(means),
        mean=statistics.mean(r["delta"] for r in take),
        scene_mean=statistics.mean(means), descriptive_scene_ci=[boot[249], boot[9749]],
        positive=sum(r["delta"] > 0 for r in take), negative=sum(r["delta"] < 0 for r in take),
        sampling_changed=sum(r["sampling_changed"] for r in take),
        repeat_mean=statistics.mean(r["repeat_delta"] for r in take),
        repeat_max=max(abs(r["repeat_delta"]) for r in take),
        repeat_sampling_changed=sum(r["repeat_sampling_changed"] for r in take))
output = dict(summary=summary, rows=rows,
    source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    scope="Same-batch one fresh AdamW step,not training efficacy. Selected-expression IoU "
          "does not require aligned query IDs;sampling changes are included as downstream effects. "
          "Repeated-head group includes genuine distinct objects,not confirmed coreference.")
(root / "role_parameter_summary_20260916.json").write_text(json.dumps(output, indent=2))
print(json.dumps(summary, indent=2))
