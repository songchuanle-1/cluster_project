"""Preselected valid-class peer control against prediction-blind query support."""
import argparse
import json
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, census_path, binding_path, data_root):
    import numpy as np
    import torch
    from scipy.spatial import cKDTree

    if sha(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    census = json.loads(census_path.read_text(encoding="utf-8"))
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or census["capture_sha256"] != CAPTURE_SHA
            or census["contract"] != "m95_valid_semantic_peer_census_v1"
            or binding["capture_sha256"] != CAPTURE_SHA
            or binding["rows_bound"] != 256):
        raise ValueError("Frozen source provenance differs")
    groups = ("fragmented", "other_limited", "covered_controls", "remainder")
    selected = {
        r["manifest_index"]: (group, r)
        for group in groups for r in census["groups"][group]["rows"]
        if r["uncovered_target"] > 0 and r["valid_peer"]
    }
    if (len(selected) != 33
            or [sum(g == group for g, _ in selected.values()) for group in groups]
            != [0, 1, 2, 30]):
        raise ValueError("Preregistered valid peer cohort differs")
    source = {r["manifest_index"]: r for r in capture["rows"]}
    bound = {r["manifest_index"]: r for r in binding["rows"]}
    pending = set(selected)
    centroids_by_scene = {}
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen feature artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in pending:
                continue
            row, identity = source[idx], bound[idx]
            group, selected_row = selected[idx]
            scene = row["scene"]
            if (artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != scene
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]
                    or identity["scene"] != scene
                    or int(identity["ann_id"]) != row["ann_id"]
                    or selected_row["scene"] != scene
                    or int(selected_row["ann_id"]) != row["ann_id"]):
                raise ValueError(f"Native identity differs: {idx}")
            masks = artifact["query_masks"].bool()
            logits = artifact["query_mask_logits"]
            target = artifact["target_union"].bool().numpy()
            semantic = np.asarray(artifact["semantic_labels"])
            physical = artifact["physical_instance_labels"].numpy()
            if (masks.shape != (128, len(target))
                    or masks.shape != logits.shape
                    or not bool(torch.isfinite(logits).all())
                    or not torch.equal(masks, logits > 0)
                    or len(semantic) != len(target)
                    or len(physical) != len(target)):
                raise ValueError(f"Native mask axis differs: {idx}")
            support = masks.any(dim=0).numpy()
            missed = target & ~support
            category = selected_row["category"]
            peer = ~target & ~support & (semantic == category) & (physical >= 0)
            if (category < 0 or int(missed.sum()) != selected_row["uncovered_target"]
                    or int(peer.sum()) != selected_row["same_category_uncovered"]
                    or not missed.any() or not peer.any() or not support.any()):
                raise ValueError(f"Frozen cohort membership differs: {idx}")
            if scene not in centroids_by_scene:
                scene_path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
                if sha(scene_path) != identity["scene_sha256"]:
                    raise ValueError(f"Scene bytes differ: {scene}")
                xyz, _, sp, _, _ = torch.load(
                    scene_path, map_location="cpu", weights_only=False)
                original, inverse = np.unique(sp, return_inverse=True)
                if (not np.array_equal(original, row["original_superpoint_ids"])
                        or not np.array_equal(inverse, row["sample_inverse"])
                        or len(original) != identity["superpoints"]):
                    raise ValueError(f"Physical axis differs: {scene}")
                counts = np.bincount(inverse, minlength=len(original))
                centroids = np.zeros((len(original), 3), dtype=np.float64)
                np.add.at(centroids, inverse, xyz)
                centroids /= counts[:, None]
                spacing = float(np.median(
                    cKDTree(centroids).query(centroids, k=2)[0][:, 1]))
                if not np.isfinite(spacing) or spacing <= 0:
                    raise ValueError(f"Invalid scene spacing: {scene}")
                centroids_by_scene[scene] = centroids, spacing
            centroids, spacing = centroids_by_scene[scene]
            def distance(mask):
                tree = cKDTree(centroids[mask])
                a = float(np.median(tree.query(centroids[missed])[0] / spacing))
                b = float(np.median(tree.query(centroids[peer])[0] / spacing))
                return {"target": a, "peer": b, "target_closer": a < b}
            rolled = np.roll(support, len(support) // 2)
            results[idx] = {
                "manifest_index": idx, "scene": scene, "group": group,
                "uncovered_target": int(missed.sum()),
                "same_category_peer": int(peer.sum()),
                "original": distance(support), "rolled": distance(rolled),
            }
            pending.remove(idx)
    if pending:
        raise ValueError(f"Missing native rows: {sorted(pending)}")
    output = {}
    for group in groups:
        rows = [results[i] for i in sorted(results) if results[i]["group"] == group]
        output[group] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "original_target_closer": sum(r["original"]["target_closer"] for r in rows),
            "rolled_target_closer": sum(r["rolled"]["target_closer"] for r in rows),
            "rows": rows,
        }
    return {
        "contract": "m95_valid_peer_blind_distance_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "census_sha256": sha(census_path),
        "binding_sha256": sha(binding_path), "groups": output,
        "limits": "TRAIN retrospective GT-localized control; not a causal model path or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "census", "binding", "data-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.census,
                     args.binding, args.data_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({name: {k: v for k, v in group.items() if k != "rows"}
                      for name, group in result["groups"].items()}))


if __name__ == "__main__":
    main()
