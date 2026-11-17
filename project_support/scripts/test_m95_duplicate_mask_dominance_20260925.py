"""Tests for the M95 duplicate-mask dominance diagnostic."""
import unittest
from unittest import mock

import m95_duplicate_mask_dominance_20260925 as module


class DuplicateMaskDominanceTest(unittest.TestCase):
    def setUp(self):
        self.queries_patch = mock.patch.object(module, "EXPECTED_QUERIES", 3)
        self.queries_patch.start()

    def tearDown(self):
        self.queries_patch.stop()

    def test_top_score_query_uses_stable_index_tie_break(self):
        self.assertEqual(module.top_score_query([0.5, 0.5]), 0)

    def test_iou_handles_empty_union(self):
        self.assertEqual(module.iou([False, False], [False, False]), 0.0)

    def test_duplicate_summary_counts_high_score_wrong_cluster(self):
        masks = [
            [True, True, False, False],
            [True, True, False, False],
            [False, False, True, True],
        ]
        scores = [0.9, 0.8, 0.7]
        result = module.duplicate_mask_summary(
            masks, scores, [False, False, True, True], 0
        )
        self.assertEqual(result["duplicate_query_count"], 1)
        self.assertEqual(result["target_query_count"], 1)
        self.assertEqual(result["duplicates_above_best_target"], 1)
        self.assertEqual(result["target_queries_above_selected"], 0)
        self.assertEqual(result["duplicate_target_matches"], 0)

    def test_duplicate_summary_counts_target_overlap(self):
        masks = [
            [True, True, True, False],
            [True, True, True, True],
            [False, False, True, True],
        ]
        scores = [0.9, 0.8, 0.7]
        result = module.duplicate_mask_summary(
            masks, scores, [True, True, True, False], 0
        )
        self.assertEqual(result["duplicate_target_matches"], 1)
        self.assertEqual(result["target_query_count"], 2)

    def test_analyze_rows_validates_capture_iou(self):
        row = {
            "manifest_index": 0,
            "scene": "scene0001_00",
            "scores": [0.9, 0.8, 0.7],
            "selected_query": 0,
            "ious": [0.0, 0.0, 1.0],
            "native_positive": [False, True, True],
        }
        artifact = {
            "manifest_index": 0,
            "query_masks": [
                [True, True, False, False],
                [True, True, False, False],
                [False, False, True, True],
            ],
            "target_union": [False, False, True, True],
            "physical_instance_labels": [1, 1, 2, 2],
        }
        result = module.analyze_rows([row], {0: artifact})
        self.assertEqual(result["summary"]["failed_rows"], 1)

    def test_summarize_rows_reports_competition_counts(self):
        rows = [{
            "failed": True,
            "duplicate_query_count": 2,
            "target_query_count": 1,
            "duplicates_above_best_target": 1,
            "target_queries_above_selected": 0,
            "duplicate_target_matches": 0,
        }]
        result = module.summarize_rows(rows)
        self.assertEqual(result["failed_with_duplicate_query"], 1)
        self.assertEqual(
            result["failures_with_duplicate_above_best_target"], 1
        )

    def test_duplicate_summary_requires_selected_query(self):
        with self.assertRaisesRegex(ValueError, "out of range"):
            module.duplicate_mask_summary(
                [[True]], [0.5], [True], 1
            )


if __name__ == "__main__":
    unittest.main()
