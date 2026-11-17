"""Scene-paired target score-derivative coherence on frozen native inputs."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
OUTPUT = ROOT / "pipeline/reports/m95_target_cancellation_20260927.json"
EXPECTED = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"


def analyze(data):
    if len(data["rows"]) != 128 or len(data["target_seed_direction_rows"]) != 128:
        raise ValueError("Frozen population changed")
    scenes = defaultdict(lambda: [[], []])
    missing = [0, 0]
    for row, entry in zip(data["rows"], data["target_seed_direction_rows"]):
        if row["ann_id"] != entry["ann_id"] or entry["target_seed_count"] != len(entry["seeds"]):
            raise ValueError("Expression/seed binding changed")
        failed = int(row["selected_mask_iou"] <= 0.5)
        gradients = [seed[3] for seed in entry["seeds"]]
        magnitude = sum(abs(g) for g in gradients)
        if not magnitude:
            missing[failed] += 1
            coherence = None
        else:
            coherence = -sum(gradients) / magnitude
            if not -1.000001 <= coherence <= 1.000001:
                raise ValueError("Coherence outside range")
        scenes[row["scene"]][failed].append(coherence)
    paired = []
    for scene, (success, failure) in sorted(scenes.items()):
        if not success or not failure:
            continue
        a = [x for x in success if x is not None]
        b = [x for x in failure if x is not None]
        paired.append({
            "scene": scene,
            "failure_minus_success": sum(b) / len(b) - sum(a) / len(a)
            if a and b else None,
            "success_defined": len(a), "failure_defined": len(b),
        })
    if len(scenes) != 32 or len(paired) != 20:
        raise ValueError("Scene cohort changed")
    values = [x["failure_minus_success"] for x in paired
              if x["failure_minus_success"] is not None]
    return {
        "contract": "m95_target_cancellation_v1",
        "admission": False,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "expressions": 128, "scenes": 32, "mixed_outcome_scenes": 20,
        "paired_defined_scenes": len(values),
        "failure_lower_coherence": sum(x < 0 for x in values),
        "failure_higher_coherence": sum(x > 0 for x in values),
        "equal": sum(x == 0 for x in values),
        "mean_failure_minus_success": sum(values) / len(values) if values else None,
        "undefined_success": missing[0], "undefined_failure": missing[1],
        "detail": paired,
        "limits": "Score-derivative observational screen; not feature gradients, "
                  "causal intervention, model backward, or training efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED or args.output.exists():
        raise ValueError("Frozen source changed or output exists")
    result = analyze(json.loads(SOURCE.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "paired_defined_scenes", "failure_lower_coherence",
        "failure_higher_coherence", "equal", "undefined_success",
        "undefined_failure")}))


if __name__ == "__main__":
    main()
