import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from frozen_capture_contract_20260916 import (
    fingerprint,
    file_sha256,
    model_package_sha256,
    strict_paired_summary,
)
from native_frozen_capture_20260916 import FrozenDataset
from native_endpoint_capture_20260916 import EndpointDataset
from test_paired_capture_evaluation_20260916 import row


def frozen_row():
    return dict(row(), native_input_sha256="c" * 64, checkpoint_sha256="a" * 64)


class FrozenTests(unittest.TestCase):
    def test_coordinates_change_despite_identical_support(self):
        left = dict(ids=[1, 2], xyz=np.array([[0., 1., 2.]]))
        right = copy.deepcopy(left)
        right["xyz"][0, 0] = .01
        self.assertNotEqual(fingerprint(left), fingerprint(right))

    def test_dtype_shape_order_and_containers(self):
        value = np.array([[1, 2]], dtype=np.int32)
        for other in (value.astype(np.int64), value.reshape(2, 1), value[:, ::-1]):
            self.assertNotEqual(fingerprint(value), fingerprint(other))
        self.assertNotEqual(fingerprint([1, 2]), fingerprint((1, 2)))
        self.assertEqual(fingerprint(dict(a=1, b=2)), fingerprint(dict(b=2, a=1)))

    def test_reject_unsupported_values(self):
        for value in (object(), float("nan"), np.array([object()]), {1: 2}):
            with self.assertRaises(ValueError):
                fingerprint(value)

    def test_file_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint"
            path.write_bytes(b"abc")
            self.assertEqual(file_sha256(path),
                             "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_model_package_hash_is_content_addressed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = (
                root / "framework/model/Quard_model/"
                "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort")
            package.mkdir(parents=True)
            source = package / "loss.py"
            source.write_text("VALUE = 1\n", encoding="ascii")
            first = model_package_sha256(
                root, "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort")
            source.write_text("VALUE = 2\n", encoding="ascii")
            second = model_package_sha256(
                root, "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort")
            self.assertNotEqual(first, second)

    def test_model_package_rejects_unbound_class(self):
        with self.assertRaisesRegex(ValueError, "Unbound model class"):
            model_package_sha256(Path("."), "model_other")

    def test_reject_old_archive(self):
        with self.assertRaisesRegex(ValueError, "input identity"):
            strict_paired_summary([row()], [row()],
                                  baseline_checkpoint="a" * 64, candidate_checkpoint="a" * 64)

    def test_reject_input_and_checkpoint_mismatch(self):
        for field in ("native_input_sha256", "checkpoint_sha256"):
            rhs = frozen_row()
            rhs[field] = "d" * 64
            with self.assertRaises(ValueError):
                strict_paired_summary([frozen_row()], [rhs],
                                      baseline_checkpoint="a" * 64, candidate_checkpoint="a" * 64)

    def test_allow_preregistered_distinct_checkpoints(self):
        rhs = frozen_row()
        rhs["checkpoint_sha256"] = "b" * 64
        result = strict_paired_summary([frozen_row()], [rhs],
                                      baseline_checkpoint="a" * 64, candidate_checkpoint="b" * 64)
        self.assertEqual(result["scene_balanced_delta"], 0)
        self.assertTrue(result["exact_native_input_verified"])

    def test_duplicate_remains_rejected(self):
        with self.assertRaises(ValueError):
            strict_paired_summary([frozen_row()], [frozen_row()] * 2,
                                  baseline_checkpoint="a" * 64, candidate_checkpoint="a" * 64)

    def test_dataset_adds_identity_without_mutating_item(self):
        dataset = FrozenDataset(object(), "capture", "a" * 64)
        dataset.checkpoint_sha256 = "b" * 64
        item = (np.array([1, 2]), "scene")
        with patch.object(EndpointDataset, "__getitem__", return_value=(item, [{}])):
            actual, axes = dataset[0]
        self.assertIs(actual, item)
        self.assertEqual(axes[0]["native_input_sha256"], fingerprint(item))
        self.assertEqual(axes[0]["checkpoint_sha256"], "b" * 64)


if __name__ == "__main__":
    unittest.main()
