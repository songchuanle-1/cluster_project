import copy
import json
import unittest

from frozen_capture_contract_20260916 import fingerprint
from referent_geometry_capture_20260919 import (
    BINDING_FIELDS, capture_batch, evaluate_contrasts, validate_capture,
)
from test_referent_geometry_control_20260919 import fixture as geometry_fixture


def fixture():
    coordinates, labels, _ = geometry_fixture()
    binding = {field: str(i + 1) * 64 for i, field in enumerate(BINDING_FIELDS)}
    inputs = [None] * 10
    inputs[0] = {"sample_inds": [[1, 0], [1, 0]]}
    inputs[4] = [labels, [3, 3, 3]]
    inputs[7] = [[4, 0, 3], [2, 1, 0]]
    inputs[8] = coordinates + [[10, 1, 0], [11, 1, 0], [14, 1, 0]]
    inputs[9] = [0, 6, 9]
    axes = []
    for index, physical in enumerate(inputs[4]):
        n = len(physical)
        axes.append(dict(
            capture_id="synthetic-only", scene="scene" + str(index),
            scene_occurrence=index, dataset_index=index, ann_id=10 + index,
            expression_slot=0, native_input_sha256="a" * 64,
            original_superpoint_ids=list(range(20, 20 + n)),
            sample_inverse=list(range(n)), physical_instance_labels=physical[:],
            producer_sha256=binding["producer_sha256"],
            checkpoint_sha256=binding["checkpoint_sha256"],
        ))
    return inputs, axes, binding


class GeometryCaptureTest(unittest.TestCase):
    def test_expression_local_slices_and_composed_seeds(self):
        args = fixture()
        result = capture_batch(*args)
        self.assertEqual(result["rows"][0]["composed_seed_indices"], [0, 4])
        self.assertEqual(result["rows"][1]["composed_seed_indices"], [1, 2])
        self.assertEqual(result["rows"][1]["coordinates"], args[0][8][6:])
        self.assertEqual(validate_capture(result, args[2]), result["rows"])
        self.assertNotIn("objectness_scores", str(result))

    def test_target_and_text_not_consumed(self):
        inputs, axes, binding = fixture()
        before = capture_batch(inputs, axes, binding)
        for slot in (1, 2, 3, 5, 6):
            inputs[slot] = ["changed target or language"]
        self.assertEqual(capture_batch(inputs, axes, binding), before)

    def test_capture_does_not_alias_mutable_observations(self):
        inputs, axes, binding = fixture()
        capture = capture_batch(inputs, axes, binding)
        before = copy.deepcopy(capture)
        inputs[8][0][0] = 900
        inputs[7][0][0] = 1
        axes[0]["physical_instance_labels"][0] = 5
        self.assertEqual(capture, before)
        validate_capture(capture, binding)

    def test_json_roundtrip(self):
        args = fixture()
        capture = json.loads(json.dumps(capture_batch(*args), allow_nan=False))
        self.assertEqual(validate_capture(capture, args[2]), capture["rows"])

    def test_target_order_changes_only_contrast_order(self):
        args = fixture()
        capture = capture_batch(*args)
        original = copy.deepcopy(capture)
        report = evaluate_contrasts(capture, args[2], [
            dict(row_index=0, object_ids=[1, 2]),
            dict(row_index=0, object_ids=[2, 1]),
        ])
        a, b = report["contrasts"]
        self.assertEqual(a["values"], b["values"][::-1])
        self.assertEqual(capture, original)

    def test_physical_sentinel_not_an_object(self):
        inputs, axes, binding = fixture()
        inputs[4][0][4] = 199
        axes[0]["physical_instance_labels"][4] = -1
        row = capture_batch(inputs, axes, binding)["rows"][0]
        self.assertIsNone(row["geometry"]["query_costs"][1])
        self.assertNotIn("199", row["geometry"]["object_costs"])

    def test_real_199_is_preserved(self):
        inputs, axes, binding = fixture()
        inputs[4][0] = [199 if x == 1 else x for x in inputs[4][0]]
        axes[0]["physical_instance_labels"] = inputs[4][0][:]
        self.assertIn("199", capture_batch(inputs, axes, binding)["rows"][0]["geometry"]["object_costs"])

    def test_invalid_offsets_fail_closed(self):
        for offsets in ([1, 6, 9], [0, 9, 6], [0, 6, 8], [0, 0, 9],
                        [0, 6], [False, 6, 9], [0, 6.0, 9]):
            inputs, axes, binding = fixture()
            inputs[9] = offsets
            with self.subTest(offsets=offsets), self.assertRaises(ValueError):
                capture_batch(inputs, axes, binding)

    def test_invalid_indices_and_label_mapping(self):
        for field, value in ((7, [[6], [0]]), (7, [[True], [0]]),
                             (4, [[1] * 6, [3] * 3])):
            inputs, axes, binding = fixture()
            inputs[field] = value
            with self.assertRaises(ValueError):
                capture_batch(inputs, axes, binding)
        inputs, axes, binding = fixture()
        inputs[0]["sample_inds"][0] = [3]
        with self.assertRaises(ValueError):
            capture_batch(inputs, axes, binding)

    def test_hash_tampering(self):
        args = fixture()
        capture = capture_batch(*args)
        capture["rows"][0]["coordinates"][0][0] = 100
        with self.assertRaisesRegex(ValueError, "hash"):
            validate_capture(capture, args[2])

    def test_rehashed_stale_costs_rejected(self):
        args = fixture()
        capture = capture_batch(*args)
        capture["rows"][0]["geometry"]["query_costs"][0] = 42
        capture["payload_sha256"] = fingerprint(
            {k: v for k, v in capture.items() if k != "payload_sha256"})
        with self.assertRaisesRegex(ValueError, "recomputation"):
            validate_capture(capture, args[2])

    def test_expected_source_mismatch(self):
        args = fixture()
        capture = capture_batch(*args)
        for field in BINDING_FIELDS:
            changed = dict(args[2], **{field: "f" * 64})
            with self.assertRaisesRegex(ValueError, "binding"):
                validate_capture(capture, changed)

    def test_physical_identity_strict(self):
        for field, value in (("ann_id", True), ("dataset_index", 1.0),
                             ("expression_slot", "0"),
                             ("original_superpoint_ids", [1] * 6),
                             ("native_input_sha256", "bad"),
                             ("checkpoint_sha256", "b" * 64)):
            inputs, axes, binding = fixture()
            axes[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                capture_batch(inputs, axes, binding)

    def test_nonfinite_coordinate_rejected(self):
        inputs, axes, binding = fixture()
        inputs[8][0][0] = float("nan")
        with self.assertRaises(ValueError):
            capture_batch(inputs, axes, binding)

    def test_selection_sensitivity_not_independence(self):
        inputs, axes, binding = fixture()
        before = capture_batch(inputs, axes, binding)
        inputs[0]["sample_inds"][0] = [1, 2]
        after = capture_batch(inputs, axes, binding)
        self.assertNotEqual(before["rows"][0]["geometry"]["query_costs"],
                            after["rows"][0]["geometry"]["query_costs"])
        self.assertNotEqual(before["payload_sha256"], after["payload_sha256"])

    def test_missing_and_degenerate_denominators(self):
        inputs, axes, binding = fixture()
        inputs[8][6:] = [[0, 0, 0]] * 3
        capture = capture_batch(inputs, axes, binding)
        report = evaluate_contrasts(capture, binding, [
            dict(row_index=0, object_ids=[1, 2]),
            dict(row_index=1, object_ids=[3, 4]),
        ])
        self.assertEqual(report["counts"], dict(valid=1, missing=1, tied=0))
        self.assertEqual(report["contrasts"][1]["missing_object_ids"], [3, 4])
        self.assertFalse(report["scientific_validation_complete"])

    def test_exact_ties_retained_not_successes(self):
        inputs, axes, binding = fixture()
        inputs[8][:6] = [[0, 0, 0], [1, 0, 0], [2, 0, 0],
                          [3, 0, 0], [4, 0, 0], [5, 0, 0]]
        inputs[0]["sample_inds"][0] = [1, 2]
        report = evaluate_contrasts(capture_batch(inputs, axes, binding), binding,
                                   [dict(row_index=0, object_ids=[1, 2])])
        self.assertEqual(report["counts"]["tied"], 1)
        self.assertTrue(report["contrasts"][0]["near_tie"])

    def test_near_ties_explicit_not_silently_exact(self):
        inputs, axes, binding = fixture()
        inputs[8][:6] = [[0, 0, 0], [1, 0, 0], [4, 0, 0],
                          [10, 0, 0], [11, 0, 0], [14.0000000001, 0, 0]]
        inputs[0]["sample_inds"][0] = [1, 2]
        report = evaluate_contrasts(capture_batch(inputs, axes, binding), binding,
                                   [dict(row_index=0, object_ids=[1, 2])])
        self.assertEqual(report["counts"]["valid"], 1)
        self.assertTrue(report["contrasts"][0]["near_tie"])
        self.assertGreater(report["contrasts"][0]["minimum_absolute_gap"], 0)

    def test_duplicate_expression_rejected(self):
        inputs, axes, binding = fixture()
        for key in ("capture_id", "scene", "scene_occurrence", "dataset_index",
                    "ann_id", "expression_slot"):
            axes[1][key] = axes[0][key]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            capture_batch(inputs, axes, binding)

    def test_array_adapter_preserves_slices(self):
        inputs, axes, binding = fixture()
        expected = capture_batch(inputs, axes, binding)["rows"]
        # Fingerprinting requires actual supported native array types.
        import numpy as np
        for slot in (7, 8, 9):
            inputs[slot] = np.array(inputs[slot])
        inputs[4] = [np.array(x) for x in inputs[4]]
        inputs[0]["sample_inds"] = np.array(inputs[0]["sample_inds"])
        capture = capture_batch(inputs, axes, binding)
        self.assertEqual(capture["rows"], expected)
        self.assertEqual(validate_capture(capture, binding), expected)


if __name__ == "__main__":
    unittest.main()
