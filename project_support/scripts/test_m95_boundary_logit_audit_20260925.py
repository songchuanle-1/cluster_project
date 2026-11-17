import unittest

import torch

from m95_boundary_logit_audit_20260925 import audit


class BoundaryLogitAuditTest(unittest.TestCase):
    def artifact(self, flip=False):
        logits = torch.ones(128, 2)
        logits[103, 0] = 0.01 if flip else -0.01
        masks = logits > 0
        return {"query_mask_logits": logits, "query_masks": masks,
                "target_union": torch.tensor([False, True]),
                "features": {"final": torch.zeros(2, 3)}}

    def test_crossing(self):
        before = {83: self.artifact(), 174: self.artifact()}
        after = {83: self.artifact(True), 174: self.artifact()}
        result = audit(before, after)
        crossing = result["rows"][0]["queries"][0]
        self.assertEqual(crossing["changed_point_count"], 1)
        self.assertEqual(crossing["changed_points"][0]["point_index"], 0)
        self.assertEqual(result["rows"][0]["feature_deltas"]["final"]["max_abs"], 0)
        self.assertFalse(result["admission"])

    def test_inconsistent_mask_fails_closed(self):
        before = {83: self.artifact(), 174: self.artifact()}
        after = {83: self.artifact(True), 174: self.artifact()}
        after[83]["query_masks"][103, 0] = False
        with self.assertRaisesRegex(ValueError, "threshold"):
            audit(before, after)

    def test_nonfinite_fails_closed(self):
        before = {83: self.artifact(), 174: self.artifact()}
        after = {83: self.artifact(True), 174: self.artifact()}
        after[83]["query_mask_logits"][103, 1] = float("nan")
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            audit(before, after)


if __name__ == "__main__":
    unittest.main()
