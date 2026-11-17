import unittest

from m95_target_seed_extent_20260927 import analyze
from test_m95_target_seed_full_population_20260927 import fixture


class TargetSeedExtentTest(unittest.TestCase):
    def setUp(self):
        self.source = fixture()
        for row in self.source["rows"]:
            row["physical_instance_labels"] = [1, 1, 2, 2]
            row["selected_mask"] = [True, True, False, False]
            row["ious"] = [1.0] * 128
        row = self.source["rows"][0]
        row["selected_mask"] = [True, False, False, False]
        row["ious"][0] = .5

    def test_target_undercoverage(self):
        result = analyze(self.source)
        self.assertEqual(result["failure_expressions"], 1)
        self.assertEqual(result["dominant_counts"]["undercoverage"], 1)
        self.assertEqual((result["rows"][0]["tp"], result["rows"][0]["fp"],
                          result["rows"][0]["fn"]), (1, 0, 1))

    def test_contamination(self):
        self.source["rows"][0]["selected_mask"] = [True, True, True, True]
        self.source["rows"][0]["ious"][0] = .5
        self.assertEqual(analyze(self.source)["dominant_counts"]["contamination"], 1)

    def test_iou_guard(self):
        self.source["rows"][0]["ious"][0] = .4
        with self.assertRaises(ValueError):
            analyze(self.source)

    def test_mask_axis_guard(self):
        self.source["rows"][0]["selected_mask"] = [True]
        with self.assertRaises(ValueError):
            analyze(self.source)

    def test_provenance_guard(self):
        self.source["producer_sha256"] = "other"
        with self.assertRaises(ValueError):
            analyze(self.source)


if __name__ == "__main__":
    unittest.main()
