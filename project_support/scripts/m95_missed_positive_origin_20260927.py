"""Trace missed target superpoint support to native query seed identities."""
import argparse
import json
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA, POPULATION_SHA,
    PRODUCER_SHA, sha,
)


def evaluate(artifact, source):
    import torch

    idx = source["manifest_index"]
    if (int(artifact["manifest_index"]) != idx
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != source["scene"]
            or int(artifact["axis"]["ann_id"]) != source["ann_id"]):
        raise ValueError(f"Artifact identity differs: {idx}")
    masks = artifact["query_masks"].bool()
    target = artifact["target_union"].bool()
    if masks.ndim != 2 or masks.shape != (128, target.numel()) or not target.any():
        raise ValueError(f"Native mask axis differs: {idx}")
    fps = source["fps_superpoints"]
    sampled = source["sampled_seed_indices"]
    physical = source["physical_instance_labels"]
    positives = source["native_positive"]
    targets = set(source["target_instances"])
    if len(sampled) != 128 or len(positives) != 128 or len(artifact["native_positive"]) != 128:
        raise ValueError("Query axis differs")
    if any(bool(artifact["native_positive"][i]) != bool(positives[i]) for i in range(128)):
        raise ValueError(f"Matcher set differs: {idx}")
    seeds = []
    for seed in sampled:
        if not 0 <= seed < len(fps) or not 0 <= fps[seed] < len(physical):
            raise ValueError(f"Physical seed axis differs: {idx}")
        seeds.append(physical[fps[seed]] in targets)
    positive_indices = [i for i, yes in enumerate(positives) if yes]
    if not positive_indices:
        raise ValueError("No native positive")
    pos_union = masks[positive_indices].any(dim=0)
    missed = target & ~pos_union
    all_union = masks.any(dim=0)
    hit_target_seed_negative = torch.zeros_like(target)
    hit_non_target_seed = torch.zeros_like(target)
    for i in range(128):
        if positives[i]:
            continue
        if seeds[i]:
            hit_target_seed_negative |= masks[i]
        else:
            hit_non_target_seed |= masks[i]
    if bool((missed & pos_union).any()):
        raise ValueError("Missed and positive union overlap")
    return {
        "manifest_index": idx, "scene": source["scene"], "ann_id": source["ann_id"],
        "target_size": int(target.sum()), "native_positive_count": len(positive_indices),
        "target_seed_negative_queries": sum(s and not p for s, p in zip(seeds, positives)),
        "non_target_seed_negative_queries": sum(not s and not p for s, p in zip(seeds, positives)),
        "missed_by_positive": int(missed.sum()),
        "missed_reached_any": int((missed & all_union).sum()),
        "missed_target_seed_negative": int((missed & hit_target_seed_negative).sum()),
        "missed_only_non_target_seed": int(
            (missed & ~hit_target_seed_negative & hit_non_target_seed).sum()),
        "missed_uncovered": int((missed & ~all_union).sum()),
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
        raise ValueError("Frozen cohort differs")
    pending = limited | controls
    source = {r["manifest_index"]: r for r in capture["rows"]}
    results = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Frozen artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx in pending:
                results[idx] = evaluate(artifact, source[idx])
                pending.remove(idx)
    if pending:
        raise ValueError(f"Missing frozen rows: {sorted(pending)}")
    groups = {}
    for name, indices in (("fragmented", fragmented),
                          ("other_limited", limited - fragmented),
                          ("covered_controls", controls)):
        rows = [results[i] for i in sorted(indices)]
        groups[name] = {
            "expressions": len(rows), "scenes": len({r["scene"] for r in rows}),
            "rows_with_missed_reachable": sum(r["missed_reached_any"] > 0 for r in rows),
            "rows_with_target_seed_negative": sum(
                r["missed_target_seed_negative"] > 0 for r in rows),
            "missed_target_seed_negative": sum(
                r["missed_target_seed_negative"] for r in rows),
            "missed_only_non_target_seed": sum(
                r["missed_only_non_target_seed"] for r in rows),
            "missed_uncovered": sum(r["missed_uncovered"] for r in rows),
            "rows": rows,
        }
    return {"contract": "m95_missed_positive_origin_v1", "admission": False,
            "capture_sha256": CAPTURE_SHA, "fragment_sha256": FRAGMENT_SHA,
            "population_sha256": POPULATION_SHA, "groups": groups,
            "limits": "Retrospective TRAIN target-localized frozen query-mask origin; no new model, efficacy or admission."}


def main():
    p = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "fragment", "population", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    report = analyze(args.capture, args.artifact_root, args.fragment, args.population)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "rows"}
                      for k, g in report["groups"].items()}))


if __name__ == "__main__":
    main()
