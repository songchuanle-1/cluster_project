"""Measure whether identity disagreements select better queries than scores.

This CPU-only audit uses the frozen 256-expression M95 final-stage capture.
Its estimand is restricted to non-tied score-matched pairs where identity and
score select different queries. It reports the paired IoU difference for the
identity-selected query minus the score-selected query.
"""
import argparse
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


CONTRACT = "m95_identity_actionability_v1"
SUPPORT_FLOOR = 3
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999
EXPECTED_ROWS = 256


def percentile(values, fraction):
    if not values:
        raise ValueError("Cannot take a percentile of an empty population")
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def action_pair(target_query, peer_query):
    """Build one predeclared pair-level actionability record."""
    identity_tie = target_query["identity"]["margin"] == (
        peer_query["identity"]["margin"]
    )
    score_tie = target_query["score"] == peer_query["score"]
    identity_target = target_query["identity"]["margin"] > (
        peer_query["identity"]["margin"]
    )
    score_target = target_query["score"] > peer_query["score"]
    iou_tie = target_query["iou"] == peer_query["iou"]
    identity_correct = identity_target == (
        target_query["iou"] > peer_query["iou"]
    )
    score_correct = score_target == (
        target_query["iou"] > peer_query["iou"]
    )
    row = {
        "manifest_index": int(target_query["manifest_index"]),
        "scene_id": str(target_query["scene_id"]),
        "target_query": int(target_query["query"]),
        "peer_query": int(peer_query["query"]),
        "target_iou": float(target_query["iou"]),
        "peer_iou": float(peer_query["iou"]),
        "target_score": float(target_query["score"]),
        "peer_score": float(peer_query["score"]),
        "target_identity_margin": float(target_query["identity"]["margin"]),
        "peer_identity_margin": float(peer_query["identity"]["margin"]),
        "identity_tie": identity_tie,
        "score_tie": score_tie,
        "iou_tie": iou_tie,
        "identity_target": identity_target,
        "score_target": score_target,
        "identity_correct": identity_correct and not iou_tie,
        "score_correct": score_correct and not iou_tie,
        "identity_disagrees_with_score": (
            not identity_tie and not score_tie
            and identity_target != score_target
        ),
    }
    if row["identity_disagrees_with_score"]:
        row["identity_choice_iou"] = (
            row["target_iou"] if identity_target else row["peer_iou"]
        )
        row["score_choice_iou"] = (
            row["peer_iou"] if identity_target else row["target_iou"]
        )
        row["identity_minus_score_iou"] = (
            row["identity_choice_iou"] - row["score_choice_iou"]
        )
        row["identity_margin_gap"] = (
            abs(row["target_identity_margin"] - row["peer_identity_margin"])
        )
    return row


def make_actionability_rows(manifest_index, scene_id, query_rows):
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
                action_pair(
                    {
                        **target_query,
                        "manifest_index": manifest_index,
                        "scene_id": scene_id,
                    },
                    {
                        **peer_query,
                        "manifest_index": manifest_index,
                        "scene_id": scene_id,
                    },
                )
            )
    return pair_rows


def actionability_rows(rows):
    selected = [
        row
        for row in rows
        if row["identity_disagrees_with_score"]
    ]
    keys = [
        (
            int(row["manifest_index"]),
            int(row["target_query"]),
            int(row["peer_query"]),
        )
        for row in selected
    ]
    if len(keys) != len(set(keys)):
        raise ValueError("Actionability pairs contain duplicates")
    return selected


def metric_summary(rows, all_score_matched_pairs):
    selected = actionability_rows(rows)
    if not selected:
        return {
            "score_matched_pairs": len(all_score_matched_pairs),
            "non_tied_disagreement_pairs": 0,
            "disagreement_fraction": None,
            "mean_identity_minus_score_iou": None,
            "median_identity_minus_score_iou": None,
            "mean_delta_over_all_score_matched_pairs": None,
            "positive_deltas": 0,
            "zero_deltas": 0,
            "negative_deltas": 0,
            "net_iou_gain": None,
            "gross_iou_gain": None,
            "gross_iou_loss": None,
        }
    deltas = [float(row["identity_minus_score_iou"]) for row in selected]
    positive = [value for value in deltas if value > 0.0]
    negative = [value for value in deltas if value < 0.0]
    return {
        "score_matched_pairs": len(all_score_matched_pairs),
        "non_tied_disagreement_pairs": len(selected),
        "disagreement_fraction": (
            len(selected) / len(all_score_matched_pairs)
            if all_score_matched_pairs else None
        ),
        "mean_identity_minus_score_iou": sum(deltas) / len(deltas),
        "median_identity_minus_score_iou": percentile(deltas, 0.5),
        "mean_delta_over_all_score_matched_pairs": (
            sum(deltas) / len(all_score_matched_pairs)
            if all_score_matched_pairs else None
        ),
        "positive_deltas": len(positive),
        "zero_deltas": sum(value == 0.0 for value in deltas),
        "negative_deltas": len(negative),
        "net_iou_gain": sum(deltas),
        "gross_iou_gain": sum(positive),
        "gross_iou_loss": sum(negative),
    }


def cluster_bootstrap(rows, group_key, unit, draws, seed):
    selected = actionability_rows(rows)
    grouped = defaultdict(list)
    for row in selected:
        grouped[group_key(row)].append(float(row["identity_minus_score_iou"]))
    if not grouped:
        return None
    cluster_ids = sorted(grouped)
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        sampled = rng.choices(cluster_ids, k=len(cluster_ids))
        values = [
            value
            for cluster_id in sampled
            for value in grouped[cluster_id]
        ]
        samples.append(sum(values) / len(values))
    return {
        "draws": draws,
        "seed": seed,
        "unit": unit,
        "cluster_count": len(cluster_ids),
        "point_estimate": sum(
            value for values in grouped.values() for value in values
        ) / sum(len(values) for values in grouped.values()),
        "lo": percentile(samples, 0.025),
        "hi": percentile(samples, 0.975),
    }


def leave_one_cluster_out(rows, group_key, unit):
    selected = actionability_rows(rows)
    grouped = defaultdict(list)
    for row in selected:
        grouped[group_key(row)].append(float(row["identity_minus_score_iou"]))
    if len(grouped) < 2:
        return {
            "unit": unit,
            "cluster_count": len(grouped),
            "minimum_mean_delta": None,
            "maximum_mean_delta": None,
            "all_positive": False,
        }
    estimates = {}
    for omitted in grouped:
        values = [
            value
            for cluster_id, cluster_values in grouped.items()
            if cluster_id != omitted
            for value in cluster_values
        ]
        estimates[omitted] = sum(values) / len(values)
    values = list(estimates.values())
    return {
        "unit": unit,
        "cluster_count": len(grouped),
        "minimum_mean_delta": min(values),
        "maximum_mean_delta": max(values),
        "all_positive": all(value > 0.0 for value in values),
        "most_influential_cluster": (
            list(influential)
            if isinstance(influential := min(
                estimates,
                key=lambda key: (estimates[key], key),
            ), tuple)
            else [influential]
        ),
    }


def margin_gap_strata(rows):
    selected = actionability_rows(rows)
    if not selected:
        return []
    boundaries = [
        percentile(
            [row["identity_margin_gap"] for row in selected],
            fraction,
        )
        for fraction in (0.25, 0.5, 0.75)
    ]
    result = []
    for index in range(4):
        lower = float("-inf") if index == 0 else boundaries[index - 1]
        upper = float("inf") if index == 3 else boundaries[index]
        group = [
            row
            for row in selected
            if (
                (index == 0 or row["identity_margin_gap"] > lower)
                and (index == 3 or row["identity_margin_gap"] <= upper)
            )
        ]
        deltas = [row["identity_minus_score_iou"] for row in group]
        result.append(
            {
                "stratum": index + 1,
                "lower_margin_gap_exclusive": (
                    None if index == 0 else lower
                ),
                "upper_margin_gap_inclusive": (
                    None if index == 3 else upper
                ),
                "pairs": len(group),
                "mean_identity_minus_score_iou": (
                    sum(deltas) / len(deltas) if deltas else None
                ),
                "positive_deltas": sum(value > 0.0 for value in deltas),
                "negative_deltas": sum(value < 0.0 for value in deltas),
            }
        )
    return result


def summarize_actionability(rows, draws=BOOTSTRAP_DRAWS):
    selected = actionability_rows(rows)
    result = metric_summary(rows, rows)
    result.update(
        {
            "score_match_tolerance": SCORE_MATCH_TOLERANCE,
            "support_floor": SUPPORT_FLOOR,
            "scene_cluster_bootstrap": cluster_bootstrap(
                rows,
                lambda row: row["scene_id"],
                "scene",
                draws,
                BOOTSTRAP_SEED,
            ),
            "target_query_cluster_bootstrap": cluster_bootstrap(
                rows,
                lambda row: (
                    int(row["manifest_index"]),
                    int(row["target_query"]),
                ),
                "target_query",
                draws,
                BOOTSTRAP_SEED,
            ),
            "expression_cluster_bootstrap": cluster_bootstrap(
                rows,
                lambda row: int(row["manifest_index"]),
                "expression",
                draws,
                BOOTSTRAP_SEED,
            ),
            "leave_one_scene_out": leave_one_cluster_out(
                rows,
                lambda row: row["scene_id"],
                "scene",
            ),
            "leave_one_target_query_out": leave_one_cluster_out(
                rows,
                lambda row: (
                    int(row["manifest_index"]),
                    int(row["target_query"]),
                ),
                "target_query",
            ),
            "leave_one_expression_out": leave_one_cluster_out(
                rows,
                lambda row: int(row["manifest_index"]),
                "expression",
            ),
            "identity_margin_gap_strata": margin_gap_strata(rows),
            "selected_pairs": [
                {
                    "manifest_index": int(row["manifest_index"]),
                    "scene_id": row["scene_id"],
                    "target_query": int(row["target_query"]),
                    "peer_query": int(row["peer_query"]),
                    "identity_minus_score_iou": row[
                        "identity_minus_score_iou"
                    ],
                    "identity_margin_gap": row["identity_margin_gap"],
                }
                for row in selected
            ],
        }
    )
    return result


def extract_final_pair_rows(report, manifest, artifacts):
    report_rows = validate_capture(
        report,
        manifest,
        EXPECTED_CHECKPOINT_SHA256,
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")

    pair_rows = []
    attempted_queries = 0
    skipped_missing_prototype = 0
    expression_count = 0
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

        query_rows = []
        for query in candidate_queries:
            attempted_queries += 1
            mask = masks[query]
            selected = [
                vector
                for vector, take in zip(features, mask)
                if take
            ]
            if not selected:
                skipped_missing_prototype += 1
                continue
            width = len(selected[0])
            if not width or any(len(vector) != width for vector in selected):
                skipped_missing_prototype += 1
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
                skipped_missing_prototype += 1
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
                skipped_missing_prototype += 1
                continue
            dominant_id = dominant[query]
            query_rows.append(
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
        if query_rows:
            expression_count += 1
        pair_rows.extend(
            make_actionability_rows(
                index,
                str(manifest_row["scene_id"]),
                query_rows,
            )
        )

    for index in range(EXPECTED_ROWS):
        if int(report_rows[index]["manifest_index"]) != index:
            raise ValueError("Validated capture row ordering differs")
    return {
        "pair_rows": pair_rows,
        "eligible_expressions": expression_count,
        "attempted_queries": attempted_queries,
        "skipped_missing_prototype": skipped_missing_prototype,
    }


def analyze(report, manifest, artifacts, draws=BOOTSTRAP_DRAWS):
    extracted = extract_final_pair_rows(report, manifest, artifacts)
    result = summarize_actionability(extracted["pair_rows"], draws=draws)
    result["eligible_expressions"] = extracted["eligible_expressions"]
    result["attempted_queries"] = extracted["attempted_queries"]
    result["skipped_missing_prototype"] = extracted[
        "skipped_missing_prototype"
    ]
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
                "CPU-only actionability audit of non-tied score "
                "disagreements on the frozen 256-expression M95 capture."
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
        json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True)
        + "\n",
        encoding="ascii",
    )
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"selected_pairs"}
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
