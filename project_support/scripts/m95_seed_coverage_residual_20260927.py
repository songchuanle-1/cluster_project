"""Audit non-target-seeded adequate alternatives in frozen mask-limited rows."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

PRIOR_SHA = "22d0b83e3d3a4dd4cce7487193de02a356b4d0373505eb2fa35286a2781dfb3c"


def analyze(capture, prior):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or prior["capture_sha256"] != CAPTURE_SHA
            or prior["target_seed_failures"] != 8
            or prior["with_adequate_target_seed_alternative"] != 4):
        raise ValueError("Frozen source/provenance differs")
    rows = capture["rows"]
    if (len(rows) != 256 or
            sorted(row["manifest_index"] for row in rows) != list(range(256))):
        raise ValueError("Manifest coverage differs")
    prior_rows = {r["manifest_index"]: r for r in prior["rows"]}
    if len(prior_rows) != 8:
        raise ValueError("Prior target-seed failure rows differ")
    residual = []
    for row in rows:
        index = row["manifest_index"]
        if index not in prior_rows or prior_rows[index]["adequate_alternatives"]:
            continue
        saved = prior_rows[index]
        selected = row["selected_query"]
        seeds = row["sampled_seed_indices"]
        fps = row["fps_superpoints"]
        physical = row["physical_instance_labels"]
        ious = row["ious"]
        scores = row["scores"]
        if (len(seeds) != 128 or len(ious) != 128 or len(scores) != 128
                or not 0 <= selected < 128
                or any(not 0 <= i < len(fps) or not 0 <= fps[i] < len(physical)
                       for i in seeds)
                or any(not 0 <= iou <= 1 for iou in ious)):
            raise ValueError("Native query or physical seed axis differs")
        target = set(row["target_instances"])
        if (row["scene"] != saved["scene"] or row["ann_id"] != saved["ann_id"]
                or abs(ious[selected] - saved["selected_iou"]) > 1e-6
                or physical[fps[seeds[selected]]] not in target):
            raise ValueError("Prior failure identity differs")
        target_bound = [physical[fps[seed]] in target for seed in seeds]
        if any(ious[q] > .5 for q in range(128) if target_bound[q] and q != selected):
            raise ValueError("Prior target-seeded alternative count differs")
        alternatives = [q for q in range(128)
                        if q != selected and not target_bound[q] and ious[q] > .5]
        ranking = sorted(range(128), key=lambda q: (-scores[q], q))
        best = max(alternatives, key=lambda q: (ious[q], scores[q], -q)) if alternatives else None
        residual.append({
            "manifest_index": index, "scene": row["scene"], "ann_id": row["ann_id"],
            "selected_iou": ious[selected],
            "adequate_non_target_seed_queries": len(alternatives),
            "best": None if best is None else {
                "query": best, "iou": ious[best], "score": scores[best],
                "rank": ranking.index(best) + 1,
                "physical_seed_instance": physical[fps[seeds[best]]],
            },
        })
    if len(residual) != 4:
        raise ValueError("Four-row residual population differs")
    return {
        "contract": "m95_seed_coverage_residual_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "prior_sha256": PRIOR_SHA,
        "residual_expressions": 4,
        "residual_scenes": len({r["scene"] for r in residual}),
        "with_adequate_non_target_seed_query": sum(
            bool(r["adequate_non_target_seed_queries"]) for r in residual),
        "rows": sorted(residual, key=lambda r: r["manifest_index"]),
        "limits": "TRAIN same-forward GT oracle, no deployed identity signal or admission.",
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
