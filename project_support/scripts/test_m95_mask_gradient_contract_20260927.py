import unittest

import torch

from m95_mask_gradient_contract_20260927 import evaluate
from m95_target_seed_full_population_20260927 import MANIFEST_SHA


class MaskGradientTest(unittest.TestCase):
    def setUp(self):
        self.row = {
            "manifest_index": 5, "scene": "scene", "ann_id": 2,
            "selected_query": 0, "ious": [1 / 3] * 128,
            "native_positive": [True] * 128,
        }
        self.artifact = {
            "manifest_index": 5, "manifest_sha256": MANIFEST_SHA,
            "axis": {"scene": "scene", "ann_id": 2},
            "query_mask_logits": torch.tensor([[2., -2., 2.]] * 128),
            "query_masks": torch.tensor([[True, False, True]] * 128),
            "target_union": torch.tensor([True, True, False]),
        }

    def test_correct_direction(self):
        result = evaluate(self.row, self.artifact)
        self.assertEqual((result["fn"], result["fp"]), (1, 1))
        self.assertEqual(result["fn_nonzero_correct_direction"], 1)
        self.assertEqual(result["fp_nonzero_correct_direction"], 1)

    def test_mismatch_fails(self):
        self.row["ious"][0] = 1.0
        with self.assertRaises(ValueError):
            evaluate(self.row, self.artifact)

    def test_negative_query_fails(self):
        self.row["native_positive"][0] = False
        with self.assertRaises(ValueError):
            evaluate(self.row, self.artifact)


if __name__ == "__main__":
    unittest.main()
