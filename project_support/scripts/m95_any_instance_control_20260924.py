"""Scene-balanced any-instance control over the M95 identity-control replay."""

import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_CONTRACT = "m95_manifest_identity_control_analysis_v1"
OUTPUT_CONTRACT = "m95_any_instance_selector_control_v1"
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 1999


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score_pick(scores, allowed):
    if len(scores) != len(allowed):
        raise ValueError("Scores and selector support differ")
    indices = [index for index, value in enumerate(allowed) if value]
    if not indices:
        return None
    return max(indices, key=lambda index: (scores[index], -index))


def _validate_number(value, label):
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise ValueError(label + " must be finite numeric")
    return float(value)


def _selector_summary(rows, selector_key):
    successes = []
    by_scene = defaultdict(list)
    for row in rows:
        selected = row.get(selector_key)
        if selected is None:
            continue
        success = float(row["ious"][selected] > 0.5)
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


def _bootstrap_scene_mean(values_by_scene, draws, seed):
    scene_values = [
        sum(values) / len(values) for values in values_by_scene.values()
    ]
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


def _paired_summary(rows, value_key, draws, seed):
    values = []
    by_scene = defaultdict(list)
    for row in rows:
        value = row.get(value_key)
        if value is None:
            continue
        value = _validate_number(value, value_key)
        values.append(value)
        by_scene[str(row["scene_id"])].append(value)
    if not values:
        return {
            "available": 0,
            "scenes": 0,
            "pooled_mean": None,
            "scene_bootstrap_95ci": None,
        }
    return {
        "available": len(values),
        "scenes": len(by_scene),
        "pooled_mean": sum(values) / len(values),
        "scene_bootstrap_95ci": _bootstrap_scene_mean(
            by_scene, draws=draws, seed=seed
        ),
    }


def analyze_rows(rows, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    if not rows:
        raise ValueError("Analysis has no rows")
    enriched = []
    for row in rows:
        scores = [
            _validate_number(value, "score") for value in row.get("scores", [])
        ]
        ious = [
            _validate_number(value, "IoU") for value in row.get("ious", [])
        ]
        dominant = row.get("dominant_instance")
        if not scores or len(scores) != len(ious) or len(scores) != len(dominant):
            raise ValueError("Query score, IoU and dominant-instance axes differ")
        any_instance_query = score_pick(
            scores, [value is not None for value in dominant]
        )
        if any_instance_query is None:
            raise ValueError("Row has no query dominating an instance")
        deployed_query = row.get("deployed_query")
        target_positive_query = row.get("target_positive_query")
        if type(deployed_query) is not int or not 0 <= deployed_query < len(scores):
            raise ValueError("Invalid deployed query")
        if target_positive_query is not None and (
            type(target_positive_query) is not int
            or not 0 <= target_positive_query < len(scores)
        ):
            raise ValueError("Invalid target-positive query")
        enriched.append(
            {
                **row,
                "any_instance_query": any_instance_query,
                "any_instance_iou": ious[any_instance_query],
                "any_instance_minus_deployed_iou": (
                    ious[any_instance_query] - ious[deployed_query]
                ),
                "target_positive_minus_any_instance_iou": (
                    None
                    if target_positive_query is None
                    else ious[target_positive_query] - ious[any_instance_query]
                ),
            }
        )

    changed = sum(
        row["any_instance_query"] != row["deployed_query"] for row in enriched
    )
    return {
        "expressions": len(enriched),
        "scenes": len({str(row["scene_id"]) for row in enriched}),
        "selector_changed_rows": changed,
        "selectors": {
            "deployed": _selector_summary(enriched, "deployed_query"),
            "any_instance": _selector_summary(enriched, "any_instance_query"),
            "target_positive": _selector_summary(enriched, "target_positive_query"),
        },
        "paired_controls": {
            "any_instance_minus_deployed": _paired_summary(
                enriched,
                "any_instance_minus_deployed_iou",
                draws=draws,
                seed=seed,
            ),
            "target_positive_minus_any_instance": _paired_summary(
                enriched,
                "target_positive_minus_any_instance_iou",
                draws=draws,
                seed=seed,
            ),
        },
    }


def analyze_document(document, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    if document.get("contract") != ANALYSIS_CONTRACT:
        raise ValueError("Wrong identity-control analysis contract")
    return analyze_rows(document.get("rows"), draws=draws, seed=seed)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, default=BOOTSTRAP_DRAWS)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.draws <= 0:
        raise ValueError("Bootstrap draws must be positive")
    analysis_path = Path(args.analysis).resolve()
    output_path = Path(args.output).resolve()
    if not analysis_path.is_file():
        raise ValueError("Identity-control analysis does not exist")
    if output_path.exists():
        raise ValueError("Refusing to overwrite an analysis output")
    document = json.loads(analysis_path.read_text(encoding="utf-8"))
    result = analyze_document(document, draws=args.draws, seed=args.seed)
    result.update(
        {
            "schema_version": 1,
            "contract": OUTPUT_CONTRACT,
            "scope": (
                "CPU-only negative control over frozen M95 identity-control "
                "rows. No model execution, training, queue mutation, admission "
                "or deployable efficacy claim."
            ),
            "source_analysis": {
                "path": str(analysis_path),
                "sha256": file_sha256(analysis_path),
            },
            "selector_contract": {
                "any_instance": (
                    "highest frozen score among queries whose dominant "
                    "physical instance is non-null; score ties use lower index"
                ),
                "target_positive": (
                    "highest frozen score among native matcher positives"
                ),
            },
            "not_evidence_of": [
                "admission",
                "native backward",
                "resource gate",
                "deployable efficacy",
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
