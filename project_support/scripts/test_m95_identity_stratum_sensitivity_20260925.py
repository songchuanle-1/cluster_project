import unittest

from m95_identity_stratum_sensitivity_20260925 import (
    attach_pair_metadata,
    peer_count_bucket,
    sensitivity_summary,
)


def pair(manifest_index, scene_id, identity, score):
    return {
        "manifest_index": manifest_index,
        "scene_id": scene_id,
        "pair_key": [manifest_index, manifest_index, manifest_index + 100],
        "identity_matches_iou": identity,
        "score_matches_iou": score,
        "identity_only_matches_iou": identity and not score,
        "score_only_matches_iou": score and not identity,
        "identity_disagrees_with_score": identity != score,
    }


class StratumSensitivityTest(unittest.TestCase):
    def test_peer_count_buckets(self):
        self.assertEqual(peer_count_bucket(1), "1")
        self.assertEqual(peer_count_bucket(2), "2-3")
        self.assertEqual(peer_count_bucket(3), "2-3")
        self.assertEqual(peer_count_bucket(4), "4+")
        with self.assertRaises(ValueError):
            peer_count_bucket(0)

    def test_metadata_is_attached_by_manifest_index(self):
        rows = attach_pair_metadata(
            [pair(0, "scene-a", True, False)],
            {0: {"target_class": "chair", "peer_count": 2}},
        )
        self.assertEqual(rows[0]["target_class"], "chair")
        self.assertEqual(rows[0]["peer_count_bucket"], "2-3")

    def test_leave_one_out_detects_single_class_concentration(self):
        rows = [
            pair(0, "scene-a", True, False),
            pair(1, "scene-b", True, False),
            pair(2, "scene-c", False, True),
            pair(3, "scene-d", False, True),
        ]
        metadata = {
            0: {"target_class": "driver", "peer_count": 1},
            1: {"target_class": "driver", "peer_count": 2},
            2: {"target_class": "control", "peer_count": 1},
            3: {"target_class": "control", "peer_count": 2},
        }
        result = sensitivity_summary(rows, metadata)
        self.assertFalse(
            result["stability"]["all_leave_one_class_out_positive"]
        )
        self.assertLessEqual(
            result["stability"]["minimum_leave_one_class_out"],
            0.0,
        )
        self.assertEqual(
            result["stability"]["represented_classes"],
            ["control", "driver"],
        )

    def test_all_leave_one_out_positive_is_reported(self):
        rows = [
            pair(0, "scene-a", True, False),
            pair(1, "scene-b", True, False),
            pair(2, "scene-c", True, False),
            pair(3, "scene-d", True, False),
            pair(4, "scene-e", True, False),
            pair(5, "scene-f", True, False),
        ]
        metadata = {
            0: {"target_class": "alpha", "peer_count": 1},
            1: {"target_class": "alpha", "peer_count": 1},
            2: {"target_class": "beta", "peer_count": 2},
            3: {"target_class": "beta", "peer_count": 2},
            4: {"target_class": "gamma", "peer_count": 4},
            5: {"target_class": "gamma", "peer_count": 4},
        }
        result = sensitivity_summary(rows, metadata)
        self.assertTrue(
            result["stability"]["all_leave_one_class_out_positive"]
        )
        self.assertGreater(
            result["stability"]["minimum_leave_one_class_out"],
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
