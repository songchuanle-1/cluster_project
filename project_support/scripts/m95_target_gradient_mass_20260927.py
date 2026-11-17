"""Frozen native target-score gradient mass, paired by scene."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_target_seed_size_native_20260927.json"
PRIOR = ROOT / "pipeline/reports/m95_target_seed_direction_native_20260927.json"
OUTPUT = ROOT / "pipeline/reports/m95_target_gradient_mass_20260927.json"
EXPECTED = "97d95b265b3e1a79e65f01748946f9eab9ff81d90efcfc05365894ddce58106c"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(data, old):
    if len(data["rows"]) != len(old["rows"]) or len(data["rows"]) != 128:
        raise ValueError("Frozen population changed")
    scenes = defaultdict(lambda: [[], []])
    zero = [0, 0]
    for row, entry, previous, prior_entry in zip(
            data["rows"], data["target_seed_direction_rows"],
            old["rows"], old["target_seed_direction_rows"]):
        if (row["scene"], row["ann_id"], row["batch_input_sha256"],
                row["selected_seed"]) != (
                previous["scene"], previous["ann_id"],
                previous["batch_input_sha256"], previous["selected_seed"]):
            raise ValueError("Expression/input binding changed")
        if (entry["ann_id"] != prior_entry["ann_id"] or
                entry["target_seed_count"] != len(entry["seeds"]) or
                prior_entry["target_seed_count"] != len(prior_entry["seeds"]) or
                [int(seed[0]) for seed in entry["seeds"]] !=
                [int(seed[0]) for seed in prior_entry["seeds"]]):
            raise ValueError("Native target-seed identity changed")
        if not 0 < entry["physical_target_superpoints"] <= entry["scene_superpoints"]:
            raise ValueError("Invalid physical support")
        if not 0 < entry["valid_fps_count"] <= len(row["topk"]) + 256:
            raise ValueError("Invalid FPS support")
        failed = int(row["selected_mask_iou"] <= .5)
        mass = sum(abs(seed[3]) for seed in entry["seeds"])
        count = entry["target_seed_count"]
        zero[failed] += count == 0
        scenes[row["scene"]][failed].append({
            "mass_per_target_superpoint": mass / entry["physical_target_superpoints"],
            "per_seed_magnitude": mass / count if count else None,
        })
    paired = []
    for scene, (success, failure) in sorted(scenes.items()):
        if not success or not failure:
            continue
        def mean(rows, key):
            values = [row[key] for row in rows if row[key] is not None]
            return sum(values) / len(values) if values else None
        a, b = mean(success, "mass_per_target_superpoint"), mean(
            failure, "mass_per_target_superpoint")
        x, y = mean(success, "per_seed_magnitude"), mean(
            failure, "per_seed_magnitude")
        paired.append({
            "scene": scene, "failure_minus_success_mass_per_target": b - a,
            "failure_minus_success_per_seed": (
                y - x if x is not None and y is not None else None),
        })
    if len(scenes) != 32 or len(paired) != 20:
        raise ValueError("Frozen scene cohort changed")
    def summary(key):
        values = [r[key] for r in paired if r[key] is not None]
        return {
            "scenes": len(values),
            "failure_lower": sum(v < 0 for v in values),
            "failure_higher": sum(v > 0 for v in values),
            "equal": sum(v == 0 for v in values),
            "mean_difference": sum(values) / len(values) if values else None,
        }
    return {
        "contract": "m95_target_gradient_mass_v1", "admission": False,
        "source_sha256": digest(SOURCE), "prior_sha256": digest(PRIOR),
        "expressions": 128, "scenes": 32, "mixed_outcome_scenes": 20,
        "zero_target_seed_success": zero[0],
        "zero_target_seed_failure": zero[1],
        "mass_per_target_superpoint": summary(
            "failure_minus_success_mass_per_target"),
        "per_seed_magnitude": summary("failure_minus_success_per_seed"),
        "detail": paired,
        "limits": "Passive frozen TRAIN score-gradient audit; not a new loss, "
                  "matched intervention, native new-model backward or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if digest(SOURCE) != EXPECTED or args.output.exists():
        raise ValueError("Frozen input hash differs or output exists")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    old = json.loads(PRIOR.read_text(encoding="utf-8"))
    result = analyze(data, old)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "mass": result["mass_per_target_superpoint"],
        "per_seed": result["per_seed_magnitude"],
    }))


if __name__ == "__main__":
    main()
