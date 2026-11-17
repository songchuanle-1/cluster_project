"""Pre-registered, scene-target grouped diagnostic of a frozen native capture."""
import argparse
import json
import math
from pathlib import Path

from m95_multiword_native_31_20260928 import CHECKPOINT_SHA, MANIFEST_SHA, frozen_rows


def summarize(manifest, capture):
    frozen = {(r["scene"], int(r["ann_id"])): r for r in manifest["records"]}
    if (manifest.get("contract") != "m95_multiword_capture_manifest_v1"
            or capture.get("contract") != "m95_multiword_native_31_v1"
            or capture.get("manifest_sha256") != MANIFEST_SHA
            or capture.get("checkpoint_sha256") != CHECKPOINT_SHA):
        raise ValueError("Frozen capture identity differs")
    rows = {}
    for row in capture["rows"]:
        key = row["scene"], int(row["ann_id"])
        if key not in frozen or key in rows:
            raise ValueError("Unexpected or duplicate native row")
        if (row["arm"] != frozen[key]["arm"]
                or sorted(map(int, row["target_instances"])) !=
                sorted(map(int, frozen[key]["target_instances"]))):
            raise ValueError("Native arm or target differs")
        value = float(row["selected_mask_iou"])
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Invalid native mask IoU")
        if not isinstance(row["seed_majority_matches_target"], bool):
            raise ValueError("Invalid native seed agreement")
        rows[key] = row
    if set(rows) != set(frozen):
        raise ValueError("Incomplete frozen native capture")

    units = {}
    for pair in manifest["pairs"]:
        key = pair["scene"], int(pair["ann_id"])
        source = rows[key]
        if source["arm"] != "phrase":
            raise ValueError("Invalid exposed pair")
        target = tuple(sorted(map(int, source["target_instances"])))
        controls = []
        for control in pair["all_controls"]:
            control_row = rows[pair["scene"], int(control["ann_id"])]
            if (control_row["arm"] != "phrase_absent"
                    or tuple(sorted(map(int, control_row["target_instances"]))) != target):
                raise ValueError("Control physical target differs")
            controls.append(control_row)
        if not controls:
            raise ValueError("Missing matched controls")
        unit = pair["scene"], target
        units.setdefault(unit, []).append({
            "exposed_ann_id": key[1],
            "control_ann_ids": [int(c["ann_id"]) for c in controls],
            "mask_iou_delta": float(source["selected_mask_iou"]) -
                              sum(float(c["selected_mask_iou"]) for c in controls) / len(controls),
            "seed_agreement_delta": int(source["seed_majority_matches_target"]) -
                                    sum(int(c["seed_majority_matches_target"])
                                        for c in controls) / len(controls),
        })
    if len(units) != 7 or sum(map(len, units.values())) != 11:
        raise ValueError("Frozen scene-target units differ")
    unit_rows = [
        {"scene": scene, "target_instances": list(target), "exposed_count": len(deltas),
         "mask_iou_delta": sum(d["mask_iou_delta"] for d in deltas) / len(deltas),
         "seed_agreement_delta": sum(d["seed_agreement_delta"] for d in deltas) / len(deltas),
         "contrasts": deltas}
        for (scene, target), deltas in sorted(units.items())
    ]
    scenes = sorted({r["scene"] for r in unit_rows})
    return {
        "contract": "m95_multiword_native31_grouped_diagnosis_v1",
        "admission": False, "native_rows": len(rows), "scene_target_units": len(units),
        "units": unit_rows,
        "scenes": [
            {"scene": scene,
             "unit_count": sum(r["scene"] == scene for r in unit_rows),
             "mean_unit_mask_iou_delta": sum(
                 r["mask_iou_delta"] for r in unit_rows if r["scene"] == scene)
                 / sum(r["scene"] == scene for r in unit_rows)}
            for scene in scenes],
        "limits": "Text-confounded, two scenes; no row-level inference, causal effect or training efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen_rows(args.manifest)
    result = summarize(json.loads(args.manifest.read_text(encoding="utf-8")),
                       json.loads(args.capture.read_text(encoding="utf-8")))
    if args.output.exists():
        raise ValueError("Do not overwrite an existing diagnosis")
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
