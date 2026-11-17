"""Synthetic constructor tests: no native data or third-party imports."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from frozen_capture_contract_20260916 import file_sha256
import relocated_native_factory_20260920 as factory


class AssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.rows = []
        for name in factory.REQUIRED_ASSETS | {"roberta-base/tokenizer.json"}:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="ascii")
            self.rows.append(dict(path=str(path), sha256=file_sha256(path)))

    def test_all_constructor_assets(self):
        factory.verify_assets(self.root, self.rows)

    def test_missing_required_asset(self):
        rows = [r for r in self.rows if not r["path"].endswith("merges.txt")]
        with self.assertRaisesRegex(ValueError, "Missing constructor"):
            factory.verify_assets(self.root, rows)

    def test_unrecorded_optional_tokenizer_file(self):
        (self.root / "roberta-base/added_tokens.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "Tokenizer file inventory"):
            factory.verify_assets(self.root, self.rows)

    def test_changed_bytes(self):
        Path(self.rows[0]["path"]).write_text("changed")
        with self.assertRaisesRegex(ValueError, "input hash"):
            factory.verify_assets(self.root, self.rows)

    def test_duplicate_and_missing_files(self):
        with self.assertRaisesRegex(ValueError, "distinct"):
            factory.verify_files(self.rows + self.rows[:1])
        Path(self.rows[0]["path"]).unlink()
        with self.assertRaisesRegex(ValueError, "Missing or redirected"):
            factory.verify_files(self.rows)

    def test_symlink_rejected(self):
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaisesRegex(ValueError, "redirected"):
                factory.verify_files(self.rows)


class ConstructorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.code = self.root / "Cluster"
        self.docs = {}
        for name in factory.DOCUMENTS:
            path = self.root / (name + ".json")
            if name == "config":
                path = self.code / "configs/Quard/ctf_hcg_csort" / (factory.MODEL_CLASS + ".yaml")
                path.parent.mkdir(parents=True)
            path.write_text("{}", encoding="ascii")
            self.docs[name] = dict(path=str(path), sha256=file_sha256(path))
        self.sources = []
        for name in ("framework/__init__.py", "framework/dataset/__init__.py",
                     "framework/dataset/scannetv2.py"):
            path = self.code / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic", encoding="ascii")
            self.sources.append(dict(path=str(path), sha256=file_sha256(path)))
        self.request = dict(
            contract="relocated-native-factory-v1", code_root=str(self.code),
            documents=self.docs, assets=[], dataset_sources=self.sources,
            capture_id="saved3040-3893")
        self.train = dict(type="scannetv2_sample_graph_edge", dataset="scanrefer",
                          prefix="train", training=True, data_root="original", aug=True)
        self.config = types.SimpleNamespace(data=types.SimpleNamespace(train=self.train))
        self.torch = Mock()
        self.torch.cuda.is_initialized.return_value = False
        self.gorilla = Mock()
        self.gorilla.Config.fromfile.return_value = self.config
        self.dataset = types.ModuleType("framework.dataset")
        self.dataset.__file__ = str(self.code / "framework/dataset/__init__.py")
        self.dataset.build_dataset = Mock()
        self.location = Mock()
        self.events = []
        self.location.verify.side_effect = lambda: self.events.append("verify")
        def imports(name):
            self.events.append(name)
            return {"torch": self.torch, "gorilla": self.gorilla,
                    "framework.dataset": self.dataset}[name]
        for patcher in (
                patch.object(factory, "DESTINATION", self.root),
                patch.object(factory, "verify_assets"),
                patch.object(factory, "SavedPhysicalLocation", return_value=self.location),
                patch.object(factory, "assemble_inputs", return_value={"synthetic": True}),
                patch.object(factory.importlib, "import_module", side_effect=imports),
                patch.dict(os.environ)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_native_constructor_order_without_sampling(self):
        before_path = list(sys.path)
        original = copy.deepcopy(self.train)
        self.assertEqual(factory.construct_inputs(self.request), {"synthetic": True})
        self.assertEqual(self.events, ["verify", "torch", "gorilla", "framework.dataset", "verify"])
        self.assertEqual(before_path, sys.path)
        self.assertEqual(self.train, original)
        actual = self.dataset.build_dataset.call_args.args[0]
        self.assertEqual(actual, dict(original, data_root=str(factory.DESTINATION_DATA)))
        factory.assemble_inputs.assert_called_once()
        self.assertEqual(factory.assemble_inputs.call_args.args[1], b"{}")
        self.torch.load.assert_not_called()

    def test_source_drift_before_import(self):
        Path(self.sources[0]["path"]).write_text("drift")
        with self.assertRaisesRegex(ValueError, "input hash"):
            factory.construct_inputs(self.request)
        factory.importlib.import_module.assert_not_called()

    def test_location_failure_before_import(self):
        self.location.verify.side_effect = ValueError("destination mismatch")
        with self.assertRaisesRegex(ValueError, "destination"):
            factory.construct_inputs(self.request)
        factory.importlib.import_module.assert_not_called()

    def test_wrong_train_configuration(self):
        for key, value in (("training", False), ("dataset", "multi3drefer"),
                           ("prefix", "val"), ("type", "other")):
            with self.subTest(key=key), patch.dict(self.train, {key: value}):
                with self.assertRaisesRegex(ValueError, "TRAIN configuration"):
                    factory.construct_inputs(self.request)
        self.dataset.build_dataset.assert_not_called()

    def test_wrong_entrypoint_and_restored_path(self):
        original_path = list(sys.path)
        self.dataset.__file__ = str(self.root / "shadow.py")
        with self.assertRaisesRegex(ValueError, "entrypoint identity"):
            factory.construct_inputs(self.request)
        self.assertEqual(sys.path, original_path)
        self.dataset.build_dataset.assert_not_called()

    def test_preimported_native_dependency(self):
        with patch.dict(sys.modules, {"framework": types.ModuleType("framework")}):
            with self.assertRaisesRegex(ValueError, "imported before"):
                factory.construct_inputs(self.request)
        factory.importlib.import_module.assert_not_called()

    def test_constructor_failure_restores_path(self):
        original_path = list(sys.path)
        self.dataset.build_dataset.side_effect = RuntimeError("constructor failed")
        with self.assertRaisesRegex(RuntimeError, "constructor failed"):
            factory.construct_inputs(self.request)
        self.assertEqual(sys.path, original_path)
        factory.assemble_inputs.assert_not_called()

    def test_cuda_initialized_blocks_constructor(self):
        self.torch.cuda.is_initialized.return_value = True
        with self.assertRaisesRegex(ValueError, "CUDA"):
            factory.construct_inputs(self.request)
        self.dataset.build_dataset.assert_not_called()

    def test_document_and_source_inventory(self):
        for key in ("documents", "dataset_sources"):
            bad = copy.deepcopy(self.request)
            if key == "documents":
                bad[key].pop("checkpoint")
            else:
                bad[key].pop()
            with self.subTest(key=key), self.assertRaises(ValueError):
                factory.construct_inputs(bad)
        factory.importlib.import_module.assert_not_called()


class EntrypointTest(unittest.TestCase):
    def test_unpinned_loader_rejected(self):
        with self.assertRaisesRegex(ValueError, "active pinned"):
            factory.read_pinned_request()

    def test_nonisolated_public_entrypoint_rejected(self):
        with patch.object(factory.sys, "flags", types.SimpleNamespace(isolated=False)):
            with self.assertRaisesRegex(ValueError, "Isolated CPU"):
                factory.build_inputs()

    def test_pinned_request_rechecked(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / factory.REQUEST
            path.write_text('{"contract": "synthetic"}')
            loader = Mock(active=True, files={
                factory.REQUEST: (path, file_sha256(path))},
                loaded={factory.__name__: factory})
            with patch.object(factory, "__loader__", loader):
                self.assertEqual(factory.read_pinned_request(), {"contract": "synthetic"})
                loader.verify.assert_called_once()
                path.write_text("{}")
                with self.assertRaisesRegex(ValueError, "request changed"):
                    factory.read_pinned_request()


if __name__ == "__main__":
    unittest.main()
