import importlib.util
from pathlib import Path
import unittest

import torch

from m95_native_mask_backward_20260927 import evaluate
from m95_target_seed_full_population_20260927 import MANIFEST_SHA


class NativeMaskBackwardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = (Path(__file__).resolve().parents[1] /
                "framework/model/Quard_model/"
                "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py")
        spec = importlib.util.spec_from_file_location("test_m95_loss", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.criterion = module.Criterion.__new__(module.Criterion)

    def setUp(self):
        self.row = {
            "manifest_index": 5, "scene": "scene", "ann_id": 2,
            "selected_query": 0, "ious": [1 / 3] * 128,
            "native_positive": [True] + [False] * 127,
        }
        self.artifact = {
            "manifest_index": 5, "manifest_sha256": MANIFEST_SHA,
            "axis": {"scene": "scene", "ann_id": 2},
            "query_mask_logits": torch.tensor([[2., -2., 2.]] * 128),
            "query_masks": torch.tensor([[True, False, True]] * 128),
            "query_scores": torch.full((128,), 0.9),
            "target_union": torch.tensor([True, True, False]),
        }

    def test_matched_native_loss_corrects_fn_fp(self):
        result = evaluate(self.row, self.artifact, self.criterion)
        self.assertEqual((result["fn_correct"], result["fp_correct"]), (1, 1))
        self.assertEqual(result["score_loss"], 0.0)

    def test_unmatched_selected_fails(self):
        self.row["native_positive"][0] = False
        with self.assertRaises(ValueError):
            evaluate(self.row, self.artifact, self.criterion)

    def test_query_iou_axis_fails(self):
        self.row["ious"][0] = 1.0
        with self.assertRaises(ValueError):
            evaluate(self.row, self.artifact, self.criterion)


if __name__ == "__main__":
    unittest.main()
