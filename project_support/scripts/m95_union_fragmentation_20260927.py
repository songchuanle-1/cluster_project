"""Frozen M95 query mask union versus best-single-query coverage audit."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, MANIFEST_SHA, PRODUCER_SHA, CHECKPOINT_SHA, sha,
)


def evaluate(artifact, row):
    import torch

    if (artifact["artifact_contract"] != "m95_manifest_native_query_artifact_v1"
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]):
        raise ValueError("Artifact identity differs")
    masks = artifact["query_masks"].bool()
    target = artifact["target_union"].bool()
    if (masks.ndim != 2 or masks.shape[0] != 128
            or masks.shape[1] != len(target) or not target.any()):
        raise ValueError("Native axes differ")
    tp = (masks & target).sum(dim=1)
    fp = (masks & ~target).sum(dim=1)
    # Highest target recall, then smallest false-positive support, then index.
    best = min(range(128), key=lambda idx: (
        -int(tp[idx]), int(fp[idx]), idx))
    union = masks.any(dim=0)
    union_tp = int((union & target).sum())
    union_fp = int((union & ~target).sum())
    target_size = int(target.sum())
    best_tp = int(tp[best])
    best_fp = int(fp[best])
    return {
        "manifest_index": row["manifest_index"],
        "scene": row["scene"], "ann_id": row["ann_id"],
        "limited": max(row["ious"]) <= .5,
        "target_superpoints": target_size,
        "best_query_oracle": best,
        "best_tp": best_tp, "best_fp": best_fp,
        "union_tp": union_tp, "union_fp": union_fp,
        "best_recall": best_tp / target_size,
        "union_recall": union_tp / target_size,
        "extra_recall": (union_tp - best_tp) / target_size,
        "best_precision": best_tp / max(1, best_tp + best_fp),
        "union_precision": union_tp / max(1, union_tp + union_fp),
    }


def analyze(capture_path, artifact_root):
    import torch

    if sha(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Provenance differs")
    source = {r["manifest_index"]: r for r in capture["rows"]}
    result = {}
    for entry in capture["feature_artifacts"]:
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError(f"Artifact differs: {path}")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            idx = int(artifact["manifest_index"])
            if idx in result:
                raise ValueError("Duplicate manifest index")
            result[idx] = evaluate(artifact, source[idx])
    if sorted(result) != list(range(256)):
        raise ValueError("Incomplete population")
    groups = {}
    for limited in (True, False):
        rows = [result[i] for i in sorted(result) if result[i]["limited"] == limited]
        groups["limited" if limited else "covered"] = {
            "expressions": len(rows),
            "scenes": len({r["scene"] for r in rows}),
            "extra_recall_positive": sum(r["extra_recall"] > 0 for r in rows),
            "mean_extra_recall": sum(r["extra_recall"] for r in rows) / len(rows),
            "mean_union_precision": sum(r["union_precision"] for r in rows) / len(rows),
            "mean_best_precision": sum(r["best_precision"] for r in rows) / len(rows),
            "rows": rows,
        }
    return {
        "contract": "m95_union_fragmentation_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "groups": groups,
        "limits": "TRAIN GT oracle chooses best-query bound only for retrospective readout; no inference-time rule, native backward or trained efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    for key in ("capture", "artifact-root", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.artifact_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {n: v for n, v in g.items() if n != "rows"}
                      for k, g in result["groups"].items()}))


if __name__ == "__main__":
    main()
