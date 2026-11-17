"""Bound same-scene, same-transform target-seed failure controls."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from m95_target_seed_failure_20260927 import SOURCES


def analyze(sources):
    outputs = []
    for source in sources:
        by_scene = defaultdict(list)
        rows = source["rows"]
        identities = {(r["scene"], r["ann_id"]) for r in rows}
        if len(rows) != 128 or len(identities) != 128:
            raise ValueError("Frozen population differs")
        for row in rows:
            if not 0 <= row["selected_mask_iou"] <= 1:
                raise ValueError("Invalid native mask IoU")
            if row["selected_seed_matches_target_instance"] != (
                    row["selected_seed_instance"] in row["target_instances"]):
                raise ValueError("Physical seed binding differs")
            by_scene[row["scene"]].append(row)
        paired = []
        for row in rows:
            if (not row["selected_seed_matches_target_instance"]
                    or row["selected_mask_iou"] > .5):
                continue
            controls = [other for other in by_scene[row["scene"]]
                        if other["selected_seed_matches_target_instance"]
                        and other["selected_mask_iou"] > .5]
            paired.append({
                "scene": row["scene"], "ann_id": row["ann_id"],
                "target_instances": row["target_instances"],
                "selected_iou": row["selected_mask_iou"],
                "controls": [
                    {"ann_id": other["ann_id"],
                     "target_instances": other["target_instances"],
                     "selected_iou": other["selected_mask_iou"],
                     "same_target_instance": (
                         set(row["target_instances"]) == set(other["target_instances"]))}
                    for other in controls],
            })
        outputs.append({
            "transform_seed": source["transform_seed"],
            "target_seed_failures": len(paired),
            "with_same_scene_success_control": sum(bool(p["controls"]) for p in paired),
            "with_same_physical_target_success_control": sum(
                any(c["same_target_instance"] for c in p["controls"])
                for p in paired),
            "paired_scenes": len({p["scene"] for p in paired if p["controls"]}),
            "rows": paired,
        })
    return {
        "contract": "m95_target_seed_scene_control_v1",
        "admission": False,
        "source_sha256": [digest for _, digest in SOURCES],
        "arms": outputs,
        "limits": "TRAIN same-scene observational controls, not a same-forward matched causal mechanism.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    for path, digest in SOURCES:
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Frozen source differs")
    sources = [json.loads(path.read_text(encoding="utf-8")) for path, _ in SOURCES]
    if (sources[0]["checkpoint_sha256"] != sources[1]["checkpoint_sha256"]
            or sources[0]["population_manifest_sha256"]
            != sources[1]["population_manifest_sha256"]
            or [s["transform_seed"] for s in sources] != [1999, 2000]):
        raise ValueError("Capture provenance differs")
    for a, b in zip(
            sorted(sources[0]["rows"], key=lambda r: (r["scene"], r["ann_id"])),
            sorted(sources[1]["rows"], key=lambda r: (r["scene"], r["ann_id"]))):
        if ((a["scene"], a["ann_id"]) != (b["scene"], b["ann_id"])
                or a["target_instances"] != b["target_instances"]
                or a["batch_input_sha256"] == b["batch_input_sha256"]):
            raise ValueError("Transform identity/fingerprint differs")
    result = analyze(sources)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps([{key: value for key, value in arm.items() if key != "rows"}
                      for arm in result["arms"]]))


if __name__ == "__main__":
    main()
