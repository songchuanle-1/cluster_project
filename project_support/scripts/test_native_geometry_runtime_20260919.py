import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from frozen_capture_contract_20260916 import fingerprint
from native_geometry_runtime_20260919 import (
    capture_forward, check_capacity, source_manifest,
)
from native_frozen_capture_20260916 import FrozenDataset
from referent_geometry_capture_20260919 import validate_capture
from referent_native_expression_producer_20260919 import FROZEN_CAPTURE_PRODUCER_FILES
from test_referent_geometry_capture_20260919 import fixture


class Criterion:
    def __init__(self):
        self.hooks = [lambda module, inputs: None]

    def register_forward_pre_hook(self, hook):
        self.hooks.append(hook)
        owner = self

        class Handle:
            def remove(self):
                owner.hooks.remove(hook)

        return Handle()

    def __call__(self, inputs):
        for hook in list(self.hooks):
            if hook(self, tuple(inputs)) is not None:
                raise AssertionError("Observer changed criterion arguments")


class Model:
    def __init__(self, inputs, behavior="normal"):
        self.criterion = Criterion()
        self.inputs = inputs
        self.behavior = behavior

    def __call__(self, batch, mode):
        assert mode == "loss"
        if self.behavior != "zero":
            self.criterion(self.inputs)
        if self.behavior == "twice":
            self.criterion(self.inputs)
        if self.behavior == "raise":
            raise RuntimeError("synthetic forward error")
        if self.behavior == "mutate":
            batch["ann_ids"][0] += 1
        return (float("nan") if self.behavior == "nan" else 1.25), {}


def setup(behavior="normal"):
    inputs, axes, binding = fixture()
    batch = dict(scan_ids=[axis["scene"] for axis in axes],
                 ann_ids=[axis["ann_id"] for axis in axes], scenes_len=[1, 1])
    return Model(inputs, behavior), batch, axes, binding


class RuntimeTest(unittest.TestCase):
    def test_observer_preserves_inputs_and_existing_hooks(self):
        model, batch, axes, binding = setup()
        before = copy.deepcopy((model.inputs, batch, axes))
        hooks = model.criterion.hooks[:]
        result = capture_forward(model, batch, axes, binding)
        self.assertEqual((model.inputs, batch, axes), before)
        self.assertEqual(model.criterion.hooks, hooks)
        self.assertEqual(result["collated_input_sha256"], fingerprint(batch))
        self.assertEqual(result["criterion_calls"], 1)
        validate_capture(result["geometry"], binding)
        self.assertNotIn("native_capture_completed", result)

    def test_forward_error_removes_only_our_hook(self):
        model, batch, axes, binding = setup("raise")
        hooks = model.criterion.hooks[:]
        with self.assertRaises(RuntimeError):
            capture_forward(model, batch, axes, binding)
        self.assertEqual(model.criterion.hooks, hooks)

    def test_missing_repeated_mutated_and_nonfinite_fail_closed(self):
        for behavior in ("zero", "twice", "mutate", "nan"):
            model, batch, axes, binding = setup(behavior)
            hooks = model.criterion.hooks[:]
            with self.subTest(behavior=behavior), self.assertRaises(ValueError):
                capture_forward(model, batch, axes, binding)
            self.assertEqual(model.criterion.hooks, hooks)

    def test_capture_error_removes_hook(self):
        model, batch, axes, binding = setup()
        model.inputs[9] = [0, 6, 8]
        with self.assertRaises(ValueError):
            capture_forward(model, batch, axes, binding)
        self.assertEqual(len(model.criterion.hooks), 1)

    def test_stale_physical_axis_rejected_before_hook(self):
        for field, value in (("ann_ids", [11, 10]), ("scenes_len", [True, 1]),
                             ("scan_ids", ["scene1", "scene0"])):
            model, batch, axes, binding = setup()
            batch[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                capture_forward(model, batch, axes, binding)
            self.assertEqual(len(model.criterion.hooks), 1)

    def test_repeated_scene_checks_slot_and_native_input_binding(self):
        for bad_field in (None, "expression_slot", "native_input_sha256"):
            model, batch, axes, binding = setup()
            axes[1] = dict(copy.deepcopy(axes[0]), expression_slot=1, ann_id=11)
            model.inputs[4] = [model.inputs[4][0]] * 2
            model.inputs[8] = model.inputs[8][:6] * 2
            model.inputs[9] = [0, 6, 12]
            batch.update(scan_ids=["scene0"], scenes_len=[2])
            if bad_field is not None:
                axes[1][bad_field] = 0 if bad_field == "expression_slot" else "f" * 64
                with self.assertRaises(ValueError):
                    capture_forward(model, batch, axes, binding)
            else:
                result = capture_forward(model, batch, axes, binding)
                self.assertEqual(len(result["geometry"]["rows"]), 2)

    def test_strided_numpy_layout_and_dtype_are_fingerprinted(self):
        model, batch, axes, binding = setup()
        coordinates = np.array(model.inputs[8], dtype=np.float32, order="F")
        self.assertFalse(coordinates.flags.c_contiguous)
        model.inputs[8] = coordinates
        model.inputs[4] = [np.array(row, dtype=np.int64) for row in model.inputs[4]]
        model.inputs[7] = np.array(model.inputs[7], dtype=np.int64)
        model.inputs[9] = np.array(model.inputs[9], dtype=np.int32)
        model.inputs[0]["sample_inds"] = np.array(model.inputs[0]["sample_inds"])
        first = capture_forward(model, batch, axes, binding)
        validate_capture(json.loads(json.dumps(first["geometry"])), binding)
        model.inputs[8] = coordinates.astype(np.float64)
        second = capture_forward(model, batch, axes, binding)
        self.assertEqual(first["geometry"]["rows"], second["geometry"]["rows"])
        self.assertNotEqual(first["geometry"]["observed_criterion_sha256"],
                            second["geometry"]["observed_criterion_sha256"])

    def test_native_float_labels_are_losslessly_bound(self):
        model, batch, axes, binding = setup()
        model.inputs[4] = [np.array(row, dtype=np.float32) for row in model.inputs[4]]
        result = capture_forward(model, batch, axes, binding)
        row = result["geometry"]["rows"][0]
        self.assertIsInstance(row["observed_native_instance_labels"][0], float)
        self.assertIsInstance(row["native_instance_labels"][0], int)
        validate_capture(result["geometry"], binding)

    def test_nonintegral_nonfinite_boolean_labels_fail_closed(self):
        for bad in (1.25, float("nan"), float("inf"), True, 2 ** 54):
            model, batch, axes, binding = setup()
            model.inputs[4][0][0] = bad
            with self.subTest(label=bad), self.assertRaises(ValueError):
                capture_forward(model, batch, axes, binding)
            self.assertEqual(len(model.criterion.hooks), 1)

    def test_dataset_physical_binding_through_runtime(self):
        class Dataset:
            training = True

            def transform_train(self):
                return None, None, None, [0, 1, 2], None, None, [10, 20, 30]

            def get_sp_label(self, *args):
                return [1.0, 1.0, 1.0], {}

            def __getitem__(self, index):
                transform = self.transform_train()
                labels, _ = self.get_sp_label([0, 1, 2], [1, 1, 1], [4, 4, 4])
                item = [None] * 16
                item[0], item[1], item[5] = [10], "scene0", transform[3]
                item[11], item[15] = labels, [[1], [2], [3]]
                return tuple(item)

            def collate_fn(self, items):
                return dict(scan_ids=[x[1] for x in items],
                            ann_ids=[ann for x in items for ann in x[0]],
                            scenes_len=[len(x[0]) for x in items])

        _, _, _, binding = setup()

        class BoundDataset(FrozenDataset):
            checkpoint_sha256 = binding["checkpoint_sha256"]

        native = Dataset()
        wrapped = BoundDataset(native, "synthetic-only", binding["producer_sha256"])
        item, axes = wrapped[0]
        self.assertEqual(axes[0]["native_input_sha256"], fingerprint(item))
        batch, axes = wrapped.collate_fn([(item, axes)])
        inputs = [None] * 10
        inputs[0] = {"sample_inds": [[0, 1]]}
        inputs[4], inputs[7] = [item[11]], [[0, 2, 1]]
        inputs[8], inputs[9] = [[0, 0, 0], [1, 0, 0], [4, 0, 0]], [0, 3]
        result = capture_forward(Model(inputs), batch, axes, binding)
        self.assertEqual(result["geometry"]["rows"][0]["physical_instance_labels"], [1, 1, 1])
        self.assertNotIn("get_sp_label", vars(native))
        self.assertNotIn("transform_train", vars(native))

    def test_repeated_calls_do_not_leak_capture_or_hooks(self):
        model, batch, axes, binding = setup()
        first = capture_forward(model, batch, axes, binding)
        second = capture_forward(model, batch, axes, binding)
        first["geometry"]["rows"].clear()
        self.assertEqual(len(second["geometry"]["rows"]), 2)
        self.assertEqual(len(model.criterion.hooks), 1)

    def test_manifest_transitive_frozen_sources_and_new_runtime(self):
        manifest = source_manifest()
        paths = {row["path"] for row in manifest["sources"]}
        self.assertTrue(set(FROZEN_CAPTURE_PRODUCER_FILES).issubset(paths))
        self.assertTrue({"paired_capture_evaluation_20260916.py",
                         "referent_geometry_control_20260919.py",
                         "native_geometry_runtime_20260919.py"}.issubset(paths))
        self.assertEqual(manifest["producer_sha256"], fingerprint(manifest["sources"]))
        self.assertIn("torch", manifest["external_imports"])
        self.assertEqual(manifest, source_manifest())

    def test_manifest_rejects_outside_entry(self):
        with self.assertRaises(ValueError):
            source_manifest(entry="../outside.py")

    @patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "7"})
    def test_capacity_fails_closed_at_two_processes_or_low_memory(self):
        for processes, free in (("gpu7, 1\ngpu7, 2\n", 20000),
                                ("gpu7, 1\n", 1000)):
            with patch("native_geometry_runtime_20260919.subprocess.check_output",
                       side_effect=["gpu7, 80000, " + str(free), processes]):
                with self.assertRaises(ValueError):
                    check_capacity()

    @patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "7"})
    def test_capacity_ignores_other_gpus(self):
        with patch("native_geometry_runtime_20260919.subprocess.check_output",
                   side_effect=["gpu7, 80000, 20000", "gpu7, 1\ngpu2, 2\ngpu2, 3"]):
            self.assertEqual(check_capacity()["process_ids"], ["1"])

    @patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"})
    def test_wrong_gpu_never_queries_or_allocates(self):
        with patch("native_geometry_runtime_20260919.subprocess.check_output") as query:
            with self.assertRaises(ValueError):
                check_capacity()
            query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
