"""Focused exhaustive checks for the point-level support ceiling."""
import itertools
import unittest

import numpy as np

from m95_superpoint_oracle_20260926 import oracle


class OracleTests(unittest.TestCase):
    def test_exact_prefix_matches_exhaustive_subsets(self):
        for target_bits in itertools.product((0, 1), repeat=6):
            if not any(target_bits):
                continue
            labels = np.array(target_bits, dtype=bool)
            counts = np.array([0, 0, 1, 1, 2, 2])
            result = oracle(counts, labels)
            brute = 0.0
            for selected in itertools.product((False, True), repeat=3):
                mask = np.asarray(selected)[counts]
                union = np.count_nonzero(mask | labels)
                score = np.count_nonzero(mask & labels) / max(1, union)
                brute = max(brute, score)
            self.assertAlmostEqual(result["best_iou"], brute)

    def test_no_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Target absent"):
            oracle(np.array([0, 0, 1]), np.zeros(3, dtype=bool))


if __name__ == "__main__":
    unittest.main()
