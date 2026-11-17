import unittest

from native_feature_contrasts_20260916 import retrieval


class Tests(unittest.TestCase):
    def test_separated(self):
        result = retrieval([[1, 0], [1, 0], [0, 1], [0, 1]],
                           [0, 0, 1, 1], [1, 1, 0, 0])
        self.assertEqual(result["target_accuracy"], 1.)
        self.assertEqual(result["target_mean_margin"], 1.)

    def test_singleton_excluded(self):
        result = retrieval([[1, 0], [0, 1], [0, 1]], [0, 1, 1], [1, 0, 0])
        self.assertEqual(result["eligible"], 2)
        self.assertIsNone(result["target_accuracy"])

    def test_self_excluded(self):
        result = retrieval([[1, 0], [0, 1], [1, 0], [1, 0]],
                           [0, 0, 1, 1], [1, 0, 0, 0])
        self.assertEqual(result["target_accuracy"], 0.)
        self.assertEqual(result["target_mean_margin"], -1.)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            retrieval([[float("nan")]], [0], [1])
        with self.assertRaises(ValueError):
            retrieval([[1]], [0, 1], [1])

    def test_background_excluded(self):
        result = retrieval([[1, 1], [1, 0], [1, 0], [0, 1], [0, 1]],
                           [-100, 0, 0, 1, 1], [0, 1, 1, 0, 0])
        self.assertEqual(result["eligible"], 4)


if __name__ == "__main__":
    unittest.main()
