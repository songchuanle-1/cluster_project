import math
import unittest

from m95_score_component_control_20260924 import compare


class ScoreComponentTests(unittest.TestCase):
    def test_missing_predictions_remain_unmeasured(self):
        result = compare([(0, 0)], [[1, 0]], [[5, -5]])
        self.assertIsNone(result["score_mse"])
        self.assertIsNone(result["indicator_loss"])

    def test_eligible_sets_are_separate(self):
        result = compare([(0, 0), (1, 1), (2, 0)],
                         [[1, 0], [0, 1]],
                         [[5, -5], [-5, 5], [5, -5]], [0.8, 0.7, 0.6])
        score = result["score_mse"]
        self.assertEqual(score["original_eligible_pairs"], 2)
        self.assertEqual(score["corrected_eligible_pairs"], 3)
        self.assertAlmostEqual(score["original"], (0.2**2 + 0.4**2) / 2, places=5)
        self.assertAlmostEqual(score["corrected"],
                               (0.2**2 + 0.3**2 + 0.4**2) / 3, places=5)
        self.assertEqual(result["indicator_loss"]["positive_queries"], [0, 1, 2])
        self.assertEqual(result["indicator_loss"]["positive_count"], 3)
        self.assertEqual(result["indicator_loss"]["negative_count"], 0)
        self.assertAlmostEqual(
            result["indicator_loss"]["numerator"],
            3 * math.log(1.0 + 1e-6)
            - math.log(0.8) - math.log(0.7) - math.log(0.6),
            places=6,
        )

    def test_empty_eligible_set_is_zero(self):
        result = compare([(0, 0)], [[1, 0]], [[-5, 5]], [0.4])
        self.assertEqual(result["score_mse"]["original"], 0.0)
        self.assertAlmostEqual(
            result["indicator_loss"]["numerator"],
            math.log(1.0 + 1e-6) - math.log(0.4),
            places=6,
        )

    def test_equal_gt_masks_preserve_score_mse(self):
        result = compare([(0, 0), (1, 1), (2, 0)],
                         [[1, 0], [1, 0]],
                         [[5, -5], [5, -5], [5, -5]], [0.1, 0.2, 0.3])
        self.assertEqual(result["score_mse"]["original"],
                         result["score_mse"]["corrected"])

    def test_indicator_loss_is_independent_of_changed_mask_binding(self):
        pairs = [(0, 0), (1, 1), (2, 0)]
        scores = [0.8, 0.7, 0.6]
        original = compare(pairs, [[1, 0], [0, 1]], [[5, -5], [-5, 5], [5, -5]], scores)
        corrected = compare(pairs, [[1, 0], [1, 0]], [[5, -5], [-5, 5], [5, -5]], scores)
        self.assertGreater(original["identity_mismatch_pairs"], 0)
        self.assertEqual(original["indicator_loss"], corrected["indicator_loss"])

    def test_duplicate_positive_query_fails_closed(self):
        with self.assertRaises(ValueError):
            compare([(0, 0), (0, 1)], [[1, 0], [0, 1]],
                    [[5, -5], [-5, 5]], [0.8, 0.7])

    def test_invalid_scores(self):
        for scores in (
            [0.2, 0.3],
            [math.nan],
            [0.0],
            [1.0],
            ["0.2"],
            [True],
        ):
            with self.subTest(scores=scores), self.assertRaises(ValueError):
                compare([(0, 0)], [[1, 0]], [[1, 0]], scores)


if __name__ == "__main__":
    unittest.main()
