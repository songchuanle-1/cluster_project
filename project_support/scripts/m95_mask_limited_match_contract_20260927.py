"""Check native positive membership for the four frozen mask-limited rows."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

PRIOR_SHA = "915e1d7e9385392a4f30da35a50b2698b54e005394caeb1d6d6a5ed2d3ca6bd5"


def analyze(capture, prior):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or prior["capture_sha256"] != CAPTURE_SHA
            or prior["residual_expressions"] != 4
            or prior["with_adequate_non_target_seed_query"] != 0):
        raise ValueError("Frozen source provenance differs")
    rows = capture["rows"]
    if (len(rows) != 256
            or sorted(r["manifest_index"] for r in rows) != list(range(256))):
        raise ValueError("Manifest population differs")
    prior_rows = {r["manifest_index"]: r for r in prior["rows"]}
    if len(prior_rows) != 4:
        raise ValueError("Frozen residual count differs")
    result = []
    for row in rows:
        idx = row["manifest_index"]
        if idx not in prior_rows:
            continue
        old = prior_rows[idx]
        selected = row["selected_query"]
        seeds = row["sampled_seed_indices"]
        fps = row["fps_superpoints"]
        physical = row["physical_instance_labels"]
        positive = row["native_positive"]
        ious = row["ious"]
        cause = row["native_match_cause"]
        if (len(seeds) != 128 or len(positive) != 128 or len(ious) != 128
                or len(cause["native_positive"]) != 128
                or not 0 <= selected < 128
                or cause["native_positive"] != positive
                or any(not 0 <= seed < len(fps)
                       or not 0 <= fps[seed] < len(physical) for seed in seeds)):
            raise ValueError("Native matcher/physical seed axes differ")
        target = set(row["target_instances"])
        if (old["scene"] != row["scene"] or old["ann_id"] != row["ann_id"]
                or abs(old["selected_iou"] - ious[selected]) > 1e-6
                or physical[fps[seeds[selected]]] not in target):
            raise ValueError("Frozen residual identity differs")
        physical_target = [physical[fps[seed]] in target for seed in seeds]
        pos_target = [q for q in range(128) if positive[q] and physical_target[q]]
        if any(ious[q] > .5 for q in range(128)):
            raise ValueError("Residual actually has an adequate query")
        result.append({
            "manifest_index": idx, "scene": row["scene"], "ann_id": row["ann_id"],
            "selected_query": selected, "selected_native_positive": positive[selected],
            "selected_nearest_gt": selected in cause["nearest_query_per_gt"],
            "selected_instance_member": any(
                selected in group for group in cause["member_queries_per_gt"]),
            "physical_target_seed_queries": sum(physical_target),
            "native_positive_target_seed_queries": len(pos_target),
            "native_positive_target_seed_best_iou": (
                max(ious[q] for q in pos_target) if pos_target else None),
        })
    if len(result) != 4:
        raise ValueError("Residual row coverage differs")
    return {
        "contract": "m95_mask_limited_match_contract_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "prior_sha256": PRIOR_SHA,
        "rows": sorted(result, key=lambda r: r["manifest_index"]),
        "selected_matcher_positive": sum(r["selected_native_positive"] for r in result),
        "failure_expressions": 4,
        "failure_scenes": len({r["scene"] for r in result}),
        "limits": "TRAIN native matcher readout, not a new loss or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.output.exists() or sha(args.capture) != CAPTURE_SHA
            or sha(args.prior) != PRIOR_SHA):
        raise ValueError("Output exists or frozen source differs")
    result = analyze(json.loads(args.capture.read_text(encoding="utf-8")),
                     json.loads(args.prior.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}))


if __name__ == "__main__":
    main()
