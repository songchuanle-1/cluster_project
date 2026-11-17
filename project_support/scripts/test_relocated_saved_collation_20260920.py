"""Synthetic saved-location to collation integration; no native data or Torch."""
import copy
import json
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest.mock import Mock

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from relocated_saved_collation_20260920 import run_collation, require_cpu
import test_saved_physical_location_20260920 as location_tests


class CollationTest(unittest.TestCase):
    def setUp(self):
        self.fixture = location_tests.LocationTest()
        self.fixture.setUp()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "collated"
        for payload in self.fixture.payloads.values():
            index = payload["dataset_index"]
            payload["axes"] = [
                dict(scene="synthetic_%d" % index, ann_id=i, expression_slot=i,
                     scene_occurrence=0, dataset_index=index,
                     native_input_sha256=fingerprint(payload["item"]),
                     original_superpoint_ids=[0], sample_inverse=[0],
                     physical_instance_labels=[1])
                for i in range(len(payload["axes"]))]
        self.collate = Mock(side_effect=self.collate_batch)
        self.validate = Mock()
        self.save = Mock(side_effect=lambda value, stream: pickle.dump(value, stream))
        self.load_batch = Mock(side_effect=lambda path: pickle.loads(path.read_bytes()))

    @staticmethod
    def collate_batch(samples):
        item, axes = samples[0]
        return dict(
            scenes_len=[len(axes)], scan_ids=[axes[0]["scene"]],
            ann_ids=[axis["ann_id"] for axis in axes], synthetic_item=copy.deepcopy(item)
        ), copy.deepcopy(axes)

    def run_job(self):
        f = self.fixture
        return run_collation(f.adapter(), f.exporter, f.ids, f.read_json, f.load,
                             self.collate, self.validate, self.save, self.load_batch,
                             self.output)

    def assert_failed_output(self):
        self.assertTrue((self.output / "failure.json").is_file())
        self.assertFalse((self.output / "collation.json").exists())
        self.assertEqual(list(self.output.glob("batch_*.pth")), [])

    def test_exact_two_groups_full31_provenance_and_byte_bound_outputs(self):
        original = copy.deepcopy(self.fixture.payloads)
        report = self.run_job()
        self.assertEqual(report["original_dataset_indices"], [3040, 3893])
        self.assertEqual(report["registry_denominator"], 31)
        self.assertEqual(report["binding_counts"], {"bound": 4, "missing_capture": 27})
        self.assertEqual(report["observed_binding"], self.fixture.contract["original_binding"])
        self.assertEqual(report, json.loads((self.output / "collation.json").read_text()))
        self.assertEqual(self.collate.call_count, 4)
        self.assertEqual(self.validate.call_count, 2)
        self.assertEqual(self.fixture.payloads, original)
        for row in report["artifacts"]:
            self.assertEqual(file_sha256(row["path"]), row["sha256"])
            self.assertEqual(Path(row["path"]).stat().st_size, row["bytes"])
        self.assertFalse(report["native_execution_verified"])
        self.assertFalse(report["admission"])

    def test_existing_output_preserved_without_loading(self):
        self.output.mkdir()
        sentinel = self.output / "foreign"
        sentinel.write_text("keep")
        with self.assertRaises(FileExistsError):
            self.run_job()
        self.fixture.load.assert_not_called()
        self.assertEqual(sentinel.read_text(), "keep")

    def test_bad_input_prevents_collation_and_output_creation(self):
        self.fixture.source_check.return_value = {}
        with self.assertRaises(ValueError):
            self.run_job()
        self.collate.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_input_mutation_fails(self):
        def mutate(samples):
            samples[0][0].append("mutated")
            return self.collate_batch(samples)
        self.collate.side_effect = mutate
        with self.assertRaisesRegex(ValueError, "mutated"):
            self.run_job()
        self.assert_failed_output()

    def test_axes_substitution_fails(self):
        def substitute(samples):
            batch, axes = self.collate_batch(samples)
            axes[0]["ann_id"] = -1
            return batch, axes
        self.collate.side_effect = substitute
        with self.assertRaisesRegex(ValueError, "axes"):
            self.run_job()
        self.assert_failed_output()

    def test_batch_axis_identity_reuses_replay_validator(self):
        def invalid(samples):
            batch, axes = self.collate_batch(samples)
            batch["ann_ids"][0] = -1
            return batch, axes
        self.collate.side_effect = invalid
        with self.assertRaisesRegex(ValueError, "identity"):
            self.run_job()
        self.assert_failed_output()

    def test_native_field_validator_failure_is_not_ignored(self):
        self.validate.side_effect = ValueError("Native feature differs")
        with self.assertRaisesRegex(ValueError, "Native feature"):
            self.run_job()
        self.save.assert_not_called()
        self.assert_failed_output()

    def test_mutating_validator_rejected(self):
        self.validate.side_effect = lambda item, batch, axes: batch.update(changed=True)
        with self.assertRaisesRegex(ValueError, "validator mutated"):
            self.run_job()
        self.assert_failed_output()

    def test_nondeterministic_collation_rejected(self):
        def nondeterministic(samples):
            batch, axes = self.collate_batch(samples)
            batch["counter"] = self.collate.call_count
            return batch, axes
        self.collate.side_effect = nondeterministic
        with self.assertRaisesRegex(ValueError, "Repeated"):
            self.run_job()
        self.assert_failed_output()

    def test_partial_second_write_removes_only_owned_batches(self):
        def save(value, stream):
            if self.save.call_count == 2:
                (self.output / "foreign").write_text("keep")
                stream.write(b"partial")
                raise OSError("disk write failure")
            pickle.dump(value, stream)
        self.save.side_effect = save
        with self.assertRaisesRegex(OSError, "disk write"):
            self.run_job()
        self.assert_failed_output()
        self.assertEqual((self.output / "foreign").read_text(), "keep")

    def test_readback_tamper_removes_partial_outputs(self):
        self.load_batch.side_effect = lambda path: {}
        with self.assertRaisesRegex(ValueError, "readback"):
            self.run_job()
        self.assert_failed_output()

    def test_late_source_drift_removes_both_batches(self):
        f = self.fixture
        f.source_check.side_effect = [f.contract["original_binding"],
                                     f.contract["original_binding"], {}]
        with self.assertRaisesRegex(ValueError, "source"):
            self.run_job()
        self.assertEqual(self.save.call_count, 2)
        self.assert_failed_output()

    def test_serialization_mutation_rejected(self):
        def mutate(value, stream):
            pickle.dump(value, stream)
            value["batch"]["ann_ids"][0] = -1
        self.save.side_effect = mutate
        with self.assertRaisesRegex(ValueError, "serialization"):
            self.run_job()
        self.assert_failed_output()

    def test_late_output_drift_rejected(self):
        def mutate_late(value, stream):
            pickle.dump(value, stream)
            if self.save.call_count == 2:
                (self.output / "batch_3040.pth").write_bytes(b"changed")
        self.save.side_effect = mutate_late
        with self.assertRaisesRegex(ValueError, "Output changed"):
            self.run_job()
        self.assert_failed_output()

    def test_non_cpu_nested_value_rejected(self):
        device_value = Mock()
        device_value.device.type = "cuda"
        with self.assertRaisesRegex(ValueError, "CPU-only"):
            require_cpu({"nested": [device_value]})


if __name__ == "__main__":
    unittest.main()
