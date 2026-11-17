"""Tests for the exact-capture identity reproducibility gate."""
import copy
import unittest

import m95_exact_capture_reproducibility_20260925 as reproducibility


class ReproducibilityTest(unittest.TestCase):
    def document(self, index=0):
        return {
            "contract": "m95_manifest_identity_control_analysis_v1",
            "source_capture": {
                "sha256": reproducibility.REFERENCE_CAPTURE_SHA256,
                "checkpoint_sha256": reproducibility.EXPECTED_CHECKPOINT_SHA256,
            },
            "manifest": {"sha256": reproducibility.EXPECTED_MANIFEST_SHA256},
            "rows": [
                {
                    "manifest_index": row,
                    "scene_id": "scene%04d_00" % row,
                    "ann_id": row,
                    "stratum": "ambiguous",
                    "query_count": 2,
                    "deployed_query": 0,
                    "target_positive_query": 1,
                    "target_objectness_query": 1,
                    "class_matched_selector_query": 1,
                    "class_matched_non_target_query": 0,
                    "native_positive": [False, True],
                    "dominant_instance": [1, 2],
                    "fps_seed_inside_target": [False, True],
                    "scores": [0.25, 0.75],
                    "ious": [0.0, 1.0],
                    "stage_identity": {
                        "final": {
                            "cosine_to_target": 1.0,
                            "cosine_to_same_class_peer": 0.5,
                            "margin": 0.5,
                        }
                    },
                    "score_matched_pair": {
                        "positive_index": 1,
                        "negative_index": 0,
                        "score_difference": 0.5,
                        "tie_break_sha256": "a" * 64,
                    },
                    "positive_minus_deployed_iou": 1.0,
                    "class_selector_minus_deployed_iou": 1.0,
                    "objectness_minus_deployed_iou": 1.0,
                    "class_non_target_minus_deployed_iou": 0.0,
                    "primary_pair_iou_uplift": 1.0,
                    "primary_pair_score_difference": 0.5,
                }
                for row in range(256)
            ],
        }

    def test_exact_identity_analysis_passes(self):
        result = reproducibility.compare_identity_analyses(
            self.document(), self.document()
        )
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["comparison"]["mismatch_count"], 0)
        self.assertEqual(result["comparison"]["selector_mismatches"], 0)

    def test_selector_mismatch_fails_closed(self):
        candidate = self.document()
        candidate["rows"][7]["target_positive_query"] = 0
        result = reproducibility.compare_identity_analyses(
            self.document(), candidate
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["comparison"]["selector_mismatches"], 1)

    def test_score_tolerance_is_enforced(self):
        candidate = self.document()
        candidate["rows"][5]["scores"][1] += 1e-4
        result = reproducibility.compare_identity_analyses(
            self.document(), candidate
        )
        self.assertEqual(result["status"], "fail")
        self.assertGreater(
            result["comparison"]["maximum_score_delta"], 1e-6
        )

    def test_mask_iou_drift_is_enforced(self):
        candidate = self.document()
        candidate["rows"][11]["ious"][1] = 0.5
        result = reproducibility.compare_identity_analyses(
            self.document(), candidate
        )
        self.assertEqual(result["status"], "fail")
        self.assertGreater(result["comparison"]["maximum_iou_delta"], 1e-6)

    def test_identity_feature_drift_is_enforced(self):
        candidate = self.document()
        candidate["rows"][3]["stage_identity"]["final"]["margin"] = 0.25
        result = reproducibility.compare_identity_analyses(
            self.document(), candidate
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(
            result["comparison"]["identity_feature_mismatches"], 1
        )

    def test_wrong_checkpoint_fails_before_compare(self):
        candidate = self.document()
        candidate["source_capture"]["checkpoint_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            reproducibility.compare_identity_analyses(
                self.document(), candidate
            )

    def test_duplicate_rows_fail(self):
        candidate = self.document()
        candidate["rows"][4] = copy.deepcopy(candidate["rows"][3])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            reproducibility.compare_identity_analyses(
                self.document(), candidate
            )


if __name__ == "__main__":
    unittest.main()
