"""Synthetic CPU Torch-module checks; never a native model or dataset test."""
import importlib.util
import unittest

from native_geometry_runtime_20260919 import capture_forward
from referent_geometry_capture_20260919 import validate_capture
from test_referent_geometry_capture_20260919 import fixture


@unittest.skipUnless(importlib.util.find_spec("torch"), "Torch not installed locally")
class SyntheticTorchTest(unittest.TestCase):
    def build(self, raises=False):
        import torch
        inputs, axes, binding = fixture()
        inputs[4] = [torch.tensor(x, dtype=torch.float32) for x in inputs[4]]
        inputs[7] = torch.tensor(inputs[7], dtype=torch.int64)
        inputs[8] = torch.tensor(inputs[8], dtype=torch.float32).t().contiguous().t()
        inputs[9] = torch.tensor(inputs[9], dtype=torch.int32)
        inputs[0]["sample_inds"] = torch.tensor(inputs[0]["sample_inds"])

        class Criterion(torch.nn.Module):
            def forward(self, *args):
                return torch.tensor(1.25)

        class Model(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.criterion = Criterion()

            def forward(self, batch, mode):
                loss = self.criterion(*inputs)
                if raises:
                    raise RuntimeError("synthetic error")
                return loss, {}

        batch = dict(scan_ids=[a["scene"] for a in axes],
                     scenes_len=torch.tensor([1, 1]),
                     ann_ids=torch.tensor([a["ann_id"] for a in axes]))
        return Model(), batch, axes, binding

    def test_strided_float_labels_real_module_hooks(self):
        args = self.build()
        report = capture_forward(*args)
        self.assertEqual(report["loss"], 1.25)
        validate_capture(report["geometry"], args[3])
        self.assertEqual(len(args[0].criterion._forward_pre_hooks), 0)

    def test_exception_removes_real_module_hook(self):
        args = self.build(raises=True)
        with self.assertRaises(RuntimeError):
            capture_forward(*args)
        self.assertEqual(len(args[0].criterion._forward_pre_hooks), 0)


if __name__ == "__main__":
    unittest.main()
