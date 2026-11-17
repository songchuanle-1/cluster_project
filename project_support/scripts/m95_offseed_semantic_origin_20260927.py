"""Classify off-seed mask support relative to frozen target semantics."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA, POPULATION_SHA,
    PRODUCER_SHA, sha,
)


def evaluate(artifact, row):
    import torch

    idx = row["manifest_index"]
    if (int(artifact["manifest_index"]) != idx
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Identity mismatch")
    masks = artifact["query_masks"].bool()
    target = artifact["target_union"].bool()
    semantics = artifact["semantic_labels"]
    if masks.shape != (128, target.numel()) or len(semantics) != target.numel():
        raise ValueError("Native axis mismatch")
    target_classes = [int(semantics[i]) for i in torch.where(target)[0] if int(semantics[i]) >= 0]
    target_class = Counter(target_classes).most_common(1)[0][0] if target_classes else None
    fps, seeds, positives = (row[name] for name in (
        "fps_superpoints", "sampled_seed_indices", "native_positive"))
    if len(seeds) != 128 or len(positives) != 128:
        raise ValueError("Query count differs")
    if any(bool(artifact["native_positive"][i]) != bool(positives[i]) for i in range(128)):
        raise ValueError("Native matcher differs")
    positive_ids = [i for i, yes in enumerate(positives) if yes]
    if not positive_ids:
        raise ValueError("No positive queries")
    missed = target & ~masks[positive_ids].any(dim=0)
    same = torch.zeros_like(target)
    different = torch.zeros_like(target)
    unknown = torch.zeros_like(target)
    same_queries = 0
    different_queries = 0
    for i in range(128):
        if positives[i]:
            continue
        seed = seeds[i]
        if not 0 <= seed < len(fps) or not 0 <= fps[seed] < len(semantics):
            raise ValueError("Seed-superpoint identity differs")
        cls = int(semantics[fps[seed]])
        if target_class is None or cls < 0:
            unknown |= masks[i]
        elif cls == target_class:
            same |= masks[i]
            same_queries += 1
        else:
            different |= masks[i]
            different_queries += 1
    reached = missed & (same | different | unknown)
    return {
        "manifest_index": idx, "scene": row["scene"], "target_class": target_class,
        "target_size": int(target.sum()), "positive_count": len(positive_ids),
        "same_class_negative_queries": same_queries,
        "different_class_negative_queries": different_queries,
        "missed_by_positive": int(missed.sum()),
        "missed_reached_by_negative": int(reached.sum()),
        "reached_same_class": int((missed & same).sum()),
        "reached_only_different_class": int((missed & ~same & different).sum()),
        "reached_only_unknown": int((missed & ~same & ~different & unknown).sum()),
        "missed_uncovered": int((missed & ~reached).sum()),
    }


def analyze(capture_path, artifact_root, fragment_path, population_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA), (fragment_path, FRAGMENT_SHA),
                           (population_path, POPULATION_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen source differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256
            or fragment["capture_sha256"] != CAPTURE_SHA
            or population["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen provenance differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohorts differ")
    pending = limited | controls
    source = {r["manifest_index"]: r for r in capture["rows"]}
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx in pending:
                results[idx] = evaluate(artifact, source[idx])
                pending.remove(idx)
    if pending:
        raise ValueError(f"Missing rows: {sorted(pending)}")
    groups = {}
    for name, ids in (("fragmented", fragmented),
                      ("other_limited", limited - fragmented),
                      ("covered_controls", controls)):
        rows = [results[i] for i in sorted(ids)]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "rows_with_same_class_reach": sum(r["reached_same_class"] > 0 for r in rows),
            "reached_same_class": sum(r["reached_same_class"] for r in rows),
            "reached_only_different_class": sum(r["reached_only_different_class"] for r in rows),
            "reached_only_unknown": sum(r["reached_only_unknown"] for r in rows),
            "missed_uncovered": sum(r["missed_uncovered"] for r in rows),
            "rows": rows,
        }
    return {"contract": "m95_offseed_semantic_origin_v1", "admission": False,
            "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
            "population_sha256": POPULATION_SHA, "groups": groups,
            "limits": "Frozen TRAIN GT-localized observational semantic origin; no intervention, novelty or admission."}


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({name: {k: v for k, v in group.items() if k != "rows"}
                      for name, group in result["groups"].items()}))


if __name__ == "__main__":
    main()
