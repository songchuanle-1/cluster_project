import unittest

from m95_failure_partition_20260923 import (
    EXPECTED_MANIFEST_SHA256, feature_audit, identity, mask_support, row_audit, summarize,
)


def fixture(ious=None, positive=None, seed=None):
    ious = [0.2, 0.8, 0.7] if ious is None else ious
    positive = [False, True, True] if positive is None else positive
    seed = positive if seed is None else seed
    m = {"manifest_index": 0, "scene_id": "s", "ann_id": 1,
         "target_object_id": "2", "same_class_peer_object_ids": ["3"]}
    r = {"manifest_index": 0, "scene_id": "s", "ann_id": 1, "stratum": "ambiguous",
         "query_count": 3, "scores": [0.9, 0.8, 0.7], "ious": ious,
         "native_positive": positive, "fps_seed_inside_target": seed,
         "dominant_instance": [3, 2, 2], "deployed_query": 0, "deployed_iou": ious[0],
         "target_positive_query": next((i for i, v in enumerate(positive) if v), None),
         "target_objectness_query": next((i for i, v in enumerate(seed) if v), None),
         "score_matched_pair": None}
    return r, m


class PartitionTests(unittest.TestCase):
    def test_partition_cases_and_threshold(self):
        cases = [
            ([0.6, 0.8, 0.7], [False, True, True], "deployed_success"),
            ([0.5, 0.5, 0.0], [False, True, True], "no_acceptable_query"),
            ([0.2, 0.8, 0.7], [False, False, False], "recoverable_no_native_positive"),
            ([0.2, 0.8, 0.7], [True, False, False], "recoverable_positive_set_excludes_acceptable"),
            ([0.2, 0.8, 0.7], [False, True, True], "recoverable_positive_selector_repairs"),
            ([0.2, 0.4, 0.8], [False, True, True], "recoverable_within_positive_score_failure"),
        ]
        for ious, positive, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(row_audit(*fixture(ious, positive))["partition"], expected)

    def test_exact_overlap_not_iou_equivalence(self):
        r, m = fixture(seed=[False, False, True])
        r["ious"][2] = r["ious"][1]
        detail = row_audit(r, m)
        self.assertTrue(detail["common_support"])
        self.assertFalse(detail["same_selected_query"])
        self.assertEqual(detail["best_acceptable_score_rank"], 2)

    def test_missing_control_no_fallback(self):
        detail = row_audit(*fixture(seed=[False] * 3))
        self.assertIsNone(detail["same_selected_query"])
        self.assertFalse(detail["common_support"])

    def test_pair_can_overlap_positive_set(self):
        r, m = fixture(positive=[True, True, True])
        r["score_matched_pair"] = {"positive_index": 1, "negative_index": 0}
        self.assertTrue(row_audit(r, m)["pair"]["negative_also_native_positive"])
        r["score_matched_pair"]["negative_index"] = 2
        with self.assertRaises(ValueError):
            row_audit(r, m)

    def test_invalid_axes_and_nan_rejected(self):
        for field, value in (("scores", [1]), ("scores", [float("nan"), 0.8, 0.7]),
                             ("native_positive", [0, 1, 1])):
            r, m = fixture()
            r[field] = value
            with self.assertRaises(ValueError):
                row_audit(r, m)

    def test_identity_and_mixed_support_orthogonal(self):
        _, m = fixture()
        self.assertEqual(identity(None, m), "no_instance")
        self.assertEqual(identity(99, m), "outside_target_and_registered_peers")
        support = mask_support([True] * 3, [True, False, False], [2, 3, -1], {"3"})
        self.assertTrue(support["mixed_known_instance_support"])
        self.assertEqual(support["target_fraction"], 1 / 3)

    def test_feature_self_overlap_and_missing_peer(self):
        r, m = fixture(ious=[0, 1, 1])
        r["dominant_instance"] = [3, 2, 2]
        detail = row_audit(r, m)
        a = {
            "artifact_contract": "m95_manifest_native_query_artifact_v1",
            "manifest_sha256": EXPECTED_MANIFEST_SHA256, "manifest_index": 0,
            "physical_instance_labels": [2, 3], "target_union": [True, False],
            "query_masks": [[False, True], [True, False], [True, False]],
            "query_scores": r["scores"], "native_positive": r["native_positive"],
            "fps_seed_inside_target": r["fps_seed_inside_target"],
            "features": {"final": [[1, 0], [0, 1]]},
        }
        result = feature_audit(a, r, m, detail)
        self.assertEqual(result["stages"]["final"]["overlapping_acceptable_minus_deployed"], 2)
        self.assertIsNone(result["stages"]["final"]["query_excluded_acceptable_minus_deployed"])
        self.assertTrue(result["support"]["acceptable"]["exactly_target_union"])
        m["same_class_peer_object_ids"] = []
        result = feature_audit(a, r, m, detail)
        self.assertIsNone(result["stages"]["final"]["overlapping_acceptable_minus_deployed"])

    def test_summary_missing_features_not_zero(self):
        result = summarize([row_audit(*fixture())])
        self.assertEqual(result["features"]["stages"]["final"]["overlapping"]["available"], 0)
        self.assertEqual(result["features"]["stages"]["final"]["overlapping"]["missing_of_recoverable"], 1)


if __name__ == "__main__":
    unittest.main()
