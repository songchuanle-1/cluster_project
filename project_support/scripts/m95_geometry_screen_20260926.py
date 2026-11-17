"""Frozen, deployment-visible geometry features and paired controls."""
import argparse
import hashlib
import json
from pathlib import Path

CAPTURE_SHA = "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a"
BINDING_SHA = "bde38848d2036d3d2c5b71640a12190106214a0437b28931a9109eaaf238c085"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def graph_features(mask, edges):
    import numpy as np
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components

    mask = np.asarray(mask, dtype=bool)
    edges = np.asarray(edges, dtype=np.int64).reshape(-1, 2)
    selected = np.flatnonzero(mask)
    if not len(selected):
        return {"boundary_fraction": 0.0, "components": 0}
    boundary = float(np.mean(mask[edges[:, 0]] != mask[edges[:, 1]])) if len(edges) else 0.0
    inside = edges[mask[edges[:, 0]] & mask[edges[:, 1]]] if len(edges) else edges
    matrix = coo_matrix((np.ones(len(inside) * 2),
                         (np.r_[inside[:, 0], inside[:, 1]],
                          np.r_[inside[:, 1], inside[:, 0]])),
                        shape=(len(mask), len(mask))).tocsr()
    _, labels = connected_components(matrix, directed=False)
    return {"boundary_fraction": boundary,
            "components": int(np.unique(labels[selected]).size)}


def scene_graph(xyz, inverse, superpoint_count):
    import numpy as np
    from scipy.spatial import cKDTree

    sums = np.zeros((superpoint_count, 3), dtype=np.float64)
    counts = np.bincount(inverse, minlength=superpoint_count)
    if np.any(counts == 0):
        raise ValueError("Empty superpoint")
    np.add.at(sums, inverse, xyz)
    centroids = sums / counts[:, None]
    neighbors = cKDTree(centroids).query(centroids, k=min(7, superpoint_count))[1]
    neighbors = np.atleast_2d(neighbors)
    edges = set()
    for source, row in enumerate(neighbors):
        for target in np.atleast_1d(row):
            target = int(target)
            if source != target:
                edges.add(tuple(sorted((source, target))))
    return np.asarray(sorted(edges), dtype=np.int64).reshape(-1, 2)


def matched_pairs(rows):
    limited = [r for r in rows if r["selected_iou"] <= 0.5]
    success = [r for r in rows if r["selected_iou"] > 0.5]
    pairs = []
    for row in limited:
        same = [s for s in success if s["scene"] == row["scene"]]
        group = same or [s for s in success if s["scene"] != row["scene"]]
        match = min(group, key=lambda s: (
            abs(s["size_fraction"] - row["size_fraction"]),
            s["manifest_index"]))
        pairs.append({
            "limited_index": row["manifest_index"],
            "success_index": match["manifest_index"],
            "same_scene": bool(same),
            "size_difference": abs(match["size_fraction"] - row["size_fraction"]),
            "boundary_difference": row["boundary_fraction"] - match["boundary_fraction"],
            "shuffled_boundary_difference": (
                row["shuffled_boundary_fraction"] - match["shuffled_boundary_fraction"]),
        })
    return pairs


def analyze(capture_path, binding_path, artifacts, data_root):
    import numpy as np
    import torch

    if sha(capture_path) != CAPTURE_SHA or sha(binding_path) != BINDING_SHA:
        raise ValueError("Frozen capture or geometry binding differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if (not capture["native_capture_completed"] or len(capture["rows"]) != 256
            or binding["rows_bound"] != 256):
        raise ValueError("Frozen manifest incomplete")
    by_index = {int(r["manifest_index"]): r for r in capture["rows"]}
    bound = {int(r["manifest_index"]): r for r in binding["rows"]}
    graphs = {}
    for index, row in by_index.items():
        b = bound[index]
        if (row["scene"] != b["scene"] or int(row["ann_id"]) != b["ann_id"]
                or len(row["original_superpoint_ids"]) != b["superpoints"]):
            raise ValueError("Frozen geometry identity differs")
        scene = row["scene"]
        if scene in graphs:
            continue
        path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
        if sha(path) != b["scene_sha256"]:
            raise ValueError("Scene bytes differ")
        xyz, _, sp, _, _ = torch.load(path, map_location="cpu", weights_only=False)
        ids, inverse = np.unique(sp, return_inverse=True)
        if (not np.array_equal(ids, row["original_superpoint_ids"])
                or not np.array_equal(inverse, row["sample_inverse"])):
            raise ValueError("Scene-to-support axis differs")
        graphs[scene] = scene_graph(xyz, inverse, len(ids))
    results = {}
    for entry in capture["feature_artifacts"]:
        path = artifacts / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            row = by_index[index]
            if (index in results or artifact["manifest_sha256"] != capture["manifest"]["sha256"]
                    or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError("Artifact identity differs")
            masks = artifact["query_masks"].bool()
            selection = int(row["selected_query"])
            mask = masks[selection].numpy()
            target = artifact["target_union"].bool().numpy()
            iou = float(np.count_nonzero(mask & target) /
                        max(1, np.count_nonzero(mask | target)))
            if abs(iou - row["ious"][selection]) > 1e-6:
                raise ValueError("Native selected IoU differs")
            edges = graphs[row["scene"]]
            original = graph_features(mask, edges)
            shuffled = graph_features(np.roll(mask, 1), edges)
            if original != graph_features(mask, edges):
                raise ValueError("Nonrepeatable geometry")
            results[index] = {
                "manifest_index": index, "scene": row["scene"],
                "size_fraction": float(mask.mean()), "selected_iou": iou,
                "boundary_fraction": original["boundary_fraction"],
                "components": original["components"],
                "shuffled_boundary_fraction": shuffled["boundary_fraction"],
                "shuffled_components": shuffled["components"],
            }
    if set(results) != set(by_index):
        raise ValueError("Missing expression features")
    rows = [results[i] for i in sorted(results)]
    pairs = matched_pairs(rows)
    return {
        "contract": "m95_target_blind_geometry_screen_v1",
        "capture_sha256": CAPTURE_SHA, "binding_sha256": BINDING_SHA,
        "rows": rows, "matched_pairs": pairs,
        "limited_rows": len(pairs),
        "same_scene_pairs": sum(p["same_scene"] for p in pairs),
        "admission": False,
        "interpretation": "Retrospective screen, not causal or training admission.",
    }


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "binding", "artifacts", "data-root", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    result = analyze(a.capture, a.binding, a.artifacts, a.data_root)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="ascii")
    print(json.dumps({k: result[k] for k in ("limited_rows", "same_scene_pairs", "admission")}))


if __name__ == "__main__":
    main()
