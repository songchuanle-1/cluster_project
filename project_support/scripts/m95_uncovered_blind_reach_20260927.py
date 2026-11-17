"""Target-blind all-query native support with GT held to retrospective evaluation."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA, POPULATION_SHA,
    PRODUCER_SHA, sha,
)


def analyze(capture_path, artifact_root, fragment_path, population_path,
            binding_path, data_root):
    import numpy as np
    import torch
    from scipy.spatial import cKDTree

    for path, expected in ((capture_path, CAPTURE_SHA), (fragment_path, FRAGMENT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or fragment["capture_sha256"] != CAPTURE_SHA
            or population["capture_sha256"] != CAPTURE_SHA
            or binding["capture_sha256"] != CAPTURE_SHA
            or binding["rows_bound"] != 256):
        raise ValueError("Frozen provenance differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohorts differ")
    source = {r["manifest_index"]: r for r in capture["rows"]}
    bound = {r["manifest_index"]: r for r in binding["rows"]}
    pending = limited | controls
    graphs = {}
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in pending:
                continue
            row = source[idx]
            identity = bound[idx]
            scene = row["scene"]
            if (artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != scene
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]
                    or identity["scene"] != scene
                    or int(identity["ann_id"]) != row["ann_id"]):
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
                    or not target.any()
                    or len(semantic) != len(target)
                    or len(physical) != len(target)):
                raise ValueError(f"Native axis differs: {idx}")
            if scene not in graphs:
                scene_path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
                if sha(scene_path) != identity["scene_sha256"]:
                    raise ValueError(f"Scene source differs: {scene}")
                xyz, _, sp, _, _ = torch.load(
                    scene_path, map_location="cpu", weights_only=False)
                original, inverse = np.unique(sp, return_inverse=True)
                if (not np.array_equal(original, row["original_superpoint_ids"])
                        or not np.array_equal(inverse, row["sample_inverse"])
                        or len(original) != identity["superpoints"]):
                    raise ValueError(f"Physical support axis differs: {scene}")
                counts = np.bincount(inverse, minlength=len(original))
                centroids = np.zeros((len(original), 3), dtype=np.float64)
                np.add.at(centroids, inverse, xyz)
                centroids /= counts[:, None]
                spacing = float(np.median(cKDTree(centroids).query(
                    centroids, k=2)[0][:, 1]))
                if not np.isfinite(spacing) or spacing <= 0:
                    raise ValueError(f"Scene spacing invalid: {scene}")
                graphs[scene] = centroids, spacing
            centroids, spacing = graphs[scene]
            support = masks.any(dim=0).numpy()
            unseen_target = ~support & target
            unseen_background = ~support & ~target
            category = Counter(semantic[target]).most_common(1)[0][0]
            same_class = unseen_background & (semantic == category) & (physical >= 0)
            out = {
                "manifest_index": idx, "scene": scene, "ann_id": row["ann_id"],
                "uncovered_target": int(unseen_target.sum()),
                "uncovered_background": int(unseen_background.sum()),
                "uncovered_same_class": int(same_class.sum()),
                "blind_support": int(support.sum()),
            }
            if support.any() and unseen_target.any():
                tree = cKDTree(centroids[support])
                target_d = tree.query(centroids[unseen_target])[0] / spacing
                out["target_distance_median"] = float(np.median(target_d))
                for arm, region in (("background", unseen_background),
                                    ("same_class", same_class)):
                    out[arm + "_distance_median"] = (
                        float(np.median(tree.query(centroids[region])[0] / spacing))
                        if region.any() else None)
            else:
                out["target_distance_median"] = None
                out["background_distance_median"] = None
                out["same_class_distance_median"] = None
            results[idx] = out
            pending.remove(idx)
    if pending:
        raise ValueError(f"Missing native rows: {sorted(pending)}")
    groups = {}
    for name, ids in (("fragmented", fragmented),
                      ("other_limited", limited - fragmented),
                      ("covered_controls", controls)):
        rows = [results[i] for i in sorted(ids)]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "uncovered_target": sum(r["uncovered_target"] for r in rows),
            "paired_background": sum(r["background_distance_median"] is not None
                                     for r in rows),
            "paired_same_class": sum(r["same_class_distance_median"] is not None
                                     for r in rows),
            "target_closer_background": sum(
                r["target_distance_median"] < r["background_distance_median"]
                for r in rows if r["background_distance_median"] is not None),
            "target_closer_same_class": sum(
                r["target_distance_median"] < r["same_class_distance_median"]
                for r in rows if r["same_class_distance_median"] is not None),
            "rows": rows,
        }
    return {
        "contract": "m95_uncovered_blind_reach_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
        "population_sha256": POPULATION_SHA, "binding_sha256": sha(binding_path),
        "groups": groups,
        "limits": "Frozen TRAIN retrospective GT strata, target-blind support source; no causal mechanism or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population",
                 "binding", "data-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.fragment,
                     args.population, args.binding, args.data_root)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({name: {k: v for k, v in group.items() if k != "rows"}
                      for name, group in report["groups"].items()}))


if __name__ == "__main__":
    main()
