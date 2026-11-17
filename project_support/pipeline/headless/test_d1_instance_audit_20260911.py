"""Synthetic CPU checks of the exact instance-attribution function."""
import ast
from pathlib import Path
import unittest
import numpy as np

path = Path(__file__).with_name("d1_instance_audit_20260911.py")
fn = next(n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "mask_stats")
scope = dict(np=np)
exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), scope)
stats = scope["mask_stats"]


class InstanceTests(unittest.TestCase):
    def setUp(self):
        self.instances = np.array([0, 0, 1, 1, 2, 2, -1])
        self.semantic = np.array([4, 4, 4, 4, 6, 6, -100])
        self.gt = self.instances == 0

    def call(self, mask):
        return stats(np.array(mask, bool), self.gt, self.instances, self.semantic, 0)

    def test_target(self):
        r = self.call([1, 1, 0, 0, 0, 0, 0])
        self.assertEqual(r["label"], "target_pass50")
        self.assertEqual(r["same_semantic_other_instances"], 1)

    def test_wrong_same_class(self):
        r = self.call([0, 0, 1, 1, 0, 0, 0])
        self.assertEqual(r["label"], "wrong_instance_same_semantic")
        self.assertEqual(r["fp"], 2)
        self.assertEqual(r["fn"], 2)

    def test_wrong_other_class(self):
        self.assertEqual(self.call([0, 0, 0, 0, 1, 1, 0])["label"], "wrong_instance_different_semantic")

    def test_empty(self):
        r = self.call([0] * 7)
        self.assertEqual(r["label"], "empty_prediction")
        self.assertIsNone(r["precision"])
        self.assertIsNone(r["best_instance"])

    def test_mixed_not_object_failure(self):
        self.assertEqual(self.call([1, 0, 1, 0, 1, 0, 1])["label"], "no_instance_pass50")

    def test_unknown_semantic(self):
        self.semantic[:2] = -100
        self.assertEqual(self.call([0, 0, 1, 1, 0, 0, 0])["label"], "wrong_instance_semantic_unknown")

    def test_bad_gt_join(self):
        self.gt = self.instances == 1
        with self.assertRaises(AssertionError):
            self.call([1] * 7)

    def test_precision_recall(self):
        r = self.call([1, 0, 0, 0, 0, 0, 1])
        self.assertEqual((r["tp"], r["fp"], r["fn"]), (1, 1, 1))
        self.assertEqual((r["precision"], r["recall"]), (.5, .5))


if __name__ == "__main__":
    unittest.main()
