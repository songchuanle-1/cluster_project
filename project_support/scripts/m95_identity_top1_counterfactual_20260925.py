"""Evaluate identity margins at the expression-level top-1 decision.

This CPU-only control uses the frozen 256-expression M95 capture. It compares
native scores and support-excluded identity margins on the same query universe
and reports a within-expression permutation null. It does not train, admit, or
evaluate a deployable selector.
"""
import argparse
import json
import math
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_MANIFEST_SHA256,
    as_list,
    bool_list,
    file_sha256,
    float_list,
    int_list,
    load_artifacts,
    load_json,
    mask_iou,
    validate_capture,
    validate_manifest_hash,
)
from m95_identity_self_support_control_20260925 import (
    identity_from_stats,
    prototype_stats,
    support_stats,
)
from m95_identity_support_sensitivity_20260925 import (
    EXPECTED_CAPTURE_SHA256,
    identity_from_stats_at_floor,
)


CONTRACT = "m95_identity_top1_counterfactual_v1"
EXPECTED_ROWS = 256
SUPPORT_FLOOR = 3
BOOTSTRAP_DRAWS = 10000
PERMUTATION_DRAWS = 10000
BOOTSTRAP_SEED = 1999
PERMUTATION_SEED = 20260925
SUCCESS_IOU = 0.5


def percentile(values, fraction):
    if not values:
        raise ValueError("Cannot take a percentile of an empty population")
    ordered = sorted(float(value) for value in values)
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def top_query(rows, value_key):
    if not rows:
        raise ValueError("Cannot select from an empty query universe")
    return max(
        rows,
        key=lambda row: (float(row[value_key]), -int(row["query"])),
    )


def expression_result(manifest_index, scene_id, query_rows):
    if not query_rows:
        raise ValueError("Expression has no identity-eligible queries")
    score_choice = top_query(query_rows, "score")
    identity_choice = top_query(query_rows, "identity_margin")
    oracle_choice = top_query(query_rows, "iou")
    return {
        "manifest_index": int(manifest_index),
        "scene_id": str(scene_id),
        "eligible_queries": len(query_rows),
        "score_query": int(score_choice["query"]),
        "identity_query": int(identity_choice["query"]),
        "oracle_query": int(oracle_choice["query"]),
        "score_iou": float(score_choice["iou"]),
        "identity_iou": float(identity_choice["iou"]),
        "oracle_iou": float(oracle_choice["iou"]),
        "identity_minus_score_iou": (
            float(identity_choice["iou"]) - float(score_choice["iou"])
        ),
        "oracle_minus_score_iou": (
            float(oracle_choice["iou"]) - float(score_choice["iou"])
        ),
        "same_query": int(score_choice["query"]) == int(identity_choice["query"]),
        "score_success": float(score_choice["iou"]) > SUCCESS_IOU,
        "identity_success": float(identity_choice["iou"]) > SUCCESS_IOU,
        "identity_margin": float(identity_choice["identity_margin"]),
        "score": float(score_choice["score"]),
    }


def mean(values):
    values = list(values)
    return sum(float(value) for value in values) / len(values) if values else None


def scene_balanced_mean(rows, value_key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["scene_id"])].append(float(row[value_key]))
    scene_means = [mean(values) for values in grouped.values()]
    return {
        "expressions": len(rows),
        "scenes": len(grouped),
        "pooled_mean": mean(row[value_key] for row in rows),
        "scene_balanced_mean": mean(scene_means),
    }


def scene_bootstrap(rows, value_key, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["scene_id"])].append(float(row[value_key]))
    if not grouped:
        raise ValueError("Cannot bootstrap an empty expression population")
    scene_means = [mean(values) for values in grouped.values()]
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        sampled = rng.choices(scene_means, k=len(scene_means))
        samples.append(sum(sampled) / len(sampled))
    point = sum(scene_means) / len(scene_means)
    return {
        "draws": draws,
        "seed": seed,
        "unit": "scene",
        "scene_count": len(scene_means),
        "point_estimate": point,
        "lo": percentile(samples, 0.025),
        "hi": percentile(samples, 0.975),
    }


def leave_one_scene_out(rows, value_key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["scene_id"])].append(float(row[value_key]))
    if len(grouped) < 2:
        return {
            "scene_count": len(grouped),
            "minimum_mean": None,
            "maximum_mean": None,
            "all_positive": False,
        }
    estimates = {}
    for omitted in grouped:
        values = [
            value
            for scene_id, scene_values in grouped.items()
            if scene_id != omitted
            for value in scene_values
        ]
        estimates[omitted] = mean(values)
    return {
        "scene_count": len(grouped),
        "minimum_mean": min(estimates.values()),
        "maximum_mean": max(estimates.values()),
        "all_positive": all(value > 0.0 for value in estimates.values()),
        "most_influential_scene": min(
            estimates,
            key=lambda scene_id: (estimates[scene_id], scene_id),
        ),
    }


def success_summary(rows, key):
    successes = [bool(row[key]) for row in rows]
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row["scene_id"])].append(float(bool(row[key])))
    return {
        "available": len(successes),
        "success_rate": mean(successes),
        "scene_balanced_success": mean(mean(values) for values in grouped.values()),
        "scenes": len(grouped),
    }


def summarize(rows):
    if not rows:
        raise ValueError("Top-1 counterfactual has no eligible expressions")
    indices = [int(row["manifest_index"]) for row in rows]
    if len(indices) != len(set(indices)):
        raise ValueError("Top-1 counterfactual contains duplicate expressions")
    delta = {
        "identity_minus_score": scene_balanced_mean(
            rows, "identity_minus_score_iou"
        ),
        "oracle_minus_score": scene_balanced_mean(
            rows, "oracle_minus_score_iou"
        ),
    }
    delta["identity_minus_score"]["scene_bootstrap_95ci"] = scene_bootstrap(
        rows, "identity_minus_score_iou"
    )
    delta["oracle_minus_score"]["scene_bootstrap_95ci"] = scene_bootstrap(
        rows, "oracle_minus_score_iou"
    )
    values = [float(row["identity_minus_score_iou"]) for row in rows]
    return {
        "expressions": len(rows),
        "scenes": len({str(row["scene_id"]) for row in rows}),
        "same_query": sum(bool(row["same_query"]) for row in rows),
        "identity_changed_query": sum(not bool(row["same_query"]) for row in rows),
        "positive_deltas": sum(value > 0.0 for value in values),
        "zero_deltas": sum(value == 0.0 for value in values),
        "negative_deltas": sum(value < 0.0 for value in values),
        "paired_effects": delta,
        "leave_one_scene_out_identity_minus_score": leave_one_scene_out(
            rows, "identity_minus_score_iou"
        ),
        "success": {
            "score": success_summary(rows, "score_success"),
            "identity": success_summary(rows, "identity_success"),
        },
    }


def permutation_null(expression_rows, draws=PERMUTATION_DRAWS, seed=PERMUTATION_SEED):
    if not expression_rows:
        raise ValueError("Permutation control requires expressions")
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        deltas = []
        for row in expression_rows:
            query_rows = row["query_rows"]
            margins = [float(query["identity_margin"]) for query in query_rows]
            shuffled = list(margins)
            rng.shuffle(shuffled)
            identity_iou = max(
                zip(query_rows, shuffled),
                key=lambda item: (item[1], -int(item[0]["query"])),
            )[0]["iou"]
            deltas.append(identity_iou - float(row["score_iou"]))
        samples.append(mean(deltas))
    observed = mean(row["identity_minus_score_iou"] for row in expression_rows)
    center = mean(samples)
    extreme = sum(
        abs(value - center) >= abs(observed - center)
        for value in samples
    )
    return {
        "draws": draws,
        "seed": seed,
        "unit": "within_expression_identity_margin_permutation",
        "observed_expression_balanced_mean": observed,
        "null_mean": center,
        "null_95_interval": [
            percentile(samples, 0.025),
            percentile(samples, 0.975),
        ],
        "two_sided_empirical_p": (extreme + 1) / (draws + 1),
    }


def expression_query_rows(report, manifest, artifacts):
    report_rows = validate_capture(
        report,
        manifest,
        EXPECTED_CHECKPOINT_SHA256,
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")
    expressions = []
    attempted_queries = 0
    skipped_missing_identity = 0
    for index in range(EXPECTED_ROWS):
        manifest_row = manifest[index]
        artifact = artifacts[index]
        labels = int_list(
            artifact["physical_instance_labels"],
            "physical instance labels",
        )
        target = bool_list(artifact["target_union"], "target union")
        masks = [
            bool_list(mask, "query mask")
            for mask in as_list(artifact["query_masks"])
        ]
        scores = float_list(artifact["query_scores"], "query scores")
        if len(labels) != len(target):
            raise ValueError("Target and label axes differ")
        if any(len(mask) != len(labels) for mask in masks):
            raise ValueError("Query mask support differs from labels")
        if len(masks) != len(scores):
            raise ValueError("Query axes differ")
        target_ids = sorted(
            {
                int(label)
                for take, label in zip(target, labels)
                if take and label >= 0
            }
        )
        peer_ids = sorted(
            {
                int(value)
                for value in manifest_row["same_class_peer_object_ids"]
            }
        )
        if not target_ids or not peer_ids:
            continue
        features = [
            float_list(vector, "final feature")
            for vector in as_list(artifact["features"]["final"])
        ]
        if len(features) != len(labels):
            raise ValueError("Final feature support differs from labels")
        target_stats = prototype_stats(features, labels, target_ids)
        peer_stats = prototype_stats(features, labels, peer_ids)

        query_rows = []
        for query, mask in enumerate(masks):
            attempted_queries += 1
            selected = [
                vector
                for vector, take in zip(features, mask)
                if take
            ]
            if not selected:
                skipped_missing_identity += 1
                continue
            width = len(selected[0])
            if not width or any(len(vector) != width for vector in selected):
                skipped_missing_identity += 1
                continue
            query_prototype = [
                sum(vector[column] for vector in selected) / len(selected)
                for column in range(width)
            ]
            if identity_from_stats(
                query_prototype,
                target_stats,
                peer_stats,
            ) is None:
                skipped_missing_identity += 1
                continue
            excluded = support_stats(
                features,
                labels,
                target_ids + peer_ids,
                mask,
            )
            identity = identity_from_stats_at_floor(
                query_prototype,
                target_stats,
                peer_stats,
                excluded,
                SUPPORT_FLOOR,
            )
            if identity is None:
                skipped_missing_identity += 1
                continue
            query_rows.append(
                {
                    "query": query,
                    "score": scores[query],
                    "iou": mask_iou(mask, target),
                    "identity_margin": float(identity["margin"]),
                }
            )

        if query_rows:
            result = expression_result(
                index,
                str(manifest_row["scene_id"]),
                query_rows,
            )
            result["query_rows"] = query_rows
            result["native_selected_query"] = int(
                report_rows[index]["selected_query"]
            )
            result["native_selected_iou"] = float(
                report_rows[index]["ious"][result["native_selected_query"]]
            )
            expressions.append(result)

    for index in range(EXPECTED_ROWS):
        if int(report_rows[index]["manifest_index"]) != index:
            raise ValueError("Validated capture row ordering differs")
    return {
        "expressions": expressions,
        "attempted_queries": attempted_queries,
        "skipped_missing_identity": skipped_missing_identity,
    }


def analyze(report, manifest, artifacts, draws=BOOTSTRAP_DRAWS,
            permutation_draws=PERMUTATION_DRAWS):
    extracted = expression_query_rows(report, manifest, artifacts)
    rows = extracted["expressions"]
    summary = summarize(rows)
    summary["permutation_null"] = permutation_null(
        rows,
        draws=permutation_draws,
    )
    return {
        "summary": summary,
        "rows": [
            {
                key: value
                for key, value in row.items()
                if key != "query_rows"
            }
            for row in rows
        ],
        "counts": {
            "attempted_queries": extracted["attempted_queries"],
            "identity_eligible_queries": sum(
                int(row["eligible_queries"]) for row in rows
            ),
            "skipped_missing_identity": extracted[
                "skipped_missing_identity"
            ],
        },
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument(
        "--permutation-draws",
        type=int,
        default=PERMUTATION_DRAWS,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.draws <= 0 or args.permutation_draws <= 0:
        raise ValueError("Draw counts must be positive")
    capture_path = Path(args.capture).resolve()
    manifest_path = Path(args.manifest).resolve()
    output_path = Path(args.output).resolve()
    if output_path.exists():
        raise ValueError("Refusing to overwrite an analysis output")
    capture_sha256 = file_sha256(capture_path)
    if capture_sha256 != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture hash differs from the frozen identity capture")
    manifest_sha256 = file_sha256(manifest_path)
    manifest = validate_manifest_hash(
        load_json(manifest_path),
        manifest_sha256,
        EXPECTED_MANIFEST_SHA256,
    )
    report = load_json(capture_path)
    if report.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint differs from M95")
    artifacts = load_artifacts(
        capture_path,
        report,
        EXPECTED_MANIFEST_SHA256,
    )
    result = analyze(
        report,
        manifest,
        artifacts,
        draws=args.draws,
        permutation_draws=args.permutation_draws,
    )
    result.update(
        {
            "schema_version": 1,
            "contract": CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only expression-level top-1 counterfactual on the "
                "frozen 256-expression M95 capture."
            ),
            "source_capture": {
                "path": str(capture_path),
                "sha256": capture_sha256,
                "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
                "producer_sha256": report.get("producer_sha256"),
            },
            "manifest": {
                "path": str(manifest_path),
                "sha256": manifest_sha256,
                "rows": len(manifest),
            },
            "pairing_contract": (
                "Native score and support-excluded identity select from the "
                "same identity-eligible query universe within each expression."
            ),
            "admission": False,
            "native_backward_measured": False,
            "resources_measured": False,
            "not_evidence_of": [
                "admission",
                "native backward",
                "resource gate",
                "deployable efficacy",
                "population effect",
                "novelty",
                "whole-mechanism benefit",
            ],
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True)
        + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
