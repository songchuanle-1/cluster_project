"""Size-normalized frozen target FPS coverage, grouped by scene."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "pipeline/reports"
SOURCE = REPORT / "m95_target_seed_size_native_20260927.json"
PREVIOUS = REPORT / "m95_target_seed_direction_native_20260927.json"
OUTPUT = REPORT / "m95_target_seed_size_summary_20260927.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("Output exists")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    old = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    if len(data["rows"]) != 128 or len(old["rows"]) != 128:
        raise ValueError("Population differs")
    scenes = defaultdict(lambda: [[], []])
    for row, entry, prev, old_entry in zip(
            data["rows"], data["target_seed_direction_rows"],
            old["rows"], old["target_seed_direction_rows"]):
        if (row["ann_id"] != entry["ann_id"] or
                row["batch_input_sha256"] != prev["batch_input_sha256"] or
                row["selected_seed"] != prev["selected_seed"] or
                entry["target_seed_count"] != old_entry["target_seed_count"]):
            raise ValueError("Frozen expression binding changed")
        target = entry["physical_target_superpoints"]
        scene = entry["scene_superpoints"]
        fps = entry["valid_fps_count"]
        if not 0 < target <= scene or fps <= 0:
            raise ValueError("Invalid physical support denominator")
        ratio = (entry["target_seed_count"] / fps) / (target / scene)
        scenes[row["scene"]][int(row["selected_mask_iou"] <= .5)].append(ratio)
    paired = []
    for scene, (success, failure) in sorted(scenes.items()):
        if not success or not failure:
            continue
        paired.append({"scene": scene, "failure_minus_success":
                       sum(failure) / len(failure) -
                       sum(success) / len(success)})
    result = {
        "contract": "m95_target_seed_size_summary_v1",
        "admission": False, "source_sha256": sha(SOURCE),
        "previous_sha256": sha(PREVIOUS),
        "expressions": len(data["rows"]), "scenes": len(scenes),
        "mixed_outcome_scenes": len(paired),
        "failure_lower_normalized": sum(
            x["failure_minus_success"] < 0 for x in paired),
        "failure_higher_normalized": sum(
            x["failure_minus_success"] > 0 for x in paired),
        "equal": sum(x["failure_minus_success"] == 0 for x in paired),
        "mean_scene_difference": sum(
            x["failure_minus_success"] for x in paired) / len(paired),
        "detail": paired,
        "limits": "Physical size-normalized FPS coverage association only; "
                  "not a selector intervention, efficacy or admission.",
    }
    if len(scenes) != 32 or len(paired) != 20:
        raise ValueError("Scene cohort differs")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "failure_lower_normalized", "failure_higher_normalized", "equal",
        "mean_scene_difference")}))


if __name__ == "__main__":
    main()
