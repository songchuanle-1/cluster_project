"""Analyze the frozen M95 manifest-bound identity-control capture.

This is a CPU-only post-capture analyzer. It does not train, mutate the queue,
or admit a mechanism. All estimands and controls come from the pre-registered
manifest contract.
"""
import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = (
    ROOT / "pipeline" / "diagnostic_runs" / "m95_identity_controls_20260922"
    / "manifest.json"
)
EXPECTED_MANIFEST_SHA256 = (
    "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
)
EXPECTED_CHECKPOINT_SHA256 = (
    "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
)
MANIFEST_CONTRACT = "m95_preregistered_identity_controls_v1"
CAPTURE_ARTIFACT_CONTRACT = "m95_manifest_native_query_artifact_v1"
ANALYSIS_CONTRACT = "m95_manifest_identity_control_analysis_v1"
SCORE_MATCH_CONTRACT = "m95_identity_controls_v1|score_match"
STAGES = ("raw_3d", "raw_2d", "projected_3d", "projected_2d", "fused", "final")
PRIMARY_MIN_PAIRS = 64
PRIMARY_MIN_SCENES = 64
PRIMARY_MIN_POINT = 0.05
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def as_list(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list):
        raise ValueError("Expected a list-like value")
    return value


def bool_list(value, name):
    values = as_list(value)
    if any(not isinstance(item, bool) for item in values):
        raise ValueError(name + " must contain booleans")
    return values


def float_list(value, name):
    values = as_list(value)
    result = []
    for item in values:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(name + " must contain numbers")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(name + " contains a nonfinite value")
        result.append(number)
    return result


def int_list(value, name):
    values = as_list(value)
    result = []
    for item in values:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError(name + " must contain integers")
        result.append(int(item))
    return result


def manifest_rows(document, expected_sha256):
    if document.get("contract") != MANIFEST_CONTRACT:
        raise ValueError("Wrong manifest contract")
    rows = document.get("rows")
    if not isinstance(rows, list) or len(rows) != 256:
        raise ValueError("Expected 256 manifest rows")
    indexed = {}
    keys = set()
    for expected_index, row in enumerate(rows):
        if int(row.get("manifest_index", -1)) != expected_index:
            raise ValueError("Manifest indices are not contiguous")
        key = (str(row.get("scene_id")), int(row.get("ann_id")))
        if key in keys:
            raise ValueError("Duplicate manifest expression")
        keys.add(key)
        if expected_index in indexed:
            raise ValueError("Duplicate manifest index")
        indexed[expected_index] = dict(row)
    if len(indexed) != 256:
        raise ValueError("Manifest index coverage differs")
    return indexed


def validate_manifest_hash(document, actual_sha256, expected_sha256):
    if actual_sha256 != expected_sha256:
        raise ValueError("Manifest hash differs from the frozen contract")
    return manifest_rows(document, expected_sha256)


def score_pick(scores, allowed):
    if len(scores) != len(allowed):
        raise ValueError("Query scores and allowed mask differ")
    indices = [index for index, value in enumerate(allowed) if value]
    if not indices:
        return None
    return max(indices, key=lambda index: (scores[index], -index))


def dominant_overlap(mask, labels):
    if len(mask) != len(labels):
        raise ValueError("Query mask and physical labels differ")
    counts = Counter(
        label
        for selected, label in zip(mask, labels)
        if selected and label >= 0
    )
    if not counts:
        return None
    return min(counts, key=lambda label: (-counts[label], label))


def mask_iou(mask, target):
    if len(mask) != len(target):
        raise ValueError("Query mask and target union differ")
    overlap = sum(selected and truth for selected, truth in zip(mask, target))
    union = sum(selected or truth for selected, truth in zip(mask, target))
    return overlap / max(union, 1)


def score_match_pair(scores, positive_indices, negative_indices):
    candidates = []
    for positive_index in positive_indices:
        for negative_index in negative_indices:
            if negative_index == positive_index:
                continue
            difference = abs(scores[positive_index] - scores[negative_index])
            if difference > 0.1:
                continue
            payload = "%s|%d|%d" % (
                SCORE_MATCH_CONTRACT,
                int(positive_index),
                int(negative_index),
            )
            digest = hashlib.sha256(payload.encode("ascii")).hexdigest()
            candidates.append(
                (difference, digest, int(positive_index), int(negative_index))
            )
    if not candidates:
        return None
    difference, digest, positive, negative = min(candidates)
    return {
        "positive_index": positive,
        "negative_index": negative,
        "score_difference": difference,
        "tie_break_sha256": digest,
    }


def bootstrap_scene_values(values_by_scene, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    if not values_by_scene:
        return None
    scene_values = [sum(values) / len(values) for values in values_by_scene.values()]
    rng = random.Random(seed)
    sampled = []
    for _ in range(draws):
        values = rng.choices(scene_values, k=len(scene_values))
        sampled.append(sum(values) / len(values))
    sampled.sort()
    return {
        "draws": draws,
        "seed": seed,
        "unit": "scene",
        "point_estimate": sum(scene_values) / len(scene_values),
        "scene_count": len(scene_values),
        "lo": sampled[int(0.025 * (draws - 1))],
        "hi": sampled[int(0.975 * (draws - 1))],
    }


def paired_summary(rows, value_key, draws=BOOTSTRAP_DRAWS):
    values_by_scene = defaultdict(list)
    selected = []
    for row in rows:
        value = row.get(value_key)
        if value is None:
            continue
        values_by_scene[str(row["scene_id"])].append(float(value))
        selected.append(float(value))
    if not selected:
        return {
            "available": 0,
            "scenes": 0,
            "pooled_mean": None,
            "scene_bootstrap_95ci": None,
        }
    return {
        "available": len(selected),
        "scenes": len(values_by_scene),
        "pooled_mean": sum(selected) / len(selected),
        "scene_bootstrap_95ci": bootstrap_scene_values(
            values_by_scene, draws=draws
        ),
    }


def selector_summary(rows, selector_key):
    successes = []
    by_scene = defaultdict(list)
    for row in rows:
        selected = row.get(selector_key)
        if selected is None:
            continue
        success = float(float(row["ious"][selected]) > 0.5)
        successes.append(success)
        by_scene[str(row["scene_id"])].append(success)
    if not successes:
        return {
            "available": 0,
            "scenes": 0,
            "success_rate": None,
            "scene_balanced_success": None,
        }
    scene_rates = [sum(values) / len(values) for values in by_scene.values()]
    return {
        "available": len(successes),
        "scenes": len(by_scene),
        "success_rate": sum(successes) / len(successes),
        "scene_balanced_success": sum(scene_rates) / len(scene_rates),
    }


def mean_feature(features, mask):
    selected = [vector for vector, take in zip(features, mask) if take]
    if not selected:
        return None
    width = len(selected[0])
    if width == 0 or any(len(vector) != width for vector in selected):
        raise ValueError("Feature vectors differ")
    return [
        sum(float(vector[index]) for vector in selected) / len(selected)
        for index in range(width)
    ]


def cosine(left, right):
    if left is None or right is None or len(left) != len(right) or not left:
        return None
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    return dot / (left_norm * right_norm)


def stage_identity_margins(features, query_mask, target, labels, peer_ids):
    peer_mask = [str(label) in peer_ids for label in labels]
    target_proto = mean_feature(features, target)
    peer_proto = mean_feature(features, peer_mask)
    query_proto = mean_feature(features, query_mask)
    if target_proto is None or peer_proto is None or query_proto is None:
        return {}
    target_similarity = cosine(query_proto, target_proto)
    peer_similarity = cosine(query_proto, peer_proto)
    if target_similarity is None or peer_similarity is None:
        return {}
    return {
        "cosine_to_target": target_similarity,
        "cosine_to_same_class_peer": peer_similarity,
        "margin": target_similarity - peer_similarity,
    }


def compact_row(artifact, report_row, manifest_row):
    scores = float_list(artifact.get("query_scores"), "query scores")
    masks = [bool_list(mask, "query mask") for mask in as_list(artifact["query_masks"])]
    native_positive = bool_list(artifact.get("native_positive"), "native positives")
    seed_inside = bool_list(
        artifact.get("fps_seed_inside_target"), "FPS seed support"
    )
    labels = int_list(
        artifact.get("physical_instance_labels"), "physical instance labels"
    )
    target = bool_list(artifact.get("target_union"), "target union")
    query_count = len(scores)
    if query_count == 0:
        raise ValueError("Empty query axis")
    for name, values in (
        ("masks", masks),
        ("native positives", native_positive),
        ("FPS seed support", seed_inside),
    ):
        if len(values) != query_count:
            raise ValueError(name + " length differs from query count")
    if any(len(mask) != len(labels) for mask in masks):
        raise ValueError("Query mask support differs from physical labels")
    if len(target) != len(labels):
        raise ValueError("Target union differs from support")
    if len(report_row.get("scores", [])) != query_count:
        raise ValueError("Capture report query scores differ")
    for index, score in enumerate(scores):
        if not math.isclose(score, float(report_row["scores"][index]), abs_tol=1e-7):
            raise ValueError("Capture report and artifact scores differ")
    if [bool(value) for value in report_row["native_positive"]] != native_positive:
        raise ValueError("Capture report and artifact positives differ")
    if [bool(value) for value in report_row["seed_inside"]] != seed_inside:
        raise ValueError("Capture report and artifact seed support differ")
    ious = [mask_iou(mask, target) for mask in masks]
    report_ious = float_list(report_row.get("ious"), "capture report IoUs")
    if len(report_ious) != query_count:
        raise ValueError("Capture report IoU axis differs")
    if any(not math.isclose(value, report_ious[index], abs_tol=1e-7)
           for index, value in enumerate(ious)):
        raise ValueError("Capture report and artifact IoUs differ")

    target_id = str(manifest_row["target_object_id"])
    peer_ids = {str(value) for value in manifest_row["same_class_peer_object_ids"]}
    class_ids = peer_ids | {target_id}
    dominant = [dominant_overlap(mask, labels) for mask in masks]
    dominant_ids = [
        None if value is None else str(value) for value in dominant
    ]
    deployed = score_pick(scores, [True] * query_count)
    positive = score_pick(scores, native_positive)
    objectness = score_pick(scores, seed_inside)
    class_selector = score_pick(
        scores, [value in class_ids for value in dominant_ids]
    )
    class_non_target = score_pick(
        scores, [value in peer_ids for value in dominant_ids]
    )
    negative_indices = [
        index for index, value in enumerate(dominant_ids) if value in peer_ids
    ]
    pair = score_match_pair(
        scores,
        [index for index, value in enumerate(native_positive) if value],
        negative_indices,
    )

    stage_values = {}
    if positive is not None:
        features = artifact.get("features")
        if not isinstance(features, dict):
            raise ValueError("Artifact features are missing")
        for stage in STAGES:
            if stage not in features:
                continue
            matrix = [float_list(row, stage + " feature") for row in as_list(features[stage])]
            if len(matrix) != len(labels):
                raise ValueError("Feature support differs from physical labels")
            values = stage_identity_margins(
                matrix, masks[positive], target, labels, peer_ids
            )
            if values:
                stage_values[stage] = values

    row = {
        "manifest_index": int(manifest_row["manifest_index"]),
        "scene_id": str(manifest_row["scene_id"]),
        "ann_id": int(manifest_row["ann_id"]),
        "stratum": manifest_row["stratum"],
        "query_count": query_count,
        "scores": scores,
        "ious": ious,
        "native_positive": native_positive,
        "fps_seed_inside_target": seed_inside,
        "dominant_instance": dominant,
        "deployed_query": deployed,
        "target_positive_query": positive,
        "target_objectness_query": objectness,
        "class_matched_selector_query": class_selector,
        "class_matched_non_target_query": class_non_target,
        "score_matched_pair": pair,
        "deployed_iou": ious[deployed],
        "target_positive_iou": None if positive is None else ious[positive],
        "target_objectness_iou": None if objectness is None else ious[objectness],
        "class_matched_selector_iou": (
            None if class_selector is None else ious[class_selector]
        ),
        "class_matched_non_target_iou": (
            None if class_non_target is None else ious[class_non_target]
        ),
        "stage_identity": stage_values,
    }
    row["positive_minus_deployed_iou"] = (
        None if positive is None else row["target_positive_iou"] - row["deployed_iou"]
    )
    row["objectness_minus_deployed_iou"] = (
        None if objectness is None
        else row["target_objectness_iou"] - row["deployed_iou"]
    )
    row["class_selector_minus_deployed_iou"] = (
        None if class_selector is None
        else row["class_matched_selector_iou"] - row["deployed_iou"]
    )
    row["class_non_target_minus_deployed_iou"] = (
        None if class_non_target is None
        else row["class_matched_non_target_iou"] - row["deployed_iou"]
    )
    if pair is not None:
        positive_index = pair["positive_index"]
        negative_index = pair["negative_index"]
        row["primary_pair_target_iou"] = ious[positive_index]
        row["primary_pair_non_target_iou"] = ious[negative_index]
        row["primary_pair_iou_uplift"] = (
            ious[positive_index] - ious[negative_index]
        )
        row["primary_pair_score_difference"] = (
            scores[positive_index] - scores[negative_index]
        )
    else:
        row["primary_pair_target_iou"] = None
        row["primary_pair_non_target_iou"] = None
        row["primary_pair_iou_uplift"] = None
        row["primary_pair_score_difference"] = None
    return row


def summarize_stage_identity(rows):
    summary = {}
    for stage in STAGES:
        values = [
            row["stage_identity"][stage]["margin"]
            for row in rows
            if stage in row["stage_identity"]
        ]
        if not values:
            summary[stage] = {
                "available": 0,
                "mean_margin": None,
                "positive_margin_fraction": None,
            }
            continue
        summary[stage] = {
            "available": len(values),
            "mean_margin": sum(values) / len(values),
            "positive_margin_fraction": (
                sum(value > 0.0 for value in values) / len(values)
            ),
        }
    return summary


def validate_artifact_header(artifact, manifest_sha256):
    if artifact.get("artifact_contract") != CAPTURE_ARTIFACT_CONTRACT:
        raise ValueError("Wrong artifact contract")
    if artifact.get("manifest_sha256") != manifest_sha256:
        raise ValueError("Artifact manifest hash differs")


def load_artifacts(capture_path, report, manifest_sha256):
    import torch

    artifacts = report.get("feature_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Capture report has no feature artifacts")
    loaded = {}
    for item in artifacts:
        relative = Path(str(item.get("path")))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Artifact path escapes capture directory")
        path = capture_path.parent / relative
        if not path.is_file():
            raise ValueError("Artifact file is missing")
        if file_sha256(path) != item.get("sha256"):
            raise ValueError("Artifact hash differs from the capture report")
        rows = torch.load(path, map_location="cpu", weights_only=True)
        if not isinstance(rows, list) or len(rows) != int(item.get("rows", -1)):
            raise ValueError("Artifact row count differs")
        for row in rows:
            validate_artifact_header(row, manifest_sha256)
            index = int(row.get("manifest_index", -1))
            if index in loaded:
                raise ValueError("Duplicate artifact manifest index")
            loaded[index] = row
    return loaded


def validate_capture(report, manifest, expected_checkpoint_sha256):
    if report.get("artifact_contract") != CAPTURE_ARTIFACT_CONTRACT:
        raise ValueError("Wrong capture artifact contract")
    if report.get("native_capture_completed") is not True:
        raise ValueError("Native capture is not complete")
    if report.get("checkpoint_sha256") != expected_checkpoint_sha256:
        raise ValueError("Capture checkpoint differs from M95")
    capture_manifest = report.get("manifest", {})
    if capture_manifest.get("sha256") != EXPECTED_MANIFEST_SHA256:
        raise ValueError("Capture manifest hash differs")
    if int(capture_manifest.get("rows", -1)) != 256:
        raise ValueError("Capture manifest row count differs")
    report_rows = report.get("rows")
    if not isinstance(report_rows, list) or len(report_rows) != 256:
        raise ValueError("Expected 256 capture rows")
    by_index = {}
    for row in report_rows:
        index = int(row.get("manifest_index", -1))
        if index in by_index:
            raise ValueError("Duplicate capture manifest index")
        expected = manifest.get(index)
        if expected is None:
            raise ValueError("Capture manifest index is unexpected")
        if (
            str(row.get("scene")) != str(expected["scene_id"])
            or int(row.get("ann_id")) != int(expected["ann_id"])
            or row.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256
        ):
            raise ValueError("Capture row differs from the frozen manifest")
        by_index[index] = row
    if set(by_index) != set(manifest):
        raise ValueError("Capture row coverage differs")
    return by_index


def analyze_artifacts(
    report,
    manifest,
    artifacts,
    checkpoint_sha256=EXPECTED_CHECKPOINT_SHA256,
    draws=BOOTSTRAP_DRAWS,
):
    report_rows = validate_capture(report, manifest, checkpoint_sha256)
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")
    rows = []
    for index in range(256):
        manifest_row = manifest[index]
        artifact = artifacts[index]
        if artifact.get("manifest_index") != index:
            raise ValueError("Artifact index differs from manifest")
        rows.append(compact_row(artifact, report_rows[index], manifest_row))

    primary = paired_summary(rows, "primary_pair_iou_uplift", draws=draws)
    ci = primary["scene_bootstrap_95ci"]
    primary_pairs = primary["available"]
    independent_scenes = primary["scenes"]
    point_estimate = None if ci is None else ci["point_estimate"]
    ci_lower = None if ci is None else ci["lo"]
    reasons = []
    if primary_pairs < PRIMARY_MIN_PAIRS:
        reasons.append("complete_pairs_below_64")
    if independent_scenes < PRIMARY_MIN_SCENES:
        reasons.append("independent_scenes_below_64")
    if point_estimate is None or point_estimate < PRIMARY_MIN_POINT:
        reasons.append("point_estimate_below_0.05")
    if ci_lower is None or ci_lower <= 0.0:
        reasons.append("scene_bootstrap_lower_bound_not_above_zero")
    supported = not reasons

    strata = {}
    for stratum in ("ambiguous", "class_unique"):
        stratum_rows = [row for row in rows if row["stratum"] == stratum]
        strata[stratum] = {
            "expressions": len(stratum_rows),
            "scenes": len({row["scene_id"] for row in stratum_rows}),
            "primary": paired_summary(
                stratum_rows, "primary_pair_iou_uplift", draws=draws
            ),
        }

    score_differences = [
        row["primary_pair_score_difference"]
        for row in rows
        if row["primary_pair_score_difference"] is not None
    ]
    score_margin = None
    if score_differences:
        score_margin = {
            "available": len(score_differences),
            "mean_absolute_score_difference": (
                sum(abs(value) for value in score_differences)
                / len(score_differences)
            ),
            "max_absolute_score_difference": max(
                abs(value) for value in score_differences
            ),
        }

    return {
        "rows": rows,
        "summary": {
            "expressions": len(rows),
            "scenes": len({row["scene_id"] for row in rows}),
            "strata": strata,
            "selectors": {
                "deployed": selector_summary(rows, "deployed_query"),
                "target_positive": selector_summary(
                    rows, "target_positive_query"
                ),
                "target_objectness": selector_summary(
                    rows, "target_objectness_query"
                ),
                "class_matched_selector": selector_summary(
                    rows, "class_matched_selector_query"
                ),
                "class_matched_non_target": selector_summary(
                    rows, "class_matched_non_target_query"
                ),
            },
            "paired_controls": {
                "target_positive_minus_deployed": paired_summary(
                    rows, "positive_minus_deployed_iou", draws=draws
                ),
                "target_objectness_minus_deployed": paired_summary(
                    rows, "objectness_minus_deployed_iou", draws=draws
                ),
                "class_selector_minus_deployed": paired_summary(
                    rows, "class_selector_minus_deployed_iou", draws=draws
                ),
                "class_non_target_minus_deployed": paired_summary(
                    rows, "class_non_target_minus_deployed_iou", draws=draws
                ),
            },
            "primary_estimand": {
                "name": "scene_balanced_paired_target_iou_uplift",
                "available": primary_pairs,
                "scenes": independent_scenes,
                "pooled_mean": primary["pooled_mean"],
                "scene_balanced_mean": point_estimate,
                "scene_bootstrap_95ci": ci,
                "score_match": score_margin,
                "supported": supported,
                "rejection_reasons": reasons,
            },
            "stage_identity_margins": summarize_stage_identity(rows),
        },
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument(
        "--expected-manifest-sha256",
        default=EXPECTED_MANIFEST_SHA256,
    )
    parser.add_argument(
        "--expected-checkpoint-sha256",
        default=EXPECTED_CHECKPOINT_SHA256,
    )
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.draws <= 0:
        raise ValueError("Bootstrap draws must be positive")
    capture_path = Path(args.capture).resolve()
    output_path = Path(args.output).resolve()
    if not capture_path.is_file():
        raise ValueError("Capture report does not exist")
    if output_path.exists():
        raise ValueError("Refusing to overwrite an analysis output")
    manifest_path = Path(args.manifest).resolve()
    manifest_sha256 = file_sha256(manifest_path)
    manifest = validate_manifest_hash(
        load_json(manifest_path),
        manifest_sha256,
        args.expected_manifest_sha256,
    )
    report = load_json(capture_path)
    artifacts = load_artifacts(capture_path, report, manifest_sha256)
    result = analyze_artifacts(
        report,
        manifest,
        artifacts,
        checkpoint_sha256=args.expected_checkpoint_sha256,
        draws=args.draws,
    )
    result.update(
        {
            "schema_version": 1,
            "contract": ANALYSIS_CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only analysis of the frozen manifest-bound M95 capture. "
                "No model execution, training, queue mutation, admission, or "
                "deployable-efficacy claim."
            ),
            "source_capture": {
                "path": str(capture_path),
                "sha256": file_sha256(capture_path),
                "producer_sha256": report.get("producer_sha256"),
                "checkpoint_sha256": report.get("checkpoint_sha256"),
                "model_source_sha256": report.get("model_source_sha256"),
                "config_sha256": report.get("config_sha256"),
            },
            "manifest": {
                "path": str(manifest_path),
                "sha256": manifest_sha256,
                "rows": len(manifest),
                "contract": MANIFEST_CONTRACT,
            },
            "candidate_handoff": {
                "referent-supervision-axis": "primary_estimand",
                "referent-causality-audit": "primary_estimand",
                "modality-identity-preservation": "stage_identity_margins",
                "referent-discrimination": "class_matched_selector",
                "instance-identity-representation": (
                    "class_matched_non_target_and_stage_identity"
                ),
            },
            "not_evidence_of": [
                "admission",
                "deployable efficacy",
                "population effect",
                "novelty",
                "whole-mechanism benefit",
            ],
        }
    )
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
