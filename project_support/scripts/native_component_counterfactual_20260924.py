"""Replay native M95 captures into matched mask/score component arms.

This is a CPU-only post-capture diagnostic. It does not train, mutate the
queue, or admit a mechanism.
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    as_list,
    file_sha256,
    float_list,
    int_list,
    load_artifacts,
    load_json,
    validate_artifact_header,
    validate_capture,
    validate_manifest_hash,
)
from m95_score_component_control_20260924 import compare


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
ANALYSIS_CONTRACT = "m95_native_component_counterfactual_v1"
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999


def _mean_pair_value(result, key):
    rows = result["pairs"]
    if not rows:
        raise ValueError("Component replay has no matched pairs")
    return sum(float(row[key]) for row in rows) / len(rows)


def component_arms(result):
    """Build original, mask-only, label-only and coupled loss arms."""
    if result.get("score_mse") is None or result.get("indicator_loss") is None:
        raise ValueError("Native component replay requires scores")
    original_mask = (
        _mean_pair_value(result, "original_bce")
        + _mean_pair_value(result, "original_dice")
    )
    corrected_mask = (
        _mean_pair_value(result, "corrected_bce")
        + _mean_pair_value(result, "corrected_dice")
    )
    original_score = float(result["score_mse"]["original"])
    corrected_score = float(result["score_mse"]["corrected"])
    indicator = float(result["indicator_loss"]["per_matched_pair"])
    arms = {
        "original": {
            "mask": original_mask,
            "score": original_score,
            "indicator": indicator,
            "total": original_mask + original_score + indicator,
        },
        "mask_only": {
            "mask": corrected_mask,
            "score": original_score,
            "indicator": indicator,
            "total": corrected_mask + original_score + indicator,
        },
        "label_only": {
            "mask": original_mask,
            "score": corrected_score,
            "indicator": indicator,
            "total": original_mask + corrected_score + indicator,
        },
        "coupled": {
            "mask": corrected_mask,
            "score": corrected_score,
            "indicator": indicator,
            "total": corrected_mask + corrected_score + indicator,
        },
    }
    return {
        "arms": arms,
        "deltas": {
            "mask_only_mask_harm": original_mask - corrected_mask,
            "label_only_score_harm": original_score - corrected_score,
            "coupled_mask_harm": original_mask - corrected_mask,
            "coupled_score_harm": original_score - corrected_score,
            "coupled_total_harm": (
                arms["original"]["total"] - arms["coupled"]["total"]
            ),
            "indicator_change": (
                arms["original"]["indicator"] - arms["coupled"]["indicator"]
            ),
        },
    }


def _query_masks(artifact):
    masks = [
        [bool(value) for value in as_list(row)]
        for row in as_list(artifact.get("query_masks"))
    ]
    if not masks:
        raise ValueError("Artifact has no query masks")
    return masks


def _query_logits(artifact):
    logits = [
        float_list(row, "query mask logits")
        for row in as_list(artifact.get("query_mask_logits"))
    ]
    if not logits:
        raise ValueError("Artifact has no query mask logits")
    return logits


def _native_pairs(row):
    cause = row.get("native_match_cause")
    if not isinstance(cause, dict):
        raise ValueError("Native matcher causes are missing")
    raw_pairs = cause.get("matched_query_gt_pairs")
    if not isinstance(raw_pairs, list) or not raw_pairs:
        raise ValueError("Native matched pairs are missing")
    pairs = []
    for pair in raw_pairs:
        if (
            not isinstance(pair, list)
            or len(pair) != 2
            or any(type(value) is not int for value in pair)
        ):
            raise ValueError("Native matched pair is invalid")
        pairs.append((pair[0], pair[1]))
    return pairs


def analyze_expression(artifact, capture_row, manifest_row, manifest_sha256):
    validate_artifact_header(artifact, manifest_sha256)
    index = int(manifest_row["manifest_index"])
    if int(artifact.get("manifest_index", -1)) != index:
        raise ValueError("Artifact index differs from manifest")
    if int(capture_row.get("manifest_index", -1)) != index:
        raise ValueError("Capture index differs from manifest")
    if (
        str(capture_row.get("scene")) != str(manifest_row["scene_id"])
        or int(capture_row.get("ann_id")) != int(manifest_row["ann_id"])
    ):
        raise ValueError("Capture expression differs from manifest")

    scores = float_list(artifact.get("query_scores"), "query scores")
    report_scores = float_list(capture_row.get("scores"), "report scores")
    if len(scores) != len(report_scores):
        raise ValueError("Artifact and report score axes differ")
    if any(abs(left - right) > 1e-7 for left, right in zip(scores, report_scores)):
        raise ValueError("Artifact and report scores differ")

    logits = _query_logits(artifact)
    masks = _query_masks(artifact)
    if len(logits) != len(scores) or len(masks) != len(scores):
        raise ValueError("Artifact query axes differ")
    if any(len(row) != len(masks[0]) for row in masks + logits):
        raise ValueError("Artifact query support differs")
    if any(
        bool(logit > 0.0) != mask
        for logit_row, mask_row in zip(logits, masks)
        for logit, mask in zip(logit_row, mask_row)
    ):
        raise ValueError("Artifact logits and masks disagree")

    labels = int_list(
        artifact.get("physical_instance_labels"), "physical instance labels"
    )
    if len(labels) != len(masks[0]):
        raise ValueError("Artifact labels differ from query support")
    cause = capture_row["native_match_cause"]
    object_ids = int_list(cause.get("object_ids"), "native object IDs")
    if len(set(object_ids)) != len(object_ids):
        raise ValueError("Native object IDs are duplicated")
    gt_masks = [
        [label == object_id for label in labels]
        for object_id in object_ids
    ]
    pairs = _native_pairs(capture_row)
    result = compare(pairs, gt_masks, logits, scores)
    arms = component_arms(result)

    return {
        "manifest_index": index,
        "scene_id": str(manifest_row["scene_id"]),
        "ann_id": int(manifest_row["ann_id"]),
        "stratum": str(manifest_row["stratum"]),
        "query_count": len(scores),
        "gt_count": len(object_ids),
        "pair_count": result["pair_count"],
        "identity_mismatch_pairs": result["identity_mismatch_pairs"],
        "changed_mask_pairs": result["changed_mask_pairs"],
        "score_filter_crossings": result["score_filter_crossings"],
        "original_score_eligible_pairs": result["score_mse"][
            "original_eligible_pairs"
        ],
        "corrected_score_eligible_pairs": result["score_mse"][
            "corrected_eligible_pairs"
        ],
        "arms": arms["arms"],
        "deltas": arms["deltas"],
    }


def _scene_balanced(rows, key):
    values_by_scene = defaultdict(list)
    values = []
    for row in rows:
        value = row["deltas"].get(key)
        if value is None:
            continue
        value = float(value)
        values.append(value)
        values_by_scene[row["scene_id"]].append(value)
    if not values:
        return {
            "available_expressions": 0,
            "scenes": 0,
            "pooled_mean": None,
            "scene_balanced_mean": None,
        }
    scene_means = [
        sum(scene_values) / len(scene_values)
        for scene_values in values_by_scene.values()
    ]
    return {
        "available_expressions": len(values),
        "scenes": len(values_by_scene),
        "pooled_mean": sum(values) / len(values),
        "scene_balanced_mean": sum(scene_means) / len(scene_means),
    }


def _bootstrap_scene_mean(rows, key, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    values_by_scene = defaultdict(list)
    for row in rows:
        value = row["deltas"].get(key)
        if value is not None:
            values_by_scene[row["scene_id"]].append(float(value))
    if not values_by_scene:
        return None
    scene_values = [
        sum(values) / len(values)
        for values in values_by_scene.values()
    ]
    rng = random.Random(seed)
    sampled = sorted(
        sum(rng.choices(scene_values, k=len(scene_values))) / len(scene_values)
        for _ in range(draws)
    )
    return {
        "draws": draws,
        "seed": seed,
        "unit": "scene",
        "point_estimate": sum(scene_values) / len(scene_values),
        "scene_count": len(scene_values),
        "lo": sampled[int(0.025 * (draws - 1))],
        "hi": sampled[int(0.975 * (draws - 1))],
    }


def summarize(rows, draws=BOOTSTRAP_DRAWS):
    if not rows:
        raise ValueError("No expressions were replayed")
    if len({row["manifest_index"] for row in rows}) != len(rows):
        raise ValueError("Replay contains duplicate manifest rows")
    metrics = {}
    for key in (
        "mask_only_mask_harm",
        "label_only_score_harm",
        "coupled_mask_harm",
        "coupled_score_harm",
        "coupled_total_harm",
        "indicator_change",
    ):
        metrics[key] = _scene_balanced(rows, key)
    metrics["coupled_total_harm"]["scene_bootstrap_95ci"] = (
        _bootstrap_scene_mean(rows, "coupled_total_harm", draws=draws)
    )
    pair_count = sum(row["pair_count"] for row in rows)
    return {
        "expressions": len(rows),
        "scenes": len({row["scene_id"] for row in rows}),
        "pair_count": pair_count,
        "rows_with_identity_mismatch": sum(
            row["identity_mismatch_pairs"] > 0 for row in rows
        ),
        "identity_mismatch_pairs": sum(
            row["identity_mismatch_pairs"] for row in rows
        ),
        "rows_with_changed_mask": sum(
            row["changed_mask_pairs"] > 0 for row in rows
        ),
        "changed_mask_pairs": sum(
            row["changed_mask_pairs"] for row in rows
        ),
        "score_filter_crossings": sum(
            row["score_filter_crossings"] for row in rows
        ),
        "original_score_eligible_pairs": sum(
            row["original_score_eligible_pairs"] for row in rows
        ),
        "corrected_score_eligible_pairs": sum(
            row["corrected_score_eligible_pairs"] for row in rows
        ),
        "metrics": metrics,
    }


def analyze_capture(report, manifest, artifacts, draws=BOOTSTRAP_DRAWS):
    report_rows = validate_capture(
        report, manifest, EXPECTED_CHECKPOINT_SHA256
    )
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")
    rows = [
        analyze_expression(
            artifacts[index],
            report_rows[index],
            manifest[index],
            EXPECTED_MANIFEST_SHA256,
        )
        for index in range(256)
    ]
    return {"rows": rows, "summary": summarize(rows, draws=draws)}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument(
        "--expected-manifest-sha256",
        default=EXPECTED_MANIFEST_SHA256,
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
    result = analyze_capture(
        report, manifest, artifacts, draws=args.draws
    )
    result.update(
        {
            "schema_version": 1,
            "contract": ANALYSIS_CONTRACT,
            "scope": (
                "CPU-only matched-arm replay of one native M95 capture. "
                "No model execution, native backward, resource measurement, "
                "training, queue mutation, admission, or efficacy claim."
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
            },
            "arm_contract": {
                "mask_only": (
                    "correct repeated-GT masks for BCE/Dice; retain native "
                    "hard-IoU score targets and eligibility"
                ),
                "label_only": (
                    "retain native masks for BCE/Dice; correct hard-IoU score "
                    "targets and eligibility"
                ),
                "coupled": "correct both mask and score-target components",
                "positive_delta": "original loss minus intervention loss",
            },
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
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
