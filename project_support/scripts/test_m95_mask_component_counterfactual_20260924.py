import math
import unittest

from m95_mask_component_counterfactual_20260924 import compare


class ComponentCounterfactualTests(unittest.TestCase):
    def test_one_match_per_gt_is_null(self):
        result = compare([(0, 0), (1, 1)], [[1, 0], [0, 1]],
                         [[5, -5], [-5, 5]])
        self.assertEqual(result["identity_mismatch_pairs"], 0)
        self.assertEqual(result["score_filter_crossings"], 0)
        self.assertEqual(result["original_bce"], result["corrected_bce"])
        self.assertEqual(result["original_dice"], result["corrected_dice"])
        self.assertIsNone(result["score_mse"])
        self.assertIsNone(result["indicator_loss"])

    def test_early_repeat_changes_only_later_gt(self):
        result = compare([(0, 0), (1, 1), (2, 0)],
                         [[1, 0], [0, 1]],
                         [[5, -5], [-5, 5], [5, -5]])
        self.assertEqual(result["identity_mismatch_pairs"], 1)
        self.assertEqual(result["changed_mask_pairs"], 1)
        self.assertEqual(result["score_filter_crossings"], 1)
        self.assertEqual([p["addressed_gt"] for p in result["pairs"]],
                         [0, 0, 0])
        self.assertGreater(result["original_bce"], result["corrected_bce"])
        self.assertGreater(result["original_dice"], result["corrected_dice"])
        self.assertFalse(result["pairs"][1]["original_score_eligible"])
        self.assertTrue(result["pairs"][1]["corrected_score_eligible"])

    def test_late_repeat_is_null(self):
        result = compare([(0, 0), (1, 1), (2, 1)],
                         [[1, 0], [0, 1]],
                         [[5, -5], [-5, 5], [-5, 5]])
        self.assertEqual(result["identity_mismatch_pairs"], 0)
        self.assertEqual(result["changed_mask_pairs"], 0)

    def test_same_binary_mask_has_identity_mismatch_without_loss_effect(self):
        result = compare([(0, 0), (1, 1), (2, 0)],
                         [[1, 0], [1, 0]],
                         [[5, -5], [5, -5], [5, -5]])
        self.assertEqual(result["identity_mismatch_pairs"], 1)
        self.assertEqual(result["changed_mask_pairs"], 0)
        self.assertEqual(result["original_bce"], result["corrected_bce"])

    def test_threshold_is_strict_and_score_target_is_hard_iou(self):
        result = compare([(0, 0)], [[1, 0, 0, 0]],
                         [[5, 5, -5, -5]])
        self.assertFalse(result["pairs"][0]["original_score_eligible"])
        self.assertLess(result["pairs"][0]["original_score_target"], 0.5)

    def test_invalid_axes_fail_closed(self):
        for pairs, masks, logits in (
            ([(0, 2)], [[1, 0]], [[1, 0]]),
            ([(0, 0)], [[1, 2]], [[1, 0]]),
            ([(0, 0)], [[1, 0]], [[math.nan, 0]]),
            ([(1, 0)], [[1, 0]], [[1, 0]]),
            ([(0, 0)], [[1, 0]], [[1]]),
        ):
            with self.subTest(pairs=pairs, masks=masks, logits=logits):
                with self.assertRaises(ValueError):
                    compare(pairs, masks, logits)


if __name__ == "__main__":
    unittest.main()
