import copy
import unittest

from sampling_pair_contract_20260916 import sampling_paired_summary
from test_frozen_capture_contract_20260916 import frozen_row
from test_hierarchical_partition_contract_20260916 import valid_observation


class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.row = frozen_row()
        self.row["fps_superpoints"] = [0, 1]
        self.row["sampled_seed_indices"] = [0] * len(self.row["scores"])
        hierarchy = valid_observation()
        for key, value in hierarchy.items():
            if key != "original_superpoint_ids":
                self.row[key] = value
        self.row["original_superpoint_ids"] = [10, 11, 12, 13]
        self.row["sample_inverse"] = [0, 1, 2, 3]
        self.row["native_input_sha256"] = "b" * 64
        self.row["checkpoint_sha256"] = "a" * 64
        self.args = dict(baseline_checkpoint="a" * 64, candidate_checkpoint="a" * 64)

    def test_identical_support(self):
        result = sampling_paired_summary([self.row], [self.row], **self.args)
        self.assertTrue(result["fps_support_verified"])
        self.assertTrue(result["hierarchical_partition_verified"])
        self.assertEqual(result["scene_balanced_delta"], 0)

    def test_fps_order_is_not_a_set(self):
        rhs = copy.deepcopy(self.row)
        rhs["fps_superpoints"].reverse()
        with self.assertRaisesRegex(ValueError, "order differs"):
            sampling_paired_summary([self.row], [rhs], **self.args)

    def test_learned_selection_may_change(self):
        rhs = copy.deepcopy(self.row)
        rhs["sampled_seed_indices"] = [1] * len(rhs["scores"])
        result = sampling_paired_summary([self.row], [rhs], **self.args)
        self.assertFalse(result["query_selection_conditioned"])

    def test_hierarchical_partition_must_match(self):
        rhs = copy.deepcopy(self.row)
        rhs["hierarchical_fps_positions"][0][0][0] = 0.25
        with self.assertRaisesRegex(ValueError, "hash differs"):
            sampling_paired_summary([self.row], [rhs], **self.args)

    def test_missing_invalid_fps(self):
        for fps in (None, [], [-1], [999999], [True], [0.0]):
            with self.subTest(fps=fps), self.assertRaises(ValueError):
                rhs = dict(self.row, fps_superpoints=fps)
                sampling_paired_summary([self.row], [rhs], **self.args)

    def test_invalid_query_binding(self):
        for indices in (None, [], [-1] * len(self.row["scores"]),
                        [2] * len(self.row["scores"])):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                rhs = dict(self.row, sampled_seed_indices=indices)
                sampling_paired_summary([self.row], [rhs], **self.args)

    def test_input_gate_remains(self):
        rhs = dict(self.row, native_input_sha256="d" * 64)
        with self.assertRaisesRegex(ValueError, "inputs differ"):
            sampling_paired_summary([self.row], [rhs], **self.args)


if __name__ == "__main__":
    unittest.main()
