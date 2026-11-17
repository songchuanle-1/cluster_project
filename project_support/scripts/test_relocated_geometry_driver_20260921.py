"""Synthetic integration only: native execution checks/model/evaluator are mocked."""
import copy
from contextlib import nullcontext
import json
import unittest
from unittest.mock import Mock, patch

from frozen_capture_contract_20260916 import fingerprint
from native_registry_geometry_runner_20260920 import dump_new
from relocated_geometry_driver_20260921 import run_relocated
import test_relocated_saved_replay_20260921 as replay_tests


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.fixture = replay_tests.ReplayTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        loc = f.location_fixture
        self.output = f.output.parent / "geometry"
        self.factory = Mock(return_value=object())
        self.execution = Mock()
        self.source = Mock(return_value=copy.deepcopy(f.binding))
        self.observe = Mock(return_value=dict(
            server="server-4", gpu=0, observed_at=100, memory_total_mib=32000,
            memory_used_mib=0, utilization_percent=0, process_count=0))
        self.kwargs = dict(
            location=f.location, exporter=loc.exporter, registry={"pairs": []},
            registry_ids=loc.ids, read_json=loc.read_json, load_item=loc.load,
            load_batch=f.load_batch, completed=f.completed, collation_output=f.output,
            manifest_sha256="a"*64, expected_binding=f.binding,
            expected_full_binding_sha256=fingerprint(loc.joins),
            expected_indices=[3040, 3893], gpu=0, observe_capacity=self.observe,
            clock=lambda: 101, required_memory_mib=4000, coordinated_slot=True,
            execution_check=self.execution, source_check=self.source,
            model_factory=self.factory, forward_context=nullcontext, output=self.output)
        self.forward = self.enterContext(patch(
            "relocated_geometry_driver_20260921.replay_forward", side_effect=self.capture))
        self.evaluator = self.enterContext(patch(
            "relocated_geometry_driver_20260921.evaluate",
            return_value={"overall": {"requested": 31, "counts": {"missing_binding": 27}}}))

    def capture(self, model, prepared, binding, sink):
        records = []
        for step, (saved, digest) in enumerate(prepared):
            self.assertEqual(fingerprint(saved), digest)
            self.assertEqual(saved["source_binding"], binding)
            record = {"synthetic_index": saved["dataset_index"]}
            sink(step, saved["dataset_index"], record)
            records.append(record)
        return records

    def run_driver(self, **changes):
        return run_relocated(**dict(self.kwargs, **changes))

    def assert_failed_output(self):
        self.assertTrue((self.output / "failure.json").is_file())
        self.assertFalse((self.output / "capture.json").exists())

    def test_saved_receipt_to_capture_preserves_full31_indices_and_no_resampling(self):
        f = self.fixture
        calls = f.fixture.collate.call_count
        report = self.run_driver()
        self.assertEqual(report["original_dataset_indices"], [3040, 3893])
        self.assertEqual(report["registry_denominators"]["requested"], 31)
        self.assertEqual(report["completed_items"], 2)
        self.assertEqual(f.fixture.collate.call_count, calls)
        self.assertEqual(f.location_fixture.load.call_count, 2)
        self.assertEqual(self.execution.call_count, 2)
        self.assertEqual(report["expected_binding"], f.binding)
        for flag in ("native_execution_verified", "scientific_validation_complete",
                     "admission", "training_launch", "new_train_transforms"):
            self.assertIs(report[flag], False)
        self.assertFalse((self.output / "failure.json").exists())

    def test_gpu1_is_also_allowed(self):
        self.observe.return_value["gpu"] = 1
        self.assertEqual(self.run_driver(gpu=1)["capacity"]["gpu"], 1)

    def test_disallowed_gpu_and_missing_coordination_block_loading(self):
        for changes in (dict(gpu=7), dict(gpu=True), dict(coordinated_slot=False)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_driver(**changes)
        self.fixture.load_batch.assert_not_called()
        self.factory.assert_not_called()

    def test_external_execution_rejection_blocks_deserialization(self):
        self.execution.side_effect = ValueError("runtime unavailable")
        with self.assertRaisesRegex(ValueError, "runtime"):
            self.run_driver()
        self.fixture.load_batch.assert_not_called()
        self.factory.assert_not_called()

    def test_source_drift_blocks_deserialization(self):
        self.source.return_value = {}
        with self.assertRaises(ValueError):
            self.run_driver()
        self.fixture.load_batch.assert_not_called()

    def test_foreign_busy_gpu_blocks_allocation(self):
        self.observe.return_value["process_count"] = 1
        with self.assertRaises(ValueError):
            self.run_driver()
        self.factory.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_stale_capacity_blocks_allocation(self):
        with self.assertRaises(ValueError):
            self.run_driver(clock=lambda: 161)
        self.factory.assert_not_called()

    def test_existing_output_preserved(self):
        self.output.mkdir()
        (self.output / "foreign").write_text("preserve", encoding="ascii")
        with self.assertRaises(FileExistsError):
            self.run_driver()
        self.assertEqual((self.output / "foreign").read_text(), "preserve")
        self.execution.assert_not_called()

    def test_nested_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "separate"):
            self.run_driver(output=self.fixture.output / "nested")
        self.execution.assert_not_called()

    def test_tampered_batch_blocks_model(self):
        (self.fixture.output / "collated" / "batch_3040.pth").write_bytes(b"bad")
        with self.assertRaises(ValueError):
            self.run_driver()
        self.factory.assert_not_called()

    def test_wrong_full_registry_digest_blocks_loading(self):
        with self.assertRaises(ValueError):
            self.run_driver(expected_full_binding_sha256="0"*64)
        self.fixture.load_batch.assert_not_called()
        self.factory.assert_not_called()

    def test_factory_failure_publishes_only_failure(self):
        self.factory.side_effect = RuntimeError("allocation failed")
        with self.assertRaises(RuntimeError):
            self.run_driver()
        self.assert_failed_output()

    def test_forward_failure_publishes_only_failure(self):
        self.forward.side_effect = RuntimeError("forward failed")
        with self.assertRaises(RuntimeError):
            self.run_driver()
        self.assert_failed_output()

    def test_incomplete_forward_rejected(self):
        self.forward.side_effect = lambda *args: []
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            self.run_driver()
        self.assert_failed_output()

    def test_post_forward_source_drift_rejected(self):
        self.source.side_effect = [self.fixture.binding, self.fixture.binding, {}]
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assert_failed_output()

    def test_post_forward_batch_bytes_drift_rejected(self):
        def mutate(*args):
            records = self.capture(*args)
            (self.fixture.output / "collated" / "batch_3040.pth").write_bytes(b"drift")
            return records
        self.forward.side_effect = mutate
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assert_failed_output()

    def test_post_forward_prepared_mutation_rejected(self):
        def mutate(model, prepared, binding, sink):
            records = self.capture(model, prepared, binding, sink)
            prepared[0][0]["dataset_index"] = 999
            return records
        self.forward.side_effect = mutate
        with self.assertRaisesRegex(ValueError, "changed"):
            self.run_driver()
        self.assert_failed_output()

    def test_publication_failure_never_leaves_success(self):
        def fail(path, value):
            if path.name == "capture.json":
                raise OSError("publication failed")
            dump_new(path, value)
        with patch("relocated_geometry_driver_20260921.dump_new", side_effect=fail):
            with self.assertRaises(OSError):
                self.run_driver()
        self.assert_failed_output()
        report = json.loads((self.output / "failure.json").read_text())
        self.assertFalse(report["native_execution_verified"])


class CaptureIntegrationTests(unittest.TestCase):
    def test_real_replay_hook_and_evaluator_with_synthetic_saved_model(self):
        import test_saved_geometry_replay_20260920 as original_tests
        from saved_geometry_replay_20260920 import prepare_replay
        from test_native_registry_geometry_runner_20260920 import setup

        f = original_tests.ReplayTest()
        f.setUp()
        self.addCleanup(f.doCleanups)
        prepared, joins = prepare_replay(f.request, f.exporter, f.load)
        expected = f.request["physical"]["observed_binding"]
        location = Mock(contract={"original_binding": expected})
        output = f.physical.parent / "geometry"
        observation = dict(
            server="server-4", gpu=0, observed_at=100, memory_total_mib=32000,
            memory_used_mib=0, utilization_percent=0, process_count=0)
        with patch("relocated_geometry_driver_20260921.prepare_relocated_replay",
                   return_value=(prepared, joins)), patch(
                       "relocated_geometry_driver_20260921.verify_completion"):
            report = run_relocated(
                location, f.exporter, setup()[3], [], Mock(), Mock(), Mock(),
                completed=None, collation_output=f.collated, manifest_sha256="a"*64,
                expected_binding=expected, expected_full_binding_sha256=fingerprint(joins),
                expected_indices=[1], gpu=0, observe_capacity=lambda gpu: observation,
                clock=lambda: 101, required_memory_mib=4000, coordinated_slot=True,
                execution_check=Mock(), source_check=lambda: expected,
                model_factory=lambda: f.model, forward_context=nullcontext, output=output)
        self.assertEqual(report["registry_denominators"]["requested"], 2)
        self.assertEqual(report["registry_denominators"]["counts"]["missing_binding"], 1)
        record = json.loads((output / "geometry_000.json").read_text())
        self.assertEqual(record["criterion_calls"], 1)
        self.assertEqual(record["loss"], 1.25)
        self.assertEqual(len(f.model.criterion.hooks), 1)
        self.assertEqual(fingerprint(prepared[0][0]), prepared[0][1])
        self.assertFalse(report["native_execution_verified"])


if __name__ == "__main__":
    unittest.main()
