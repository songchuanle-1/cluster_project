import unittest
from itertools import product

from m95_repeated_gt_mask_contract_20260924 import audit, mask_binding, mismatch_from_counts


class RepeatedGTMaskContractTest(unittest.TestCase):
    def test_single_gt(self):
        self.assertEqual(mask_binding([0, 0, 0], 1)["mismatched_pair_positions"], [])

    def test_one_match_per_gt(self):
        self.assertEqual(mask_binding([0, 1], 2)["mismatched_pair_positions"], [])

    def test_native_order_extra_first_gt(self):
        self.assertEqual(mask_binding([0, 1, 0], 2)["addressed_mask_gt_ids"], [0, 0, 0])
        self.assertEqual(mask_binding([0, 1, 0], 2)["mismatched_pair_positions"], [1])

    def test_extra_later_gt_can_be_safe(self):
        self.assertEqual(mask_binding([0, 1, 1], 2)["mismatched_pair_positions"], [])

    def test_three_gt(self):
        self.assertEqual(mask_binding([0, 1, 2, 0], 3)["mismatched_pair_positions"], [1, 2])

    def test_invalid_axis(self):
        with self.assertRaises(ValueError):
            mask_binding([0, 2], 2)
        with self.assertRaises(ValueError):
            mask_binding([0, 0], 2)

    def test_count_rule_exhaustive_small_cases(self):
        for n_gt in range(1, 5):
            for counts in product(range(1, 4), repeat=n_gt):
                ids = [gt for gt, count in enumerate(counts) for _ in range(count)]
                binding = mask_binding(ids, n_gt)
                observed = [0] * n_gt
                for position in binding["mismatched_pair_positions"]:
                    observed[ids[position]] += 1
                self.assertEqual(observed, mismatch_from_counts(list(counts)))
                self.assertEqual(sum(observed) == 0, all(c == 1 for c in counts[:-1]))

    def test_earlier_repeat_corrupts_following_gt_only(self):
        self.assertEqual(mismatch_from_counts([2, 1, 3]), [0, 1, 3])
        self.assertEqual(mismatch_from_counts([1, 1, 3]), [0, 0, 0])
        with self.assertRaises(ValueError):
            mismatch_from_counts([1, 0])

    def test_source_hash(self):
        self.assertFalse(audit()["admission"])


if __name__ == "__main__":
    unittest.main()
