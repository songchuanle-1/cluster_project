import copy
import unittest

from referent_object_rank_capture_20260919 import (
    build_capture,
    stable_sha256,
)
from referent_target_rank_evaluator_20260919 import (
    evaluate_capture,
    validate_capture_document,
)


def registry_fixture():
    rows = [
        {
            "registry_key": "sceneA:0:10",
            "scene": "sceneA",
            "target_object_id": "1",
            "same_class_candidate_ids": ["2", "3"],
            "primary_rank_eligible": True,
        },
        {
            "registry_key": "sceneB:0:11",
            "scene": "sceneB",
            "target_object_id": "4",
            "same_class_candidate_ids": [],
            "primary_rank_eligible": False,
        },
    ]
    return {"schema_version": 1, "registry_sha256": stable_sha256(rows), "rows": rows}


def binding_fixture():
    return {
        "code_commit": "a" * 40,
        "config_sha256": "b" * 64,
        "model_package_sha256": "c" * 64,
        "checkpoint_sha256": "d" * 64,
    }


def expression_fixture():
    return [{
        "registry_key": "sceneA:0:10",
        "scene": "sceneA",
        "target_object_id": "1",
        "native_input_sha256": "1" * 64,
        "hierarchical_partition_sha256": "2" * 64,
        "instance_labels": [1, 1, 2, 2, 3, 3],
        "query_seed_indices": [0, 2, 4],
        "referent_costs": [0.2, 0.1, 0.3],
        "objectness_costs": [0.7, 0.6, 0.5],
    }]


class ReferentObjectRankCaptureTest(unittest.TestCase):
    def test_valid_capture_passes_frozen_evaluator(self):
        registry = registry_fixture()
        capture = build_capture(registry, expression_fixture(), binding_fixture())
        validate_capture_document(capture, registry)
        summary = evaluate_capture(registry, capture)
        self.assertEqual(summary["complete_rank_eligible_expressions"], 1)
        self.assertEqual(summary["rejected_rank_eligible_expressions"], 0)
        self.assertEqual(summary["rows"][0]["scores"]["referent"]["rank"], 2)
        self.assertEqual(summary["rows"][0]["scores"]["objectness"]["rank"], 3)
        self.assertEqual(
            capture["rows"][0]["object_support_size"],
            {"1": 2, "2": 2, "3": 2},
        )
        self.assertEqual(
            capture["rows"][0]["native_query_costs"],
            {
                "1": {"referent": [0.2], "objectness": [0.7]},
                "2": {"referent": [0.1], "objectness": [0.6]},
                "3": {"referent": [0.3], "objectness": [0.5]},
            },
        )

    def test_missing_eligible_expression_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "rank-eligible registry"):
            build_capture(registry_fixture(), [], binding_fixture())

    def test_unknown_expression_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["registry_key"] = "sceneA:9:999"
        with self.assertRaisesRegex(ValueError, "Unknown or ineligible"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_empty_candidate_instance_mask_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["instance_labels"][4] = 9
        expressions[0]["instance_labels"][5] = 9
        with self.assertRaisesRegex(ValueError, "empty native instance mask"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_wrong_query_seed_length_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["query_seed_indices"] = [0, 2]
        with self.assertRaisesRegex(ValueError, "seed indices differ"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_nonfinite_cost_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["referent_costs"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "Nonfinite cost"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_candidate_without_seed_coverage_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["query_seed_indices"][2] = 0
        with self.assertRaisesRegex(ValueError, "no native query seed coverage"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_best_query_per_axis_is_selected(self):
        expressions = expression_fixture()
        expressions[0]["query_seed_indices"].append(0)
        expressions[0]["referent_costs"].append(0.4)
        expressions[0]["objectness_costs"].append(0.1)
        capture = build_capture(registry_fixture(), expressions, binding_fixture())
        assignment = capture["rows"][0]["native_query_assignment"]["1"]
        self.assertEqual(assignment["referent_selected_query"], 0)
        self.assertEqual(assignment["objectness_selected_query"], 3)

    def test_out_of_range_seed_index_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["query_seed_indices"][0] = 99
        with self.assertRaisesRegex(ValueError, "outside native support"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_target_mismatch_is_rejected(self):
        expressions = expression_fixture()
        expressions[0]["target_object_id"] = "2"
        with self.assertRaisesRegex(ValueError, "target differs"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_duplicate_expression_is_rejected(self):
        expressions = expression_fixture()
        expressions.append(copy.deepcopy(expressions[0]))
        with self.assertRaisesRegex(ValueError, "Duplicate expression"):
            build_capture(registry_fixture(), expressions, binding_fixture())

    def test_invalid_commit_hash_is_rejected(self):
        binding = binding_fixture()
        binding["code_commit"] = "short"
        with self.assertRaisesRegex(ValueError, "code_commit"):
            build_capture(registry_fixture(), expression_fixture(), binding)


if __name__ == "__main__":
    unittest.main()
