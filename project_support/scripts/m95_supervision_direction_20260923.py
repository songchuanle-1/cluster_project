"""Describe frozen indicator supervision, not an intervention or candidate."""
import argparse
import hashlib
import json
import math
import os
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path

FOLLOWUP_SHA256 = "444aa9c8af032709010e8f4f148ce42ec5020eb9b94d7a2663f857e4d7418132"
LOSS_SHA256 = "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def indicator_direction(query):
    probability = query["score"]
    label = query["native_positive"]
    if type(label) is not bool or not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Invalid frozen indicator probability or label")
    if query["target_seed"] and not label:
        raise ValueError("Target-seeded query outside native positives")
    # d CE / d positive logit = p - y, before eos weight and num_boxes.
    derivative = probability - int(label)
    return {
        **query,
        "positive_logit_derivative_before_weight_normalization": derivative,
        "gradient_descent_direction": (
            "increase" if derivative < 0 else "decrease" if derivative > 0 else "zero"
        ),
        "matched_mask_bce_dice": label,
    }


def analyze(report):
    if report["contract"] != "m95_failure_followup_v1" or report["admission"] is not False:
        raise ValueError("Wrong follow-up contract")
    rows, seen = [], set()
    for row in report["supervision_focus"]:
        index = row["manifest_index"]
        if index in seen:
            raise ValueError("Duplicate focus expression")
        seen.add(index)
        acceptable = [indicator_direction(q) for q in row["acceptable"]]
        if not acceptable or any(q["iou"] <= 0.5 for q in acceptable):
            raise ValueError("Invalid acceptable-query set")
        positive = indicator_direction(row["positive"])
        if not positive["native_positive"] or positive["iou"] > 0.5:
            raise ValueError("Positive selector must fail on focus rows")
        excluded = row["partition"] == "recoverable_positive_set_excludes_acceptable"
        within = row["partition"] == "recoverable_within_positive_score_failure"
        has_positive = any(q["native_positive"] for q in acceptable)
        if not (excluded or within) or has_positive != within:
            raise ValueError("Partition and observed labels disagree")
        rows.append({
            "manifest_index": index, "scene_id": row["scene_id"],
            "partition": row["partition"], "seed_control_missing": row["seed"] is None,
            "positive_selector": positive, "acceptable": acceptable,
            "acceptable_positive_queries": sum(q["native_positive"] for q in acceptable),
            "acceptable_negative_queries": sum(not q["native_positive"] for q in acceptable),
            "interpretation": (
                "No acceptable mask receives positive indicator or matched mask supervision."
                if excluded else
                "Failed and acceptable native-positive queries share the positive label; "
                "this label does not specify their within-positive ordering."
            ),
        })
    groups = {}
    for partition in sorted({r["partition"] for r in rows}):
        group = [r for r in rows if r["partition"] == partition]
        groups[partition] = {
            "expressions": len(group), "scenes": len({r["scene_id"] for r in group}),
            "missing_seed_controls": sum(r["seed_control_missing"] for r in group),
            "non_target_seeded_positive_selectors": sum(
                not r["positive_selector"]["target_seed"] for r in group),
            "acceptable_positive_queries": sum(r["acceptable_positive_queries"] for r in group),
            "acceptable_negative_queries": sum(r["acceptable_negative_queries"] for r in group),
            "positive_selector_identity": dict(Counter(
                r["positive_selector"]["identity"] for r in group)),
        }
    return {
        "rows": rows, "groups": groups,
        "expressions": len(rows), "scenes": len({r["scene_id"] for r in rows}),
        "analytic_contract": {
            "derivative": "d(loss_indi)/d(z_positive) = weight * (p - y) / num_boxes",
            "reported_value": "p - y only; excludes eos weighting and batch normalization",
            "fixed_labels": True, "native_backward_executed": False,
            "parameter_gradient_measured": False, "counterfactual_update_executed": False,
        },
        "limitations": [
            "Frozen TRAIN failure-selected expressions, not population or held-out efficacy.",
            "Queries within an expression are not independent samples.",
            "The indicator contribution is not the total multi-loss parameter gradient.",
            "Shared parameters and mask/semantic losses can change update direction.",
            "Zero at exact probability endpoints reflects saved precision, not proof of zero true gradient.",
            "Supervision mismatch does not establish that mask-aware relabeling improves training.",
            "No new supervision unit, native backward, resource gate or admission is established.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--followup", required=True)
    parser.add_argument("--loss", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name == "nt" or socket.gethostname() != "das" or os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("Native evidence analysis is restricted to server-6 CPU")
    for path, expected in ((args.followup, FOLLOWUP_SHA256), (args.loss, LOSS_SHA256)):
        if sha256(path) != expected:
            raise ValueError("Frozen source hash mismatch")
    result = analyze(json.loads(Path(args.followup).read_text(encoding="utf-8")))
    result.update({
        "contract": "m95_supervision_direction_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(), "cpu_only": True, "admission": False,
        "evidence": [{"path": str(p), "sha256": sha256(p)}
                     for p in (args.followup, args.loss, __file__)],
    })
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({k: result[k] for k in ("contract", "expressions", "scenes", "groups")}))


if __name__ == "__main__":
    main()
