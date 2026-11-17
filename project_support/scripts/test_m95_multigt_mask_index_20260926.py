import unittest

from m95_multigt_mask_index_20260926 import audit


class NativeMaskIndexTest(unittest.TestCase):
    def test_single_gt_unaffected_and_multi_gt_affected(self):
        capture = {
            "producer_sha256": "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a",
            "capture_mode": "full_train_scan", "native_match_cause_completed": True,
            "rows": [],
        }
        for i in range(256):
            multi = i == 1
            pairs = [[0, 0], [1, 1], [2, 0]] if multi else [[0, 0], [1, 0]]
            capture["rows"].append({
                "manifest_index": i, "scene": "scene%03d" % i, "ann_id": i,
                "stratum": "ambiguous" if i < 128 else "class_unique",
                "target_instances": [10, 11] if multi else [10],
                "selected_query": 0, "ious": [0.0 if multi else 0.9],
                "native_match_cause": {
                    "object_ids": [10, 11] if multi else [10],
                    "matched_query_gt_pairs": pairs,
                    "native_positive": [True] * len(pairs),
                },
            })
        result = audit(capture)
        self.assertEqual(result["summary"]["all"]["multi_gt"], 1)
        self.assertEqual(result["summary"]["all"]["affected"], 1)
        self.assertEqual(result["rows"][1]["affected_queries"], [1])

    def test_mismatched_positive_axis_rejected(self):
        capture = {"producer_sha256": "206c594d8c5219c6e249d89f7cb91815467bd443a030bc8bbd76d457de0b485a",
                   "capture_mode": "full_train_scan", "native_match_cause_completed": True,
                   "rows": [{"native_match_cause": {
                       "object_ids": [10], "matched_query_gt_pairs": [[0, 0]],
                       "native_positive": [False]}}],
                   }
        capture["rows"][0].update(target_instances=[10])
        with self.assertRaisesRegex(ValueError, "positive axis"):
            audit(capture)


if __name__ == "__main__":
    unittest.main()
