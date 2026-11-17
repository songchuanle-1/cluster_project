"""Frozen, scene-paired size-stratified target-gradient screen."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
EXPECTED = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"


def analyze(data):
    rows = data["rows"]
    entries = data["target_seed_direction_rows"]
    if len(rows) != 128 or len(entries) != 128:
        raise ValueError("Frozen cohort changed")
    sizes = [entry["physical_target_superpoints"] for entry in entries]
    boundary = median(sizes)
    groups = defaultdict(lambda: defaultdict(lambda: [[], []]))
    for row, entry in zip(rows, entries):
        if row["ann_id"] != entry["ann_id"]:
            raise ValueError("Expression identity changed")
        count = entry["target_seed_count"]
        if count != len(entry["seeds"]) or entry["physical_target_superpoints"] <= 0:
            raise ValueError("Invalid target support")
        arm = "small" if entry["physical_target_superpoints"] <= boundary else "large"
        failed = int(row["selected_mask_iou"] <= 0.5)
        mass = sum(abs(seed[3]) for seed in entry["seeds"])
        groups[arm][row["scene"]][failed].append(
            mass / entry["physical_target_superpoints"])
    result = {}
    for arm in ("small", "large"):
        pairs = []
        for scene, (success, failure) in sorted(groups[arm].items()):
            if success and failure:
                pairs.append({"scene": scene, "failure_minus_success":
                              sum(failure) / len(failure) -
                              sum(success) / len(success)})
        result[arm] = {
            "expressions": sum(len(v[0]) + len(v[1])
                               for v in groups[arm].values()),
            "paired_scenes": len(pairs),
            "failure_lower": sum(p["failure_minus_success"] < 0 for p in pairs),
            "failure_higher": sum(p["failure_minus_success"] > 0 for p in pairs),
            "equal": sum(p["failure_minus_success"] == 0 for p in pairs),
            "detail": pairs,
        }
    return {
        "contract": "m95_target_size_interaction_v1",
        "admission": False,
        "source_sha256": EXPECTED,
        "median_physical_target_superpoints": boundary,
        "arms": result,
        "limits": "Frozen TRAIN observational subgroup screen, not a new "
                  "supervision unit, causal intervention, or validation gain.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Output exists or frozen source hash differs")
    result = analyze(json.loads(SOURCE.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: {m: v[m] for m in (
        "expressions", "paired_scenes", "failure_lower", "failure_higher", "equal")}
        for k, v in result["arms"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
