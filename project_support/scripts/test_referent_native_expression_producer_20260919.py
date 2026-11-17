import copy
import itertools
import unittest
from referent_native_expression_producer_20260919 import (
    frozen_capture_producer_sha256,
    native_capture_binding,
    produce_expression_inputs,
)
from referent_object_rank_capture_20260919 import (
    build_capture,
    stable_sha256,
)
from referent_target_rank_evaluator_20260919 import evaluate_capture


def registry_fixture():
    rows = [
        {
            "registry_key": "sceneA:0:10",
            "scene": "sceneA",
            "ann_id": "10",
            "dataset_order": {"step": 0, "expression_slot": 0},
            "target_object_id": "1",
            "same_class_candidate_ids": ["2", "3"],
            "primary_rank_eligible": True,
        },
        {
            "registry_key": "sceneB:0:11",
            "scene": "sceneB",
            "ann_id": "11",
            "dataset_order": {"step": 0, "expression_slot": 1},
            "target_object_id": "4",
            "same_class_candidate_ids": [],
            "primary_rank_eligible": False,
        },
    ]
    return {
        "schema_version": 1,
        "sources": {
            "config": {
                "path": "/data/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml",
                "sha256": "b" * 64,
            }
        },
        "registry_sha256": stable_sha256(rows),
        "rows": rows,
    }


def capture_fixture():
    return {
        "native_capture_completed": True,
        "model_class": "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort",
        "producer_sha256": frozen_capture_producer_sha256(),
        "config_path": "configs/Quard/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml",
        "config_sha256": "b" * 64,
        "model_source_sha256": "c" * 64,
        "checkpoint_sha256": "d" * 64,
        "rows": [
            {
                "scene": "sceneA",
                "ann_id": 10,
                "dataset_index": 0,
                "expression_slot": 0,
                "original_superpoint_ids": [1, 1, 2, 2, 3, 3],
                "instance_labels": [1, 1, 2, 2, 3, 3],
                "fps_superpoints": [0, 1, 2, 3, 4, 5],
                "sampled_seed_indices": [0, 2, 4],
                "scores": [0.7, 0.2, 0.5],
                "ious": [0.25, 0.75, 0.35],
                "objectness_scores": [0.25, 0.75, 0.35],
                "objectness_score_semantics": "target_independent_objectness_probability",
                "native_input_sha256": "1" * 64,
                "hierarchical_partition_sha256": "2" * 64,
            },
            {
                "scene": "sceneB",
                "ann_id": 11,
                "dataset_index": 0,
                "expression_slot": 1,
                "original_superpoint_ids": [4],
                "instance_labels": [4],
                "fps_superpoints": [0],
                "sampled_seed_indices": [0],
                "scores": [0.6],
                "ious": [0.4],
                "objectness_scores": [0.4],
                "objectness_score_semantics": "target_independent_objectness_probability",
                "native_input_sha256": "3" * 64,
                "hierarchical_partition_sha256": "4" * 64,
            },
        ],
    }


def binding_fixture():
    return {
        "code_commit": "a" * 40,
        "config_sha256": "b" * 64,
        "model_package_sha256": "c" * 64,
        "checkpoint_sha256": "d" * 64,
    }


class ReferentNativeExpressionProducerTest(unittest.TestCase):
    def test_support_reordering_preserves_object_scores(self):
        registry = registry_fixture()
        original = capture_fixture()
        reference = build_capture(
            registry, produce_expression_inputs(original, registry), binding_fixture()
        )["rows"][0]
        for permutation in itertools.permutations(range(6)):
            capture = copy.deepcopy(original)
            row = capture["rows"][0]
            inverse = {old: new for new, old in enumerate(permutation)}
            for field in ("instance_labels", "original_superpoint_ids"):
                row[field] = [row[field][index] for index in permutation]
            row["fps_superpoints"] = [
                inverse[index] for index in row["fps_superpoints"]
            ]
            actual = build_capture(
                registry, produce_expression_inputs(capture, registry), binding_fixture()
            )["rows"][0]
            self.assertEqual(actual["scores"], reference["scores"])
            self.assertEqual(actual["object_support_size"], reference["object_support_size"])
            self.assertEqual(actual["native_query_assignment"], reference["native_query_assignment"])

    def test_fps_reordering_preserves_composed_seed_indices(self):
        original = capture_fixture()
        original["rows"][0]["fps_superpoints"] = [4, 0, 2]
        original["rows"][0]["sampled_seed_indices"] = [1, 2, 0]
        expected = produce_expression_inputs(original, registry_fixture())
        for permutation in itertools.permutations(range(3)):
            capture = copy.deepcopy(original)
            row = capture["rows"][0]
            inverse = {old: new for new, old in enumerate(permutation)}
            row["fps_superpoints"] = [row["fps_superpoints"][i] for i in permutation]
            row["sampled_seed_indices"] = [
                inverse[index] for index in row["sampled_seed_indices"]
            ]
            self.assertEqual(
                produce_expression_inputs(capture, registry_fixture()), expected
            )

    def test_query_reordering_preserves_scores_and_remaps_ownership(self):
        registry = registry_fixture()
        original = capture_fixture()
        reference = build_capture(
            registry, produce_expression_inputs(original, registry), binding_fixture()
        )["rows"][0]
        for permutation in itertools.permutations(range(3)):
            capture = copy.deepcopy(original)
            row = capture["rows"][0]
            for field in ("sampled_seed_indices", "scores", "ious", "objectness_scores"):
                row[field] = [row[field][index] for index in permutation]
            actual = build_capture(
                registry, produce_expression_inputs(capture, registry), binding_fixture()
            )["rows"][0]
            self.assertEqual(actual["scores"], reference["scores"])
            for old, object_id in enumerate(("1", "2", "3")):
                self.assertEqual(
                    actual["native_query_assignment"][object_id]["query_indices"],
                    [permutation.index(old)],
                )

    def test_target_iou_is_not_an_objectness_fallback(self):
        capture = capture_fixture()
        del capture["rows"][0]["objectness_scores"]
        with self.assertRaisesRegex(ValueError, "objectness"):
            produce_expression_inputs(capture, registry_fixture())

    def test_target_iou_semantics_are_rejected(self):
        capture = capture_fixture()
        capture["rows"][0]["objectness_score_semantics"] = "target_mask_iou"
        with self.assertRaisesRegex(ValueError, "objectness"):
            produce_expression_inputs(capture, registry_fixture())

    def test_target_overlap_does_not_change_objectness_costs(self):
        capture = capture_fixture()
        before = produce_expression_inputs(capture, registry_fixture())
        capture["rows"][0]["ious"] = [0.9, 0.1, 0.0]
        after = produce_expression_inputs(capture, registry_fixture())
        self.assertEqual(before, after)

    def test_objectness_axis_requires_valid_probabilities(self):
        for value in ([], [0.2], [True, 0.2, 0.3],
                      [float("nan"), 0.2, 0.3], [1.1, 0.2, 0.3]):
            with self.subTest(value=value):
                capture = capture_fixture()
                capture["rows"][0]["objectness_scores"] = value
                with self.assertRaises(ValueError):
                    produce_expression_inputs(capture, registry_fixture())

    def test_missing_objectness_semantics_are_rejected(self):
        capture = capture_fixture()
        del capture["rows"][0]["objectness_score_semantics"]
        with self.assertRaisesRegex(ValueError, "objectness"):
            produce_expression_inputs(capture, registry_fixture())

    def test_valid_capture_projects_to_frozen_path(self):
        expressions = produce_expression_inputs(capture_fixture(), registry_fixture())
        self.assertEqual(len(expressions), 1)
        self.assertEqual(expressions[0]["query_seed_indices"], [0, 2, 4])
        self.assertEqual(expressions[0]["referent_costs"], [-0.7, -0.2, -0.5])
        self.assertEqual(expressions[0]["objectness_costs"], [0.75, 0.25, 0.65])

        capture = build_capture(registry_fixture(), expressions, binding_fixture())
        summary = evaluate_capture(registry_fixture(), capture)
        self.assertEqual(summary["complete_rank_eligible_expressions"], 1)
        self.assertEqual(summary["rows"][0]["scores"]["referent"]["rank"], 1)
        self.assertEqual(summary["rows"][0]["scores"]["objectness"]["rank"], 3)

    def test_missing_eligible_expression_is_rejected(self):
        capture = capture_fixture()
        capture["rows"] = capture["rows"][1:]
        with self.assertRaisesRegex(ValueError, "missing a rank-eligible"):
            produce_expression_inputs(capture, registry_fixture())

    def test_sampled_indices_are_resolved_through_native_fps(self):
        capture = capture_fixture()
        row = capture["rows"][0]
        row["fps_superpoints"] = [4, 0, 2]
        row["sampled_seed_indices"] = [0, 1, 2]
        expressions = produce_expression_inputs(capture, registry_fixture())
        self.assertEqual(expressions[0]["query_seed_indices"], [4, 0, 2])
        result = build_capture(registry_fixture(), expressions, binding_fixture())
        self.assertEqual(
            result["rows"][0]["native_query_assignment"]["1"]["query_indices"],
            [1],
        )
        self.assertEqual(result["rows"][0]["scores"]["referent"]["1"], -0.2)

    def test_missing_or_invalid_fps_axis_is_rejected(self):
        for value in (None, [], [True], [-1], [6], [0.5]):
            with self.subTest(fps=value):
                capture = capture_fixture()
                capture["rows"][0]["fps_superpoints"] = value
                with self.assertRaisesRegex(ValueError, "FPS"):
                    produce_expression_inputs(capture, registry_fixture())

    def test_sampled_index_must_be_on_fps_axis(self):
        capture = capture_fixture()
        capture["rows"][0]["fps_superpoints"] = [0, 2, 4]
        with self.assertRaisesRegex(ValueError, "seed index is invalid"):
            produce_expression_inputs(capture, registry_fixture())

    def test_capture_identity_rejects_lossy_coercion(self):
        for field in ("ann_id", "dataset_index", "expression_slot"):
            for value in (True, False, 0.0, 10.9, -1, " 0", "+0", "00"):
                with self.subTest(field=field, value=value):
                    capture = capture_fixture()
                    capture["rows"][0][field] = value
                    with self.assertRaisesRegex(ValueError, "physical identity"):
                        produce_expression_inputs(capture, registry_fixture())

    def test_registry_identity_rejects_lossy_coercion(self):
        for field in ("ann_id", "step", "expression_slot"):
            for value in (False, 0.0, 10.9, -1, "00"):
                with self.subTest(field=field, value=value):
                    registry = registry_fixture()
                    row = registry["rows"][0]
                    container = row if field == "ann_id" else row["dataset_order"]
                    container[field] = value
                    registry["registry_sha256"] = stable_sha256(registry["rows"])
                    with self.assertRaisesRegex(ValueError, "physical identity"):
                        produce_expression_inputs(capture_fixture(), registry)

    def test_canonical_string_identities_are_supported(self):
        capture = capture_fixture()
        for row in capture["rows"]:
            for field in ("ann_id", "dataset_index", "expression_slot"):
                row[field] = str(row[field])
        self.assertEqual(len(produce_expression_inputs(capture, registry_fixture())), 1)

    def test_unknown_capture_expression_is_rejected(self):
        capture = capture_fixture()
        capture["rows"][0]["ann_id"] = 99
        with self.assertRaisesRegex(ValueError, "unregistered expression"):
            produce_expression_inputs(capture, registry_fixture())

    def test_frozen_capture_producer_hash_mismatch_is_rejected(self):
        capture = capture_fixture()
        capture["producer_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "frozen producer bundle"):
            produce_expression_inputs(capture, registry_fixture())

    def test_binding_is_derived_from_validated_capture(self):
        binding = native_capture_binding(
            capture_fixture(),
            registry_fixture(),
            "a" * 40,
        )
        self.assertEqual(
            binding,
            {
                "code_commit": "a" * 40,
                "config_sha256": "b" * 64,
                "model_package_sha256": "c" * 64,
                "checkpoint_sha256": "d" * 64,
            },
        )

    def test_binding_rejects_invalid_code_commit(self):
        with self.assertRaisesRegex(ValueError, "code_commit"):
            native_capture_binding(
                capture_fixture(),
                registry_fixture(),
                "short",
            )

    def test_query_axis_mismatch_is_rejected(self):
        capture = capture_fixture()
        capture["rows"][0]["ious"].pop()
        with self.assertRaisesRegex(ValueError, "query axes differ"):
            produce_expression_inputs(capture, registry_fixture())

    def test_config_hash_mismatch_is_rejected(self):
        capture = capture_fixture()
        capture["config_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "config hash differs"):
            produce_expression_inputs(capture, registry_fixture())

    def test_out_of_range_seed_is_rejected(self):
        capture = capture_fixture()
        capture["rows"][0]["sampled_seed_indices"][0] = 99
        with self.assertRaisesRegex(ValueError, "seed index is invalid"):
            produce_expression_inputs(capture, registry_fixture())

    def test_nonbinary_query_probability_is_rejected(self):
        capture = capture_fixture()
        capture["rows"][0]["ious"][0] = 1.2
        with self.assertRaisesRegex(ValueError, "outside"):
            produce_expression_inputs(capture, registry_fixture())

    def test_duplicate_capture_expression_is_rejected(self):
        capture = capture_fixture()
        capture["rows"].append(copy.deepcopy(capture["rows"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate native capture"):
            produce_expression_inputs(capture, registry_fixture())


if __name__ == "__main__":
    unittest.main()
