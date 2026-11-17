import unittest

import torch

from m95_final_stage_drift_20260925 import summarize


class FinalStageDriftTest(unittest.TestCase):
    def artifact(self):
        return {
            "features": {"fused": torch.zeros(3, 2),
                         "final": torch.zeros(3, 2)},
            "target_union": torch.tensor([False, True, True]),
            "query_masks": torch.zeros(128, 3, dtype=torch.bool),
        }

    def test_point_localization(self):
        before = {83: self.artifact(), 174: self.artifact()}
        after = {83: self.artifact(), 174: self.artifact()}
        after[174]["features"]["final"][1] = torch.tensor([0.2, 0.1])
        after[174]["query_masks"][70, 1] = True
        result = summarize(before, after)
        row = result["rows"][1]
        self.assertEqual(row["final_points_above_1e-2"], 1)
        self.assertEqual(row["changed_mask_points"], [1])
        self.assertEqual(row["final_energy_top1_fraction"], 1.0)
        self.assertAlmostEqual(row["changed_mask_point_deltas"][0]["final_max_abs"], 0.2)
        self.assertFalse(result["admission"])

    def test_nonfinite_fails_closed(self):
        before = {83: self.artifact(), 174: self.artifact()}
        after = {83: self.artifact(), 174: self.artifact()}
        after[83]["features"]["final"][0, 0] = float("nan")
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            summarize(before, after)


if __name__ == "__main__":
    unittest.main()
