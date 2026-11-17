"""Within-expression same-class target-permutation control for referent rank.

The frozen registry predeclares a within-scene candidate permutation control.
This CPU-only module replaces the designated target by a uniformly sampled
member of the same expression's predeclared same-class pool. The candidate
scores, scene weights, pool sizes, and query assignments remain unchanged, so
the control measures whether the observed target-specific separation exceeds
an exchangeable-label null without running a model.
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from referent_target_rank_evaluator_20260919 import (
    SCORE_NAMES,
    file_sha256,
    rank_capture_row,
    stable_sha256,
    validate_capture_document,
    validate_registry_document,
)


SCHEMA_VERSION = 1
DEFAULT_DRAWS = 10000
PERMUTATION_UNIT = "target_identity_within_expression_same_class_pool"


def _percentile(values, probability):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot compute a percentile of an empty sample")
    position = probability * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _validated_rows(registry, capture):
    registry_rows = validate_registry_document(registry)
    capture_rows = validate_capture_document(capture, registry)
    valid = []
    rejected = []
    for registry_row in registry_rows:
        if not registry_row["primary_rank_eligible"]:
            continue
        key = registry_row["registry_key"]
        capture_row = capture_rows.get(key)
        if capture_row is None:
            rejected.append({"registry_key": key, "reason": "missing_expression"})
            continue
        try:
            rank_capture_row(capture_row, registry_row)
        except ValueError as exc:
            rejected.append({"registry_key": key, "reason": str(exc)})
            continue

        pool_ids = [
            registry_row["target_object_id"],
            *registry_row["same_class_candidate_ids"],
        ]
        score_maps = {}
        ranks = {}
        for score_name in SCORE_NAMES:
            score_map = capture_row["scores"][score_name]
            score_maps[score_name] = {
                object_id: float(score_map[object_id])
                for object_id in pool_ids
            }
            ordered = sorted(pool_ids, key=lambda object_id: score_maps[score_name][object_id])
            ranks[score_name] = {
                object_id: index + 1 for index, object_id in enumerate(ordered)
            }
        valid.append({
            "registry_key": key,
            "scene": registry_row["scene"],
            "target_object_id": registry_row["target_object_id"],
            "pool_ids": pool_ids,
            "score_maps": score_maps,
            "ranks": ranks,
        })

    if not valid:
        raise ValueError("No expression passed the complete rank contract")
    return valid, rejected


def _scene_balanced(rows, selections, getter):
    by_scene = defaultdict(list)
    for row, selected_id in zip(rows, selections):
        by_scene[row["scene"]].append(float(getter(row, selected_id)))
    scene_means = [
        sum(values) / len(values) for values in by_scene.values()
    ]
    return sum(scene_means) / len(scene_means)


def _assignment_metrics(rows, selections):
    if len(rows) != len(selections):
        raise ValueError("Permutation selection count differs from valid rows")

    metrics = {}
    for score_name in SCORE_NAMES:
        metrics[score_name + "_top1"] = _scene_balanced(
            rows,
            selections,
            lambda row, object_id, name=score_name: (
                row["ranks"][name][object_id] == 1
            ),
        )
        metrics[score_name + "_normalized_excess"] = _scene_balanced(
            rows,
            selections,
            lambda row, object_id, name=score_name: (
                (row["ranks"][name][object_id] - 1)
                / (len(row["pool_ids"]) - 1)
            ),
        )

    metrics["paired_top1_lift"] = (
        metrics["referent_top1"] - metrics["objectness_top1"]
    )
    metrics["paired_normalized_excess_difference"] = (
        metrics["referent_normalized_excess"]
        - metrics["objectness_normalized_excess"]
    )
    return metrics


def _distribution(values):
    return {
        "draws": len(values),
        "mean": sum(values) / len(values),
        "ci95": {
            "low": _percentile(values, 0.025),
            "high": _percentile(values, 0.975),
        },
        "minimum": min(values),
        "maximum": max(values),
    }


def _upper_tail_p(observed, null_values):
    return (
        1 + sum(value >= observed for value in null_values)
    ) / (len(null_values) + 1)


def _lower_tail_p(observed, null_values):
    return (
        1 + sum(value <= observed for value in null_values)
    ) / (len(null_values) + 1)


def _holm_adjust(p_values):
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted = {}
    running = 0.0
    total = len(ordered)
    for index, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (total - index) * value))
        adjusted[name] = running
    return adjusted


def evaluate_permutation_control(registry, capture, draws=DEFAULT_DRAWS):
    if isinstance(draws, bool) or not isinstance(draws, int) or draws <= 0:
        raise ValueError("Permutation draws must be a positive integer")

    rows, rejected = _validated_rows(registry, capture)
    observed = _assignment_metrics(
        rows,
        [row["target_object_id"] for row in rows],
    )

    seed_material = stable_sha256({
        "registry_sha256": registry["registry_sha256"],
        "capture": capture,
        "draws": draws,
        "unit": PERMUTATION_UNIT,
    })
    rng = random.Random(int(seed_material[:16], 16))
    null_rows = []
    for _ in range(draws):
        selections = [
            row["pool_ids"][rng.randrange(len(row["pool_ids"]))]
            for row in rows
        ]
        null_rows.append(_assignment_metrics(rows, selections))

    metric_names = list(observed)
    null_distribution = {
        name: _distribution([row[name] for row in null_rows])
        for name in metric_names
    }
    raw_p_values = {
        "referent_top1": _upper_tail_p(
            observed["referent_top1"],
            [row["referent_top1"] for row in null_rows],
        ),
        "objectness_top1": _upper_tail_p(
            observed["objectness_top1"],
            [row["objectness_top1"] for row in null_rows],
        ),
        "referent_normalized_excess": _lower_tail_p(
            observed["referent_normalized_excess"],
            [row["referent_normalized_excess"] for row in null_rows],
        ),
        "objectness_normalized_excess": _lower_tail_p(
            observed["objectness_normalized_excess"],
            [row["objectness_normalized_excess"] for row in null_rows],
        ),
        "paired_top1_lift": _upper_tail_p(
            observed["paired_top1_lift"],
            [row["paired_top1_lift"] for row in null_rows],
        ),
        "paired_normalized_excess_difference": _lower_tail_p(
            observed["paired_normalized_excess_difference"],
            [row["paired_normalized_excess_difference"] for row in null_rows],
        ),
    }
    return {
        "contract": {
            "permutation_unit": PERMUTATION_UNIT,
            "replacement_distribution": (
                "uniform over the target plus every predeclared same-class "
                "candidate in the same expression"
            ),
            "shared_assignment_across_scores": True,
            "scene_balance": "equal scene means after target replacement",
            "p_value_rule": (
                "upper tail for top1 and paired top1 lift; lower tail for "
                "normalized excess and paired normalized-excess difference"
            ),
            "multiplicity": "Holm adjustment over six diagnostic p-values",
            "seed_sha256": seed_material,
            "draws": draws,
        },
        "cohort": {
            "complete_rank_eligible_expressions": len(rows),
            "complete_scenes": len({row["scene"] for row in rows}),
            "rejected_rank_eligible_expressions": len(rejected),
            "pool_size_min": min(len(row["pool_ids"]) for row in rows),
            "pool_size_max": max(len(row["pool_ids"]) for row in rows),
        },
        "observed": observed,
        "null_distribution": null_distribution,
        "p_values": raw_p_values,
        "holm_adjusted_p_values": _holm_adjust(raw_p_values),
        "rejected": rejected,
    }


def build_report(registry, capture, registry_path, capture_path, draws=DEFAULT_DRAWS):
    result = evaluate_permutation_control(registry, capture, draws=draws)
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": (
            "CPU-only within-expression same-class target-permutation control "
            "for referent target rank; no model forward, imputation, queue "
            "mutation, or efficacy claim"
        ),
        "inputs": {
            "registry": {
                "path": str(registry_path),
                "sha256": file_sha256(registry_path),
            },
            "capture": {
                "path": str(capture_path),
                "sha256": file_sha256(capture_path),
            },
        },
        "binding": capture["binding"],
        "control": result,
        "limitations": [
            "The null is conditional on the frozen registry and complete score "
            "maps; rejected expressions are excluded without imputation.",
            "Independent uniform target replacement is a specificity control, "
            "not a model of geometric difficulty or query independence.",
            "Monte Carlo p-values have resolution 1/(draws+1) and are "
            "diagnostic only.",
            "No native scores or mIoU evidence exist in a synthetic artifact.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    args = parser.parse_args()

    registry_path = Path(args.registry).resolve()
    capture_path = Path(args.capture).resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    report = build_report(
        registry,
        capture,
        registry_path=registry_path,
        capture_path=capture_path,
        draws=args.draws,
    )
    output_path = Path(args.output).resolve()
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "cohort": report["control"]["cohort"],
        "observed": report["control"]["observed"],
        "holm_adjusted_p_values": (
            report["control"]["holm_adjusted_p_values"]
        ),
        "output_sha256": file_sha256(output_path),
    }, indent=2))


if __name__ == "__main__":
    main()
