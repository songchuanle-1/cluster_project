import copy
import json
import tempfile
import unittest
from pathlib import Path

from referent_target_rank_evaluator_20260919 import (
    build_report,
    evaluate_capture,
    stable_sha256,
    validate_capture_document,
    validate_registry_document,
)


def registry_fixture():
    rows = [
        {
            "registry_key": "sceneA:0:1",
            "scene": "sceneA",
            "target_object_id": "0",
            "same_class_candidate_ids": ["2"],
            "primary_rank_eligible": True,
        },
        {
            "registry_key": "sceneA:1:2",
            "scene": "sceneA",
            "target_object_id": "2",
            "same_class_candidate_ids": ["0", "3", "4"],
            "primary_rank_eligible": True,
        },
        {
            "registry_key": "sceneA:2:3",
            "scene": "sceneA",
            "target_object_id": "3",
            "same_class_candidate_ids": [],
            "primary_rank_eligible": False,
        },
        {
            "registry_key": "sceneB:0:4",
            "scene": "sceneB",
            "target_object_id": "4",
            "same_class_candidate_ids": ["5"],
            "primary_rank_eligible": True,
        },
    ]
    return {"schema_version": 1, "registry_sha256": stable_sha256(rows), "rows": rows}


def capture_fixture(registry):
    zero64 = "0" * 64
    binding = {
        "config_path": "configs/example.yaml",
        "config_sha256": zero64,
        "code_commit": "a" * 40,
        "model_class": "model_example",
        "model_package_sha256": zero64,
        "checkpoint_sha256": zero64,
    }
    rows = [
        {
            "registry_key": "sceneA:0:1",
            "scene": "sceneA",
            "target_object_id": "0",
            "native_input_sha256": "1" * 64,
            "hierarchical_partition_sha256": "2" * 64,
            "scores": {
                "referent": {"0": 0.1, "2": 0.8},
                "objectness": {"0": 0.2, "2": 0.7},
            },
            "mask_sha256": {"0": "3" * 64, "2": "4" * 64},
        },
        {
            "registry_key": "sceneA:1:2",
            "scene": "sceneA",
            "target_object_id": "2",
            "native_input_sha256": "5" * 64,
            "hierarchical_partition_sha256": "6" * 64,
            "scores": {
                "referent": {"0": 0.2, "2": 0.7, "3": 0.1, "4": 0.4},
                "objectness": {"0": 0.2, "2": 0.9, "3": 0.1, "4": 0.4},
            },
            "mask_sha256": {
                "0": "7" * 64,
                "2": "8" * 64,
                "3": "9" * 64,
                "4": "a" * 64,
            },
        },
        {
            "registry_key": "sceneB:0:4",
            "scene": "sceneB",
            "target_object_id": "4",
            "native_input_sha256": "b" * 64,
            "hierarchical_partition_sha256": "c" * 64,
            "scores": {
                "referent": {"4": 0.2, "5": 0.9},
                "objectness": {"4": 0.9, "5": 0.1},
            },
            "mask_sha256": {"4": "d" * 64, "5": "e" * 64},
        },
    ]
    return {
        "schema_version": 1,
        "registry_sha256": registry["registry_sha256"],
        "binding": binding,
        "capture_contract": {
            "score_direction": "lower_is_better",
            "missing_data_policy": "reject_expression_no_imputation",
            "required_score_names": ["referent", "objectness"],
            "tie_policy": "reject",
        },
        "rows": rows,
    }


class ReferentTargetRankEvaluatorTest(unittest.TestCase):
    def test_valid_capture_returns_complete_rank_rows(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        summary = evaluate_capture(registry, capture)
        self.assertEqual(summary["complete_rank_eligible_expressions"], 3)
        self.assertEqual(summary["rejected_rank_eligible_expressions"], 0)
        self.assertEqual(summary["score_summaries"]["referent"]["expression_mean_rank"], 2.0)

    def test_scene_balance_differs_from_expression_pooling(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        summary = evaluate_capture(registry, capture)["score_summaries"]["referent"]
        self.assertAlmostEqual(summary["expression_top1_success"], 2.0 / 3.0)
        self.assertAlmostEqual(summary["scene_balanced_top1_success"], 0.75)

    def test_missing_candidate_invalidates_expression(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        del capture["rows"][0]["scores"]["referent"]["2"]
        summary = evaluate_capture(registry, capture)
        self.assertEqual(summary["complete_rank_eligible_expressions"], 2)
        self.assertEqual(
            summary["rejected"],
            [
                {
                    "registry_key": "sceneA:0:1",
                    "reason": "Native candidate coverage differs from registry",
                }
            ],
        )

    def test_extra_candidate_invalidates_expression(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        capture["rows"][0]["scores"]["referent"]["9"] = 0.5
        summary = evaluate_capture(registry, capture)
        self.assertEqual(summary["complete_rank_eligible_expressions"], 2)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native candidate coverage differs from registry",
        )

    def test_tied_scores_are_rejected(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        capture["rows"][0]["scores"]["referent"]["2"] = 0.1
        summary = evaluate_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native score ties are not admissible",
        )

    def test_missing_mask_identity_is_rejected(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        del capture["rows"][0]["mask_sha256"]["2"]
        summary = evaluate_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native mask coverage differs from registry",
        )

    def test_registry_hash_mismatch_is_rejected(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        capture["registry_sha256"] = "f" * 64
        with self.assertRaises(ValueError):
            validate_capture_document(capture, registry)

    def test_registry_content_mutation_is_rejected(self):
        registry = registry_fixture()
        registry["rows"][0]["target_object_id"] = "9"
        with self.assertRaises(ValueError):
            validate_registry_document(registry)

    def test_build_report_preserves_input_hashes(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        with tempfile.TemporaryDirectory() as directory:
            registry_path = Path(directory) / "registry.json"
            capture_path = Path(directory) / "capture.json"
            registry_path.write_text(json.dumps(registry), encoding="ascii")
            capture_path.write_text(json.dumps(capture), encoding="ascii")
            report = build_report(
                copy.deepcopy(registry),
                copy.deepcopy(capture),
                registry_path=registry_path,
                capture_path=capture_path,
            )
        self.assertEqual(report["inputs"]["registry"]["content_sha256"], registry["registry_sha256"])
        self.assertEqual(report["evaluation_contract"]["tie_policy"], "reject")

    def test_no_missing_expression_is_imputed(self):
        registry = registry_fixture()
        capture = capture_fixture(registry)
        del capture["rows"][1]
        summary = evaluate_capture(registry, capture)
        self.assertEqual(summary["complete_rank_eligible_expressions"], 2)
        self.assertEqual(
            summary["rejected"][0],
            {"registry_key": "sceneA:1:2", "reason": "missing_expression"},
        )


if __name__ == "__main__":
    unittest.main()
