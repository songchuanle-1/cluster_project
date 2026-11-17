"""Decompose M95 identity evidence into target attraction and peer rejection.

This CPU-only diagnostic reuses the frozen 256-expression M95 capture. It
compares three pair-level selectors on the same score-matched population:

* target similarity alone,
* low peer similarity alone, and
* their difference, which is the full identity margin.

The result is oracle diagnostic evidence, not a deployable selector, a
mechanism claim, or an admission receipt.
"""
import argparse
import json
import random
from collections import Counter, defaultdict
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
    prototype_stats,
    support_stats,
)
from m95_identity_support_sensitivity_20260925 import (
    EXPECTED_CAPTURE_SHA256,
    SCORE_MATCH_TOLERANCE,
    identity_from_stats_at_floor,
)


CONTRACT = "m95_identity_component_decomposition_v1"
EXPECTED_ROWS = 256
FINAL_STAGE = "final"
SUPPORT_FLOOR = 3
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999
METHODS = ("target_similarity", "peer_rejection", "identity_margin")


def percentile(values, fraction):
    if not values:
        raise ValueError("Cannot take a percentile of an empty population")
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def method_choice(pair, method):
    target = pair["target"]
    peer = pair["peer"]
    if method == "target_similarity":
        left = target["target_similarity"]
        right = peer["target_similarity"]
        prefer_high = True
    elif method == "peer_rejection":
        left = target["peer_similarity"]
        right = peer["peer_similarity"]
        prefer_high = False
    elif method == "identity_margin":
        left = (
            target["target_similarity"] - target["peer_similarity"]
        )
        right = (
            peer["target_similarity"] - peer["peer_similarity"]
        )
        prefer_high = True
    else:
        raise ValueError("Unknown identity component method: %s" % method)

    if left == right:
        return None
    target_wins = left > right if prefer_high else left < right
    return "target" if target_wins else "peer"


def score_choice(pair):
    if pair["target"]["score"] == pair["peer"]["score"]:
        return None
    return (
        "target"
        if pair["target"]["score"] > pair["peer"]["score"]
        else "peer"
    )


def iou_choice(pair):
    if pair["target"]["iou"] == pair["peer"]["iou"]:
        return None
    return (
        "target"
        if pair["target"]["iou"] > pair["peer"]["iou"]
        else "peer"
    )


def cluster_bootstrap_mean(rows, group_key, value_key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(float(row[value_key]))
    if not grouped:
        return None
    cluster_ids = sorted(grouped)
    rng = random.Random(BOOTSTRAP_SEED)
    samples = []
    for _ in range(BOOTSTRAP_DRAWS):
        sampled = rng.choices(cluster_ids, k=len(cluster_ids))
        values = [
            value
            for cluster_id in sampled
            for value in grouped[cluster_id]
        ]
        samples.append(sum(values) / len(values))
    point_estimate = (
        sum(value for values in grouped.values() for value in values)
        / sum(len(values) for values in grouped.values())
    )
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
        "cluster_count": len(cluster_ids),
        "point_estimate": point_estimate,
        "lo": percentile(samples, 0.025),
        "hi": percentile(samples, 0.975),
    }


def selector_rows(pair_rows, method):
    rows = []
    for pair in pair_rows:
        component = method_choice(pair, method)
        score = score_choice(pair)
        truth = iou_choice(pair)
        component_correct = (
            component is not None
            and truth is not None
            and component == truth
        )
        score_correct = (
            score is not None
            and truth is not None
            and score == truth
        )
        rows.append(
            {
                "manifest_index": pair["manifest_index"],
                "scene_id": pair["scene_id"],
                "target_query": pair["target_query"],
                "component_correct": float(component_correct),
                "score_correct": float(score_correct),
                "difference": float(component_correct - score_correct),
                "component_disagrees_with_score": (
                    component is not None
                    and score is not None
                    and component != score
                ),
            }
        )
    return rows


def summarize_selector(pair_rows, method):
    rows = selector_rows(pair_rows, method)
    positive = sum(row["difference"] > 0.0 for row in rows)
    negative = sum(row["difference"] < 0.0 for row in rows)
    return {
        "pairs": len(rows),
        "component_accuracy": (
            sum(row["component_correct"] for row in rows) / len(rows)
            if rows else None
        ),
        "score_accuracy": (
            sum(row["score_correct"] for row in rows) / len(rows)
            if rows else None
        ),
        "component_minus_score": (
            sum(row["difference"] for row in rows) / len(rows)
            if rows else None
        ),
        "positive_deltas": positive,
        "negative_deltas": negative,
        "zero_deltas": len(rows) - positive - negative,
        "component_disagrees_with_score": sum(
            row["component_disagrees_with_score"] for row in rows
        ),
        "scene_bootstrap": cluster_bootstrap_mean(
            rows,
            lambda row: row["scene_id"],
            "difference",
        ),
        "target_query_bootstrap": cluster_bootstrap_mean(
            rows,
            lambda row: (
                row["manifest_index"],
                row["target_query"],
            ),
            "difference",
        ),
    }


def decomposition_rows(pair_rows):
    rows = []
    for pair in pair_rows:
        identity = method_choice(pair, "identity_margin")
        score = score_choice(pair)
        if identity is None or score is None or identity == score:
            continue
        identity_row = pair[identity]
        score_row = pair[score]
        target_delta = (
            identity_row["target_similarity"]
            - score_row["target_similarity"]
        )
        peer_delta = (
            identity_row["peer_similarity"]
            - score_row["peer_similarity"]
        )
        margin_delta = (
            identity_row["target_similarity"]
            - identity_row["peer_similarity"]
            - score_row["target_similarity"]
            + score_row["peer_similarity"]
        )
        if abs(margin_delta - (target_delta - peer_delta)) > 1e-12:
            raise ValueError("Identity margin decomposition is inconsistent")
        rows.append(
            {
                "manifest_index": pair["manifest_index"],
                "scene_id": pair["scene_id"],
                "target_query": pair["target_query"],
                "identity_choice": identity,
                "score_choice": score,
                "identity_minus_score_iou": (
                    identity_row["iou"] - score_row["iou"]
                ),
                "target_similarity_delta": target_delta,
                "peer_similarity_delta": peer_delta,
                "identity_margin_delta": margin_delta,
                "target_assisted": float(target_delta > 0.0),
                "peer_rejected": float(peer_delta < 0.0),
            }
        )
    return rows


def decomposition_category(row):
    target_assisted = row["target_similarity_delta"] > 0.0
    peer_rejected = row["peer_similarity_delta"] < 0.0
    if target_assisted and peer_rejected:
        return "target_assisted_and_peer_rejected"
    if target_assisted:
        return "target_assisted_only"
    if peer_rejected:
        return "peer_rejected_only"
    return "neither_component_helps"


def summarize_decomposition(pair_rows):
    rows = decomposition_rows(pair_rows)
    if not rows:
        raise ValueError("No identity-score disagreement pairs")
    grouped = defaultdict(list)
    for row in rows:
        grouped[decomposition_category(row)].append(row)

    categories = {}
    for category, category_rows in sorted(grouped.items()):
        deltas = [
            row["identity_minus_score_iou"] for row in category_rows
        ]
        categories[category] = {
            "pairs": len(category_rows),
            "identity_better": sum(value > 0.0 for value in deltas),
            "identity_worse": sum(value < 0.0 for value in deltas),
            "ties": sum(value == 0.0 for value in deltas),
            "mean_identity_minus_score_iou": sum(deltas) / len(deltas),
            "mean_target_similarity_delta": sum(
                row["target_similarity_delta"] for row in category_rows
            )
            / len(category_rows),
            "mean_peer_similarity_delta": sum(
                row["peer_similarity_delta"] for row in category_rows
            )
            / len(category_rows),
        }

    deltas = [row["identity_minus_score_iou"] for row in rows]
    return {
        "non_tied_disagreement_pairs": len(rows),
        "identity_better": sum(value > 0.0 for value in deltas),
        "identity_worse": sum(value < 0.0 for value in deltas),
        "ties": sum(value == 0.0 for value in deltas),
        "mean_identity_minus_score_iou": sum(deltas) / len(deltas),
        "mean_target_similarity_delta": sum(
            row["target_similarity_delta"] for row in rows
        )
        / len(rows),
        "mean_peer_similarity_delta": sum(
            row["peer_similarity_delta"] for row in rows
        )
        / len(rows),
        "target_similarity_delta_bootstrap": cluster_bootstrap_mean(
            rows,
            lambda row: (
                row["manifest_index"],
                row["target_query"],
            ),
            "target_similarity_delta",
        ),
        "peer_similarity_delta_bootstrap": cluster_bootstrap_mean(
            rows,
            lambda row: (
                row["manifest_index"],
                row["target_query"],
            ),
            "peer_similarity_delta",
        ),
        "scene_target_similarity_delta_bootstrap": cluster_bootstrap_mean(
            rows,
            lambda row: row["scene_id"],
            "target_similarity_delta",
        ),
        "scene_peer_similarity_delta_bootstrap": cluster_bootstrap_mean(
            rows,
            lambda row: row["scene_id"],
            "peer_similarity_delta",
        ),
        "categories": categories,
    }


def extract_pair_rows(report, manifest, artifacts):
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
    eligible_expressions = 0
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
            continue

        features = [
            float_list(vector, FINAL_STAGE + " feature")
            for vector in as_list(artifact["features"][FINAL_STAGE])
        ]
        if len(features) != len(labels):
            raise ValueError("Feature support differs from labels")

        target_stats = prototype_stats(features, labels, target_ids)
        peer_stats = prototype_stats(features, labels, peer_ids)
        dominant = [dominant_overlap(mask, labels) for mask in masks]
        target_set = set(target_ids)
        peer_set = set(peer_ids)
        candidate_queries = [
            query
            for query, dominant_id in enumerate(dominant)
            if dominant_id in target_set | peer_set
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
                    "query": query,
                    "score": scores[query],
                    "iou": mask_iou(mask, target),
                    "native_positive": positive[query],
                    "truth": (
                        "target"
                        if dominant_id in target_set
                        else "peer"
                    ),
                    "target_similarity": identity["target_similarity"],
                    "peer_similarity": identity["peer_similarity"],
                }
            )

        if query_rows:
            eligible_expressions += 1
        for target_query in query_rows:
            if (
                target_query["truth"] != "target"
                or not target_query["native_positive"]
            ):
                continue
            for peer_query in query_rows:
                if (
                    peer_query["truth"] != "peer"
                    or abs(
                        target_query["score"] - peer_query["score"]
                    )
                    > SCORE_MATCH_TOLERANCE
                ):
                    continue
                pair_rows.append(
                    {
                        "manifest_index": index,
                        "scene_id": str(manifest_row["scene_id"]),
                        "target_query": target_query["query"],
                        "peer_query": peer_query["query"],
                        "target": target_query,
                        "peer": peer_query,
                    }
                )

    for index in range(EXPECTED_ROWS):
        if int(report_rows[index]["manifest_index"]) != index:
            raise ValueError("Validated capture row ordering differs")
    return {
        "pair_rows": pair_rows,
        "eligible_expressions": eligible_expressions,
        "attempted_queries": attempted_queries,
        "skipped_missing_prototype": skipped_missing_prototype,
    }


def analyze(report, manifest, artifacts):
    extracted = extract_pair_rows(report, manifest, artifacts)
    pair_rows = extracted.pop("pair_rows")
    return {
        "selectors": {
            method: summarize_selector(pair_rows, method)
            for method in METHODS
        },
        "decomposition": summarize_decomposition(pair_rows),
        "counts": extracted,
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
    output_path = Path(args.output).resolve()
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
    result = analyze(report, manifest, artifacts)
    result.update(
        {
            "schema_version": 1,
            "contract": CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only component decomposition on the frozen "
                "256-expression M95 final-stage identity capture."
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
                "final_stage": FINAL_STAGE,
                "support_floor": SUPPORT_FLOOR,
                "score_match_tolerance": SCORE_MATCH_TOLERANCE,
                "selectors": {
                    "target_similarity": "choose higher target similarity",
                    "peer_rejection": "choose lower peer similarity",
                    "identity_margin": (
                        "choose higher target-minus-peer similarity"
                    ),
                },
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
    write_json(output_path, result)
    print(
        json.dumps(
            {
                "selectors": result["selectors"],
                "decomposition": result["decomposition"],
                "counts": result["counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
