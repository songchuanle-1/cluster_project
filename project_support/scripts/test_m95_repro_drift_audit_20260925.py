"""Focused tests for the failed-gate decomposition."""
import copy
import unittest

from m95_repro_drift_audit_20260925 import audit


class DriftAuditTest(unittest.TestCase):
    def setUp(self):
        rows = [{
            "manifest_index": index,
            "scene_id": "scene%04d_00" % index,
            "ann_id": index,
            "deployed_query": 0,
            "ious": [0.75] + [0.0] * 127,
            "scores": [0.9] + [0.0] * 127,
            "score_matched_pair": None,
        } for index in range(256)]
        common = {"contract": "m95_manifest_identity_control_analysis_v1",
                  "manifest": {"sha256": "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"}}
        self.reference = {**common, "source_capture": {
            "sha256": "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
        }, "rows": rows}
        self.candidate = copy.deepcopy(self.reference)
        self.candidate["source_capture"] = {
            "sha256": "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a",
            "checkpoint_sha256": "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e",
        }

    def test_nonselected_drift_does_not_relax_gate(self):
        self.candidate["rows"][4]["ious"][7] = 0.2
        result = audit(self.reference, self.candidate)
        self.assertEqual(result["strict_reproducibility_status"], "fail")
        self.assertEqual(result["selected_iou_changes"], [])
        self.assertEqual(result["iou_drift_queries"][0]["query"], 7)

    def test_threshold_and_selected_change_exposed(self):
        self.candidate["rows"][3]["ious"][0] = 0.4
        result = audit(self.reference, self.candidate)
        self.assertEqual(result["iou_threshold_flips"], [[3, 0]])
        self.assertEqual(result["selected_iou_changes"], [3])

    def test_wrong_capture_fails_closed(self):
        self.candidate["source_capture"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "capture"):
            audit(self.reference, self.candidate)

    def test_pair_numeric_drift_is_not_structural_change(self):
        pair = {"positive_index": 3, "negative_index": 4,
                "tie_break_sha256": "a" * 64, "score_difference": 0.1}
        self.reference["rows"][2]["score_matched_pair"] = pair
        self.candidate["rows"][2]["score_matched_pair"] = dict(
            pair, score_difference=0.1000002
        )
        self.assertEqual(audit(self.reference, self.candidate)["score_matched_pair_changes"], [])
        self.candidate["rows"][2]["score_matched_pair"]["positive_index"] = 5
        self.assertEqual(audit(self.reference, self.candidate)["score_matched_pair_changes"], [2])

    def test_duplicate_row_fails_closed(self):
        self.candidate["rows"][5]["manifest_index"] = 4
        with self.assertRaisesRegex(ValueError, "coverage"):
            audit(self.reference, self.candidate)


if __name__ == "__main__":
    unittest.main()
