"""Hash-bound native RGB dispersion in deployed M95 masks."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
BINDING_SHA = "bde38848d2036d3d2c5b71640a12190106214a0437b28931a9109eaaf238c085"


def digest(path):
    block = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            block.update(chunk)
    return block.hexdigest()


def rgb_dispersion(mask, rgb, counts):
    chosen = np.flatnonzero(mask)
    if not len(chosen):
        return 0.0
    weight = counts[chosen].astype(float)
    mean = np.average(rgb[chosen], axis=0, weights=weight)
    return float(np.average(np.sum((rgb[chosen] - mean) ** 2, axis=1), weights=weight))


def scene_rgb(path, expected_sha, row):
    if digest(path) != expected_sha:
        raise ValueError("Scene bytes differ")
    _, colors, superpoints, _, _ = torch.load(path, map_location="cpu", weights_only=False)
    ids, inverse = np.unique(superpoints, return_inverse=True)
    if (not np.array_equal(ids, row["original_superpoint_ids"])
            or not np.array_equal(inverse, row["sample_inverse"])):
        raise ValueError("RGB-to-support binding differs")
    counts = np.bincount(inverse)
    sums = np.zeros((len(ids), 3), dtype=np.float64)
    np.add.at(sums, inverse, colors)
    return sums / counts[:, None], counts


def match(rows, subset):
    successes = [r for r in rows if r["selected_iou"] > .5]
    pairs = []
    for row in subset:
        same = [r for r in successes if r["scene"] == row["scene"]]
        pool = same or successes
        other = min(pool, key=lambda r: (
            abs(r["size_fraction"] - row["size_fraction"]), r["manifest_index"]))
        pairs.append({
            "index": row["manifest_index"], "control_index": other["manifest_index"],
            "same_scene": bool(same),
            "difference": row["dispersion"] - other["dispersion"],
            "shuffled_difference": row["shuffled_dispersion"] - other["shuffled_dispersion"],
        })
    return pairs


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "binding", "artifacts", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.capture) != CAPTURE_SHA or digest(a.binding) != BINDING_SHA:
        raise ValueError("Frozen inputs differ")
    capture = json.loads(a.capture.read_text(encoding="utf-8"))
    bound = {int(r["manifest_index"]): r for r in
             json.loads(a.binding.read_text(encoding="utf-8"))["rows"]}
    native = {int(r["manifest_index"]): r for r in capture["rows"]}
    if len(native) != 256 or len(bound) != 256:
        raise ValueError("Capture or binding incomplete")
    scene_features, results = {}, {}
    for entry in capture["feature_artifacts"]:
        path = a.artifacts / entry["path"]
        if digest(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            row, binding = native[index], bound[index]
            if (index in results or row["scene"] != binding["scene"]
                    or int(row["ann_id"]) != binding["ann_id"]
                    or artifact["axis"]["scene"] != row["scene"]):
                raise ValueError("Axis mismatch")
            scene = row["scene"]
            if scene not in scene_features:
                scene_features[scene] = scene_rgb(
                    a.data_root / "scannetv2" / "train" / (scene + "_refer.pth"),
                    binding["scene_sha256"], row)
            rgb, counts = scene_features[scene]
            selected = int(row["selected_query"])
            mask = artifact["query_masks"][selected].bool().numpy()
            if len(mask) != len(rgb) or len(mask) != len(row["sample_inverse"][:len(rgb)]):
                raise ValueError("Mask/RGB axis mismatch")
            target = artifact["target_union"].bool().numpy()
            iou = float(np.count_nonzero(mask & target) /
                        max(1, np.count_nonzero(mask | target)))
            if abs(iou - row["ious"][selected]) > 1e-6:
                raise ValueError("Native IoU differs")
            dispersion = rgb_dispersion(mask, rgb, counts)
            if dispersion != rgb_dispersion(mask, rgb, counts):
                raise ValueError("Nonrepeatable feature")
            results[index] = {
                "manifest_index": index, "scene": scene,
                "selected_iou": iou, "size_fraction": float(mask.mean()),
                "best_single_iou": float(max(row["ious"])),
                "dispersion": dispersion,
                "shuffled_dispersion": rgb_dispersion(mask, np.roll(rgb, 1, axis=0), counts),
            }
    if set(results) != set(range(256)):
        raise ValueError("Missing native expression")
    rows = [results[i] for i in sorted(results)]
    failed = match(rows, [r for r in rows if r["selected_iou"] <= .5])
    limited = match(rows, [r for r in rows if r["best_single_iou"] <= .5])
    result = {"contract": "m95_target_blind_rgb_dispersion_v1",
              "capture_sha256": CAPTURE_SHA, "binding_sha256": BINDING_SHA,
              "rows": rows, "failed_pairs": failed, "limited_pairs": limited,
              "admission": False}
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({"rows": len(rows), "failed": len(failed), "limited": len(limited),
                      "same_scene_failed": sum(x["same_scene"] for x in failed),
                      "same_scene_limited": sum(x["same_scene"] for x in limited)}))


if __name__ == "__main__":
    main()
