"""Small support and error-accounting checks for the frozen analysis."""
import unittest

import torch

from m95_mask_error_partition_20260926 import mask_partition


class MaskPartitionTest(unittest.TestCase):
    def test_fn_dominant(self):
        target = torch.tensor([1, 1, 1, 1, 0, 0], dtype=torch.bool)
        masks = torch.tensor([[1, 0, 0, 0, 0, 0]], dtype=torch.bool)
        got = mask_partition(masks, target)
        self.assertEqual((got["tp"], got["fp"], got["fn"]), (1, 0, 3))
        self.assertTrue(got["fn_dominant"])
        self.assertEqual(got["recall"], 0.25)

    def test_fp_dominant(self):
        target = torch.tensor([1, 0, 0, 0], dtype=torch.bool)
        masks = torch.tensor([[1, 1, 1, 0]], dtype=torch.bool)
        got = mask_partition(masks, target)
        self.assertEqual((got["tp"], got["fp"], got["fn"]), (1, 2, 0))
        self.assertTrue(got["fp_dominant"])
        self.assertAlmostEqual(got["iou"], 1 / 3)

    def test_best_query_and_empty(self):
        target = torch.tensor([0, 1, 1], dtype=torch.bool)
        masks = torch.tensor([[0, 0, 0], [0, 1, 1]], dtype=torch.bool)
        got = mask_partition(masks, target)
        self.assertEqual(got["query"], 1)
        self.assertEqual((got["tp"], got["fp"], got["fn"]), (2, 0, 0))


if __name__ == "__main__":
    unittest.main()
