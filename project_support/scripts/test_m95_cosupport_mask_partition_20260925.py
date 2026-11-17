"""Focused tests for the M95 mask co-support partition."""
import tempfile
import unittest
from pathlib import Path

import m95_cosupport_mask_partition_20260925 as analyzer


def cause():
    return {
        "object_ids": [10, 20],
        "nearest_query_per_gt": [0, 2],
        "member_queries_per_gt": [[], [1]],
        "native_positive": [True, True, True],
    }


class CauseTest(unittest.TestCase):
    def test_target_causes_are_partitioned(self):
        sets = analyzer.target_cause_sets(cause(), "10")
        self.assertEqual(sets["target"], {0})
        self.assertEqual(sets["all"], {0, 1, 2})

    def test_other_positive_is_not_target_bound(self):
        self.assertEqual(analyzer.selection_class(1, {"all": {1}, "nearest": set(), "member": set()}), "other_gt_only")

    def test_missing_target_fails(self):
        with self.assertRaisesRegex(ValueError, "target object"):
            analyzer.target_cause_sets(cause(), "99")


class MaskTest(unittest.TestCase):
    def test_mask_overlap_uses_union(self):
        result = analyzer.mask_overlap(
            [True, True, False],
            [False, True, True],
        )
        self.assertEqual(result["overlap_superpoints"], 1)
        self.assertEqual(result["mask_superpoints"], 2)
        self.assertEqual(result["overlap_fraction"], 0.5)
        self.assertAlmostEqual(result["mask_iou"], 1.0 / 3.0)

    def test_mask_shape_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "differ"):
            analyzer.mask_overlap([True], [True, False])


class SummaryTest(unittest.TestCase):
    def test_summary_separates_selected_classes(self):
        rows = [
            {
                "scene_id": "a", "selected_class": "other_gt_only",
                "selected_success": False, "selected_iou": 0.25,
                "overlap_fraction": 0.5, "mask_iou": 0.4,
                "target_positive_query": 1, "selected_query": 2,
                "iou_delta_vs_target_positive": 0.1,
                "success_delta_vs_target_positive": 0.0,
            },
            {
                "scene_id": "b", "selected_class": "target_member",
                "selected_success": True, "selected_iou": 0.75,
                "overlap_fraction": 0.9, "mask_iou": 0.8,
                "target_positive_query": 2, "selected_query": 2,
                "iou_delta_vs_target_positive": 0.0,
                "success_delta_vs_target_positive": 0.0,
            },
        ]
        summary = analyzer.summarize_rows(rows, draws=10)
        self.assertEqual(summary["classes"]["other_gt_only"]["rows"], 1)
        self.assertEqual(summary["classes"]["target_member"]["rows"], 1)
        self.assertEqual(summary["changed_from_target_positive"]["rows"], 1)


class OutputTest(unittest.TestCase):
    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "output.json"
            path.write_text("original", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "already exists"):
                analyzer.write_json(path, {"new": True})
            self.assertEqual(path.read_text(encoding="ascii"), "original")


if __name__ == "__main__":
    unittest.main()
