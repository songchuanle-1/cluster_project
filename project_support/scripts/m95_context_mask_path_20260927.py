"""Selected context seed versus physical mask association on one native capture."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "pipeline/reports/m95_seed_mask_reachability_1999_20260927.json"
SOURCE_SHA = "e48cec2a0d4794cc1c14588afdd173bcafc310f2d71be0d0caa8778cde50f090"
CHECKPOINT_SHA = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def analyze(source):
    if (source["checkpoint_sha256"] != CHECKPOINT_SHA
            or source["population_manifest_sha256"] != MANIFEST_SHA
            or source["transform_seed"] != 1999
            or not source["exact_input_fingerprints"]
            or not source["mask_reachability"]):
        raise ValueError("Native source provenance differs")
    seen = set()
    arms = defaultdict(list)
    outside = defaultdict(int)
    scenes = defaultdict(lambda: defaultdict(list))
    for row in source["rows"]:
        key = (row["scene"], row["ann_id"])
        if key in seen:
            raise ValueError("Duplicate native expression")
        seen.add(key)
        iou = row["selected_mask_iou"]
        physical_iou = row["selected_mask_seed_instance_iou"]
        if not 0 <= iou <= 1 or not 0 <= physical_iou <= 1:
            raise ValueError("IoU outside unit range")
        if row["selected_seed_is_context"] and iou <= .5:
            arm = "context_failure"
        elif iou <= .5:
            arm = "other_failure"
        else:
            arm = "success"
        arms[arm].append(physical_iou)
        outside[arm] += int(not row["selected_seed_in_selected_mask"])
        scenes[key[0]][arm].append(physical_iou)
    if len(seen) != 128:
        raise ValueError("Frozen population changed")
    pairs = []
    for scene, groups in sorted(scenes.items()):
        if groups["context_failure"] and groups["other_failure"]:
            pairs.append({
                "scene": scene,
                "context_count": len(groups["context_failure"]),
                "other_count": len(groups["other_failure"]),
                "physical_iou_difference": (
                    sum(groups["context_failure"])/len(groups["context_failure"])
                    - sum(groups["other_failure"])/len(groups["other_failure"])),
            })
    return {
        "contract": "m95_context_mask_path_v1",
        "admission": False,
        "source_sha256": SOURCE_SHA,
        "arms": {name: {
            "expressions": len(arms[name]),
            "scenes": sum(bool(group[name]) for group in scenes.values()),
            "physical_iou_mean": sum(arms[name])/len(arms[name]) if arms[name] else None,
            "physical_iou_over_half": sum(x > .5 for x in arms[name]),
            "selected_seed_outside_mask": outside[name],
        } for name in ("context_failure", "other_failure", "success")},
        "paired_scenes": pairs,
        "limits": "Same-forward TRAIN association only; no mechanism, causal intervention, admission or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("Output exists or source hash changed")
    result = analyze(json.loads(SOURCE.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"arms": result["arms"],
                      "paired_scenes": len(result["paired_scenes"])}))


if __name__ == "__main__":
    main()
