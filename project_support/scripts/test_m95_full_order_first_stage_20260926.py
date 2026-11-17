import unittest
from unittest.mock import patch

from m95_full_order_first_stage_20260926 import compare_snapshots


class FirstStageComparatorTest(unittest.TestCase):
    def test_stage_order_and_delta(self):
        keys = ("input", "input_indices", "first", "first_indices",
                "sparse", "sparse_indices")
        left = {key: key + "_a" for key in keys}
        right = {key: key + "_b" for key in keys}
        with patch("m95_full_order_first_stage_20260926.digest",
                   side_effect=lambda value: value), patch(
                       "m95_full_order_first_stage_20260926.compare_tensors",
                       side_effect=lambda a, b: (a, b)):
            result = compare_snapshots(left, right)
        self.assertEqual(list(result), list(keys))
        self.assertEqual(result["input"]["delta"], ("input_a", "input_b"))
        self.assertEqual(result["sparse_indices"]["replay_sha256"],
                         "sparse_indices_b")


if __name__ == "__main__":
    unittest.main()
