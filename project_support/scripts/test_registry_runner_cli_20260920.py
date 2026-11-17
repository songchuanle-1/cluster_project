"""Synthetic CLI integration only: no native data, Torch or GPU execution."""
from contextlib import ExitStack, nullcontext, redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import native_registry_geometry_runner_20260920 as runner
from frozen_capture_contract_20260916 import file_sha256, model_package_sha256
from test_native_registry_geometry_runner_20260920 import setup


class RunnerCliTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.base = Path(self.stack.enter_context(tempfile.TemporaryDirectory())).resolve()
        self.root = self.base / "Cluster"
        self.out = self.base / "pipeline" / "synthetic-capture"
        self.native, _, self.model, self.registry, _, _ = setup()
        self.config = self.root / "configs/Quard/ctf_hcg_csort" / (runner.MODEL_CLASS + ".yaml")
        self.dataset_source = self.root / "framework/dataset/scannetv2.py"
        self.checkpoint = self.base / "synthetic.pth"
        self.registry_path = self.base / "registry.json"
        self.expected_path = self.base / "expected.json"
        model_source = (self.root / "framework/model/Quard_model" /
                        runner.MODEL_CLASS / "__init__.py")
        for path in (self.config, self.dataset_source, self.checkpoint, model_source):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic fixture\n", encoding="ascii")
        self.registry_path.write_text(json.dumps(self.registry), encoding="ascii")
        self.expected = dict(
            producer_sha256=runner.runner_manifest()["producer_sha256"],
            model_source_sha256=model_package_sha256(self.root, runner.MODEL_CLASS),
            config_sha256=file_sha256(self.config),
            checkpoint_sha256=file_sha256(self.checkpoint),
            dataset_source_sha256=file_sha256(self.dataset_source),
            registry_sha256=file_sha256(self.registry_path))
        self.save_expected()
        self.model.cuda = Mock(return_value=self.model)
        self.model.eval = Mock(return_value=self.model)
        self.model.load_state_dict = Mock()
        self.network = Mock(return_value=self.model)
        self.build = Mock(return_value=self.native)
        self.capacity = self.stack.enter_context(patch.object(
            runner, "check_capacity", return_value={"synthetic_only": True}))
        self.stack.enter_context(patch.object(runner, "AUTHORIZED_ROOT", self.root))
        self.stack.enter_context(patch.object(
            runner.inspect, "getfile", return_value=str(self.dataset_source)))
        self.stack.enter_context(patch.object(
            runner.importlib, "import_module", return_value=SimpleNamespace(Network=self.network)))
        class ConfigMap(dict):
            __getattr__ = dict.__getitem__
            __setattr__ = dict.__setitem__
        self.cfg = SimpleNamespace(model=ConfigMap(), data=SimpleNamespace(
            train=SimpleNamespace(data_root="synthetic")))
        self.torch = SimpleNamespace(
            set_num_threads=Mock(), cuda=SimpleNamespace(
                set_per_process_memory_fraction=Mock()),
            load=Mock(return_value={"model": {
                "weight": 1, "text_encoder.embeddings.position_ids": 2}}),
            no_grad=nullcontext)
        self.stack.enter_context(patch.dict(sys.modules, {
            "torch": self.torch,
            "gorilla": SimpleNamespace(set_random_seed=Mock(), Config=SimpleNamespace(
                fromfile=Mock(return_value=self.cfg))),
            "framework": SimpleNamespace(),
            "framework.dataset": SimpleNamespace(build_dataset=self.build)}))
        self.stack.enter_context(patch.dict(os.environ))
        old_path = sys.path[:]
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), old_path))

    def save_expected(self):
        self.expected_path.write_text(json.dumps(self.expected), encoding="ascii")

    def run_cli(self, extra=()):
        with redirect_stdout(io.StringIO()):
            runner.main(["--root", str(self.root), "--checkpoint", str(self.checkpoint),
                         "--registry", str(self.registry_path),
                         "--expected-binding", str(self.expected_path),
                         "--output", str(self.out), *extra])

    def test_success_reads_exact_binding_and_emits_complete_bundle(self):
        self.run_cli()
        report = runner.verify_output(self.out, self.expected)
        self.assertEqual(report["completed_items"], 1)
        self.assertEqual(report["original_dataset_indices"], [1])
        self.assertEqual(report["registry_denominators"]["requested"], 2)
        self.assertFalse(report["native_execution_verified"])
        self.assertFalse(report["scientific_validation_complete"])
        self.model.load_state_dict.assert_called_once_with({"weight": 1}, strict=True)
        self.assertEqual(len(self.model.criterion.hooks), 1)

    def test_binding_mismatch_prevents_capacity_and_native_import_work(self):
        self.expected["checkpoint_sha256"] = "0" * 64
        self.save_expected()
        with self.assertRaisesRegex(ValueError, "binding differs"):
            self.run_cli()
        self.capacity.assert_not_called()
        self.build.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_extra_binding_key_rejected(self):
        self.expected["unverified"] = True
        self.save_expected()
        with self.assertRaisesRegex(ValueError, "binding differs"):
            self.run_cli()
        self.capacity.assert_not_called()

    def test_malformed_binding_file_rejected(self):
        self.expected_path.write_text("{", encoding="ascii")
        with self.assertRaises(json.JSONDecodeError):
            self.run_cli()
        self.capacity.assert_not_called()

    def test_capacity_failure_prevents_dataset_and_output(self):
        self.capacity.side_effect = ValueError("synthetic process cap")
        with self.assertRaisesRegex(ValueError, "process cap"):
            self.run_cli()
        self.build.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_unauthorized_root_and_existing_output_rejected(self):
        with patch.object(runner, "AUTHORIZED_ROOT", self.base / "elsewhere"):
            with self.assertRaisesRegex(ValueError, "authorized"):
                self.run_cli()
        self.out.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "new project-local"):
            self.run_cli()
        self.capacity.assert_not_called()

    def test_outside_output_and_item_limits_rejected(self):
        self.out = self.base / "outside"
        with self.assertRaisesRegex(ValueError, "project-local"):
            self.run_cli()
        for limit in ("0", "3"):
            with self.assertRaisesRegex(ValueError, "one or two"):
                self.run_cli(("--items", limit))
        self.capacity.assert_not_called()

    def test_loaded_dataset_source_mismatch_rejected(self):
        with patch.object(runner.inspect, "getfile", return_value=str(self.checkpoint)):
            with self.assertRaisesRegex(ValueError, "dataset implementation"):
                self.run_cli()
        self.network.assert_not_called()

    def test_missing_metadata_prevents_model_capture(self):
        self.native.scene_inputs[1][0]["object_id"] = "88"
        with self.assertRaisesRegex(ValueError, "unambiguous native metadata"):
            self.run_cli()
        self.network.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_model_load_failure_is_pre_capture_rejection(self):
        self.model.load_state_dict.side_effect = RuntimeError("synthetic incompatible state")
        with self.assertRaisesRegex(RuntimeError, "incompatible state"):
            self.run_cli()
        self.model.cuda.assert_not_called()
        self.assertFalse(self.out.exists())

    def test_capture_failure_writes_failure_not_success_and_restores_hooks(self):
        self.model.behavior = "raise"
        with self.assertRaises(RuntimeError):
            self.run_cli()
        failure = json.loads((self.out / "failure.json").read_text())
        self.assertFalse(failure["native_capture_completed"])
        self.assertFalse((self.out / "capture.json").exists())
        self.assertEqual(len(self.model.criterion.hooks), 1)
        with self.assertRaisesRegex(ValueError, "Failed capture"):
            runner.verify_output(self.out, self.expected)

    def test_post_capture_source_drift_rejected_with_partial_geometry(self):
        capture = runner.capture_planned
        def drift(*args, **kwargs):
            records = capture(*args, **kwargs)
            self.config.write_text("# changed after capture\n", encoding="ascii")
            return records
        with patch.object(runner, "capture_planned", side_effect=drift):
            with self.assertRaisesRegex(ValueError, "binding differs"):
                self.run_cli()
        self.assertTrue((self.out / "geometry_000.json").exists())
        self.assertTrue((self.out / "failure.json").exists())
        self.assertFalse((self.out / "capture.json").exists())
        with self.assertRaises(ValueError):
            runner.verify_output(self.out, self.expected)

    def test_missing_marker_and_changed_artifact_rejected(self):
        self.run_cli()
        marker = self.out / "capture.json"
        text = marker.read_text()
        marker.unlink()
        with self.assertRaises(FileNotFoundError):
            runner.verify_output(self.out, self.expected)
        marker.write_text(text, encoding="ascii")
        (self.out / "geometry_000.json").write_text("{}", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "artifact differs"):
            runner.verify_output(self.out, self.expected)

    def test_inventory_traversal_duplicates_and_extra_files_rejected(self):
        self.run_cli()
        marker = self.out / "capture.json"
        original = json.loads(marker.read_text())
        for name in ("../outside.json", "bindings.json"):
            report = copy.deepcopy(original)
            report["artifacts"][-1]["path"] = name
            marker.write_text(json.dumps(report), encoding="ascii")
            with self.assertRaisesRegex(ValueError, "artifact inventory"):
                runner.verify_output(self.out, self.expected)
        marker.write_text(json.dumps(original), encoding="ascii")
        (self.out / ".pending_partial").write_text("{", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "Partial"):
            runner.verify_output(self.out, self.expected)

    def test_success_marker_publication_failure_preserves_failure_artifact(self):
        link = os.link
        def fail_marker(source, dest):
            if Path(dest).name == "capture.json":
                raise OSError("synthetic disk failure")
            return link(source, dest)
        with patch.object(runner.os, "link", side_effect=fail_marker):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.run_cli()
        self.assertFalse((self.out / "capture.json").exists())
        self.assertTrue((self.out / "failure.json").exists())
        self.assertFalse(list(self.out.glob(".pending_*")))


class AtomicPublicationTest(unittest.TestCase):
    def test_nonfinite_payload_does_not_create_partial_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.json"
            with self.assertRaises(ValueError):
                runner.dump_new(path, {"first": 1, "last": float("nan")})
            self.assertEqual(list(path.parent.iterdir()), [])

    def test_no_overwrite_and_temporary_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.json"
            runner.dump_new(path, {"first": 1})
            with self.assertRaises(FileExistsError):
                runner.dump_new(path, {"second": 2})
            self.assertEqual(json.loads(path.read_text()), {"first": 1})
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_failed_fsync_does_not_publish_partial_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.json"
            with patch.object(runner.os, "fsync", side_effect=OSError("synthetic fsync")):
                with self.assertRaises(OSError):
                    runner.dump_new(path, {"first": 1})
            self.assertEqual(list(path.parent.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
