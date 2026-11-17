"""Read-only same-expression target-seeded query alternatives."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)


def analyze(capture):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"):
        raise ValueError("Native capture provenance differs")
    rows = capture["rows"]
    if (len(rows) != 256
            or sorted(r["manifest_index"] for r in rows) != list(range(256))):
        raise ValueError("Manifest population differs")
    failures = []
    for row in rows:
        selected = row["selected_query"]
        seeds = row["sampled_seed_indices"]
        fps = row["fps_superpoints"]
        physical = row["physical_instance_labels"]
        ious = row["ious"]
        scores = row["scores"]
        if not 0 <= selected < 128 or any(
                len(axis) != 128 for axis in (seeds, ious, scores)):
            raise ValueError("Native query axis differs")
        if any(not 0 <= i < len(fps) or not 0 <= fps[i] < len(physical)
               for i in seeds):
            raise ValueError("Physical seed axis differs")
        if any(not 0 <= iou <= 1 for iou in ious):
            raise ValueError("Native IoU outside unit range")
        target = set(row["target_instances"])
        bound = [physical[fps[i]] in target for i in seeds]
        if not bound[selected] or ious[selected] > .5:
            continue
        alternatives = [q for q in range(128)
                        if q != selected and bound[q] and ious[q] > .5]
        score_rank = sorted(range(128), key=lambda q: (-scores[q], q))
        best = max(alternatives, key=lambda q: (ious[q], scores[q], -q)) if alternatives else None
        failures.append({
            "manifest_index": row["manifest_index"],
            "scene": row["scene"], "ann_id": row["ann_id"],
            "selected_query": selected, "selected_iou": ious[selected],
            "selected_score": scores[selected],
            "target_seed_queries": sum(bound),
            "adequate_alternatives": len(alternatives),
            "best_alternative": None if best is None else {
                "query": best, "iou": ious[best], "score": scores[best],
                "score_rank": score_rank.index(best) + 1,
            },
        })
    return {
        "contract": "m95_target_seed_query_counterfactual_v1",
        "admission": False, "capture_sha256": CAPTURE_SHA,
        "population_expressions": 256,
        "target_seed_failures": len(failures),
        "scenes": len({r["scene"] for r in failures}),
        "with_adequate_target_seed_alternative": sum(
            r["adequate_alternatives"] > 0 for r in failures),
        "rows": sorted(failures, key=lambda r: r["manifest_index"]),
        "limits": "Same-forward GT oracle; cannot deploy query choice or claim efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or sha(args.capture) != CAPTURE_SHA:
        raise ValueError("Frozen capture differs or output exists")
    result = analyze(json.loads(args.capture.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}))


if __name__ == "__main__":
    main()
