"""CPU checks against the project's actual IoU function."""
import ast
from pathlib import Path
import sys
import unittest

import torch
from typing import Union
from d1_candidate_bank_20260911 import bank_metrics

ROOT = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else Path("Cluster")
source = ROOT / "framework/model/Quard_model/model_base1/loss.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "get_iou")
scope = {"torch": torch, "Union": Union}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), scope)
get_iou = scope["get_iou"]


class BankTests(unittest.TestCase):
    def setUp(self):
        self.logits = torch.tensor([[0., -2.], [-2., 2.]])
        self.scores = torch.tensor([[1., 1.], [0., 0.]])
        self.mapping = torch.tensor([0, 0, 0, 1])
        self.gt = torch.tensor([1., 1., 1., 0.])

    def call(self, **kwargs):
        values = dict(logits=self.logits, scores=self.scores,
                      mapping=self.mapping, gt=self.gt, get_iou=get_iou)
        values.update(kwargs)
        return bank_metrics(**values)

    def test_zero_threshold_and_tied_scores(self):
        result = self.call()
        self.assertEqual(result["selected_index"], 0)
        self.assertGreater(result["selected_iou"], .999)
        self.assertEqual(result["selection_gap"], 0)

    def test_point_weighting_and_oracle(self):
        self.logits[1] = torch.tensor([2., 2.])
        result = self.call(scores=torch.tensor([[0., 0.], [0., 1.]]))
        self.assertAlmostEqual(result["selected_iou"], .75, places=5)
        self.assertAlmostEqual(result["selection_gap"], .25, places=5)
        self.assertAlmostEqual(1 - result["selected_iou"],
                               result["bank_limitation"] + result["selection_gap"])

    def test_empty_bank_rejected(self):
        with self.assertRaises(AssertionError):
            self.call(logits=torch.empty(0, 2), scores=torch.empty(0, 2))

    def test_nan_rejected(self):
        self.logits[0, 0] = float("nan")
        with self.assertRaises(AssertionError):
            self.call()

    def test_bad_mapping_rejected(self):
        with self.assertRaises(AssertionError):
            self.call(mapping=torch.tensor([0, 0, 0, 2]))

    def test_single_candidate(self):
        result = self.call(logits=self.logits[:1], scores=self.scores[:1])
        self.assertEqual(result["selection_gap"], 0)

    def test_empty_target_empty_prediction(self):
        result = self.call(logits=torch.full((2, 2), -1.), gt=torch.zeros(4))
        self.assertEqual(result["selected_iou"], 0)
        self.assertEqual(result["bank_limitation"], 1)


if __name__ == "__main__":
    unittest.main()
