"""Read-only target-seeded mask error partition on frozen native superpoints."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def analyze(capture):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"):
        raise ValueError("Frozen native provenance differs")
    rows = capture["rows"]
    if (len(rows) != 256
            or sorted(row["manifest_index"] for row in rows) != list(range(256))):
        raise ValueError("Frozen manifest population differs")
    failures = []
    for row in rows:
        query = row["selected_query"]
        if not 0 <= query < 128:
            raise ValueError("Query outside native range")
        seed = row["sampled_seed_indices"][query]
        fps = row["fps_superpoints"]
        physical = row["physical_instance_labels"]
        mask = row["selected_mask"]
        target = set(row["target_instances"])
        if (not target or not 0 <= seed < len(fps)
                or not 0 <= fps[seed] < len(physical)
                or len(mask) != len(physical)):
            raise ValueError("Seed, mask and physical instance axes differ")
        if physical[fps[seed]] not in target:
            continue
        tp = sum(bool(p) and inst in target for p, inst in zip(mask, physical))
        fp = sum(bool(p) and inst not in target for p, inst in zip(mask, physical))
        fn = sum(not bool(p) and inst in target for p, inst in zip(mask, physical))
        recomputed = tp / max(tp + fp + fn, 1)
        if abs(recomputed - row["ious"][query]) > 1e-6:
            raise ValueError("Recomputed native selected mask IoU differs")
        if row["ious"][query] > .5:
            continue
        failures.append({
            "manifest_index": row["manifest_index"],
            "scene": row["scene"], "ann_id": row["ann_id"],
            "target_instance": sorted(target),
            "tp": tp, "fp": fp, "fn": fn,
            "target_size": tp + fn,
            "mask_size": tp + fp,
            "target_miss_fraction": fn / max(tp + fn, 1),
            "mask_contamination_fraction": fp / max(tp + fp, 1),
            "dominant": ("undercoverage" if fn > fp else
                         "contamination" if fp > fn else "tie"),
            "iou": recomputed,
        })
    counts = Counter(r["dominant"] for r in failures)
    return {
        "contract": "m95_target_seed_extent_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "population_expressions": 256,
        "failure_expressions": len(failures),
        "failure_scenes": len({r["scene"] for r in failures}),
        "dominant_counts": dict(counts),
        "rows": sorted(failures, key=lambda r: r["manifest_index"]),
        "limits": "Frozen TRAIN selected-mask GT partition; not causal, deployable or efficacy evidence.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or sha(args.capture) != CAPTURE_SHA:
        raise ValueError("Output exists or frozen capture differs")
    result = analyze(json.loads(args.capture.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}))


if __name__ == "__main__":
    main()
