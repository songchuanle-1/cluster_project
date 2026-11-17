"""Measure target-versus-peer identity discriminability in the frozen M95 capture.

This is a CPU-only diagnostic on the existing 256-expression capture. Query
identity margins use target and same-class-peer instance prototypes, so they
are oracle diagnostics rather than deployable selector results.
"""
import argparse
import hashlib
import json
import math
import random
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
    score_pick,
    validate_capture,
    validate_manifest_hash,
)


EXPECTED_CAPTURE_SHA256 = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
)
EXPECTED_ROWS = 256
MIN_PROTOTYPE_POINTS = 3
SCORE_MATCH_TOLERANCE = 0.1
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999
ANALYSIS_CONTRACT = "m95_instance_identity_discriminability_v1"


def cosine(left, right):
    if left is None or right is None or len(left) != len(right) or not left:
        return None
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    return dot / (left_norm * right_norm)


def mean_selected(rows, mask):
    selected = [row for row, take in zip(rows, mask) if take]
    if not selected:
        return None
    width = len(selected[0])
    if width == 0 or any(len(row) != width for row in selected):
        raise ValueError("Feature vectors differ")
    return [
        sum(float(row[index]) for row in selected) / len(selected)
        for index in range(width)
    ]


def instance_prototypes(rows, labels, instance_ids):
    wanted = {int(instance_id) for instance_id in instance_ids}
    grouped = defaultdict(list)
    for row, label in zip(rows, labels):
        instance = int(label)
        if instance in wanted:
            grouped[instance].append(row)
    prototypes = {}
    for instance in sorted(grouped):
        if len(grouped[instance]) >= MIN_PROTOTYPE_POINTS:
            prototypes[instance] = mean_selected(
                grouped[instance], [True] * len(grouped[instance])
            )
    return prototypes


def maximum_similarity(prototype, candidates):
    similarities = [
        cosine(prototype, candidate) for candidate in candidates.values()
    ]
    similarities = [value for value in similarities if value is not None]
    return max(similarities) if similarities else None


def query_identity(vectors, mask, labels, target_ids, peer_ids):
    query_prototype = mean_selected(vectors, mask)
    if query_prototype is None:
        return None
    target_prototypes = instance_prototypes(vectors, labels, target_ids)
    peer_prototypes = instance_prototypes(vectors, labels, peer_ids)
    target_similarity = maximum_similarity(query_prototype, target_prototypes)
    peer_similarity = maximum_similarity(query_prototype, peer_prototypes)
    if target_similarity is None or peer_similarity is None:
        return None
    return {
        "target_similarity": target_similarity,
        "peer_similarity": peer_similarity,
        "margin": target_similarity - peer_similarity,
    }


def balanced_accuracy(rows):
    counts = Counter()
    for row in rows:
        truth = row["truth"]
        prediction = row["prediction"]
        counts[(truth, prediction)] += 1
    recalls = []
    for label in ("target", "peer"):
        denominator = counts[(label, "target")] + counts[(label, "peer")]
        if denominator:
            recalls.append(counts[(label, label)] / denominator)
    if not recalls:
        return None
    return sum(recalls) / len(recalls)


def scene_bootstrap(values_by_scene, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    groups = [values for values in values_by_scene.values() if values]
    if not groups:
        return None
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        selected = rng.choices(groups, k=len(groups))
        samples.append(sum(sum(group) / len(group) for group in selected) / len(groups))
    samples.sort()
    return {
        "draws": draws,
        "seed": seed,
        "unit": "scene",
        "scene_count": len(groups),
        "point_estimate": (
            sum(sum(group) / len(group) for group in groups) / len(groups)
        ),
        "lo": samples[int(0.025 * (draws - 1))],
        "hi": samples[int(0.975 * (draws - 1))],
    }


def summarize_query_classification(rows):
    if not rows:
        return {
            "eligible_expressions": 0,
            "queries": 0,
            "target_queries": 0,
            "peer_queries": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "scene_bootstrap_balanced_accuracy": None,
        }
    correct = sum(row["truth"] == row["prediction"] for row in rows)
    per_scene = defaultdict(list)
    for row in rows:
        per_scene[str(row["scene_id"])].append(
            float(row["truth"] == row["prediction"])
        )
    return {
        "eligible_expressions": len({row["manifest_index"] for row in rows}),
        "queries": len(rows),
        "target_queries": sum(row["truth"] == "target" for row in rows),
        "peer_queries": sum(row["truth"] == "peer" for row in rows),
        "accuracy": correct / len(rows),
        "balanced_accuracy": balanced_accuracy(rows),
        "scene_bootstrap_accuracy": scene_bootstrap(per_scene),
    }


def classify_pair(target_query, peer_query):
    identity = int(target_query["margin"] > peer_query["margin"])
    identity_tie = target_query["margin"] == peer_query["margin"]
    score = int(target_query["score"] > peer_query["score"])
    score_tie = target_query["score"] == peer_query["score"]
    iou = int(target_query["iou"] > peer_query["iou"])
    return {
        "identity_target": identity,
        "identity_tie": identity_tie,
        "score_target": score,
        "score_tie": score_tie,
        "iou_target": iou,
        "identity_matches_iou": identity == iou and not identity_tie,
        "score_matches_iou": score == iou and not score_tie,
        "identity_disagrees_with_score": (
            not identity_tie and not score_tie and identity != score
        ),
    }


def summarize_pairs(rows):
    if not rows:
        return {
            "expressions": 0,
            "pairs": 0,
            "identity_matches_iou": 0,
            "score_matches_iou": 0,
            "identity_only_matches_iou": 0,
            "score_only_matches_iou": 0,
            "identity_disagrees_with_score": 0,
            "identity_accuracy": None,
            "score_accuracy": None,
            "identity_minus_score": None,
            "scene_bootstrap": None,
        }
    per_scene = defaultdict(lambda: {
        "identity": [],
        "score": [],
        "difference": [],
    })
    for row in rows:
        scene = str(row["scene_id"])
        identity = float(row["identity_matches_iou"])
        score = float(row["score_matches_iou"])
        per_scene[scene]["identity"].append(identity)
        per_scene[scene]["score"].append(score)
        per_scene[scene]["difference"].append(identity - score)
    return {
        "expressions": len({row["manifest_index"] for row in rows}),
        "pairs": len(rows),
        "identity_matches_iou": sum(row["identity_matches_iou"] for row in rows),
        "score_matches_iou": sum(row["score_matches_iou"] for row in rows),
        "identity_only_matches_iou": sum(
            row["identity_matches_iou"] and not row["score_matches_iou"]
            for row in rows
        ),
        "score_only_matches_iou": sum(
            row["score_matches_iou"] and not row["identity_matches_iou"]
            for row in rows
        ),
        "identity_disagrees_with_score": sum(
            row["identity_disagrees_with_score"] for row in rows
        ),
        "identity_accuracy": (
            sum(row["identity_matches_iou"] for row in rows) / len(rows)
        ),
        "score_accuracy": (
            sum(row["score_matches_iou"] for row in rows) / len(rows)
        ),
        "identity_minus_score": (
            sum(
                row["identity_matches_iou"] - row["score_matches_iou"]
                for row in rows
            )
            / len(rows)
        ),
        "scene_bootstrap": {
            field: scene_bootstrap(
                {
                    scene: values[field]
                    for scene, values in per_scene.items()
                }
            )
            for field in ("identity", "score", "difference")
        },
    }


def analyze(report, manifest, artifacts):
    report_rows = validate_capture(
        report, manifest, EXPECTED_CHECKPOINT_SHA256
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")

    query_rows = {stage: [] for stage in STAGES}
    pair_rows = {stage: [] for stage in STAGES}
    expression_rows = []

    for index in range(EXPECTED_ROWS):
        manifest_row = manifest[index]
        artifact = artifacts[index]
        capture_row = report_rows[index]
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
            expression_rows.append(
                {
                    "manifest_index": index,
                    "scene_id": str(manifest_row["scene_id"]),
                    "eligible": False,
                    "reason": "missing_target_or_peer",
                }
            )
            continue

        dominant = [dominant_overlap(mask, labels) for mask in masks]
        peer_set = set(peer_ids)
        per_stage_queries = {}
        for stage in STAGES:
            feature_rows = [
                float_list(vector, stage + " feature")
                for vector in as_list(artifact["features"][stage])
            ]
            if len(feature_rows) != len(labels):
                raise ValueError("Feature support differs from labels")
            stage_queries = []
            for query, mask in enumerate(masks):
                identity = query_identity(
                    feature_rows, mask, labels, target_ids, peer_ids
                )
                if identity is None:
                    continue
                dominant_id = dominant[query]
                if dominant_id not in set(target_ids) | peer_set:
                    continue
                truth = "target" if dominant_id in target_ids else "peer"
                prediction = (
                    "target" if identity["margin"] > 0.0 else "peer"
                )
                entry = {
                    "manifest_index": index,
                    "scene_id": str(manifest_row["scene_id"]),
                    "query": query,
                    "score": scores[query],
                    "iou": mask_iou(mask, target),
                    "native_positive": positive[query],
                    "dominant": str(dominant_id),
                    "truth": truth,
                    "prediction": prediction,
                    **identity,
                }
                stage_queries.append(entry)
                query_rows[stage].append(entry)
                if not any(positive):
                    continue
                if truth == "peer":
                    for positive_query in stage_queries:
                        if (
                            positive_query["native_positive"]
                            and abs(positive_query["score"] - entry["score"])
                            <= SCORE_MATCH_TOLERANCE
                        ):
                            pair = {
                                "manifest_index": index,
                                "scene_id": str(manifest_row["scene_id"]),
                                **classify_pair(positive_query, entry),
                            }
                            pair_rows[stage].append(pair)
            per_stage_queries[stage] = stage_queries

        expression_rows.append(
            {
                "manifest_index": index,
                "scene_id": str(manifest_row["scene_id"]),
                "eligible": True,
                "target_instances": target_ids,
                "peer_instances": peer_ids,
                "query_count": len(masks),
                "stages": {
                    stage: {
                        "queries": len(per_stage_queries[stage]),
                        "target": sum(
                            query["truth"] == "target"
                            for query in per_stage_queries[stage]
                        ),
                        "peer": sum(
                            query["truth"] == "peer"
                            for query in per_stage_queries[stage]
                        ),
                    }
                    for stage in STAGES
                },
            }
        )

    return {
        "stages": {
            stage: {
                "query_classification": summarize_query_classification(
                    query_rows[stage]
                ),
                "score_matched_query_pairs": summarize_pairs(pair_rows[stage]),
            }
            for stage in STAGES
        },
        "expressions": expression_rows,
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
                "CPU-only instance-prototype discriminability diagnostic on "
                "the frozen 256-expression M95 capture."
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
                "identity_prediction": (
                    "target when nearest target-instance prototype cosine "
                    "exceeds nearest same-class-peer prototype cosine"
                ),
                "pair_denominator": (
                    "native-positive query versus same-class-peer-dominant "
                    "query with absolute score difference <= 0.1"
                ),
            },
            "candidate_handoff": {
                "referent-supervision-axis": (
                    "identity verdict availability versus native-positive "
                    "membership"
                ),
                "referent-discrimination": (
                    "identity verdict versus score verdict on matched queries"
                ),
                "instance-identity-representation": (
                    "target-versus-peer query classification by stage"
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
