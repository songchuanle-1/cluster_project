"""Focused tests for the exact match-cause partition analyzer."""
import json
import tempfile
import unittest
from pathlib import Path

import m95_exact_match_cause_partition_20260925 as analyzer


def cause():
    return {
        "sampled_pos": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0],
                        [2.0, 0.0, 0.0]],
        "obj_pos": [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
        "sampled_instance_labels": [10, 20, 20],
        "object_ids": [10, 20],
        "nearest_query_per_gt": [0, 2],
        "member_queries_per_gt": [[], [1]],
        "native_positive": [True, True, True],
        "matched_query_gt_pairs": [[0, 0], [1, 1], [2, 1]],
    }


def expression():
    return {
        "manifest_index": 0,
        "scene": "scene0000_00",
        "ann_id": 7,
        "target_object_id": "10",
        "selected_query": 1,
        "scores": [0.2, 0.9, 0.8],
        "ious": [0.2, 0.1, 0.9],
        "native_match_cause": cause(),
    }


class CauseContractTest(unittest.TestCase):
    def test_target_causes_are_disjoint(self):
        sets = analyzer.target_cause_sets(cause(), "10")
        self.assertEqual(sets["target_positive"], {0})
        self.assertEqual(sets["target_nearest"], {0})
        self.assertEqual(sets["target_member"], set())
        self.assertEqual(sets["other_gt_only"], {1, 2})

    def test_native_positive_contradiction_fails(self):
        row = cause()
        row["native_positive"][2] = False
        with self.assertRaisesRegex(ValueError, "positive vector"):
            analyzer.target_cause_sets(row, "10")

    def test_missing_target_fails(self):
        with self.assertRaisesRegex(ValueError, "target object"):
            analyzer.target_cause_sets(cause(), "99")


class SelectionTest(unittest.TestCase):
    def test_top_score_uses_lowest_query_on_tie(self):
        self.assertEqual(analyzer.top_score_query({2, 4}, [0, 0, 0.5, 0, 0.5]), 2)

    def test_expression_partitions_oracle_selectors(self):
        row = analyzer.analyze_expression(expression())
        self.assertEqual(row["selections"]["deployed"]["query"], 1)
        self.assertEqual(row["selections"]["all_native_positive"]["query"], 1)
        self.assertEqual(row["selections"]["target_positive"]["query"], 0)
        self.assertEqual(row["selections"]["target_nearest"]["query"], 0)
        self.assertIsNone(row["selections"]["target_member"])
        self.assertTrue(row["target_positive_changed_from_deployed"])
        self.assertTrue(row["target_positive_changed_from_native_positive"])

    def test_invalid_iou_fails(self):
        row = expression()
        row["ious"][0] = 1.1
        with self.assertRaisesRegex(ValueError, "outside"):
            analyzer.analyze_expression(row)


class OutputTest(unittest.TestCase):
    def test_summary_counts_target_positive_bucket(self):
        row = analyzer.analyze_expression(expression())
        summary = analyzer.summarize([row], draws=10)
        self.assertEqual(summary["query_cause_counts"]["target_positive"], 1)
        self.assertEqual(summary["query_cause_counts"]["target_nearest"], 1)
        self.assertEqual(summary["query_cause_counts"]["target_member"], 0)
        self.assertEqual(summary["query_cause_counts"]["other_gt_only"], 2)

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.json"
            path.write_text("original", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "already exists"):
                analyzer.write_json(path, {"new": True})
            self.assertEqual(path.read_text(encoding="ascii"), "original")

    def test_json_output_is_ascii(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result.json"
            analyzer.write_json(path, {"value": "ascii"})
            self.assertEqual(json.loads(path.read_text(encoding="ascii")),
                             {"value": "ascii"})


if __name__ == "__main__":
    unittest.main()
