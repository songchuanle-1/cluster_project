import unittest

from m95_pair_union_bound_20260926 import pair_bound


class PairUnionBoundTest(unittest.TestCase):
    def test_two_parts_rescue_uncovered_target(self):
        import torch

        masks = torch.tensor([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=torch.bool)
        target = torch.tensor([1, 1, 0, 0], dtype=torch.bool)
        single, _, pair, indices = pair_bound(masks, target)
        self.assertEqual(single, 0.5)
        self.assertEqual(pair, 1.0)
        self.assertEqual(indices, [0, 1])

    def test_distractor_cannot_improve(self):
        import torch

        masks = torch.tensor([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=torch.bool)
        target = torch.tensor([1, 1, 0, 0], dtype=torch.bool)
        self.assertEqual(pair_bound(masks, target), (1.0, 0, 1.0, None))

    def test_one_mask_and_empty_target(self):
        import torch

        masks = torch.tensor([[0, 1, 0]], dtype=torch.bool)
        target = torch.tensor([0, 0, 0], dtype=torch.bool)
        self.assertEqual(pair_bound(masks, target), (0.0, 0, 0.0, None))


if __name__ == "__main__":
    unittest.main()
