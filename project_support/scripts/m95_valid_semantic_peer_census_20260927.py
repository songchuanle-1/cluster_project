"""Audit semantic-label validity in frozen missing-target same-class controls."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA, POPULATION_SHA,
    PRODUCER_SHA, sha,
)


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
        raise ValueError("Frozen source provenance differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    if len(limited) != 16 or len(controls) != 16 or len(fragmented) != 4:
        raise ValueError("Frozen cohorts differ")
    source = {r["manifest_index"]: r for r in capture["rows"]}
    rows = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            row = source[idx]
            if (idx in rows or artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != row["scene"]
                    or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
                raise ValueError(f"Frozen identity differs: {idx}")
            masks = artifact["query_masks"].bool()
            logits = artifact["query_mask_logits"]
            target = artifact["target_union"].bool()
            semantic = torch.as_tensor(artifact["semantic_labels"]).long()
            physical = artifact["physical_instance_labels"].long()
            if (masks.shape != (128, target.numel()) or masks.shape != logits.shape
                    or not torch.isfinite(logits).all() or not torch.equal(logits > 0, masks)
                    or not target.any() or semantic.shape != target.shape
                    or physical.shape != target.shape):
                raise ValueError(f"Native axis differs: {idx}")
            category = Counter(semantic[target].tolist()).most_common(1)[0][0]
            missed = target & ~masks.any(dim=0)
            same = ~target & ~masks.any(dim=0) & (semantic == category) & (physical >= 0)
            rows[idx] = {
                "manifest_index": idx, "scene": row["scene"],
                "ann_id": row["ann_id"], "category": category,
                "valid_category": category >= 0,
                "uncovered_target": int(missed.sum()),
                "same_category_uncovered": int(same.sum()),
                "valid_peer": category >= 0 and bool(same.any()),
            }
    if sorted(rows) != list(range(256)):
        raise ValueError("Incomplete frozen manifest")
    groups = {}
    for name, ids in (("fragmented", fragmented), ("other_limited", limited - fragmented),
                      ("covered_controls", controls),
                      ("remainder", set(range(256)) - limited - controls)):
        part = [rows[i] for i in sorted(ids)]
        with_miss = [r for r in part if r["uncovered_target"]]
        groups[name] = {
            "expressions": len(part), "scenes": len({r["scene"] for r in part}),
            "missed_target_expressions": len(with_miss),
            "unknown_target_category": sum(not r["valid_category"] for r in with_miss),
            "sentinel_permissive_peers": sum(r["same_category_uncovered"] > 0
                                             for r in with_miss),
            "valid_same_category_peers": sum(r["valid_peer"] for r in with_miss),
            "rows": part,
        }
    return {
        "contract": "m95_valid_semantic_peer_census_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
        "population_sha256": POPULATION_SHA, "groups": groups,
        "limits": "Retrospective frozen TRAIN semantic provenance, not intervention or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({name: {k: v for k, v in group.items() if k != "rows"}
                      for name, group in result["groups"].items()}))


if __name__ == "__main__":
    main()
