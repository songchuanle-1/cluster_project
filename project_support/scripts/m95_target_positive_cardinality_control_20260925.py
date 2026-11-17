"""Cardinality-matched placebo control for M95 target-positive selection."""

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path


ANALYSIS_CONTRACT = "m95_manifest_identity_control_analysis_v1"
OUTPUT_CONTRACT = "m95_target_positive_cardinality_control_v1"
BOOTSTRAP_DRAWS = 10000
RANDOM_DRAWS = 2000
SEED = 1999


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_number(value, label):
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise ValueError(label + " must be finite numeric")
    return float(value)


def score_pick(scores, indices):
    if not indices:
        return None
    return max(indices, key=lambda index: (scores[index], -index))


def scene_balanced(values):
    by_scene = defaultdict(list)
    for scene_id, value in values:
        by_scene[str(scene_id)].append(value)
    if not by_scene:
        return None
    rates = [sum(items) / len(items) for items in by_scene.values()]
    return sum(rates) / len(rates)


def bootstrap_scene_mean(values, draws, seed):
    by_scene = defaultdict(list)
    for scene_id, value in values:
        by_scene[str(scene_id)].append(value)
    scene_values = [sum(items) / len(items) for items in by_scene.values()]
    if not scene_values:
        raise ValueError("No scene values for bootstrap")
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


def summarize_selector(rows, field):
    values = [
        (row["scene_id"], float(row[field] > 0.5))
        for row in rows
        if row.get(field) is not None
    ]
    ious = [
        row[field]
        for row in rows
        if row.get(field) is not None
    ]
    if not values:
        return {
            "available": 0,
            "scenes": 0,
            "success_rate": None,
            "scene_balanced_success": None,
            "mean_iou": None,
        }
    return {
        "available": len(values),
        "scenes": len({str(scene) for scene, _ in values}),
        "success_rate": sum(value for _, value in values) / len(values),
        "scene_balanced_success": scene_balanced(values),
        "mean_iou": sum(ious) / len(ious),
    }


def summarize_paired(rows, field, draws=BOOTSTRAP_DRAWS, seed=SEED):
    values = [
        (row["scene_id"], finite_number(row[field], field))
        for row in rows
        if row.get(field) is not None
    ]
    if not values:
        return {
            "available": 0,
            "scenes": 0,
            "pooled_mean": None,
            "scene_bootstrap_95ci": None,
        }
    return {
        "available": len(values),
        "scenes": len({str(scene) for scene, _ in values}),
        "pooled_mean": sum(value for _, value in values) / len(values),
        "scene_bootstrap_95ci": bootstrap_scene_mean(values, draws, seed),
    }


def analyze_rows(
    rows,
    random_draws=RANDOM_DRAWS,
    bootstrap_draws=BOOTSTRAP_DRAWS,
    seed=SEED,
):
    if not rows:
        raise ValueError("Analysis has no rows")
    if random_draws <= 0 or bootstrap_draws <= 0:
        raise ValueError("Draw counts must be positive")

    rng = random.Random(seed)
    enriched = []
    for row in rows:
        scores = [finite_number(value, "score") for value in row.get("scores", [])]
        ious = [finite_number(value, "IoU") for value in row.get("ious", [])]
        positive = row.get("native_positive")
        if not scores or len(scores) != len(ious):
            raise ValueError("Query score and IoU axes differ")
        if not isinstance(positive, list) or len(positive) != len(scores):
            raise ValueError("Native-positive axis differs")
        if any(type(value) is not bool for value in positive):
            raise ValueError("Native-positive flags must be boolean")

        positive_indices = [index for index, value in enumerate(positive) if value]
        if not positive_indices:
            raise ValueError("Row has no native-positive query")
        if len(positive_indices) > len(scores):
            raise ValueError("Positive cardinality exceeds candidate universe")

        native_query = score_pick(scores, positive_indices)
        topk_query = score_pick(
            scores,
            sorted(range(len(scores)), key=lambda index: (-scores[index], index))[
                : len(positive_indices)
            ],
        )
        random_ious = []
        native_ge_random = 0
        native_gt_random = 0
        native_eq_random = 0
        for _ in range(random_draws):
            sampled = rng.sample(range(len(scores)), len(positive_indices))
            selected = score_pick(scores, sampled)
            value = ious[selected]
            random_ious.append(value)
            native_ge_random += int(ious[native_query] >= value)
            native_gt_random += int(ious[native_query] > value)
            native_eq_random += int(ious[native_query] == value)
        random_mean_iou = sum(random_ious) / len(random_ious)
        random_mean_success = (
            sum(value > 0.5 for value in random_ious) / len(random_ious)
        )
        positive_quantile = (
            native_gt_random + 0.5 * native_eq_random
        ) / len(random_ious)

        enriched.append(
            {
                "manifest_index": int(row["manifest_index"]),
                "scene_id": str(row["scene_id"]),
                "positive_cardinality": len(positive_indices),
                "native_query": native_query,
                "native_iou": ious[native_query],
                "native_success": float(ious[native_query] > 0.5),
                "topk_query": topk_query,
                "topk_iou": ious[topk_query],
                "topk_success": float(ious[topk_query] > 0.5),
                "random_mean_iou": random_mean_iou,
                "random_mean_success": random_mean_success,
                "native_minus_topk_iou": ious[native_query] - ious[topk_query],
                "native_minus_random_mean_iou": ious[native_query] - random_mean_iou,
                "native_success_minus_random_mean": (
                    float(ious[native_query] > 0.5) - random_mean_success
                ),
                "positive_set_quantile": positive_quantile,
            }
        )

    changed = sum(row["native_query"] != row["topk_query"] for row in enriched)
    return {
        "expressions": len(enriched),
        "scenes": len({str(row["scene_id"]) for row in enriched}),
        "topk_selector_changed_rows": changed,
        "positive_cardinality": {
            "minimum": min(row["positive_cardinality"] for row in enriched),
            "maximum": max(row["positive_cardinality"] for row in enriched),
            "mean": sum(row["positive_cardinality"] for row in enriched)
            / len(enriched),
        },
        "selectors": {
            "native_positive_top_score": summarize_selector(enriched, "native_iou"),
            "same_cardinality_top_score": summarize_selector(enriched, "topk_iou"),
            "random_mean_iou": {
                "available": len(enriched),
                "scenes": len({str(row["scene_id"]) for row in enriched}),
                "mean_iou": sum(row["random_mean_iou"] for row in enriched)
                / len(enriched),
                "mean_success": sum(
                    row["random_mean_success"] for row in enriched
                )
                / len(enriched),
            },
        },
        "paired_controls": {
            "native_positive_minus_topk": summarize_paired(
                enriched,
                "native_minus_topk_iou",
                draws=bootstrap_draws,
                seed=seed,
            ),
            "native_positive_minus_random_mean": summarize_paired(
                enriched,
                "native_minus_random_mean_iou",
                draws=bootstrap_draws,
                seed=seed,
            ),
            "native_success_minus_random_mean": summarize_paired(
                enriched,
                "native_success_minus_random_mean",
                draws=bootstrap_draws,
                seed=seed,
            ),
        },
        "positive_set_quantile": {
            "mean": sum(row["positive_set_quantile"] for row in enriched)
            / len(enriched),
            "native_strictly_above_random_rate": sum(
                row["positive_set_quantile"] == 1.0 for row in enriched
            )
            / len(enriched),
            "native_at_or_below_random_median_rate": sum(
                row["positive_set_quantile"] <= 0.5 for row in enriched
            )
            / len(enriched),
        },
        "random_control": {
            "draws_per_expression": random_draws,
            "seed": seed,
            "sampling": "uniform without replacement from all query indices",
            "cardinality": "exactly the native-positive query count",
            "selection": "highest frozen score inside the sampled subset",
        },
    }


def analyze_document(
    document,
    random_draws=RANDOM_DRAWS,
    bootstrap_draws=BOOTSTRAP_DRAWS,
    seed=SEED,
):
    if document.get("contract") != ANALYSIS_CONTRACT:
        raise ValueError("Wrong identity-control analysis contract")
    return analyze_rows(
        document.get("rows"),
        random_draws=random_draws,
        bootstrap_draws=bootstrap_draws,
        seed=seed,
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--random-draws", type=int, default=RANDOM_DRAWS)
    parser.add_argument("--bootstrap-draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args()


def main():
    args = parse_args()
    analysis_path = Path(args.analysis).resolve()
    output_path = Path(args.output).resolve()
    if not analysis_path.is_file():
        raise ValueError("Identity-control analysis does not exist")
    if output_path.exists():
        raise ValueError("Refusing to overwrite an analysis output")
    document = json.loads(analysis_path.read_text(encoding="utf-8"))
    result = analyze_document(
        document,
        random_draws=args.random_draws,
        bootstrap_draws=args.bootstrap_draws,
        seed=args.seed,
    )
    result.update(
        {
            "schema_version": 1,
            "contract": OUTPUT_CONTRACT,
            "scope": (
                "CPU-only cardinality-matched placebo control over frozen M95 "
                "identity-control rows. No model execution, native backward, "
                "training, resource, admission or deployable efficacy claim."
            ),
            "source_analysis": {
                "path": str(analysis_path),
                "sha256": file_sha256(analysis_path),
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
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
