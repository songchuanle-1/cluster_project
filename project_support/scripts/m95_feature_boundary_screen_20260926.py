"""Prediction-blind feature contrast on frozen M95 selected-mask edges."""
import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
BINDING_SHA = "bde38848d2036d3d2c5b71640a12190106214a0437b28931a9109eaaf238c085"
FEATURES = ("raw_2d", "raw_3d", "fused", "final")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contrast(feature, edges, mask, labels):
    import numpy as np

    feature = np.asarray(feature, dtype=np.float64)
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    mask = np.asarray(mask, dtype=bool)
    labels = np.asarray(labels)
    if feature.shape[0] != len(mask) or len(mask) != len(labels):
        raise ValueError("Feature/support axes differ")
    norm = np.linalg.norm(feature, axis=1)
    scaled = feature / np.maximum(norm[:, None], 1e-12)
    dist = 1 - np.sum(scaled[edges[:, 0]] * scaled[edges[:, 1]], axis=1)
    crossing = mask[edges[:, 0]] != mask[edges[:, 1]]
    inside = mask[edges[:, 0]] & mask[edges[:, 1]]
    identity_boundary = labels[edges[:, 0]] != labels[edges[:, 1]]
    valid = (norm[edges[:, 0]] > 1e-12) & (norm[edges[:, 1]] > 1e-12)

    def group(selected):
        values = dist[selected & valid]
        return {"edges": len(values), "mean": float(values.mean()) if len(values) else None}

    return {
        "cross": group(crossing), "inside": group(inside),
        "same_instance_cross": group(crossing & ~identity_boundary),
        "different_instance_cross": group(crossing & identity_boundary),
        "same_instance_all": group(~identity_boundary),
        "different_instance_all": group(identity_boundary),
    }


def analyze(capture_path, binding_path, artifact_root, data_root):
    import numpy as np
    import torch
    from m95_geometry_screen_20260926 import scene_graph

    if sha(capture_path) != CAPTURE_SHA or sha(binding_path) != BINDING_SHA:
        raise ValueError("Frozen capture/binding hashes differ")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if not capture["native_capture_completed"] or len(capture["rows"]) != 256:
        raise ValueError("Capture incomplete")
    expected = {int(row["manifest_index"]): row for row in capture["rows"]}
    bound = {int(row["manifest_index"]): row for row in binding["rows"]}
    graphs = {}
    for index, row in expected.items():
        scene = row["scene"]
        receipt = bound[index]
        if scene != receipt["scene"] or row["ann_id"] != receipt["ann_id"]:
            raise ValueError("Geometry row identity differs")
        if scene in graphs:
            continue
        path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
        if sha(path) != receipt["scene_sha256"]:
            raise ValueError("Scene identity differs")
        xyz, _, superpoints, _, _ = torch.load(path, map_location="cpu", weights_only=False)
        ids, inverse = np.unique(superpoints, return_inverse=True)
        if (not np.array_equal(ids, row["original_superpoint_ids"])
                or not np.array_equal(inverse, row["sample_inverse"])):
            raise ValueError("Scene-to-support binding differs")
        graphs[scene] = scene_graph(xyz, inverse, len(ids))

    results = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Feature artifact identity differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            row = expected[index]
            if (index in results or artifact["manifest_sha256"] != capture["manifest"]["sha256"]
                    or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError("Artifact axis differs")
            selected = int(row["selected_query"])
            mask = artifact["query_masks"][selected].bool().numpy()
            target = artifact["target_union"].bool().numpy()
            iou = float(np.count_nonzero(mask & target) /
                        max(1, np.count_nonzero(mask | target)))
            if abs(iou - row["ious"][selected]) > 1e-6:
                raise ValueError("Selected IoU differs")
            labels = np.asarray(artifact["physical_instance_labels"])
            edges = graphs[row["scene"]]
            features = {}
            for key in FEATURES:
                values = artifact["features"][key].numpy()
                original = contrast(values, edges, mask, labels)
                shuffled = contrast(np.roll(values, 1, axis=0), edges, mask, labels)
                if contrast(values, edges, mask, labels) != original:
                    raise ValueError("Feature contrast not repeatable")
                features[key] = {"original": original, "rotated": shuffled}
            results[index] = {
                "manifest_index": index, "scene": row["scene"],
                "selected_iou": iou, "no_acceptable": max(row["ious"]) <= 0.5,
                "features": features,
            }
    if set(results) != set(expected):
        raise ValueError("Incomplete feature capture")
    rows = [results[i] for i in sorted(results)]
    return {
        "contract": "m95_feature_boundary_screen_v1",
        "capture_sha256": CAPTURE_SHA, "binding_sha256": BINDING_SHA,
        "rows": rows, "scenes": len(graphs),
        "limited_rows": sum(row["no_acceptable"] for row in rows),
        "admission": False,
        "interpretation": "Offline, retrospective feature contrast; not a deployable correction.",
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "binding", "artifact-root", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    result = analyze(a.capture, a.binding, a.artifact_root, a.data_root)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps({k: result[k] for k in ("scenes", "limited_rows", "admission")}))


if __name__ == "__main__":
    main()
