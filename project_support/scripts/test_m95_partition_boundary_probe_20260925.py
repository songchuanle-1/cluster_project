import unittest

from m95_partition_boundary_probe_20260925 import boundary_observation


class BoundaryProbeTest(unittest.TestCase):
    def test_nearest_margin(self):
        result = boundary_observation(
            [0.25, 0.0], [[0.0, 0.0], [1.0, 0.0]], 0, [0.25, 0.75])
        self.assertEqual(result["distance_margin"], 0.5)
        self.assertEqual(result["second_center_id"], 1)

    def test_exact_tie_uses_first_center(self):
        result = boundary_observation(
            [0.5], [[0.0], [1.0]], 0, [0.5, 0.5])
        self.assertEqual(result["distance_margin"], 0)
        with self.assertRaisesRegex(ValueError, "assignment"):
            boundary_observation([0.5], [[0.0], [1.0]], 1, [0.5, 0.5])

    def test_mismatched_distance_fails(self):
        with self.assertRaisesRegex(ValueError, "distance"):
            boundary_observation([0.25], [[0.0], [1.0]], 0, [0.25, 0.5])

    def test_float32_cancellation_near_large_coordinates(self):
        result = boundary_observation(
            [100.001, 100.0], [[100.0, 100.0], [101.0, 100.0]],
            0, [0.0, 0.999])
        self.assertEqual(result["recorded_assignment"], 0)

    def test_invalid_coordinate_fails(self):
        with self.assertRaisesRegex(ValueError, "coordinate"):
            boundary_observation([float("nan")], [[0.0], [1.0]], 0, [0.0, 1.0])

    def test_missing_native_row_fails(self):
        with self.assertRaisesRegex(ValueError, "Native cdist"):
            boundary_observation([0.25], [[0.0], [1.0]], 0)


if __name__ == "__main__":
    unittest.main()
