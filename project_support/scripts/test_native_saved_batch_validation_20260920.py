"""Static/synthetic contract tests, not native ScanRefer or Torch validation."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from frozen_capture_contract_20260916 import fingerprint
from native_saved_batch_validation_20260920 import NativeBatchValidator, native_callbacks
from relocated_saved_collation_20260920 import require_cpu


def fixture(use_xyz=True):
    item = [
        [10, 11], "synthetic_scene", np.zeros((3, 3), dtype=np.int64),
        np.arange(9, dtype=np.float32).reshape(3, 3),
        np.ones((3, 3), dtype=np.float32), np.array([0, 1, 1], dtype=np.int64),
        [1, 2], [[1, 0, 0], [0, 1, 1]], [[1, 0], [0, 1]],
        [[1, 0], [0, 1]], ["first", "second"], np.array([1, 2], dtype=np.int64),
        [{"id": 1}, {"id": 2}], [{"map": [0]}, {"map": [1]}], [False, True],
        np.ones((3, 4), dtype=np.float32),
    ]
    axes = [dict(scene=item[1], ann_id=ann, expression_slot=i, scene_occurrence=0)
            for i, ann in enumerate(item[0])]
    batch = dict(
        ann_ids=item[0][:], scan_ids=[item[1]], batch_offsets=np.array([0, 2]),
        scenes_len=np.array([2]), coords_float=item[3].copy(),
        superpoints=item[5].copy(), feats_2d=item[15].copy(),
        gt_pmasks=copy.deepcopy(item[7]), gt_spmasks=copy.deepcopy(item[8]),
        sp_ref_masks=copy.deepcopy(item[9]), sp_ins_labels=[item[11].copy()],
        object_idss=copy.deepcopy(item[6]), meta_datas=copy.deepcopy(item[12]),
        dense_maps=copy.deepcopy(item[13]), view_dependents=item[14][:],
        feats=np.concatenate((item[4], item[3]), axis=1) if use_xyz else item[4].copy(),
        lang_tokenss=np.ones((2, 5), dtype=np.int64),
        lang_masks=np.ones((2, 5), dtype=np.int64), p2v_map=np.array([0, 1, 2]))
    torch = SimpleNamespace(
        cuda=SimpleNamespace(is_initialized=Mock(return_value=False)),
        cat=Mock(side_effect=lambda values, dim: np.concatenate(values, axis=dim)),
        load=Mock(), save=Mock())
    return item, batch, axes, torch


class ValidatorTest(unittest.TestCase):
    def setUp(self):
        self.item, self.batch, self.axes, self.torch = fixture()
        self.validate = NativeBatchValidator(self.torch, True)

    def run_check(self):
        return self.validate(self.item, self.batch, self.axes)

    def test_xyz_features_exact_and_inputs_unchanged(self):
        before = fingerprint((self.item, self.batch, self.axes))
        self.run_check()
        self.assertEqual(before, fingerprint((self.item, self.batch, self.axes)))
        self.torch.cat.assert_called_once()

    def test_non_xyz_does_not_concatenate(self):
        item, batch, axes, torch = fixture(False)
        NativeBatchValidator(torch, False)(item, batch, axes)
        torch.cat.assert_not_called()

    def test_all_passthrough_fields_checked(self):
        fields = ("coords_float", "superpoints", "feats_2d", "gt_pmasks",
                  "gt_spmasks", "sp_ref_masks", "sp_ins_labels", "object_idss",
                  "meta_datas", "dense_maps", "view_dependents")
        original = copy.deepcopy(self.batch)
        for field in fields:
            with self.subTest(field=field):
                self.batch = copy.deepcopy(original)
                self.batch[field] = []
                with self.assertRaisesRegex(ValueError, "field differs"):
                    self.run_check()

    def test_feature_dtype_mismatch_rejected(self):
        self.batch["feats"] = self.batch["feats"].astype(np.float64)
        with self.assertRaisesRegex(ValueError, "dtype"):
            self.run_check()

    def test_wrong_xyz_order_rejected(self):
        self.batch["feats"] = np.concatenate((self.item[3], self.item[4]), axis=1)
        with self.assertRaisesRegex(ValueError, "concatenation"):
            self.run_check()

    def test_wrong_offsets_rejected(self):
        self.batch["batch_offsets"] = np.array([0, 3])
        with self.assertRaisesRegex(ValueError, "index/count"):
            self.run_check()

    def test_wrong_axis_rejected(self):
        for key, value in (("scene", "other"), ("ann_id", 0),
                           ("expression_slot", 1), ("scene_occurrence", -1)):
            with self.subTest(key=key):
                axes = copy.deepcopy(self.axes)
                axes[0][key] = value
                with self.assertRaisesRegex(ValueError, "axis identity"):
                    self.validate(self.item, self.batch, axes)

    def test_wrong_item_layout_rejected(self):
        with self.assertRaisesRegex(ValueError, "sixteen"):
            self.validate(self.item[:-1], self.batch, self.axes)

    def test_missing_axis_rejected(self):
        with self.assertRaisesRegex(ValueError, "expression count"):
            self.validate(self.item, self.batch, self.axes[:-1])

    def test_saved_nonzero_occurrence_not_reindexed(self):
        for axis in self.axes:
            axis["scene_occurrence"] = 5
        before = fingerprint(self.axes)
        self.run_check()
        self.assertEqual(fingerprint(self.axes), before)

    def test_missing_required_field_rejected(self):
        del self.batch["meta_datas"]
        with self.assertRaises(KeyError):
            self.run_check()

    def test_wrong_expression_field_lengths_rejected(self):
        self.item[6] = self.batch["object_idss"] = [1]
        with self.assertRaisesRegex(ValueError, "field count"):
            self.run_check()

    def test_wrong_token_shape_rejected(self):
        self.batch["lang_tokenss"] = np.ones((1, 5))
        with self.assertRaisesRegex(ValueError, "token/mask"):
            self.run_check()

    def test_wrong_mask_shape_rejected(self):
        self.batch["lang_masks"] = np.ones((2, 4))
        with self.assertRaisesRegex(ValueError, "token/mask"):
            self.run_check()

    def test_wrong_point_map_shape_rejected(self):
        self.batch["p2v_map"] = np.array([0, 1])
        with self.assertRaisesRegex(ValueError, "point map"):
            self.run_check()

    def test_cuda_initialized_before_validation_rejected(self):
        self.torch.cuda.is_initialized.return_value = True
        with self.assertRaisesRegex(ValueError, "CUDA"):
            self.run_check()
        self.torch.cat.assert_not_called()

    def test_cuda_initialization_during_validation_rejected(self):
        self.torch.cuda.is_initialized.side_effect = [False, True]
        with self.assertRaisesRegex(ValueError, "CUDA"):
            self.run_check()

    def test_non_cpu_value_rejected_before_hashing(self):
        self.batch["feats"] = SimpleNamespace(device=SimpleNamespace(type="cuda"))
        with self.assertRaisesRegex(ValueError, "CPU-only"):
            self.run_check()
        self.torch.cat.assert_not_called()

    def test_explicit_use_xyz_required(self):
        with self.assertRaisesRegex(ValueError, "boolean"):
            NativeBatchValidator(self.torch, "false")

    def test_string_cpu_device_accepted(self):
        require_cpu(SimpleNamespace(device="cpu"))
        require_cpu(np.zeros(2))

    def test_unknown_and_accelerator_devices_rejected(self):
        for device in ("cuda", "cuda:0", "mps", "", None, object()):
            with self.subTest(device=device):
                with self.assertRaisesRegex(ValueError, "CPU-only"):
                    require_cpu(SimpleNamespace(device=device))


class CallbackTest(unittest.TestCase):
    def setUp(self):
        self.item, self.batch, self.axes, self.torch = fixture()
        self.native = SimpleNamespace(use_xyz=True)
        self.frozen = Mock()
        self.frozen.collate_fn.return_value = (self.batch, self.axes)
        patcher = patch("native_frozen_capture_20260916.FrozenDataset",
                        return_value=self.frozen)
        self.factory = patcher.start()
        self.addCleanup(patcher.stop)

    def callbacks(self):
        return native_callbacks(self.native, self.torch, "synthetic", "a" * 64)

    def test_existing_collator_and_cpu_torch_serialization_bound(self):
        callbacks = self.callbacks()
        self.factory.assert_called_once_with(self.native, "synthetic", "a" * 64)
        result = callbacks["collate"]([(self.item, self.axes)])
        self.assertIs(result[0], self.batch)
        callbacks["validate_batch"](self.item, *result)
        self.torch.load.return_value = {"batch": self.batch}
        self.assertEqual(callbacks["load_batch"]("synthetic.pth").keys(), {"batch"})
        self.torch.load.assert_called_once_with(
            "synthetic.pth", map_location="cpu", weights_only=False)
        stream = object()
        callbacks["save"](result, stream)
        self.torch.save.assert_called_once_with(result, stream)

    def test_collate_cuda_initialization_rejected(self):
        callbacks = self.callbacks()
        self.torch.cuda.is_initialized.side_effect = [False, True]
        with self.assertRaisesRegex(ValueError, "CUDA"):
            callbacks["collate"]([(self.item, self.axes)])

    def test_load_cuda_initialization_rejected(self):
        callbacks = self.callbacks()
        self.torch.cuda.is_initialized.side_effect = [False, True]
        with self.assertRaisesRegex(ValueError, "CUDA"):
            callbacks["load_batch"]("synthetic.pth")

    def test_save_cuda_initialization_rejected(self):
        callbacks = self.callbacks()
        self.torch.cuda.is_initialized.side_effect = [False, True]
        with self.assertRaisesRegex(ValueError, "CUDA"):
            callbacks["save"]({}, object())

    def test_already_initialized_prevents_collator_construction(self):
        self.torch.cuda.is_initialized.return_value = True
        with self.assertRaisesRegex(ValueError, "CUDA"):
            self.callbacks()
        self.factory.assert_not_called()

    def test_nested_gpu_input_rejected_before_collation(self):
        callbacks = self.callbacks()
        value = SimpleNamespace(device=SimpleNamespace(type="cuda"))
        with self.assertRaisesRegex(ValueError, "CPU-only"):
            callbacks["collate"]([{"nested": [value]}])
        self.frozen.collate_fn.assert_not_called()

    def test_non_cpu_deserialization_rejected(self):
        callbacks = self.callbacks()
        self.torch.load.return_value = SimpleNamespace(device=SimpleNamespace(type="cuda"))
        with self.assertRaisesRegex(ValueError, "CPU-only"):
            callbacks["load_batch"]("synthetic.pth")


class FrozenWrapperTest(unittest.TestCase):
    def test_real_frozen_wrapper_only_calls_native_collation(self):
        item, batch, axes, torch = fixture()
        native = Mock()
        native.use_xyz = True
        native.collate_fn.return_value = batch
        callbacks = native_callbacks(native, torch, "synthetic", "a" * 64)
        actual, actual_axes = callbacks["collate"]([(item, axes)])
        callbacks["validate_batch"](item, actual, actual_axes)
        self.assertEqual(native.mock_calls, [unittest.mock.call.collate_fn([item])])
        self.assertEqual(fingerprint(actual_axes), fingerprint(axes))


if __name__ == "__main__":
    unittest.main()
