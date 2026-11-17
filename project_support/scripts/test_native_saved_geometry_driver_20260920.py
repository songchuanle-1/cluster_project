"""Synthetic saved-driver integration, publication and failure boundary tests."""
import ast
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

from native_saved_geometry_driver_20260920 import run_saved
import test_saved_geometry_replay_20260920 as replay_tests
from test_native_registry_geometry_runner_20260920 import setup


class DriverTest(unittest.TestCase):
    def setUp(self):
        self.fixture = replay_tests.ReplayTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.output = f.physical.parent / "output"
        self.source = Mock(return_value=f.request["physical"]["observed_binding"])
        self.capacity = Mock(return_value=dict(coordinated_slot=True,
            process_cap_reached=False, measured_memory_sufficient=True))
        self.factory = Mock(return_value=f.model)
        self.registry = setup()[3]

    def run_driver(self):
        f = self.fixture
        return run_saved(f.request, f.exporter, self.registry, f.load,
                         self.factory, self.source, self.capacity, self.output)

    def test_end_to_end_preserves_missing_denominators_and_identities(self):
        report = self.run_driver()
        self.assertEqual(report["original_dataset_indices"], [1])
        self.assertEqual(report["completed_items"], 1)
        self.assertFalse(report["native_execution_verified"])
        self.assertFalse(report["new_train_transforms"])
        self.assertEqual(self.source.call_count, 3)
        self.assertTrue((self.output / "evaluation.json").exists())
        self.assertFalse((self.output / "failure.json").exists())
        self.assertEqual(len(self.fixture.model.criterion.hooks), 1)

    def test_cap_or_no_coordination_prevents_model_allocation(self):
        for change in (dict(process_cap_reached=True), dict(coordinated_slot=False),
                       dict(measured_memory_sufficient=False)):
            with self.subTest(change=change):
                self.capacity.return_value = dict(coordinated_slot=True,
                    process_cap_reached=False, measured_memory_sufficient=True)
                self.capacity.return_value.update(change)
                # Each preparation needs a fresh exporter.
                from referent_registry_binding_20260919 import BindingExporter
                old = self.fixture.exporter
                self.fixture.exporter = BindingExporter(self.registry,
                    old.plan["registry_sha256"], old.metadata,
                    old.source_binding, old.dataset_source_sha256)
                with self.assertRaises(ValueError):
                    self.run_driver()
                self.factory.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_forward_failure_never_publishes_success(self):
        self.fixture.model.behavior = "raise"
        with self.assertRaises(RuntimeError):
            self.run_driver()
        self.assertTrue((self.output / "failure.json").exists())
        self.assertFalse((self.output / "capture.json").exists())
        self.assertEqual(len(self.fixture.model.criterion.hooks), 1)

    def test_post_source_drift_marks_failed_bundle(self):
        self.source.side_effect = [
            self.source.return_value, self.source.return_value, {}]
        with self.assertRaises(ValueError):
            self.run_driver()
        self.assertTrue((self.output / "failure.json").exists())
        self.assertFalse((self.output / "capture.json").exists())

    def test_existing_output_is_not_overwritten(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_driver()
        self.factory.assert_not_called()

    def test_initial_source_drift_never_allocates(self):
        self.source.return_value = {}
        with self.assertRaises(ValueError):
            self.run_driver()
        self.factory.assert_not_called()
        self.capacity.assert_not_called()

    def test_artifact_mutation_during_forward_prevents_success(self):
        from saved_geometry_replay_20260920 import replay_forward
        def forward(*args, **kwargs):
            result = replay_forward(*args, **kwargs)
            self.fixture.batch_path.write_bytes(b"changed")
            return result
        with patch("native_saved_geometry_driver_20260920.replay_forward", forward):
            with self.assertRaisesRegex(ValueError, "bytes"):
                self.run_driver()
        self.assertFalse((self.output / "capture.json").exists())
        self.assertTrue((self.output / "failure.json").exists())

    def test_publication_failure_preserves_failure_marker(self):
        from native_registry_geometry_runner_20260920 import dump_new
        def publish(path, value):
            if path.name == "evaluation.json":
                raise OSError("injected persistence failure")
            dump_new(path, value)
        with patch("native_saved_geometry_driver_20260920.dump_new", publish):
            with self.assertRaises(OSError):
                self.run_driver()
        self.assertFalse((self.output / "capture.json").exists())
        self.assertTrue((self.output / "failure.json").exists())

    def test_native_cli_has_explicit_coordination_and_no_dataset_sampling(self):
        import native_saved_geometry_driver_20260920 as driver
        code = Path(driver.__file__).read_text(encoding="utf-8")
        tree = ast.parse(code)
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertIn("check_capacity", calls)
        self.assertIn("model.load_state_dict", calls)
        self.assertNotIn("native.__getitem__", calls)
        self.assertNotIn("capture_planned", calls)
        with self.assertRaisesRegex(ValueError, "coordination"):
            driver.main(["--request", "unused", "--output", "unused"])


if __name__ == "__main__":
    unittest.main()
