import unittest

from m95_native_mask_population_20260927 import cohorts


class NativeMaskPopulationTest(unittest.TestCase):
    def test_population_and_disjoint_controls(self):
        rows = [
            {"manifest_index": i, "ious": ([.5] if i < 16 else [.8]),
             "target_superpoints": i + 2}
            for i in range(256)
        ]
        limited, controls = cohorts(rows)
        self.assertEqual(len(limited), 16)
        self.assertEqual(len(controls), 16)
        self.assertFalse(limited & controls)

    def test_count_guard(self):
        with self.assertRaises(ValueError):
            cohorts([
                {"manifest_index": i, "ious": [.5],
                 "target_superpoints": 1} for i in range(256)
            ])


if __name__ == "__main__":
    unittest.main()
