"""Trace final-query-uncovered target superpoints to native sampled FPS seeds."""
import argparse
import json
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
        raise ValueError(f"Frozen identity differs: {idx}")
    masks = artifact["query_masks"].bool()
    target = artifact["target_union"].bool()
    if masks.shape != (128, target.numel()) or not target.any():
        raise ValueError(f"Native mask axis differs: {idx}")
    fps, sampled = row["fps_superpoints"], row["sampled_seed_indices"]
    if len(sampled) != 128:
        raise ValueError("Query seed axis differs")
    seed_points = []
    for i in sampled:
        if not 0 <= i < len(fps) or not 0 <= fps[i] < target.numel():
            raise ValueError(f"FPS superpoint axis differs: {idx}")
        seed_points.append(fps[i])
    seed_mask = torch.zeros_like(target)
    seed_mask[torch.tensor(seed_points, dtype=torch.long)] = True
    uncovered = target & ~masks.any(dim=0)
    return {
        "manifest_index": idx, "scene": row["scene"], "ann_id": row["ann_id"],
        "target_size": int(target.sum()),
        "target_seed_queries": sum(bool(target[i]) for i in seed_points),
        "distinct_target_seed_superpoints": int((seed_mask & target).sum()),
        "uncovered_target": int(uncovered.sum()),
        "uncovered_directly_seeded": int((uncovered & seed_mask).sum()),
        "uncovered_not_directly_seeded": int((uncovered & ~seed_mask).sum()),
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
    result = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Frozen artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx in pending:
                result[idx] = evaluate(artifact, source[idx])
                pending.remove(idx)
    if pending:
        raise ValueError(f"Missing rows: {sorted(pending)}")
    groups = {}
    for name, ids in (("fragmented", fragmented),
                      ("other_limited", limited - fragmented),
                      ("covered_controls", controls)):
        rows = [result[i] for i in sorted(ids)]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "rows_with_uncovered": sum(r["uncovered_target"] > 0 for r in rows),
            "rows_with_directly_seeded_uncovered": sum(
                r["uncovered_directly_seeded"] > 0 for r in rows),
            "rows_with_any_target_seed": sum(r["target_seed_queries"] > 0 for r in rows),
            "uncovered_total": sum(r["uncovered_target"] for r in rows),
            "uncovered_directly_seeded": sum(r["uncovered_directly_seeded"] for r in rows),
            "rows": rows,
        }
    return {"contract": "m95_uncovered_seed_reach_v1", "admission": False,
            "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
            "population_sha256": POPULATION_SHA, "groups": groups,
            "limits": "Frozen TRAIN GT-localized seed reach census only; no causal training mechanism or admission."}


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({name: {k: v for k, v in g.items() if k != "rows"}
                      for name, g in result["groups"].items()}))


if __name__ == "__main__":
    main()
