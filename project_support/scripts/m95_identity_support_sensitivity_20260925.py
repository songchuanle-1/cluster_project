"""Test sensitivity of query-support-excluded identity controls.

The primary self-support control requires at least three prototype points after
excluding the candidate query support. This CPU-only audit reports the fixed
support floors 1, 2, and 3 without selecting a floor, then compares each floor
on the common set of queries and score-matched pairs available to every floor.
"""
import argparse
import json
from collections import Counter, defaultdict
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
from m95_identity_self_support_control_20260925 import (
    identity_from_stats,
    prototype_stats,
    support_stats,
)
from m95_instance_identity_discriminability_20260925 import (
    BOOTSTRAP_SEED,
    EXPECTED_CAPTURE_SHA256,
    EXPECTED_ROWS,
    SCORE_MATCH_TOLERANCE,
    classify_pair,
    mean_selected,
    summarize_pairs,
    summarize_query_classification,
)


SUPPORT_FLOORS = (1, 2, 3)
CONTRACT = "m95_identity_support_sensitivity_v1"


def identity_at_floor(
    query_prototype,
    target_stats,
    peer_stats,
    excluded,
    floor,
):
    return identity_from_stats_at_floor(
        query_prototype,
        target_stats,
        peer_stats,
        excluded,
        floor,
    )


def identity_from_stats_at_floor(
    query_prototype,
    target_stats,
    peer_stats,
    excluded,
    floor,
):
    from m95_identity_self_support_control_20260925 import (
        nearest_prototype_similarity,
    )

    target_similarity = nearest_prototype_similarity(
        query_prototype,
        target_stats,
        excluded=excluded,
        minimum_points=floor,
    )
    peer_similarity = nearest_prototype_similarity(
        query_prototype,
        peer_stats,
        excluded=excluded,
        minimum_points=floor,
    )
    if target_similarity is None or peer_similarity is None:
        return None
    return {
        "target_similarity": target_similarity,
        "peer_similarity": peer_similarity,
        "margin": target_similarity - peer_similarity,
    }


def remaining_support_counts(stats, excluded):
    return {
        instance_id: total["count"] - excluded[instance_id]["count"]
        for instance_id, total in stats.items()
    }


def exclusion_category(target_counts, peer_counts, floor):
    target_available = any(count >= floor for count in target_counts.values())
    peer_available = any(count >= floor for count in peer_counts.values())
    if target_available and peer_available:
        return "both_available"
    if target_available:
        return "peer_below_floor"
    if peer_available:
        return "target_below_floor"
    return "both_below_floor"


def classify_pair_with_identity(target_query, peer_query, identity_key):
    target_identity = target_query[identity_key]
    peer_identity = peer_query[identity_key]
    row = {
        "manifest_index": target_query["manifest_index"],
        "scene_id": target_query["scene_id"],
        "pair_key": [
            target_query["manifest_index"],
            target_query["query"],
            peer_query["query"],
        ],
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
    return row


def make_floor_pair_rows(query_rows):
    by_expression = defaultdict(lambda: {"target": [], "peer": []})
    for row in query_rows:
        by_expression[row["manifest_index"]][row["truth"]].append(row)

    pair_rows = []
    for expression_rows in by_expression.values():
        for target_query in expression_rows["target"]:
            if not target_query["native_positive"]:
                continue
            for peer_query in expression_rows["peer"]:
                if (
                    abs(target_query["score"] - peer_query["score"])
                    <= SCORE_MATCH_TOLERANCE
                ):
                    pair_rows.append(
                        classify_pair_with_identity(
                            target_query,
                            peer_query,
                            "identity",
                        )
                    )
    return pair_rows


def make_nearest_peer_pair_rows(query_rows):
    by_expression = defaultdict(lambda: {"target": [], "peer": []})
    for row in query_rows:
        by_expression[row["manifest_index"]][row["truth"]].append(row)

    pair_rows = []
    for expression_rows in by_expression.values():
        peers = expression_rows["peer"]
        for target_query in expression_rows["target"]:
            if not target_query["native_positive"]:
                continue
            eligible = [
                peer
                for peer in peers
                if (
                    abs(target_query["score"] - peer["score"])
                    <= SCORE_MATCH_TOLERANCE
                )
            ]
            if not eligible:
                continue
            peer_query = min(
                eligible,
                key=lambda row: (
                    abs(target_query["score"] - row["score"]),
                    row["query"],
                ),
            )
            pair_rows.append(
                classify_pair_with_identity(
                    target_query,
                    peer_query,
                    "identity",
                )
            )
    return pair_rows


def pair_keys(rows):
    return {tuple(row["pair_key"]) for row in rows}


def validate_pair_rows(rows):
    keys = [tuple(row["pair_key"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Score-matched pairs contain duplicates")
    for row in rows:
        manifest_index, target_query, peer_query = row["pair_key"]
        if (
            row["manifest_index"] != manifest_index
            or target_query == peer_query
        ):
            raise ValueError("Score-matched pair key is invalid")


def filter_pair_rows(rows, keys):
    return [row for row in rows if tuple(row["pair_key"]) in keys]


def rerun_common_queries(common_entries, floor):
    rows = []
    for entry in common_entries:
        identity = entry["identities"][floor]
        rows.append(
            {
                **entry,
                "prediction": (
                    "target" if identity["margin"] > 0.0 else "peer"
                ),
                "identity": identity,
            }
        )
    return rows


def summarize_floor(query_rows, pair_rows, attempted, exclusion_counts):
    query_summary = summarize_query_classification(query_rows)
    query_summary.update(
        {
            "attempted_queries": attempted,
            "skipped_missing_prototype": attempted - len(query_rows),
            "coverage": len(query_rows) / attempted if attempted else None,
            "bootstrap_seed": BOOTSTRAP_SEED,
        }
    )
    return {
        "query_classification": query_summary,
        "score_matched_query_pairs": summarize_pairs(pair_rows),
        "exclusion_categories": dict(sorted(exclusion_counts.items())),
    }


def analyze(report, manifest, artifacts, support_floors=SUPPORT_FLOORS):
    support_floors = tuple(sorted(int(value) for value in support_floors))
    if support_floors != SUPPORT_FLOORS:
        raise ValueError("Support floors must be exactly (1, 2, 3)")

    report_rows = validate_capture(
        report, manifest, EXPECTED_CHECKPOINT_SHA256
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")

    stage_queries = {
        stage: {floor: [] for floor in support_floors}
        for stage in STAGES
    }
    stage_query_entries = {
        stage: defaultdict(dict) for stage in STAGES
    }
    attempted = {stage: 0 for stage in STAGES}
    exclusion_counts = {
        stage: {
            floor: Counter() for floor in support_floors
        }
        for stage in STAGES
    }
    ineligible_expressions = 0

    for index in range(EXPECTED_ROWS):
        manifest_row = manifest[index]
        artifact = artifacts[index]
        labels = int_list(
            artifact["physical_instance_labels"], "instance labels"
        )
        target = bool_list(artifact["target_union"], "target union")
        masks = [
            bool_list(mask, "query mask")
            for mask in as_list(artifact["query_masks"])
        ]
        scores = float_list(artifact["query_scores"], "query scores")
        positive = bool_list(
            artifact["native_positive"], "native positives"
        )
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
            ineligible_expressions += 1
            continue

        dominant = [dominant_overlap(mask, labels) for mask in masks]
        peer_set = set(peer_ids)
        candidate_queries = [
            query
            for query, dominant_id in enumerate(dominant)
            if dominant_id in set(target_ids) | peer_set
        ]

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
                    for floor in support_floors:
                        exclusion_counts[stage][floor][
                            "empty_query_prototype"
                        ] += 1
                    continue

                baseline = identity_from_stats(
                    query_prototype, target_stats, peer_stats
                )
                if baseline is None:
                    for floor in support_floors:
                        exclusion_counts[stage][floor][
                            "baseline_unavailable"
                        ] += 1
                    continue

                excluded = support_stats(
                    feature_rows,
                    labels,
                    target_ids + peer_ids,
                    mask,
                )
                target_counts = remaining_support_counts(
                    target_stats, excluded
                )
                peer_counts = remaining_support_counts(peer_stats, excluded)
                identities = {
                    floor: identity_at_floor(
                        query_prototype,
                        target_stats,
                        peer_stats,
                        excluded,
                        floor,
                    )
                    for floor in support_floors
                }

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
                    "identities": identities,
                }
                stage_query_entries[stage][(index, query)] = entry

                for floor in support_floors:
                    category = exclusion_category(
                        target_counts, peer_counts, floor
                    )
                    exclusion_counts[stage][floor][category] += 1
                    identity = identities[floor]
                    if identity is None:
                        exclusion_counts[stage][floor][
                            "skipped_missing_prototype"
                        ] += 1
                        continue
                    stage_queries[stage][floor].append(
                        {
                            **entry,
                            "prediction": (
                                "target"
                                if identity["margin"] > 0.0
                                else "peer"
                            ),
                            "identity": identity,
                        }
                    )

    stages = {}
    for stage in STAGES:
        pair_rows = {
            floor: make_floor_pair_rows(stage_queries[stage][floor])
            for floor in support_floors
        }
        nearest_peer_pair_rows = {
            floor: make_nearest_peer_pair_rows(
                stage_queries[stage][floor]
            )
            for floor in support_floors
        }
        for rows in pair_rows.values():
            validate_pair_rows(rows)
        for rows in nearest_peer_pair_rows.values():
            validate_pair_rows(rows)
        common_query_keys = set.intersection(
            *[
                {
                (row["manifest_index"], row["query"])
                for row in stage_queries[stage][floor]
                }
                for floor in support_floors
            ]
        )
        common_entries = [
            stage_query_entries[stage][key]
            for key in sorted(common_query_keys)
        ]
        common_pairs_by_floor = {
            floor: pair_keys(pair_rows[floor])
            for floor in support_floors
        }
        common_nearest_pairs_by_floor = {
            floor: pair_keys(nearest_peer_pair_rows[floor])
            for floor in support_floors
        }
        common_pair_keys = set.intersection(
            *[
                common_pairs_by_floor[floor]
                for floor in support_floors
            ]
        )
        common_nearest_pair_keys = set.intersection(
            *[
                common_nearest_pairs_by_floor[floor]
                for floor in support_floors
            ]
        )

        floor_summaries = {
            str(floor): summarize_floor(
                stage_queries[stage][floor],
                pair_rows[floor],
                attempted[stage],
                exclusion_counts[stage][floor],
            )
            for floor in support_floors
        }
        nearest_peer_summaries = {
            str(floor): summarize_pairs(nearest_peer_pair_rows[floor])
            for floor in support_floors
        }
        common_query_summaries = {}
        common_pair_summaries = {}
        common_nearest_pair_summaries = {}
        for floor in support_floors:
            common_queries = rerun_common_queries(common_entries, floor)
            summary = summarize_query_classification(common_queries)
            summary.update(
                {
                    "common_population_queries": len(common_queries),
                    "bootstrap_seed": BOOTSTRAP_SEED,
                }
            )
            common_query_summaries[str(floor)] = summary
            common_pair_summaries[str(floor)] = summarize_pairs(
                filter_pair_rows(pair_rows[floor], common_pair_keys)
            )
            common_nearest_pair_summaries[str(floor)] = summarize_pairs(
                filter_pair_rows(
                    nearest_peer_pair_rows[floor],
                    common_nearest_pair_keys,
                )
            )

        floor1_query = common_query_summaries["1"]
        floor3_query = common_query_summaries["3"]
        floor1_pair = common_pair_summaries["1"]
        floor3_pair = common_pair_summaries["3"]
        floor1_nearest_pair = common_nearest_pair_summaries["1"]
        floor3_nearest_pair = common_nearest_pair_summaries["3"]
        stages[stage] = {
            "floors": floor_summaries,
            "nearest_peer_score_matched_pairs": nearest_peer_summaries,
            "common_population": {
                "queries": len(common_query_keys),
                "score_matched_pairs": len(common_pair_keys),
                "nearest_peer_score_matched_pairs": len(
                    common_nearest_pair_keys
                ),
                "query_classification": common_query_summaries,
                "score_matched_query_pairs": common_pair_summaries,
                "nearest_peer_matched": common_nearest_pair_summaries,
                "floor1_minus_floor3": {
                    "balanced_accuracy": (
                        floor1_query["balanced_accuracy"]
                        - floor3_query["balanced_accuracy"]
                    ),
                    "identity_minus_score": (
                        floor1_pair["identity_minus_score"]
                        - floor3_pair["identity_minus_score"]
                    ),
                    "nearest_peer_identity_minus_score": (
                        floor1_nearest_pair["identity_minus_score"]
                        - floor3_nearest_pair["identity_minus_score"]
                    ),
                },
            },
        }

    return {
        "stages": stages,
        "counts": {
            "ineligible_expressions": ineligible_expressions,
            "attempted_queries_by_stage": attempted,
        },
    }


def write_json(path, document):
    path = Path(path)
    if path.exists():
        raise ValueError("Output already exists: %s" % path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=True, sort_keys=True)
        + "\n",
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
            "contract": CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only fixed-floor sensitivity audit of query-support "
                "exclusion on the frozen 256-expression M95 identity capture."
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
                "support_floors": list(SUPPORT_FLOORS),
                "score_match_tolerance": SCORE_MATCH_TOLERANCE,
                "selection_rule": (
                    "Report every fixed floor and compare all floors on the "
                    "common query and matched-pair populations; do not select "
                    "a favorable floor."
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
