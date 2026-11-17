"""Verify that frozen M95 support maps exactly to unaugmented scene geometry."""
import argparse
import hashlib
import json
from pathlib import Path


CAPTURE_SHA256 = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind_scene(original_ids, inverse, scene_superpoints):
    import numpy as np

    ids, recovered_inverse = np.unique(scene_superpoints, return_inverse=True)
    expected_ids = np.asarray(original_ids, dtype=ids.dtype)
    expected_inverse = np.asarray(inverse, dtype=recovered_inverse.dtype)
    if not np.array_equal(ids, expected_ids):
        raise ValueError("Original superpoint IDs differ")
    if not np.array_equal(recovered_inverse, expected_inverse):
        raise ValueError("Point-to-superpoint inverse differs")
    return len(ids), len(recovered_inverse)


def analyze(capture_path, data_root):
    import numpy as np
    import torch

    if sha256(capture_path) != CAPTURE_SHA256:
        raise ValueError("Frozen capture hash differs")
    capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    if (capture["manifest"]["sha256"] != MANIFEST_SHA256
            or not capture["native_capture_completed"]
            or len(capture["rows"]) != 256):
        raise ValueError("Frozen capture contract differs")
    results = []
    by_scene = {}
    for row in capture["rows"]:
        scene = row["scene"]
        path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
        if scene not in by_scene:
            if not path.is_file():
                raise ValueError("Missing scene: " + scene)
            xyz, _, superpoints, _, _ = torch.load(
                path, map_location="cpu", weights_only=False)
            if len(xyz.shape) != 2 or xyz.shape[1] != 3 or not np.isfinite(xyz).all():
                raise ValueError("Invalid scene geometry: " + scene)
            by_scene[scene] = (superpoints, len(xyz), sha256(path))
        superpoints, points, path_hash = by_scene[scene]
        superpoint_count, recovered_points = bind_scene(
            row["original_superpoint_ids"], row["sample_inverse"], superpoints)
        if points != recovered_points:
            raise ValueError("Scene coordinates differ from support")
        results.append({
            "manifest_index": int(row["manifest_index"]),
            "scene": scene, "ann_id": int(row["ann_id"]),
            "superpoints": superpoint_count, "points": points,
            "scene_sha256": path_hash,
        })
    if len({r["manifest_index"] for r in results}) != 256:
        raise ValueError("Duplicate manifest index")
    return {
        "contract": "m95_geometry_support_binding_v1",
        "capture_sha256": CAPTURE_SHA256,
        "manifest_sha256": MANIFEST_SHA256,
        "rows_bound": len(results),
        "scenes_bound": len(by_scene),
        "rows": results,
        "admission": False,
        "interpretation": "Coordinate source binding only; no task mechanism established.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    result = analyze(args.capture, args.data_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({"rows_bound": result["rows_bound"],
                      "scenes_bound": result["scenes_bound"]}))


if __name__ == "__main__":
    main()
