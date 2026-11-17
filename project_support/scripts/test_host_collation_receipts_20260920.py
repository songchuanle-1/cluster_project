"""Synthetic receipt files only; no native tensors or host execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from same_child_collation_20260920 import PROBE_RECEIPT
from scratch_collation_launch_20260920 import verify_completion


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.output = self.root / "output"
        self.collated = self.output / "collated"
        self.collated.mkdir(parents=True)
        (self.root / "sentinel").write_bytes(b"read-only-sentinel")
        (self.output / "probe-output").write_bytes(b"scratch-write-ok")
        self.binding = {"capture_id": "synthetic", "producer_sha256": "c"*64}
        self.indices = [3040, 3893]
        artifacts = []
        for index in self.indices:
            path = self.collated / ("batch_%d.pth" % index)
            raw = ("synthetic-batch-%d" % index).encode("ascii")
            path.write_bytes(raw)
            artifacts.append(dict(path=str(path), bytes=len(raw),
                                  sha256=hashlib.sha256(raw).hexdigest()))
        self.collation = dict(
            contract="relocated_saved_collation_v1", scratch=str(self.collated),
            observed_binding=self.binding, full_binding_sha256="b"*64,
            original_dataset_indices=self.indices, registry_denominator=31,
            items=[dict(dataset_index=i) for i in self.indices], artifacts=artifacts,
            callback_collation_completed=True, native_execution_verified=False,
            scientific_validation_complete=False, new_train_transforms=False,
            model_forward_completed=False, training_launch=False, admission=False)
        self.receipt = dict(
            contract="same-child-collation-v1", pid=123,
            manifest_sha256="a"*64, probe=copy.deepcopy(PROBE_RECEIPT),
            collation=self.collation, same_child_integration_completed=True,
            native_execution_verified=False, scientific_validation_complete=False,
            admission=False)

    def publish(self):
        (self.collated / "collation.json").write_text(json.dumps(self.collation))
        (self.output / "same_child.json").write_text(json.dumps(self.receipt))
        return subprocess.CompletedProcess([], 0, json.dumps(self.receipt), "")

    def verify(self, completed=None, **kwargs):
        arguments = dict(completed=completed or self.publish(), output=self.output,
                         manifest_sha256="a"*64, expected_binding=self.binding,
                         expected_full_binding_sha256="b"*64,
                         expected_indices=[3040, 3893])
        arguments.update(kwargs)
        return verify_completion(**arguments)

    def test_byte_bound_receipt_without_gate_promotion(self):
        result = self.verify()
        self.assertTrue(result["host_artifact_verification_completed"])
        self.assertFalse(result["native_execution_verified"])
        self.assertFalse(result["admission"])
        self.assertEqual(len(result["verified_files"]), 6)

    def test_nonzero_exit_rejects_even_valid_receipts(self):
        process = self.publish()
        process.returncode = 1
        with self.assertRaisesRegex(ValueError, "Child did not"):
            self.verify(process)

    def test_stdout_mismatch(self):
        process = self.publish()
        process.stdout = "{}"
        with self.assertRaisesRegex(ValueError, "Stdout"):
            self.verify(process)

    def test_missing_published_receipt(self):
        process = self.publish()
        (self.output / "same_child.json").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.verify(process)

    def test_collation_mismatch(self):
        process = self.publish()
        (self.collated / "collation.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "Published collation"):
            self.verify(process)

    def test_batch_drift(self):
        process = self.publish()
        (self.collated / "batch_3040.pth").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "size or digest"):
            self.verify(process)

    def test_paths_cannot_escape(self):
        self.collation["artifacts"][0]["path"] = str(self.root / "outside.pth")
        with self.assertRaisesRegex(ValueError, "exact output"):
            self.verify()

    def test_duplicate_artifact(self):
        self.collation["artifacts"][1] = self.collation["artifacts"][0]
        with self.assertRaisesRegex(ValueError, "exact output"):
            self.verify()

    def test_incomplete_inventory(self):
        self.collation["items"].pop()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.verify()

    def test_binding_and_manifest_are_independently_expected(self):
        for kwargs in (dict(expected_binding={"wrong": True}),
                       dict(manifest_sha256="d"*64),
                       dict(expected_full_binding_sha256="e"*64),
                       dict(expected_indices=[3893, 3040])):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.verify(**kwargs)

    def test_no_admission_or_numeric_boolean_flags(self):
        for key, value in (("admission", True), ("native_execution_verified", 0),
                           ("same_child_integration_completed", 1)):
            original = self.receipt[key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "flags"):
                self.receipt[key] = value
                self.verify()
            self.receipt[key] = original

    def test_no_forward_or_regeneration_claim(self):
        self.collation["new_train_transforms"] = True
        with self.assertRaisesRegex(ValueError, "flags"):
            self.verify()

    def test_probe_host_bytes(self):
        (self.root / "sentinel").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "probe bytes"):
            self.verify()

    def test_no_boolean_pid(self):
        self.receipt["pid"] = True
        with self.assertRaisesRegex(ValueError, "identity"):
            self.verify()

    def test_duplicate_json_keys_rejected(self):
        process = self.publish()
        process.stdout = process.stdout[:-1] + ', "pid": 123}'
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.verify(process)

    def test_nonfinite_json_rejected(self):
        process = self.publish()
        process.stdout = process.stdout[:-1] + ', "extra": NaN}'
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            self.verify(process)

    def test_missing_batch_preserves_other_outputs(self):
        process = self.publish()
        marker = self.output / "same_child.json"
        before = marker.read_bytes()
        (self.collated / "batch_3893.pth").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.verify(process)
        self.assertEqual(marker.read_bytes(), before)

    def test_hardlinked_batch_rejected(self):
        path = self.collated / "batch_3040.pth"
        (self.root / "alias").hardlink_to(path)
        with self.assertRaisesRegex(ValueError, "hardlinked"):
            self.verify()

    def test_explicit_nonempty_unique_saved_indices(self):
        for indices in ([], [3040, 3040], [True], [-1]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                self.verify(expected_indices=indices)


if __name__ == "__main__":
    unittest.main()
