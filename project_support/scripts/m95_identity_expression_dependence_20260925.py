"""Audit expression-level dependence in the frozen M95 identity control.

The corrected support-excluded identity estimator contains many target/peer
pairs per manifest expression. This CPU-only sensitivity check keeps every
pair, but adds expression-cluster resampling, leave-one-expression-out
influence, and a deterministic one-pair-per-expression control.
"""
import argparse
import hashlib
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_MANIFEST_SHA256,
    as_list,
    bool_list,
    dominant_overlap,
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
    SCORE_MATCH_TOLERANCE,
    identity_from_stats_at_floor,
)
from m95_instance_identity_discriminability_20260925 import classify_pair


CONTRACT = "m95_identity_expression_dependence_v1"
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999
SUPPORT_FLOOR = 3
SUPPORT_FLOORS = (1, 2, 3)


def pair_digest(row):
    """Return an outcome-independent deterministic identity for a pair."""
    manifest_index, target_query, peer_query = row["pair_key"]
    payload = "m95-expression-dependence|%d|%d|%d" % (
        int(manifest_index),
        int(target_query),
        int(peer_query),
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def metric_summary(rows):
    if not rows:
        return {
            "expressions": 0,
            "scenes": 0,
            "pairs": 0,
            "identity_matches_iou": 0,
            "score_matches_iou": 0,
            "identity_only_matches_iou": 0,
            "score_only_matches_iou": 0,
            "identity_disagrees_with_score": 0,
            "identity_accuracy": None,
            "score_accuracy": None,
            "identity_minus_score": None,
        }
    identity = sum(bool(row["identity_matches_iou"]) for row in rows)
    score = sum(bool(row["score_matches_iou"]) for row in rows)
    return {
        "expressions": len({row["manifest_index"] for row in rows}),
        "scenes": len({row["scene_id"] for row in rows}),
        "pairs": len(rows),
        "identity_matches_iou": identity,
        "score_matches_iou": score,
        "identity_only_matches_iou": sum(
            bool(row["identity_matches_iou"]) and not bool(row["score_matches_iou"])
            for row in rows
        ),
        "score_only_matches_iou": sum(
            bool(row["score_matches_iou"]) and not bool(row["identity_matches_iou"])
            for row in rows
        ),
        "identity_disagrees_with_score": sum(
            bool(row["identity_disagrees_with_score"]) for row in rows
        ),
        "identity_accuracy": identity / len(rows),
        "score_accuracy": score / len(rows),
        "identity_minus_score": (identity - score) / len(rows),
    }


def group_by_expression(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[int(row["manifest_index"])].append(row)
    return dict(sorted(grouped.items()))


def group_by_target_query(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[
            (
                int(row["manifest_index"]),
                int(row["pair_key"][1]),
            )
        ].append(row)
    return dict(sorted(grouped.items()))


def expression_rows(rows):
    result = []
    for manifest_index, pairs in group_by_expression(rows).items():
        summary = metric_summary(pairs)
        result.append(
            {
                "manifest_index": manifest_index,
                "scene_id": str(pairs[0]["scene_id"]),
                "difference": summary["identity_minus_score"],
                "pairs": len(pairs),
                "summary": summary,
            }
        )
    return result


def expression_balanced_summary(rows):
    expressions = expression_rows(rows)
    if not expressions:
        return {
            "expressions": 0,
            "expression_balanced_identity_minus_score": None,
            "positive_expressions": 0,
            "zero_expressions": 0,
            "negative_expressions": 0,
            "minimum_expression_difference": None,
            "maximum_expression_difference": None,
        }
    values = [row["difference"] for row in expressions]
    return {
        "expressions": len(values),
        "expression_balanced_identity_minus_score": sum(values) / len(values),
        "positive_expressions": sum(value > 0.0 for value in values),
        "zero_expressions": sum(value == 0.0 for value in values),
        "negative_expressions": sum(value < 0.0 for value in values),
        "minimum_expression_difference": min(values),
        "maximum_expression_difference": max(values),
    }


def percentile(values, fraction):
    if not values:
        raise ValueError("Cannot take a percentile of an empty population")
    ordered = sorted(values)
    return ordered[int(fraction * (len(ordered) - 1))]


def expression_cluster_bootstrap(
    rows,
    draws=BOOTSTRAP_DRAWS,
    seed=BOOTSTRAP_SEED,
):
    grouped = group_by_expression(rows)
    if not grouped:
        return None
    expression_ids = sorted(grouped)
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choices(expression_ids, k=len(expression_ids))
        sampled_rows = [
            row
            for expression_id in selected
            for row in grouped[expression_id]
        ]
        samples.append(metric_summary(sampled_rows)["identity_minus_score"])
    return {
        "draws": draws,
        "seed": seed,
        "unit": "expression",
        "point_estimate": metric_summary(rows)["identity_minus_score"],
        "expression_count": len(expression_ids),
        "lo": percentile(samples, 0.025),
        "hi": percentile(samples, 0.975),
    }


def target_query_cluster_bootstrap(
    rows,
    draws=BOOTSTRAP_DRAWS,
    seed=BOOTSTRAP_SEED,
):
    grouped = group_by_target_query(rows)
    if not grouped:
        return None
    cluster_ids = sorted(grouped)
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choices(cluster_ids, k=len(cluster_ids))
        sampled_rows = [
            row
            for cluster_id in selected
            for row in grouped[cluster_id]
        ]
        samples.append(metric_summary(sampled_rows)["identity_minus_score"])
    return {
        "draws": draws,
        "seed": seed,
        "unit": "target_query",
        "point_estimate": metric_summary(rows)["identity_minus_score"],
        "target_query_count": len(cluster_ids),
        "lo": percentile(samples, 0.025),
        "hi": percentile(samples, 0.975),
    }


def leave_one_expression_out(rows):
    grouped = group_by_expression(rows)
    if len(grouped) < 2:
        return {
            "expressions": len(grouped),
            "minimum_identity_minus_score": None,
            "maximum_identity_minus_score": None,
            "all_positive": False,
            "most_influential_manifest_index": None,
        }
    estimates = {}
    for omitted in grouped:
        retained = [
            row
            for expression_id, pairs in grouped.items()
            if expression_id != omitted
            for row in pairs
        ]
        estimates[omitted] = metric_summary(retained)["identity_minus_score"]
    values = list(estimates.values())
    minimum = min(values)
    return {
        "expressions": len(grouped),
        "minimum_identity_minus_score": minimum,
        "maximum_identity_minus_score": max(values),
        "all_positive": all(value > 0.0 for value in values),
        "most_influential_manifest_index": min(
            estimates,
            key=lambda key: (estimates[key], key),
        ),
    }


def leave_one_target_query_out(rows):
    grouped = group_by_target_query(rows)
    if len(grouped) < 2:
        return {
            "target_queries": len(grouped),
            "minimum_identity_minus_score": None,
            "maximum_identity_minus_score": None,
            "all_positive": False,
            "most_influential_cluster": None,
        }
    estimates = {}
    for omitted in grouped:
        retained = [
            row
            for cluster_id, pairs in grouped.items()
            if cluster_id != omitted
            for row in pairs
        ]
        estimates[omitted] = metric_summary(retained)["identity_minus_score"]
    values = list(estimates.values())
    minimum = min(values)
    return {
        "target_queries": len(grouped),
        "minimum_identity_minus_score": minimum,
        "maximum_identity_minus_score": max(values),
        "all_positive": all(value > 0.0 for value in values),
        "most_influential_cluster": list(
            min(
                estimates,
                key=lambda key: (estimates[key], key),
            )
        ),
    }


def deterministic_one_pair_per_expression(rows):
    selected = []
    for pairs in group_by_expression(rows).values():
        selected.append(min(pairs, key=lambda row: (pair_digest(row), row["pair_key"])))
    return selected


def summarize_dependence(rows, draws=BOOTSTRAP_DRAWS):
    if not rows:
        raise ValueError("Expression-dependence audit has no score-matched pairs")
    keys = [
        (
            int(row["manifest_index"]),
            int(row["pair_key"][1]),
            int(row["pair_key"][2]),
        )
        for row in rows
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("Score-matched pairs contain duplicates")

    full = metric_summary(rows)
    one_per_expression = deterministic_one_pair_per_expression(rows)
    return {
        "support_floor": SUPPORT_FLOOR,
        "score_match_tolerance": SCORE_MATCH_TOLERANCE,
        "full_pairs": full,
        "expression_balanced": expression_balanced_summary(rows),
        "expression_cluster_bootstrap": expression_cluster_bootstrap(
            rows,
            draws=draws,
        ),
        "target_query_cluster_bootstrap": target_query_cluster_bootstrap(
            rows,
            draws=draws,
        ),
        "leave_one_expression_out": leave_one_expression_out(rows),
        "leave_one_target_query_out": leave_one_target_query_out(rows),
        "deterministic_one_pair_per_expression": {
            "selection_rule": (
                "minimum SHA256 of contract, manifest index, target query and "
                "peer query; outcome fields are excluded"
            ),
            "summary": metric_summary(one_per_expression),
            "selected": [
                {
                    "manifest_index": int(row["manifest_index"]),
                    "scene_id": str(row["scene_id"]),
                    "pair_key": row["pair_key"],
                    "identity_matches_iou": bool(row["identity_matches_iou"]),
                    "score_matches_iou": bool(row["score_matches_iou"]),
                }
                for row in sorted(
                    one_per_expression,
                    key=lambda row: int(row["manifest_index"]),
                )
            ],
        },
    }


def pair_keys(rows):
    return {
        (
            int(row["manifest_index"]),
            int(row["pair_key"][1]),
            int(row["pair_key"][2]),
        )
        for row in rows
    }


def make_pair_rows(manifest_index, scene_id, query_rows):
    pair_rows = []
    for target_query in query_rows:
        if (
            target_query["truth"] != "target"
            or not target_query["native_positive"]
        ):
            continue
        for peer_query in query_rows:
            if (
                peer_query["truth"] != "peer"
                or abs(target_query["score"] - peer_query["score"])
                > SCORE_MATCH_TOLERANCE
            ):
                continue
            pair_rows.append(
                {
                    "manifest_index": manifest_index,
                    "scene_id": scene_id,
                    "pair_key": [
                        manifest_index,
                        target_query["query"],
                        peer_query["query"],
                    ],
                    **classify_pair(
                        {
                            "margin": target_query["identity"]["margin"],
                            "score": target_query["score"],
                            "iou": target_query["iou"],
                        },
                        {
                            "margin": peer_query["identity"]["margin"],
                            "score": peer_query["score"],
                            "iou": peer_query["iou"],
                        },
                    ),
                }
            )
    return pair_rows


def extract_final_pair_rows(report, manifest, artifacts):
    report_rows = validate_capture(
        report,
        manifest,
        EXPECTED_CHECKPOINT_SHA256,
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")

    floor_pair_rows = {floor: [] for floor in SUPPORT_FLOORS}
    floor_query_rows = {floor: [] for floor in SUPPORT_FLOORS}
    for index in range(256):
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
        positive = bool_list(artifact["native_positive"], "native positives")
        if len(labels) != len(target):
            raise ValueError("Target and label axes differ")
        if any(len(mask) != len(labels) for mask in masks):
            raise ValueError("Query mask support differs from labels")
        if not (len(masks) == len(scores) == len(positive)):
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
        dominant = [dominant_overlap(mask, labels) for mask in masks]
        target_id_set = set(target_ids)
        peer_id_set = set(peer_ids)
        candidate_queries = [
            query
            for query, dominant_id in enumerate(dominant)
            if dominant_id in target_id_set | peer_id_set
        ]

        query_rows = {floor: [] for floor in SUPPORT_FLOORS}
        for query in candidate_queries:
            mask = masks[query]
            query_prototype = None
            selected = [
                vector
                for vector, take in zip(features, mask)
                if take
            ]
            if selected:
                width = len(selected[0])
                if width and all(len(vector) == width for vector in selected):
                    query_prototype = [
                        sum(vector[column] for vector in selected) / len(selected)
                        for column in range(width)
                    ]
            if query_prototype is None:
                continue
            if (
                identity_from_stats(
                    query_prototype,
                    target_stats,
                    peer_stats,
                )
                is None
            ):
                continue
            excluded = support_stats(
                features,
                labels,
                target_ids + peer_ids,
                mask,
            )
            dominant_id = dominant[query]
            for floor in SUPPORT_FLOORS:
                identity = identity_from_stats_at_floor(
                    query_prototype,
                    target_stats,
                    peer_stats,
                    excluded,
                    floor,
                )
                if identity is None:
                    continue
                query_rows[floor].append(
                    {
                        "manifest_index": index,
                        "scene_id": str(manifest_row["scene_id"]),
                        "query": query,
                        "score": scores[query],
                        "iou": mask_iou(mask, target),
                        "native_positive": positive[query],
                        "truth": (
                            "target"
                            if dominant_id in target_id_set
                            else "peer"
                        ),
                        "identity": identity,
                    }
                )

        for floor in SUPPORT_FLOORS:
            floor_query_rows[floor].extend(query_rows[floor])
            floor_pair_rows[floor].extend(
                make_pair_rows(
                    index,
                    str(manifest_row["scene_id"]),
                    query_rows[floor],
                )
            )

    for index in range(256):
        if int(report_rows[index]["manifest_index"]) != index:
            raise ValueError("Validated capture row ordering differs")
    common_keys = set.intersection(
        *[pair_keys(floor_pair_rows[floor]) for floor in SUPPORT_FLOORS]
    )
    common_query_keys = set.intersection(
        *[
            {
                (int(row["manifest_index"]), int(row["query"]))
                for row in floor_query_rows[floor]
            }
            for floor in SUPPORT_FLOORS
        ]
    )
    common_floor3 = [
        row
        for row in floor_pair_rows[SUPPORT_FLOOR]
        if (
            int(row["manifest_index"]),
            int(row["pair_key"][1]),
            int(row["pair_key"][2]),
        )
        in common_keys
    ]
    return {
        "floor3_all": floor_pair_rows[SUPPORT_FLOOR],
        "common_support_floors": common_floor3,
        "common_support_queries": len(common_query_keys),
    }


def analyze(report, manifest, artifacts, draws=BOOTSTRAP_DRAWS):
    extracted = extract_final_pair_rows(report, manifest, artifacts)
    result = summarize_dependence(
        extracted["common_support_floors"],
        draws=draws,
    )
    result["common_support_queries"] = extracted["common_support_queries"]
    result["floor3_all_pairs_sensitivity"] = summarize_dependence(
        extracted["floor3_all"],
        draws=draws,
    )
    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.draws <= 0:
        raise ValueError("Bootstrap draws must be positive")
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
    result = analyze(report, manifest, artifacts, draws=args.draws)
    result.update(
        {
            "schema_version": 1,
            "contract": CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only expression-dependence sensitivity audit of the "
                "frozen 256-expression M95 final-stage identity control."
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
        json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(
        json.dumps(
            {
                "full_pairs": result["full_pairs"],
                "expression_balanced": result["expression_balanced"],
                "expression_cluster_bootstrap": result[
                    "expression_cluster_bootstrap"
                ],
                "target_query_cluster_bootstrap": result[
                    "target_query_cluster_bootstrap"
                ],
                "leave_one_expression_out": result[
                    "leave_one_expression_out"
                ],
                "leave_one_target_query_out": result[
                    "leave_one_target_query_out"
                ],
                "deterministic_one_pair_per_expression": result[
                    "deterministic_one_pair_per_expression"
                ]["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
