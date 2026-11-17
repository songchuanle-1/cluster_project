"""Monte Carlo calibration for the frozen referent permutation control.

This CPU-only simulation validates the statistical behavior of the target-label
permutation test before native capture is available. It measures family-wise
false-positive rate under exchangeable labels and power under a planted
target-specific referent-rank signal.
"""
import argparse
import json
import math
import random
from pathlib import Path

from referent_object_rank_capture_20260919 import (
    build_capture,
    file_sha256,
    stable_sha256,
)
from referent_within_scene_permutation_20260919 import (
    evaluate_permutation_control,
)


SCHEMA_VERSION = 1
ALPHA = 0.05
DEFAULT_SIMULATIONS = 300
DEFAULT_DRAWS = 999
MODEL_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
REFERENT_ENDPOINTS = ("referent_top1", "referent_normalized_excess")


def _wilson_interval(successes, total, z=1.959963984540054):
    if total <= 0:
        raise ValueError("Wilson interval requires a positive sample size")
    proportion = successes / total
    denominator = 1.0 + z * z / total
    center = (proportion + z * z / (2.0 * total)) / denominator
    radius = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return {"low": center - radius, "high": center + radius}


def _registry_for_replicate(rng, replicate):
    rows = []
    for scene_index in range(8):
        scene = f"scene_{scene_index:02d}"
        expression_count = rng.randint(1, 4)
        for expression_slot in range(expression_count):
            object_count = rng.randint(2, 5)
            object_ids = [str(index + 1) for index in range(object_count)]
            target_id = rng.choice(object_ids)
            rows.append({
                "registry_key": (
                    f"{scene}:{replicate}:{expression_slot}:{target_id}"
                ),
                "scene": scene,
                "ann_id": 100000 + replicate * 100 + len(rows),
                "dataset_order": {
                    "step": replicate * 100 + len(rows),
                    "expression_slot": expression_slot,
                },
                "target_object_id": target_id,
                "same_class_candidate_ids": [
                    object_id
                    for object_id in object_ids
                    if object_id != target_id
                ],
                "primary_rank_eligible": True,
            })
    return {
        "schema_version": 1,
        "registry_sha256": stable_sha256(rows),
        "sources": {
            "config": {
                "path": "configs/Quard/example/" + MODEL_CLASS + ".yaml",
                "sha256": "b" * 64,
            },
        },
        "rows": rows,
    }


def _capture_for_replicate(registry, rng, planted):
    expressions = []
    for row in registry["rows"]:
        object_ids = [
            row["target_object_id"],
            *row["same_class_candidate_ids"],
        ]
        object_ids.sort(key=int)
        referent_confidence = {
            object_id: rng.uniform(0.05, 0.95)
            for object_id in object_ids
        }
        if planted:
            competing = [
                referent_confidence[object_id]
                for object_id in object_ids
                if object_id != row["target_object_id"]
            ]
            referent_confidence[row["target_object_id"]] = min(
                0.99,
                max(competing) + 0.20,
            )
        objectness_iou = {
            object_id: rng.uniform(0.05, 0.95)
            for object_id in object_ids
        }

        labels = []
        seed_indices = []
        for object_id in object_ids:
            seed_indices.append(len(labels))
            labels.extend([int(object_id), int(object_id)])
        expressions.append({
            "registry_key": row["registry_key"],
            "scene": row["scene"],
            "target_object_id": row["target_object_id"],
            "native_input_sha256": stable_sha256({
                "registry_key": row["registry_key"],
                "axis": "native_input",
                "planted": planted,
            }),
            "hierarchical_partition_sha256": stable_sha256({
                "registry_key": row["registry_key"],
                "axis": "partition",
            }),
            "instance_labels": labels,
            "query_seed_indices": seed_indices,
            "referent_costs": [
                -referent_confidence[object_id]
                for object_id in object_ids
            ],
            "objectness_costs": [
                1.0 - objectness_iou[object_id]
                for object_id in object_ids
            ],
        })

    binding = {
        "code_commit": "a" * 40,
        "config_sha256": "b" * 64,
        "model_package_sha256": "c" * 64,
        "checkpoint_sha256": "d" * 64,
    }
    return build_capture(registry, expressions, binding)


def _summarize_arm(p_values):
    summary = {}
    for endpoint in p_values[0]:
        successes = sum(
            row[endpoint] <= ALPHA
            for row in p_values
        )
        summary[endpoint] = {
            "rejections": successes,
            "simulations": len(p_values),
            "rejection_rate": successes / len(p_values),
            "rejection_rate_ci95": _wilson_interval(
                successes,
                len(p_values),
            ),
        }
    familywise_successes = sum(
        min(row.values()) <= ALPHA
        for row in p_values
    )
    summary["holm_familywise_any"] = {
        "rejections": familywise_successes,
        "simulations": len(p_values),
        "rejection_rate": familywise_successes / len(p_values),
        "rejection_rate_ci95": _wilson_interval(
            familywise_successes,
            len(p_values),
        ),
    }
    return summary


def run_calibration(simulations=DEFAULT_SIMULATIONS, draws=DEFAULT_DRAWS):
    if (
        isinstance(simulations, bool)
        or not isinstance(simulations, int)
        or simulations <= 0
    ):
        raise ValueError("Simulation count must be a positive integer")
    if isinstance(draws, bool) or not isinstance(draws, int) or draws <= 0:
        raise ValueError("Permutation draws must be a positive integer")

    null_p_values = []
    signal_p_values = []
    pool_sizes = []
    for replicate in range(simulations):
        registry_rng = random.Random(2026091900 + replicate)
        registry = _registry_for_replicate(registry_rng, replicate)
        null_capture = _capture_for_replicate(
            registry,
            random.Random(2026091910 + replicate),
            planted=False,
        )
        signal_capture = _capture_for_replicate(
            registry,
            random.Random(2026091910 + replicate),
            planted=True,
        )
        null_result = evaluate_permutation_control(
            registry,
            null_capture,
            draws=draws,
        )
        signal_result = evaluate_permutation_control(
            registry,
            signal_capture,
            draws=draws,
        )
        null_p_values.append({
            name: value
            for name, value in null_result["holm_adjusted_p_values"].items()
        })
        signal_p_values.append({
            name: value
            for name, value in signal_result["holm_adjusted_p_values"].items()
        })
        pool_sizes.extend(
            len(row["same_class_candidate_ids"]) + 1
            for row in registry["rows"]
        )

    null_summary = _summarize_arm(null_p_values)
    signal_summary = _summarize_arm(signal_p_values)
    familywise_upper = null_summary["holm_familywise_any"][
        "rejection_rate_ci95"
    ]["high"]
    referent_power_passed = all(
        signal_summary[endpoint]["rejection_rate"] >= 0.80
        for endpoint in REFERENT_ENDPOINTS
    )
    objectness_false_positive_passed = (
        signal_summary["objectness_top1"]["rejection_rate"] <= 0.10
    )
    calibration_passed = (
        familywise_upper <= 0.10
        and referent_power_passed
        and objectness_false_positive_passed
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": (
            "CPU-only Monte Carlo calibration of the frozen within-expression "
            "same-class target-permutation control; no model forward, native "
            "capture, training, queue mutation, or efficacy claim"
        ),
        "settings": {
            "simulations": simulations,
            "permutation_draws": draws,
            "alpha": ALPHA,
            "scenes_per_simulation": 8,
            "expressions_per_scene": [1, 4],
            "objects_per_expression": [2, 5],
            "signal_rule": (
                "target referent confidence is set 0.20 above the strongest "
                "competing object before projection to native cost"
            ),
            "primary_referent_endpoints": list(REFERENT_ENDPOINTS),
        },
        "calibration_criteria": {
            "familywise_null_upper_ci95_at_most": 0.10,
            "referent_endpoint_power_at_least": 0.80,
            "objectness_top1_false_positive_rate_at_most": 0.10,
        },
        "cohort": {
            "expressions": len(pool_sizes),
            "scenes": simulations * 8,
            "pool_size_min": min(pool_sizes),
            "pool_size_max": max(pool_sizes),
            "pool_size_mean": sum(pool_sizes) / len(pool_sizes),
        },
        "null": {
            "summary": null_summary,
            "interpretation": (
                "The Holm family-wise rejection rate tests calibration of the "
                "six-endpoint diagnostic family under exchangeable labels."
            ),
        },
        "planted_signal": {
            "summary": signal_summary,
            "interpretation": (
                "Referent endpoints should reject while random objectness "
                "remains near the nominal false-positive rate."
            ),
        },
        "decision": {
            "status": "passed" if calibration_passed else "not_met",
            "referent_power_passed": referent_power_passed,
            "objectness_false_positive_passed": (
                objectness_false_positive_passed
            ),
            "familywise_null_upper_ci95": familywise_upper,
            "consequence": (
                "Permutation p-values may be reported as calibrated "
                "diagnostics on native rank-eligible rows."
                if calibration_passed
                else "Do not interpret permutation p-values below the native "
                "rank contract until the failed calibration criterion is "
                "redesigned."
            ),
        },
        "limitations": [
            "Simulated independent object scores preserve label exchangeability "
            "but do not reproduce native score dependence or geometry.",
            "The planted signal validates directional power, not the native "
            "effect size or biological/visual plausibility.",
            "Calibration is conditional on singleton query pools and no score "
            "ties; native query coverage remains handled by the separate gate.",
            "A passing simulation does not establish native specificity or "
            "target mIoU improvement.",
        ],
    }


def build_report(simulations=DEFAULT_SIMULATIONS, draws=DEFAULT_DRAWS):
    result = run_calibration(simulations=simulations, draws=draws)
    script_dir = Path(__file__).resolve().parent
    source_paths = [
        script_dir / "referent_permutation_calibration_20260919.py",
        script_dir / "referent_within_scene_permutation_20260919.py",
        script_dir / "referent_object_rank_capture_20260919.py",
        script_dir / "referent_target_rank_evaluator_20260919.py",
    ]
    result["source_hashes"] = [
        {
            "path": "scripts/" + path.name,
            "sha256": file_sha256(path),
        }
        for path in source_paths
    ]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--simulations", type=int, default=DEFAULT_SIMULATIONS)
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    args = parser.parse_args()

    report = build_report(
        simulations=args.simulations,
        draws=args.draws,
    )
    output_path = Path(args.output).resolve()
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "output": str(output_path),
        "output_sha256": file_sha256(output_path),
        "null_familywise_rejection_rate": report["null"]["summary"][
            "holm_familywise_any"
        ]["rejection_rate"],
        "referent_power": {
            endpoint: report["planted_signal"]["summary"][endpoint][
                "rejection_rate"
            ]
            for endpoint in REFERENT_ENDPOINTS
        },
        "decision": report["decision"],
    }, indent=2))


if __name__ == "__main__":
    main()
