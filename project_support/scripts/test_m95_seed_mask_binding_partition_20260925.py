"""Tests for the M95 seed/mask binding partition."""
import unittest
from unittest import mock

import m95_seed_mask_binding_partition_20260925 as module


class SeedMaskBindingPartitionTest(unittest.TestCase):
    def setUp(self):
        self.queries_patch = mock.patch.object(module, "EXPECTED_QUERIES", 2)
        self.queries_patch.start()

    def tearDown(self):
        self.queries_patch.stop()

    def row(self, selected=0, target=(1,)):
        return {
            "manifest_index": 0,
            "scene": "scene0001_00",
            "scores": [0.1, 0.9] if selected == 1 else [0.9, 0.1],
            "ious": [0.1, 0.8],
            "native_positive": [False, True],
            "selected_query": selected,
            "target_instances": list(target),
            "sampled_seed_indices": [0, 1],
            "sample_inverse": [0, 1],
            "selected_mask_endpoints": {
                "overlaps": [
                    {"instance": 1, "iou": 0.0},
                    {"instance": 2, "iou": 0.75},
                ]
            },
        }

    def artifact(self, labels=(2, 1), masks=((True, False), (False, True))):
        return {
            "artifact_contract": module.EXPECTED_ARTIFACT_CONTRACT,
            "manifest_index": 0,
            "physical_instance_labels": list(labels),
            "query_masks": [list(mask) for mask in masks],
        }

    def test_partition_query_follows_wrong_instance_seed(self):
        result = module.partition_query(self.row(), self.artifact(), 0)
        self.assertTrue(result["seed_in_wrong_instance"])
        self.assertTrue(result["seed_in_its_mask"])
        self.assertFalse(result["seed_in_target"])

    def test_partition_query_binds_target_seed(self):
        result = module.partition_query(self.row(), self.artifact(), 1)
        self.assertTrue(result["seed_in_target"])
        self.assertFalse(result["seed_in_wrong_instance"])
        self.assertTrue(result["seed_in_its_mask"])

    def test_selected_wrong_instances_uses_iou_threshold(self):
        self.assertEqual(module.selected_wrong_instances(self.row()), {2})

    def test_top_score_query_uses_stable_index_tie_break(self):
        self.assertEqual(module.top_score_query([0.5, 0.5]), 0)

    def test_mask_contains_validates_axis(self):
        with self.assertRaisesRegex(ValueError, "out of range"):
            module.mask_contains([True], 1)

    def test_analyze_rows_counts_mismatch_partition(self):
        summary = module.analyze_rows([self.row()], {0: self.artifact()})
        selected = summary["native_negative_selected"]
        self.assertEqual(selected["rows"], 1)
        self.assertEqual(selected["seed_in_its_mask"], 1)
        self.assertEqual(selected["seed_in_wrong_instance"], 1)
        self.assertEqual(selected["follows_wrong_instance_seed"], 1)
        self.assertEqual(summary["all_queries"]["queries"], 2)

    def test_analyze_rows_skips_positive_selection(self):
        summary = module.analyze_rows([self.row(selected=1)], {0: self.artifact()})
        self.assertNotIn("rows", summary["native_negative_selected"])


if __name__ == "__main__":
    unittest.main()
