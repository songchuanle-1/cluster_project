"""Run the frozen native referent chain on a synthetic self-test fixture.

This is CPU-only contract evidence. It verifies that the native expression
producer, object-rank capture builder, rank evaluator, and query-cost audit
compose without manual adaptation when the GPU capture becomes available.
"""
import argparse
import json
import math
from datetime import datetime
from pathlib import Path

from referent_native_expression_producer_20260919 import (
    MODEL_CLASS,
    OBJECTNESS_SEMANTICS,
    frozen_capture_producer_sha256,
    native_capture_binding,
    produce_expression_inputs,
)
from referent_object_rank_capture_20260919 import (
    build_capture,
    file_sha256,
    stable_sha256,
)
from referent_query_coverage_control_20260919 import audit_capture
from referent_target_rank_evaluator_20260919 import evaluate_capture
from referent_within_scene_permutation_20260919 import (
    evaluate_permutation_control,
)


def synthetic_registry():
    rows = [
        {
            "registry_key": "sceneA:0:10",
            "scene": "sceneA",
            "ann_id": 10,
            "dataset_order": {"step": 0, "expression_slot": 0},
            "target_object_id": "1",
            "same_class_candidate_ids": ["2", "3"],
            "primary_rank_eligible": True,
        },
        {
            "registry_key": "sceneB:0:11",
            "scene": "sceneB",
            "ann_id": 11,
            "dataset_order": {"step": 1, "expression_slot": 0},
            "target_object_id": "4",
            "same_class_candidate_ids": ["5", "6"],
            "primary_rank_eligible": True,
        },
    ]
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


def synthetic_native_capture():
    return {
        "native_capture_completed": True,
        "model_class": MODEL_CLASS,
        "producer_sha256": frozen_capture_producer_sha256(),
        "config_path": "configs/Quard/example/" + MODEL_CLASS + ".yaml",
        "config_sha256": "b" * 64,
        "model_source_sha256": "c" * 64,
        "checkpoint_sha256": "d" * 64,
        "rows": [
            {
                "scene": "sceneA",
                "ann_id": 10,
                "dataset_index": 0,
                "expression_slot": 0,
                "native_input_sha256": "1" * 64,
                "hierarchical_partition_sha256": "2" * 64,
                "instance_labels": [1, 1, 2, 2, 3, 3],
                "original_superpoint_ids": [0, 1, 2, 3, 4, 5],
                "fps_superpoints": [4, 0, 2],
                "sampled_seed_indices": [1, 2, 0],
                "scores": [0.2, 0.1, 0.3],
                "ious": [0.7, 0.6, 0.5],
                "objectness_scores": [0.7, 0.6, 0.5],
                "objectness_score_semantics": OBJECTNESS_SEMANTICS,
            },
            {
                "scene": "sceneB",
                "ann_id": 11,
                "dataset_index": 1,
                "expression_slot": 0,
                "native_input_sha256": "3" * 64,
                "hierarchical_partition_sha256": "4" * 64,
                "instance_labels": [4, 4, 5, 5, 6, 6],
                "original_superpoint_ids": [0, 1, 2, 3, 4, 5],
                "fps_superpoints": [2, 4, 0],
                "sampled_seed_indices": [2, 0, 1],
                "scores": [0.4, 0.2, 0.5],
                "ious": [0.8, 0.7, 0.6],
                "objectness_scores": [0.8, 0.7, 0.6],
                "objectness_score_semantics": OBJECTNESS_SEMANTICS,
            },
        ],
    }


def run_selftest():
    script_dir = Path(__file__).resolve().parent
    producer_path = script_dir / "referent_native_expression_producer_20260919.py"
    registry = synthetic_registry()
    native_capture = synthetic_native_capture()
    expression_rows = produce_expression_inputs(native_capture, registry)
    binding = native_capture_binding(
        native_capture,
        registry,
        "a" * 40,
    )
    capture = build_capture(registry, expression_rows, binding)
    rank_summary = evaluate_capture(registry, capture)
    coverage_summary = audit_capture(registry, capture)
    permutation_control = evaluate_permutation_control(
        registry,
        capture,
        draws=2048,
    )

    referent_rank = rank_summary["rows"][0]["scores"]["referent"]["rank"]
    objectness_rank = rank_summary["rows"][0]["scores"]["objectness"]["rank"]
    selection = coverage_summary["selection_verification"]
    gate_status = coverage_summary["coverage_admission_gate"]["status"]
    target_costs = capture["rows"][0]["native_query_costs"]["1"]

    checks = [
        {
            "name": "native_projection",
            "passed": len(expression_rows) == 2,
            "expressions": len(expression_rows),
        },
        {
            "name": "binding_provenance",
            "passed": (
                binding["config_sha256"]
                == native_capture["config_sha256"]
                and binding["model_package_sha256"]
                == native_capture["model_source_sha256"]
                and binding["checkpoint_sha256"]
                == native_capture["checkpoint_sha256"]
                and native_capture["producer_sha256"]
                == frozen_capture_producer_sha256()
            ),
            "binding": binding,
        },
        {
            "name": "rank_evaluator_compatibility",
            "passed": referent_rank == 2 and objectness_rank == 1,
            "referent_target_rank": referent_rank,
            "objectness_target_rank": objectness_rank,
        },
        {
            "name": "coverage_gate",
            "passed": gate_status == "passed",
            "status": gate_status,
        },
        {
            "name": "query_cost_provenance",
            "passed": (
                selection["verified_expressions"] == 2
                and selection["global_query_axes_verified"] is True
                and selection["selected_cost_equals_native_score"] is True
                and selection["selected_query_is_minimum"] is True
                and target_costs["referent"] == [-0.2]
                and len(target_costs["objectness"]) == 1
                and math.isclose(target_costs["objectness"][0], 0.3)
            ),
            "selection_verification": selection,
        },
        {
            "name": "within_scene_target_permutation",
            "passed": (
                permutation_control["contract"]["draws"] == 2048
                and permutation_control["cohort"][
                    "complete_rank_eligible_expressions"
                ] == 2
                and permutation_control["observed"]["referent_top1"]
                == rank_summary["score_summaries"]["referent"][
                    "scene_balanced_top1_success"
                ]
                and permutation_control["observed"]["objectness_top1"]
                == rank_summary["score_summaries"]["objectness"][
                    "scene_balanced_top1_success"
                ]
                and all(
                    0.0 < value <= 1.0
                    for value in permutation_control["p_values"].values()
                )
            ),
            "contract": permutation_control["contract"],
            "observed": permutation_control["observed"],
            "holm_adjusted_p_values": (
                permutation_control["holm_adjusted_p_values"]
            ),
        },
    ]
    if not all(check["passed"] for check in checks):
        raise RuntimeError("Synthetic frozen-chain self-test failed")

    sources = [
        "referent_native_expression_producer_20260919.py",
        "referent_object_rank_capture_20260919.py",
        "referent_target_rank_evaluator_20260919.py",
        "referent_query_coverage_control_20260919.py",
        "referent_within_scene_permutation_20260919.py",
        "native_frozen_capture_20260916.py",
        "frozen_capture_contract_20260916.py",
        "hierarchical_partition_contract_20260916.py",
        "native_endpoint_capture_20260916.py",
        "native_support_capture_v2_20260916.py",
        "capture_support_20260916.py",
        "physical_mask_endpoints_20260916.py",
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": (
            "CPU-only synthetic integration evidence for the frozen M95 "
            "referent native pipeline; no model forward, native score, queue "
            "mutation, training launch, or efficacy claim"
        ),
        "checks": checks,
        "observed": {
            "referent_target_rank": referent_rank,
            "objectness_target_rank": objectness_rank,
            "coverage_summary": coverage_summary["coverage_summary"],
            "selection_verification": selection,
            "permutation_control": {
                "contract": permutation_control["contract"],
                "cohort": permutation_control["cohort"],
                "observed": permutation_control["observed"],
                "null_distribution": permutation_control["null_distribution"],
                "p_values": permutation_control["p_values"],
                "holm_adjusted_p_values": (
                    permutation_control["holm_adjusted_p_values"]
                ),
            },
        },
        "source_hashes": [
            {
                "path": "scripts/" + name,
                "sha256": file_sha256(script_dir / name),
            }
            for name in sources
        ],
        "limitations": [
            "Explicit objectness scores here are synthetic. The frozen native "
            "producer emits target-mask IoUs, not this independent score axis, "
            "and is therefore not ready for paired rank/control evaluation.",
            "A declared score semantics string is not proof of independence; "
            "native producer source and matched-target intervention are required.",
            "The fixture validates contract composition, not native model behavior.",
            "Synthetic scores and query costs do not estimate target mIoU.",
            "Synthetic permutation p-values validate the control contract, "
            "not native specificity.",
            "Native candidate coverage and score separation remain unknown.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_selftest()
    output_path = Path(args.output).resolve()
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "output": str(output_path),
        "output_sha256": file_sha256(output_path),
        "checks_passed": len(report["checks"]),
    }, indent=2))


if __name__ == "__main__":
    main()
