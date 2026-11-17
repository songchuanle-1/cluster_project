import unittest

from m95_group_predicted_peer_20260926 import pair_geometry
from m95_group_predicted_peer_analyze_20260926 import analyze


class PredictedPeerTest(unittest.TestCase):
    def test_blind_pair_and_rotation(self):
        masks = [[1, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0],
                 [0, 0, 1, 0]]
        xyz = [[0, 0, 0], [1, 0, 1], [4, 0, 2], [8, 0, 3]]
        result = pair_geometry(masks, xyz)
        self.assertEqual(result["true"][0], 2)
        self.assertEqual(result["shuffled"][0], 3)
        self.assertNotIn(1, result["true"].values())

    def test_support_fails_closed(self):
        with self.assertRaises(ValueError):
            pair_geometry([[True, False]], [[0, 0, 0]])

    def test_posthoc_attribution_replays_blind_pairs(self):
        masks = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        xyz = [[0, 0, 0], [1, 0, 1], [2, 0, -1]]
        geometry = pair_geometry(masks, xyz)
        row = {
            "cohort": "lower", "scene": "scene0", "ann_id": 1, "target": "4",
            "masks": masks, "xyz": xyz, "target_mask": [1, 0, 0],
            "physical_labels": [4, 5, 6],
            "same_name_peer_ids": [5],
            "true_peer": geometry["true"], "shuffled_peer": geometry["shuffled"],
        }
        result = analyze({"contract": "m95_group_predicted_peer_v1",
                          "rows": [row]})
        self.assertEqual(result["summary"]["lower"]["true_positive_units"], 1)
        self.assertEqual(result["summary"]["lower"]["shuffled_positive_units"], 0)
        row["true_peer"][0] = 2
        with self.assertRaises(ValueError):
            analyze({"contract": "m95_group_predicted_peer_v1", "rows": [row]})


if __name__ == "__main__":
    unittest.main()
