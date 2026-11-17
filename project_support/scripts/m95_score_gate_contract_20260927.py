"""Audit existing native score-loss eligibility, without altering the loss."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

RESIDUAL_SHA = "915e1d7e9385392a4f30da35a50b2698b54e005394caeb1d6d6a5ed2d3ca6bd5"
SUPPORT_SHA = "0cc44842f05d713e2cc221de7f9a34ff4a59a3210d7b7d18c9ad9879de257cb2"


def partition(row):
    selected = row["selected_query"]
    positive = row["native_positive"]
    ious = row["ious"]
    if (not 0 <= selected < 128 or len(positive) != 128
            or len(ious) != 128 or not all(0 <= v <= 1 for v in ious)):
        raise ValueError("Query axis differs")
    matched = [q for q, ok in enumerate(positive) if ok]
    eligible = [q for q in matched if ious[q] > .5]
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "selected_positive": bool(positive[selected]),
        "selected_score_supervised": bool(positive[selected] and ious[selected] > .5),
        "matched_queries": len(matched), "score_supervised_queries": len(eligible),
        "selected_iou": ious[selected],
        "max_positive_iou": max((ious[q] for q in matched), default=None),
    }


def analyze(capture, residual, support):
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or support["capture_sha256"] != CAPTURE_SHA
            or residual["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Frozen provenance differs")
    rows = capture["rows"]
    if len(rows) != 256 or sorted(r["manifest_index"] for r in rows) != list(range(256)):
        raise ValueError("Frozen population differs")
    results = [partition(r) for r in rows]
    failure_ids = {r["manifest_index"] for r in residual["rows"]}
    control_ids = {r["manifest_index"] for r in support["control_rows"]}
    if len(failure_ids) != 4 or len(control_ids) != 4:
        raise ValueError("Frozen cohort differs")
    by_id = {r["manifest_index"]: r for r in results}
    failures = [by_id[i] for i in sorted(failure_ids)]
    controls = [by_id[i] for i in sorted(control_ids)]
    if (any(not r["selected_positive"] for r in failures)
            or any(not r["selected_positive"] for r in controls)):
        raise ValueError("Selected matcher-positive cohort differs")
    return {
        "contract": "m95_score_gate_contract_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "residual_sha256": RESIDUAL_SHA,
        "support_sha256": SUPPORT_SHA,
        "population": {
            "expressions": len(results),
            "scenes": len({r["scene"] for r in results}),
            "selected_positive": sum(r["selected_positive"] for r in results),
            "selected_score_supervised": sum(r["selected_score_supervised"] for r in results),
        },
        "failure_rows": failures, "control_rows": controls,
        "limits": "Existing score MSE gate; BCE/Dice remain. No new mechanism or admission.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--residual", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.output.exists() or sha(args.capture) != CAPTURE_SHA
            or sha(args.residual) != RESIDUAL_SHA or sha(args.support) != SUPPORT_SHA):
        raise ValueError("Frozen file hash differs or output exists")
    result = analyze(*(json.loads(path.read_text(encoding="utf-8"))
                       for path in (args.capture, args.residual, args.support)))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result["population"]))


if __name__ == "__main__":
    main()
