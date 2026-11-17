import unittest

from m95_fullscan_score_drift_20260926 import summarize


class ScoreDriftTest(unittest.TestCase):
    def test_fps_groups_and_deployed_invariance(self):
        reference = {"rows": []}
        candidate = {"rows": []}
        for index in range(256):
            reference["rows"].append({
                "manifest_index": index,
                "scores": [0.2, 0.8],
                "ious": [0.0, 0.5],
                "deployed_query": 1,
                "deployed_iou": 0.5,
            })
            candidate["rows"].append({
                "manifest_index": index,
                "scores": [0.2 + (2e-6 if index == 4 else 0), 0.8],
                "ious": [0.0, 0.5 + (0.01 if index == 83 else 0)],
                "deployed_query": 1,
                "deployed_iou": 0.5,
            })
        census = {"indices": {
            "entry_fps_differ": [4],
            "assignment_differ": [[4], [], []],
        }}
        result = summarize(reference, candidate, census)
        self.assertEqual(result["groups"]["fps_changed"]["rows"], 1)
        self.assertEqual(result["groups"]["fps_changed"]["score_drift_rows"], 1)
        self.assertEqual(result["groups"]["fps_unchanged"]["iou_drift_rows"], 1)
        self.assertEqual(result["groups"]["fps_changed"]["selected_query_changes"], 0)
        self.assertEqual(result["all_iou_drift_rows"][0]["manifest_index"], 83)

    def test_rejects_missing_query(self):
        reference = {"rows": [{"manifest_index": i, "scores": [0], "ious": [0],
                               "deployed_query": 0, "deployed_iou": 0}
                              for i in range(256)]}
        candidate = {"rows": [dict(row) for row in reference["rows"]]}
        candidate["rows"][7]["scores"] = [0, 1]
        census = {"indices": {"entry_fps_differ": [], "assignment_differ": [[], [], []]}}
        with self.assertRaisesRegex(ValueError, "Query axis"):
            summarize(reference, candidate, census)


if __name__ == "__main__":
    unittest.main()
