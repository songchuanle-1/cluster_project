import unittest

from m95_positive_coverage_20260927 import choose


class PositiveCoverageTest(unittest.TestCase):
    def test_highest_iou_positive(self):
        row = {"ious": [.9, .2, .4] + [0.] * 125,
               "native_positive": [False, True, True] + [False] * 125}
        self.assertEqual(choose(row), 2)

    def test_tie_breaks_by_query(self):
        row = {"ious": [.1, .4, .4] + [0.] * 125,
               "native_positive": [False, True, True] + [False] * 125}
        self.assertEqual(choose(row), 1)

    def test_empty_positive(self):
        self.assertIsNone(choose({
            "ious": [0.] * 128, "native_positive": [False] * 128}))

    def test_axis_guard(self):
        with self.assertRaises(ValueError):
            choose({"ious": [0.], "native_positive": [False] * 128})


if __name__ == "__main__":
    unittest.main()
