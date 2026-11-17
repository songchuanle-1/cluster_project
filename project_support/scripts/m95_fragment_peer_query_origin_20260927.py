"""Frozen per-query support origin for annotated physical same-class peers."""
import argparse
import json
from collections import Counter
from pathlib import Path

from m95_native_positive_union_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, FRAGMENT_SHA, MANIFEST_SHA,
    POPULATION_SHA, PRODUCER_SHA, sha,
)

CROSSWALK_SHA = "3e5dce0a93565b38dcd2a79379580de35b4ee5489db38cb9a35b96bbf0d7768f"


def analyze(capture_path, artifact_root, manifest_path, population_path,
            fragment_path, crosswalk_path):
    import torch

    for path, expected in ((capture_path, CAPTURE_SHA),
                           (manifest_path, MANIFEST_SHA),
                           (population_path, POPULATION_SHA),
                           (fragment_path, FRAGMENT_SHA),
                           (crosswalk_path, CROSSWALK_SHA)):
        if sha(path) != expected:
            raise ValueError(f"Frozen input differs: {path}")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    population = json.loads(population_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["capture_mode"] != "full_train_scan"
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or len(capture["rows"]) != 256 or len(manifest["rows"]) != 256
            or crosswalk["capture_sha256"] != CAPTURE_SHA
            or crosswalk["manifest_sha256"] != MANIFEST_SHA
            or population["capture_sha256"] != CAPTURE_SHA
            or fragment["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen source contract differs")
    limited = {r["manifest_index"] for r in population["limited_rows"]}
    controls = {r["manifest_index"] for r in population["control_rows"]}
    fragmented = {r["manifest_index"] for r in fragment["groups"]["limited"]["rows"]
                  if r["extra_recall"] > 0}
    rows = {}
    source = {int(r["manifest_index"]): r for r in capture["rows"]}
    physical_peers = {int(r["manifest_index"]): r for r in crosswalk["rows"]
                      if r["valid_category"] and r["missed_target"]
                      and r["present_peers"]}
    if len(fragmented) != 4 or set(physical_peers) & fragmented != {64, 104}:
        raise ValueError("Fragmented cohort differs")
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact bytes differ: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx not in physical_peers:
                continue
            if idx in rows:
                raise ValueError("Duplicate native row")
            row = source[idx]
            peer = physical_peers[idx]
            if (artifact["artifact_contract"] != capture["artifact_contract"]
                    or artifact["manifest_sha256"] != MANIFEST_SHA
                    or artifact["axis"]["scene"] != row["scene"]
                    or peer["scene"] != row["scene"]
                    or str(manifest["rows"][idx]["target_object_id"])
                    != str(row["target_object_id"])):
                raise ValueError("Native identity differs")
            masks = artifact["query_masks"].bool()
            logits = artifact["query_mask_logits"]
            target = artifact["target_union"].bool()
            physical = artifact["physical_instance_labels"].long()
            semantic = torch.as_tensor(artifact["semantic_labels"]).long()
            positive = [i for i, yes in enumerate(row["native_positive"]) if yes]
            negative = [i for i in range(128) if i not in positive]
            if (not positive or masks.shape != (128, target.numel())
                    or logits.shape != masks.shape
                    or physical.shape != target.shape
                    or semantic.shape != target.shape
                    or not torch.equal(masks, logits > 0)
                    or not torch.isfinite(logits).all()
                    or list(artifact["native_positive"]) != row["native_positive"]):
                raise ValueError("Native query contract differs")
            if Counter(semantic[target].tolist()).most_common(1)[0][0] != peer["target_category"]:
                raise ValueError("Target semantic class differs")
            best = max(positive, key=lambda i: (
                float(row["ious"][i]), -i))
            deployed = int(row["selected_query"])
            if not 0 <= deployed < 128:
                raise ValueError("Selected query differs")
            positives = masks[positive].any(dim=0)
            negatives = masks[negative].any(dim=0) if negative else torch.zeros_like(target)
            missed = target & ~masks.any(dim=0)
            if int(missed.sum()) != peer["missed_target"]:
                raise ValueError("Uncovered target differs")
            def counts(axis):
                return {
                    "total": int(axis.sum()),
                    "any_positive": int((axis & positives).sum()),
                    "any_negative": int((axis & negatives).sum()),
                    "best_positive": int((axis & masks[best]).sum()),
                    "deployed": int((axis & masks[deployed]).sum()),
                    "all_query_uncovered": int((axis & ~(positives | negatives)).sum()),
                }
            details = []
            for item in peer["peers"]:
                axis = physical == int(item["object_id"])
                c = counts(axis)
                if (c["total"] != item["sampled_superpoints"]
                        or c["all_query_uncovered"] != item["uncovered"]):
                    raise ValueError("Crosswalk peer counts differ")
                details.append({"object_id": item["object_id"], **c})
            group = ("fragmented" if idx in fragmented else
                     "other_limited" if idx in limited else
                     "covered_controls" if idx in controls else "remainder")
            rows[idx] = {
                "manifest_index": idx, "scene": row["scene"], "group": group,
                "positive_queries": len(positive), "best_positive_index": best,
                "deployed_index": deployed, "peers": details,
                "target_missed": counts(missed),
            }
    if set(rows) != set(physical_peers):
        raise ValueError(f"Incomplete eligible rows: {sorted(set(physical_peers) - set(rows))}")
    groups = {}
    for group in ("fragmented", "other_limited", "covered_controls", "remainder"):
        part = [r for r in rows.values() if r["group"] == group]
        groups[group] = {
            "expressions": len(part), "scenes": len({r["scene"] for r in part}),
            "peer_superpoints": sum(p["total"] for r in part for p in r["peers"]),
            "peer_any_positive": sum(p["any_positive"] for r in part for p in r["peers"]),
            "peer_any_negative": sum(p["any_negative"] for r in part for p in r["peers"]),
            "peer_best_positive": sum(p["best_positive"] for r in part for p in r["peers"]),
            "peer_deployed": sum(p["deployed"] for r in part for p in r["peers"]),
        }
    return {
        "contract": "m95_fragment_peer_query_origin_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "crosswalk_sha256": CROSSWALK_SHA, "groups": groups,
        "fragmented_missed_rows": [rows[i] for i in (64, 104)],
        "rows": [rows[i] for i in sorted(rows)],
        "limits": "Observational TRAIN query origin, not causal model intervention or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("capture", "artifact-root", "manifest", "population",
                 "fragment", "crosswalk", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root, args.manifest,
                     args.population, args.fragment, args.crosswalk)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="ascii")
    print(json.dumps({"groups": result["groups"],
                      "fragmented_missed_rows": result["fragmented_missed_rows"]}))


if __name__ == "__main__":
    main()
