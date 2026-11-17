import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from m95_semantic_identity_recovery_20260922 import (
    classify_pair,
    collect_unresolved_pairs,
    phrases_match,
)


class CollectUnresolvedPairsTest(unittest.TestCase):
    def test_phrase_match_handles_hypernyms_and_multiword_heads(self):
        self.assertTrue(phrases_match("monitor", "computer monitor"))
        self.assertTrue(phrases_match("chair", "wood chair"))
        self.assertFalse(phrases_match("pillow", "wood chair"))

    def test_classify_pair(self):
        self.assertEqual(classify_pair({"same_class_phrase": True}), "same-class")
        self.assertEqual(
            classify_pair({"same_class_phrase": False}), "cross-class-name"
        )

    def test_rejects_wrong_failure_count(self):
        with self.assertRaises(ValueError):
            collect_unresolved_pairs({"rows": []})

    def test_extracts_target_and_top_wrong_instance(self):
        unresolved = {
            "scene": "scene0000_00",
            "ann_id": 1,
            "dataset_index": 7,
            "selected_query": 0,
            "ious": [0.0],
            "target_instances": [3],
            "selected_mask_endpoints": {
                "overlaps": [
                    {"instance": 4, "iou": 0.1, "semantic_class": -100},
                    {"instance": 5, "iou": 0.9, "semantic_class": -100},
                ]
            },
        }
        resolved = {
            "scene": "scene0001_00",
            "ann_id": 2,
            "dataset_index": 8,
            "selected_query": 0,
            "ious": [0.0],
            "target_instances": [3],
            "selected_mask_endpoints": {
                "overlaps": [
                    {"instance": 4, "iou": 0.1, "semantic_class": 4},
                    {"instance": 5, "iou": 0.9, "semantic_class": 5},
                ]
            },
        }
        capture = {
            "rows": [unresolved] * 6 + [resolved] * 2,
        }
        rows = collect_unresolved_pairs(capture)
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["target_instance"], 3)
        self.assertEqual(rows[0]["wrong_instance"], 5)


if __name__ == "__main__":
    unittest.main()
