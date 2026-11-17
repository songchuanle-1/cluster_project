import hashlib
import unittest

from m95_identity_query_controls_20260923 import analyze_class
from m95_failure_partition_20260923 import EXPECTED_MANIFEST_SHA256


class IdentityControlsTest(unittest.TestCase):
    def setUp(self):
        mask = [True, False]
        self.frozen = {
            "manifest_index": 11, "scene_id": "scene0142_00",
            "query_indices": [0, 1, 2],
            "mask_sha256": hashlib.sha256(bytes(mask)).hexdigest(),
            "seeds": [
                {"query": 0, "positive": True, "score": .8, "seed_physical_id": 7},
                {"query": 1, "positive": False, "score": .2, "seed_physical_id": 7},
                {"query": 2, "positive": False, "score": .3, "seed_physical_id": 8},
            ],
        }
        self.row = {
            "manifest_index": 11, "scene": "scene0142_00",
            "fps_superpoints": [0, 1, 2],
            "sampled_seed_indices": [0, 1, 2],
            "native_match_cause": {
                "sampled_pos": [[0, 0, 0], [1, 0, 0], [2, 0, 0]],
                "obj_pos": [[0, 0, 0]], "sampled_instance_labels": [7, 7, 8],
                "object_ids": [7], "nearest_query_per_gt": [0],
                "member_queries_per_gt": [[1]],
                "native_positive": [True, True, False],
            },
        }
        # The matched positive is nearest by coordinate, not a member by label.
        self.row["native_match_cause"].update(
            sampled_instance_labels=[8, 8, 8], object_ids=[9],
            member_queries_per_gt=[[]], native_positive=[True, False, False],
        )
        self.artifact = {
            "artifact_contract": "m95_manifest_native_query_artifact_v1",
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "manifest_index": 11, "axis": {"scene": "scene0142_00"},
            "identity_query": {
                "query_states": [[1., 0.], [0., 1.], [1., 1.]],
                "sampled_seed_indices": [0, 1, 2],
                "sampled_superpoint_ids": [0, 1, 2],
            },
            "native_positive": [True, False, False],
            "query_scores": [.8, .2, .3],
            "query_masks": [[True, False]] * 3,
            "physical_instance_labels": [7, 7, 8],
        }

    def test_pairs_and_controls(self):
        result = analyze_class(self.frozen, self.row, self.artifact)
        self.assertEqual(len(result["same_id_pairs"]), 1)
        self.assertEqual(len(result["matched_distinct_id_controls"]), 1)
        self.assertAlmostEqual(result["same_id_pairs"][0]["score_difference"], .6)

    def test_missing_distinct_id_control_is_reported(self):
        self.artifact["physical_instance_labels"][2] = 7
        self.frozen["seeds"][2]["seed_physical_id"] = 7
        result = analyze_class(self.frozen, self.row, self.artifact)
        self.assertEqual(len(result["same_id_pairs"]), 2)
        self.assertEqual(result["missing_control_pairs"], 2)

    def test_rejects_native_cause_drift(self):
        self.row["native_match_cause"]["nearest_query_per_gt"] = [1]
        with self.assertRaisesRegex(ValueError, "nearest query"):
            analyze_class(self.frozen, self.row, self.artifact)

    def test_rejects_label_drift(self):
        self.artifact["native_positive"][1] = True
        with self.assertRaisesRegex(ValueError, "label"):
            analyze_class(self.frozen, self.row, self.artifact)

    def test_rejects_seed_drift(self):
        self.artifact["identity_query"]["sampled_superpoint_ids"][1] = 2
        with self.assertRaisesRegex(ValueError, "superpoint"):
            analyze_class(self.frozen, self.row, self.artifact)

    def test_rejects_mask_drift(self):
        self.artifact["query_masks"][0] = [False, False]
        with self.assertRaisesRegex(ValueError, "mask hash"):
            analyze_class(self.frozen, self.row, self.artifact)

    def test_rejects_artifact_from_different_manifest_row(self):
        self.artifact["manifest_index"] = 12
        with self.assertRaisesRegex(ValueError, "Manifest index"):
            analyze_class(self.frozen, self.row, self.artifact)

    def test_rejects_frozen_row_from_different_manifest_row(self):
        self.frozen["manifest_index"] = 12
        with self.assertRaisesRegex(ValueError, "Manifest index"):
            analyze_class(self.frozen, self.row, self.artifact)


if __name__ == "__main__":
    unittest.main()
