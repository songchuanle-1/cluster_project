"""Saved collation-to-replay tests with synthetic bytes; native host checks mocked."""
import copy
import json
import pickle
import subprocess
import unittest
from unittest.mock import Mock

from frozen_capture_contract_20260916 import fingerprint
from relocated_saved_replay_20260921 import prepare_relocated_replay
from same_child_collation_20260920 import PROBE_RECEIPT
import test_relocated_saved_collation_20260920 as collation_tests


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.fixture = collation_tests.CollationTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.output = self.fixture.output.parent.resolve() / "output"
        self.output.mkdir()
        self.fixture.output = self.output / "collated"
        self.collation = self.fixture.run_job()
        self.location_fixture = self.fixture.fixture
        self.location = self.location_fixture.adapter()
        self.binding = copy.deepcopy(self.location.contract["original_binding"])
        (self.output.parent / "sentinel").write_bytes(b"read-only-sentinel")
        (self.output / "probe-output").write_bytes(b"scratch-write-ok")
        self.receipt = dict(
            contract="same-child-collation-v1", pid=123, manifest_sha256="a" * 64,
            probe=copy.deepcopy(PROBE_RECEIPT), collation=self.collation,
            same_child_integration_completed=True, native_execution_verified=False,
            scientific_validation_complete=False, admission=False)
        self.publish()
        self.load_batch = Mock(side_effect=lambda path: pickle.loads(path.read_bytes()))
        self.location_fixture.load.reset_mock()
        self.location_fixture.exporter.export_item.reset_mock()

    def publish(self):
        (self.output / "collated" / "collation.json").write_text(
            json.dumps(self.collation), encoding="utf-8")
        (self.output / "same_child.json").write_text(
            json.dumps(self.receipt), encoding="utf-8")
        self.completed = subprocess.CompletedProcess([], 0, json.dumps(self.receipt), "")

    def prepare(self, **changes):
        f = self.location_fixture
        kwargs = dict(
            location=self.location, exporter=f.exporter, registry_ids=f.ids,
            read_json=f.read_json, load_item=f.load, load_batch=self.load_batch,
            completed=self.completed, output=self.output, manifest_sha256="a" * 64,
            expected_binding=self.binding,
            expected_full_binding_sha256=fingerprint(f.joins),
            expected_indices=[3040, 3893])
        kwargs.update(changes)
        return prepare_relocated_replay(**kwargs)

    def test_exact_groups_preserve_inputs_full31_and_original_binding(self):
        before = copy.deepcopy((self.location.contract, self.location_fixture.payloads))
        prepared, joins = self.prepare()
        self.assertEqual([p["dataset_index"] for p, _ in prepared], [3040, 3893])
        self.assertEqual(joins["requested"], 31)
        self.assertEqual((self.location.contract, self.location_fixture.payloads), before)
        self.assertEqual(self.location_fixture.load.call_count, 2)
        self.assertEqual(self.location_fixture.exporter.export_item.call_count, 2)
        self.assertEqual(self.fixture.collate.call_count, 4)  # Initial collation only.
        for payload, digest in prepared:
            self.assertEqual(fingerprint(payload), digest)
            self.assertEqual(payload["source_binding"], self.location_fixture.source)
        self.assertFalse(self.collation["admission"])

    def test_independent_binding_mismatch_prevents_loading(self):
        with self.assertRaises(ValueError):
            self.prepare(expected_binding={"wrong": "b" * 64})
        self.location_fixture.load.assert_not_called()
        self.load_batch.assert_not_called()

    def test_independent_registry_mismatch_prevents_loading(self):
        with self.assertRaises(ValueError):
            self.prepare(expected_full_binding_sha256="b" * 64)
        self.location_fixture.load.assert_not_called()

    def test_wrong_or_boolean_indices_rejected_before_loading(self):
        for indices in ([3893, 3040], [3040, 3040], [True, 3893], [3040]):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                self.prepare(expected_indices=indices)
        self.location_fixture.load.assert_not_called()

    def test_missing_receipt_prevents_loading(self):
        (self.output / "same_child.json").unlink()
        with self.assertRaises(ValueError):
            self.prepare()
        self.location_fixture.load.assert_not_called()

    def test_changed_batch_bytes_prevent_loading(self):
        (self.output / "collated" / "batch_3040.pth").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.prepare()
        self.location_fixture.load.assert_not_called()
        self.load_batch.assert_not_called()

    def test_rewritten_location_map_rejected_before_loading(self):
        self.collation["source_locations"][0]["destination"] = "/tmp/changed"
        self.publish()
        with self.assertRaisesRegex(ValueError, "location"):
            self.prepare()
        self.location_fixture.load.assert_not_called()

    def test_count_change_rejected_before_loading(self):
        self.collation["binding_counts"] = {"bound": 31}
        self.publish()
        with self.assertRaisesRegex(ValueError, "counts"):
            self.prepare()
        self.location_fixture.load.assert_not_called()

    def test_loader_returns_wrong_payload(self):
        def wrong(path):
            saved = pickle.loads(path.read_bytes())
            saved["axes"][0]["ann_id"] = -1
            return saved
        self.load_batch.side_effect = wrong
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            self.prepare()

    def test_source_drift_blocks_saved_batch_loading(self):
        self.location_fixture.source_check.return_value = {}
        with self.assertRaisesRegex(ValueError, "source"):
            self.prepare()
        self.load_batch.assert_not_called()

    def test_late_batch_file_mutation_rejected(self):
        def mutate(path):
            saved = pickle.loads(path.read_bytes())
            if self.load_batch.call_count == 2:
                (self.output / "collated" / "batch_3040.pth").write_bytes(b"changed")
            return saved
        self.load_batch.side_effect = mutate
        with self.assertRaises(ValueError):
            self.prepare()

    def test_late_prepared_object_mutation_rejected(self):
        loaded = []
        def mutate(path):
            saved = pickle.loads(path.read_bytes())
            if loaded:
                loaded[0]["batch"]["ann_ids"][0] = -1
            loaded.append(saved)
            return saved
        self.load_batch.side_effect = mutate
        with self.assertRaisesRegex(ValueError, "changed"):
            self.prepare()

    def test_final_source_check_rejects_drift(self):
        self.location_fixture.source_check.side_effect = [self.binding, self.binding, {}]
        with self.assertRaisesRegex(ValueError, "source"):
            self.prepare()
        self.assertEqual(self.load_batch.call_count, 2)

    def test_non_cpu_batch_rejected(self):
        value = Mock()
        value.device.type = "cuda"
        self.load_batch.return_value = {"batch": value}
        self.load_batch.side_effect = None
        with self.assertRaisesRegex(ValueError, "CPU-only"):
            self.prepare()

    def test_registry_substitution_rejected(self):
        with self.assertRaises(ValueError):
            self.prepare(registry_ids=self.location_fixture.ids[:-1] + ["other"])
        self.load_batch.assert_not_called()

    def test_gate_promotion_rejected(self):
        self.receipt["admission"] = True
        self.publish()
        with self.assertRaisesRegex(ValueError, "flags"):
            self.prepare()
        self.location_fixture.load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
