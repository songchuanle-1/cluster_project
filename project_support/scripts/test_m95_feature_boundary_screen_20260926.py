import unittest
import numpy as np
from m95_feature_boundary_screen_20260926 import contrast


class FeatureBoundaryTest(unittest.TestCase):
    def test_instance_boundary_and_internal_edge(self):
        f = np.array([[1., 0.], [1., 0.], [0., 1.]])
        got = contrast(f, [[0, 1], [1, 2]], [1, 1, 0], [5, 5, 6])
        self.assertEqual(got["inside"]["edges"], 1)
        self.assertEqual(got["cross"]["edges"], 1)
        self.assertEqual(got["same_instance_cross"]["edges"], 0)
        self.assertEqual(got["different_instance_cross"]["mean"], 1.0)

    def test_zero_norm_is_excluded(self):
        got = contrast([[0., 0.], [1., 0.]], [[0, 1]], [1, 0], [1, 2])
        self.assertEqual(got["cross"]["edges"], 0)
        self.assertIsNone(got["cross"]["mean"])

    def test_axis_rejection(self):
        with self.assertRaisesRegex(ValueError, "axes differ"):
            contrast([[1., 0.]], [[0, 1]], [1, 0], [1, 2])


if __name__ == "__main__":
    unittest.main()
