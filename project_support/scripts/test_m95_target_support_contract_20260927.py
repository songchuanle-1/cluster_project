import unittest

import torch

from m95_target_support_contract_20260927 import evaluate
from m95_target_seed_full_population_20260927 import MANIFEST_SHA


class TargetSupportTest(unittest.TestCase):
    def setUp(self):
        self.row = {
            "manifest_index": 5, "scene": "scene", "ann_id": 2,
            "selected_query": 0, "ious": [1 / 3] * 128,
            "target_instances": [7], "native_positive": [True] * 128,
            "physical_instance_labels": [7, 7, 8],
        }
        self.artifact = {
            "manifest_index": 5, "manifest_sha256": MANIFEST_SHA,
            "axis": {"scene": "scene", "ann_id": 2},
            "query_masks": torch.tensor([[True, False, True]] * 128),
            "target_union": torch.tensor([True, True, False]),
            "physical_instance_labels": torch.tensor([7, 7, 8]),
        }

    def test_identical_support(self):
        result = evaluate(self.row, self.artifact)
        self.assertEqual(result["support_disagreement"], 0)
        self.assertEqual(result["physical_selected_iou"], 1 / 3)

    def test_support_mismatch(self):
        self.artifact["target_union"] = torch.tensor([True, False, True])
        self.row["ious"][0] = 1.0
        self.assertEqual(evaluate(self.row, self.artifact)["support_disagreement"], 2)

    def test_axis_guard(self):
        self.artifact["axis"]["ann_id"] = 3
        with self.assertRaises(ValueError):
            evaluate(self.row, self.artifact)

    def test_iou_guard(self):
        self.row["ious"][0] = 0.9
        with self.assertRaises(ValueError):
            evaluate(self.row, self.artifact)


if __name__ == "__main__":
    unittest.main()
