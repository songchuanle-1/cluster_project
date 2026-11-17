import unittest

from m95_failure_followup_20260923 import (
    STAGES, decompose_pairs, keyed, matched_features, semantic_rows,
    supervision_row, support_details,
)
from m95_failure_partition_20260923 import EXPECTED_MANIFEST_SHA256, feature_audit, row_audit
from test_m95_failure_partition_20260923 import fixture


class FollowupTests(unittest.TestCase):
    def test_duplicate_index_rejected(self):
        with self.assertRaises(ValueError):
            keyed([{"manifest_index": 0}] * 2)

    def test_matched_support_not_unmatched_means(self):
        rows = []
        for i, (overlap, excluded) in enumerate(((1.0, 0.25), (100.0, None))):
            rows.append({"manifest_index": i, "scene_id": str(i), "features": {"stages": {
                stage: {"overlapping_acceptable_minus_deployed": overlap,
                        "query_excluded_acceptable_minus_deployed": excluded} for stage in STAGES}}})
        result = matched_features(rows, draws=20)["final"]
        self.assertEqual(result["overlap"]["pooled_mean"], 1)
        self.assertEqual(result["excluded_minus_overlap"]["pooled_mean"], -0.75)
        self.assertEqual(result["missing_indices"], [1])

    def test_pairs_original_preserved_with_overlapping_labels(self):
        row, m = fixture(positive=[True] * 3)
        row["score_matched_pair"] = {"positive_index": 1, "negative_index": 0}
        result = decompose_pairs({0: row}, [row_audit(row, m)], draws=20)
        self.assertEqual(result["groups"]["original_unchanged"]["available"], 1)
        self.assertAlmostEqual(result["groups"]["original_unchanged"]["pooled_mean"], 0.6)
        self.assertEqual(result["groups"]["negative_also_positive"]["available"], 1)
        self.assertEqual(result["groups"]["negative_not_positive"]["available"], 0)

    def test_missing_seed_does_not_fall_back(self):
        row, m = fixture(seed=[False] * 3)
        result = supervision_row(row, row_audit(row, m), m)
        self.assertIsNone(result["seed"])
        self.assertEqual(result["positive_minus_seed_indices"], [1, 2])

    def test_seed_positive_contract_rejects_mismatch(self):
        row, m = fixture(positive=[False, True, True], seed=[True, True, True])
        with self.assertRaises(ValueError):
            supervision_row(row, row_audit(row, m), m)

    def test_structural_missingness_not_zero(self):
        row, m = fixture(ious=[0, 1, 1])
        row["dominant_instance"] = [3, 2, 2]
        detail = row_audit(row, m)
        artifact = {
            "artifact_contract": "m95_manifest_native_query_artifact_v1",
            "manifest_sha256": EXPECTED_MANIFEST_SHA256, "manifest_index": 0,
            "physical_instance_labels": [2, 3], "target_union": [True, False],
            "query_masks": [[False, True], [True, False], [True, False]],
            "query_scores": row["scores"], "native_positive": row["native_positive"],
            "fps_seed_inside_target": row["fps_seed_inside_target"],
            "features": {"final": [[1, 0], [0, 1]]},
        }
        detail["features"] = feature_audit(artifact, row, m, detail)
        result = support_details(artifact, row, detail, m)
        self.assertEqual(result["missing_reasons"],
                         ["deployed_exhausts_peer_prototype", "acceptable_exhausts_target_prototype"])
        self.assertTrue(result["support"]["acceptable"]["exactly_target_union"])

    def test_semantic_absence_and_conflict_not_cross_class(self):
        row, m = fixture()
        m["target_class"] = "chair"
        row["dominant_instance"][0] = 99
        detail = row_audit(row, m)
        entries = [{"scene_id": "s", "object_id": "2", "object_name": "chair"}]
        result = semantic_rows(entries, {0: row}, [detail], {0: m})[0]
        self.assertEqual(result["classification"], "unresolved_missing_or_conflicting_annotation")
        entries.append({"scene_id": "s", "object_id": "99", "object_name": "table"})
        result = semantic_rows(entries, {0: row}, [detail], {0: m})[0]
        self.assertEqual(result["classification"], "different_annotation_class")
        entries.append({"scene_id": "s", "object_id": "99", "object_name": "chair"})
        result = semantic_rows(entries, {0: row}, [detail], {0: m})[0]
        self.assertEqual(result["classification"], "unresolved_missing_or_conflicting_annotation")


if __name__ == "__main__":
    unittest.main()
