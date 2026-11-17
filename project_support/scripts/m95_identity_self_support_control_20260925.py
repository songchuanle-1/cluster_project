"""Test whether M95 identity separability survives query-support exclusion.

The original identity diagnostic formed instance prototypes from all labeled
points, including points in the query mask being classified. This CPU-only
control rebuilds each prototype after subtracting the candidate query support.
It then reruns the score-matched identity-versus-score comparison on the same
frozen capture.
"""
import argparse
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_MANIFEST_SHA256,
    STAGES,
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
from m95_instance_identity_discriminability_20260925 import (
    BOOTSTRAP_SEED,
    EXPECTED_CAPTURE_SHA256,
    EXPECTED_ROWS,
    MIN_PROTOTYPE_POINTS,
    SCORE_MATCH_TOLERANCE,
    classify_pair,
    cosine,
    mean_selected,
    summarize_pairs,
    summarize_query_classification,
)


ANALYSIS_CONTRACT = "m95_identity_self_support_control_v1"


def add_vector(total, vector):
    if len(total) != len(vector):
        raise ValueError("Vector widths differ")
    for index, value in enumerate(vector):
        total[index] += float(value)


def subtract_vector(total, vector):
    if len(total) != len(vector):
        raise ValueError("Vector widths differ")
    return [left - float(right) for left, right in zip(total, vector)]


def prototype_stats(rows, labels, instance_ids):
    wanted = {int(instance_id) for instance_id in instance_ids}
    if not rows:
        return {}
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("Feature vectors differ")
    stats = {
        instance_id: {"count": 0, "sum": [0.0] * width}
        for instance_id in wanted
    }
    for row, label in zip(rows, labels):
        instance_id = int(label)
        if instance_id not in stats:
            continue
        stats[instance_id]["count"] += 1
        add_vector(stats[instance_id]["sum"], row)
    return stats


def support_stats(rows, labels, instance_ids, mask):
    wanted = {int(instance_id) for instance_id in instance_ids}
    stats = {
        instance_id: {"count": 0, "sum": [0.0] * len(rows[0])}
        for instance_id in wanted
    }
    for take, row, label in zip(mask, rows, labels):
        if not take:
            continue
        instance_id = int(label)
        if instance_id not in stats:
            continue
        stats[instance_id]["count"] += 1
        add_vector(stats[instance_id]["sum"], row)
    return stats


def nearest_prototype_similarity(
    query_prototype,
    stats,
    excluded=None,
    minimum_points=MIN_PROTOTYPE_POINTS,
):
    similarities = []
    for instance_id, total in stats.items():
        excluded_count = 0
        excluded_sum = None
        if excluded is not None:
            excluded_count = excluded[instance_id]["count"]
            excluded_sum = excluded[instance_id]["sum"]
        count = total["count"] - excluded_count
        if count < minimum_points:
            continue
        vector = total["sum"]
        if excluded_sum is not None:
            vector = subtract_vector(vector, excluded_sum)
        prototype = [value / count for value in vector]
        similarity = cosine(query_prototype, prototype)
        if similarity is not None:
            similarities.append(similarity)
    return max(similarities) if similarities else None


def identity_from_stats(
    query_prototype,
    target_stats,
    peer_stats,
    excluded=None,
):
    target_similarity = nearest_prototype_similarity(
        query_prototype, target_stats, excluded=excluded
    )
    peer_similarity = nearest_prototype_similarity(
        query_prototype, peer_stats, excluded=excluded
    )
    if target_similarity is None or peer_similarity is None:
        return None
    return {
        "target_similarity": target_similarity,
        "peer_similarity": peer_similarity,
        "margin": target_similarity - peer_similarity,
    }


def pair_with_identity(target_query, peer_query, identity_key):
    target_identity = target_query[identity_key]
    peer_identity = peer_query[identity_key]
    return {
        "manifest_index": target_query["manifest_index"],
        "scene_id": target_query["scene_id"],
        **classify_pair(
            {
                "margin": target_identity["margin"],
                "score": target_query["score"],
                "iou": target_query["iou"],
            },
            {
                "margin": peer_identity["margin"],
                "score": peer_query["score"],
                "iou": peer_query["iou"],
            },
        ),
    }


def coverage_summary(rows, attempted, skipped):
    summary = summarize_query_classification(rows)
    summary.update(
        {
            "attempted_queries": attempted,
            "skipped_missing_prototype": skipped,
            "coverage": len(rows) / attempted if attempted else None,
            "bootstrap_seed": BOOTSTRAP_SEED,
        }
    )
    return summary


def analyze(report, manifest, artifacts):
    report_rows = validate_capture(
        report, manifest, EXPECTED_CHECKPOINT_SHA256
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")

    query_rows = {
        stage: {"baseline": [], "leave_query_support_out": []}
        for stage in STAGES
    }
    pair_rows = {
        stage: {"baseline": [], "leave_query_support_out": []}
        for stage in STAGES
    }
    skipped = {stage: 0 for stage in STAGES}
    attempted = {stage: 0 for stage in STAGES}
    ineligible_expressions = 0

    for index in range(EXPECTED_ROWS):
        manifest_row = manifest[index]
        artifact = artifacts[index]
        labels = int_list(artifact["physical_instance_labels"], "instance labels")
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
            {int(value) for value in manifest_row["same_class_peer_object_ids"]}
        )
        if not target_ids or not peer_ids:
            ineligible_expressions += 1
            continue

        dominant = [dominant_overlap(mask, labels) for mask in masks]
        peer_set = set(peer_ids)
        candidate_queries = [
            query
            for query, dominant_id in enumerate(dominant)
            if dominant_id in set(target_ids) | peer_set
        ]
        per_stage_queries = {
            stage: {"baseline": [], "leave_query_support_out": []}
            for stage in STAGES
        }

        for stage in STAGES:
            feature_rows = [
                float_list(vector, stage + " feature")
                for vector in as_list(artifact["features"][stage])
            ]
            if len(feature_rows) != len(labels):
                raise ValueError("Feature support differs from labels")
            target_stats = prototype_stats(
                feature_rows, labels, target_ids
            )
            peer_stats = prototype_stats(feature_rows, labels, peer_ids)

            for query in candidate_queries:
                attempted[stage] += 1
                mask = masks[query]
                query_prototype = mean_selected(feature_rows, mask)
                if query_prototype is None:
                    skipped[stage] += 1
                    continue
                baseline = identity_from_stats(
                    query_prototype, target_stats, peer_stats
                )
                excluded = support_stats(
                    feature_rows,
                    labels,
                    target_ids + peer_ids,
                    mask,
                )
                leave_out = identity_from_stats(
                    query_prototype,
                    target_stats,
                    peer_stats,
                    excluded=excluded,
                )
                if baseline is None or leave_out is None:
                    skipped[stage] += 1
                    continue

                dominant_id = dominant[query]
                truth = "target" if dominant_id in target_ids else "peer"
                entry = {
                    "manifest_index": index,
                    "scene_id": str(manifest_row["scene_id"]),
                    "query": query,
                    "score": scores[query],
                    "iou": mask_iou(mask, target),
                    "native_positive": positive[query],
                    "truth": truth,
                    "prediction": (
                        "target" if baseline["margin"] > 0.0 else "peer"
                    ),
                    "prediction_leave_query_support_out": (
                        "target" if leave_out["margin"] > 0.0 else "peer"
                    ),
                    "baseline": baseline,
                    "leave_query_support_out": leave_out,
                }
                per_stage_queries[stage]["baseline"].append(entry)
                leave_out_entry = {
                    **entry,
                    "prediction": entry[
                        "prediction_leave_query_support_out"
                    ],
                }
                per_stage_queries[stage]["leave_query_support_out"].append(
                    leave_out_entry
                )
                query_rows[stage]["baseline"].append(entry)
                query_rows[stage]["leave_query_support_out"].append(
                    leave_out_entry
                )

                if truth != "peer":
                    continue
                for target_query in per_stage_queries[stage]["baseline"]:
                    if (
                        target_query["truth"] == "target"
                        and target_query["native_positive"]
                        and abs(target_query["score"] - entry["score"])
                        <= SCORE_MATCH_TOLERANCE
                    ):
                        pair_rows[stage]["baseline"].append(
                            pair_with_identity(
                                target_query, entry, "baseline"
                            )
                        )
                        pair_rows[stage]["leave_query_support_out"].append(
                            pair_with_identity(
                                target_query,
                                entry,
                                "leave_query_support_out",
                            )
                        )

    stages = {}
    for stage in STAGES:
        baseline_queries = query_rows[stage]["baseline"]
        leave_out_queries = query_rows[stage]["leave_query_support_out"]
        baseline_query_summary = coverage_summary(
            baseline_queries, attempted[stage], skipped[stage]
        )
        leave_out_query_summary = coverage_summary(
            leave_out_queries, attempted[stage], skipped[stage]
        )
        baseline_pair_summary = summarize_pairs(pair_rows[stage]["baseline"])
        leave_out_pair_summary = summarize_pairs(
            pair_rows[stage]["leave_query_support_out"]
        )
        stages[stage] = {
            "query_classification": {
                "baseline": baseline_query_summary,
                "leave_query_support_out": leave_out_query_summary,
                "balanced_accuracy_delta": (
                    leave_out_query_summary["balanced_accuracy"]
                    - baseline_query_summary["balanced_accuracy"]
                ),
                "scene_bootstrap_point_delta": (
                    leave_out_query_summary["scene_bootstrap_accuracy"][
                        "point_estimate"
                    ]
                    - baseline_query_summary["scene_bootstrap_accuracy"][
                        "point_estimate"
                    ]
                ),
            },
            "score_matched_query_pairs": {
                "baseline": baseline_pair_summary,
                "leave_query_support_out": leave_out_pair_summary,
                "identity_minus_score_delta": (
                    leave_out_pair_summary["identity_minus_score"]
                    - baseline_pair_summary["identity_minus_score"]
                ),
            },
        }

    return {
        "stages": stages,
        "counts": {
            "ineligible_expressions": ineligible_expressions,
            "attempted_queries_by_stage": attempted,
            "skipped_queries_by_stage": skipped,
        },
    }


def write_json(path, document):
    path = Path(path)
    if path.exists():
        raise ValueError("Output already exists: %s" % path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    capture_path = Path(args.capture).resolve()
    manifest_path = Path(args.manifest).resolve()
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
        capture_path, report, EXPECTED_MANIFEST_SHA256
    )
    result = analyze(report, manifest, artifacts)
    result.update(
        {
            "schema_version": 1,
            "contract": ANALYSIS_CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only query-support-exclusion control on the frozen "
                "256-expression M95 identity capture."
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
            "contracts": {
                "minimum_prototype_points": MIN_PROTOTYPE_POINTS,
                "score_match_tolerance": SCORE_MATCH_TOLERANCE,
                "control": (
                    "Subtract the candidate query's labeled point support "
                    "from every target and peer prototype before cosine "
                    "classification."
                ),
            },
            "candidate_handoff": {
                "referent-supervision-axis": (
                    "Does identity evidence survive removal of query support?"
                ),
                "referent-discrimination": (
                    "Does the identity-versus-score advantage survive on "
                    "the identical matched pairs?"
                ),
                "instance-identity-representation": (
                    "Is target-versus-peer separability driven by prototype "
                    "self-inclusion?"
                ),
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
    write_json(args.output, result)
    print(json.dumps(result["stages"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
