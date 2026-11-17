"""Frozen superpoint-oracle ceiling, extending cluster-instance-purity."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def oracle(counts, target):
    positives = np.bincount(counts, weights=target.astype(np.int64))
    sizes = np.bincount(counts)
    if not np.any(positives):
        raise ValueError("Target absent")
    order = sorted(range(len(sizes)), key=lambda i: (
        -(positives[i] / sizes[i]), i))
    selected_target = np.cumsum(positives[order])
    selected_other = np.cumsum((sizes - positives)[order])
    ratios = selected_target / (int(target.sum()) + selected_other)
    return {"best_iou": float(ratios.max()),
            "best_prefix": int(ratios.argmax() + 1),
            "target_points": int(target.sum()),
            "mixed_superpoints": int(np.count_nonzero(
                (positives > 0) & (positives < sizes)))}


def analyze(capture_path, data_root):
    if digest(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen capture hash differs")
    source = json.loads(capture_path.read_text(encoding="utf-8"))
    if (source["manifest"]["sha256"] != MANIFEST_SHA or
            not source["native_capture_completed"] or len(source["rows"]) != 256):
        raise ValueError("Frozen capture contract differs")
    scenes = {}
    rows = []
    for row in source["rows"]:
        scene = row["scene"]
        if scene not in scenes:
            path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
            _, _, native_sp, _, native_labels = torch.load(
                path, map_location="cpu", weights_only=False)
            native_sp, native_labels = np.asarray(native_sp), np.asarray(native_labels)
            ids, inverse = np.unique(native_sp, return_inverse=True)
            scenes[scene] = (ids, inverse, native_labels, digest(path))
        ids, inverse, labels, scene_hash = scenes[scene]
        if (not np.array_equal(ids, row["original_superpoint_ids"]) or
                not np.array_equal(inverse, row["sample_inverse"])):
            raise ValueError("Original point/superpoint axis differs")
        target_ids = {int(x) for x in row["target_instances"]}
        if int(row["target_object_id"]) not in target_ids:
            raise ValueError("Native target ID not in frozen target set")
        target = np.isin(labels, list(target_ids))
        result = oracle(inverse, target)
        best_native = max(float(v) for v in row["ious"])
        rows.append({"manifest_index": int(row["manifest_index"]),
                     "scene": scene, "stratum": row["stratum"],
                     "scene_sha256": scene_hash,
                     "best_native_query_sp_iou": best_native,
                     "native_limited": best_native <= 0.5,
                     "metric_mismatch": "native IoU uses binarized superpoint GT; oracle uses original point instance GT",
                     **result})
    rows.sort(key=lambda r: r["manifest_index"])
    if [r["manifest_index"] for r in rows] != list(range(256)):
        raise ValueError("Manifest index coverage changed")
    limited = [r for r in rows if r["native_limited"]]
    if len(limited) != 16:
        raise ValueError("Limited denominator changed")
    return {"contract": "m95_superpoint_oracle_ceiling_v1",
            "capture_sha256": CAPTURE_SHA, "manifest_sha256": MANIFEST_SHA,
            "rows": rows, "limited_rows": len(limited),
            "limited_oracle_above_half": sum(r["best_iou"] > 0.5 for r in limited),
            "limited_oracle_at_or_below_half": sum(r["best_iou"] <= 0.5 for r in limited),
            "all_oracle_above_half": sum(r["best_iou"] > 0.5 for r in rows),
            "interpretation": "Point-level support ceiling only. Cannot compare numeric IoU to native superpoint-GT IoU or infer cause of 16 superpoint-limited failures.",
            "admission": False}


def main():
    parser = argparse.ArgumentParser()
    for field in ("capture", "data-root", "output"):
        parser.add_argument("--" + field, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    result = analyze(args.capture, args.data_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({k: result[k] for k in (
        "limited_rows", "limited_oracle_above_half",
        "limited_oracle_at_or_below_half", "all_oracle_above_half")}))


if __name__ == "__main__":
    main()
