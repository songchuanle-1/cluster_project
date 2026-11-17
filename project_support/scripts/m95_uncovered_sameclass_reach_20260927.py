"""Same-class physical placebo for frozen missed-support distance."""
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
            target = artifact["target_union"].bool().numpy()
            positives = [i for i, yes in enumerate(row["native_positive"]) if yes]
            semantics = np.asarray(artifact["semantic_labels"])
            physical = artifact["physical_instance_labels"].numpy()
            if (masks.shape != (128, len(target)) or not positives
                    or len(semantics) != len(target) or len(physical) != len(target)
                    or any(bool(artifact["native_positive"][i]) != (i in positives)
                           for i in range(128))):
                raise ValueError(f"Native axis differs: {idx}")
            if scene not in graphs:
                scene_path = data_root / "scannetv2" / "train" / (scene + "_refer.pth")
                if sha(scene_path) != identity["scene_sha256"]:
                    raise ValueError(f"Scene source changed: {scene}")
                xyz, _, sp, _, _ = torch.load(
                    scene_path, map_location="cpu", weights_only=False)
                original, inverse = np.unique(sp, return_inverse=True)
                if (not np.array_equal(original, row["original_superpoint_ids"])
                        or not np.array_equal(inverse, row["sample_inverse"])
                        or len(original) != identity["superpoints"]):
                    raise ValueError(f"Physical axis changed: {scene}")
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
            unseen = ~masks.any(dim=0).numpy()
            positive_target = masks[positives].any(dim=0).numpy() & target
            missed_target = unseen & target
            target_category = Counter(semantics[target]).most_common(1)[0][0]
            same_class = unseen & ~target & (semantics == target_category) & (physical >= 0)
            out = {
                "manifest_index": idx, "scene": scene, "ann_id": row["ann_id"],
                "uncovered_target": int(missed_target.sum()),
                "same_class_background": int(same_class.sum()),
                "positive_target_support": int(positive_target.sum()),
            }
            if positive_target.any() and missed_target.any() and same_class.any():
                tree = cKDTree(centroids[positive_target])
                target_d = tree.query(centroids[missed_target])[0] / spacing
                control_d = tree.query(centroids[same_class])[0] / spacing
                out.update({
                    "status": "paired",
                    "target_distance_median": float(np.median(target_d)),
                    "same_class_distance_median": float(np.median(control_d)),
                    "target_closer": bool(np.median(target_d) < np.median(control_d)),
                })
            else:
                out["status"] = "insufficient_parts"
            results[idx] = out
            pending.remove(idx)
    if pending:
        raise ValueError(f"Missing native rows: {sorted(pending)}")
    groups = {}
    for name, ids in (("fragmented", fragmented),
                      ("other_limited", limited - fragmented),
                      ("covered_controls", controls)):
        rows = [results[i] for i in sorted(ids)]
        paired = [r for r in rows if r["status"] == "paired"]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "paired_expressions": len(paired),
            "target_closer": sum(r["target_closer"] for r in paired),
            "rows": rows,
        }
    return {
        "contract": "m95_uncovered_sameclass_reach_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
        "population_sha256": POPULATION_SHA, "binding_sha256": sha(binding_path),
        "groups": groups,
        "limits": "Frozen TRAIN GT-localized same-class control, not causal inference or admission.",
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
