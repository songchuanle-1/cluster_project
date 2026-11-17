import unittest

import numpy as np

from m95_geometry_support_binding_20260926 import bind_scene


class GeometrySupportBindingTest(unittest.TestCase):
    def test_identical_point_axis(self):
        self.assertEqual(
            bind_scene([10, 30], [0, 1, 1, 0], np.array([10, 30, 30, 10])),
            (2, 4),
        )

    def test_rejects_point_permutation(self):
        with self.assertRaisesRegex(ValueError, "inverse differs"):
            bind_scene([10, 30], [0, 1, 1, 0], np.array([30, 10, 30, 10]))

    def test_rejects_id_shift(self):
        with self.assertRaisesRegex(ValueError, "IDs differ"):
            bind_scene([10, 30], [0, 1, 1, 0], np.array([10, 40, 40, 10]))


if __name__ == "__main__":
    unittest.main()
