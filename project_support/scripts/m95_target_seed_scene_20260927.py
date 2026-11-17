"""Within-scene target-seed count contrast on a frozen native population."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_target_seed_direction_native_20260927.json"
OUTPUT = ROOT / "pipeline/reports/m95_target_seed_scene_20260927.json"
EXPECTED = "7b164b8b9732b8fff124598dc0447ede9c2cec310ad071de7bcac8df2afa8007"


def main():
    if OUTPUT.exists() or hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Frozen source differs or output exists")
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if len(data["rows"]) != 128 or len(data["target_seed_direction_rows"]) != 128:
        raise ValueError("Population differs")
    scenes = defaultdict(lambda: [[], []])
    for row, seed in zip(data["rows"], data["target_seed_direction_rows"]):
        if row["ann_id"] != seed["ann_id"]:
            raise ValueError("Expression axis mismatch")
        failed = int(row["selected_mask_iou"] <= .5)
        scenes[row["scene"]][failed].append(seed["target_seed_count"])
    detail = []
    for scene, (success, failure) in sorted(scenes.items()):
        if not success or not failure:
            continue
        detail.append({
            "scene": scene, "successes": len(success), "failures": len(failure),
            "mean_failure_minus_success": (sum(failure) / len(failure)
                                           - sum(success) / len(success)),
            "zero_success": success.count(0), "zero_failure": failure.count(0),
        })
    result = {
        "contract": "m95_target_seed_scene_v1",
        "admission": False, "source_sha256": EXPECTED,
        "scenes": len(scenes), "mixed_outcome_scenes": len(detail),
        "failure_fewer": sum(x["mean_failure_minus_success"] < 0 for x in detail),
        "failure_more": sum(x["mean_failure_minus_success"] > 0 for x in detail),
        "equal": sum(x["mean_failure_minus_success"] == 0 for x in detail),
        "mean_scene_difference": (
            sum(x["mean_failure_minus_success"] for x in detail) / len(detail)),
        "detail": detail,
        "limits": "Unnormalized seed count is confounded by target size and "
                  "does not override closed selector/ranking evidence.",
    }
    if len(scenes) != 32 or len(detail) != 20:
        raise ValueError("Scene denominator differs")
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "mixed_outcome_scenes", "failure_fewer", "failure_more", "equal")}))


if __name__ == "__main__":
    main()
