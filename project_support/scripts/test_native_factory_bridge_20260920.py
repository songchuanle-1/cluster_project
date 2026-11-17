"""Real pinned factory/bridge in isolated children; native edges are synthetic."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import same_child_collation_20260920 as bridge
from test_same_child_collation_20260920 import FACTORY


CHILD = r'''
import contextlib, importlib, json, os, sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import Mock, patch
scripts, bundle, scratch, digest, mode = sys.argv[1:]
sys.path.insert(0, scripts)
import same_child_collation_20260920 as bridge
bundle, scratch = Path(bundle), Path(scratch)
events_path = bundle / "events.jsonl"
def event(name):
    with events_path.open("a") as stream:
        stream.write(json.dumps(dict(name=name, pid=os.getpid())) + "\n")
def probe(*args):
    assert "relocated_native_factory_20260920" not in sys.modules
    event("probe")
    if mode == "probe_failure":
        raise ValueError("synthetic probe failure")
    return bridge.PROBE_RECEIPT
bridge.filesystem_probe = probe
original = bridge.checked_imports
def checked(bundle_path, sha, required, operation):
    def prepared(modules):
        factory = modules["relocated_native_factory_20260920"]
        event("pinned_factory_loaded")
        helper = importlib.import_module("_synthetic_inputs")
        inputs = helper.build_inputs()
        request = json.loads((bundle / "native_factory.json").read_text())
        root = Path(request["code_root"])
        dataset = ModuleType("framework.dataset")
        dataset.__file__ = str(root / "framework/dataset/__init__.py")
        def build_dataset(train, logger):
            event("dataset_constructor")
            assert train["data_root"] == str(root.parent / "data")
            if mode == "constructor_failure":
                raise RuntimeError("synthetic constructor failure")
            return inputs["native"]
        dataset.build_dataset = build_dataset
        train = dict(type="scannetv2_sample_graph_edge", dataset="scanrefer",
                     prefix="train", training=True, data_root="original")
        cfg = SimpleNamespace(data=SimpleNamespace(train=train))
        gorilla = Mock()
        gorilla.Config.fromfile.return_value = cfg
        inputs["torch"].cuda.is_initialized.return_value = False
        location = Mock()
        def verify():
            event("location_verify")
            if mode == "location_failure":
                raise ValueError("synthetic destination mismatch")
        location.verify.side_effect = verify
        def imports(name):
            event("import_" + name)
            return {"torch": inputs["torch"], "gorilla": gorilla,
                    "framework.dataset": dataset}[name]
        def assembly(*args):
            event("assembly")
            assert args[0] is location and args[2] is inputs["native"]
            if mode == "request_drift":
                (bundle / "native_factory.json").write_text("{}")
            if mode == "validator_failure":
                old = inputs["native"].collate_fn
                def broken(items):
                    batch = old(items)
                    batch["feats"] = batch["feats"].astype("float64")
                    return batch
                inputs["native"].collate_fn = broken
            return inputs
        if mode == "source_drift":
            Path(request["dataset_sources"][0]["path"]).write_text("drift")
        original_path = list(sys.path)
        with contextlib.ExitStack() as stack:
            for patcher in (
                patch.object(factory, "DESTINATION", root.parent),
                patch.object(factory, "DESTINATION_DATA", root.parent / "data"),
                patch.object(factory, "SavedPhysicalLocation", return_value=location),
                patch.object(factory, "assemble_inputs", side_effect=assembly),
                patch.object(factory.importlib, "import_module", side_effect=imports),
            ):
                stack.enter_context(patcher)
            try:
                result = operation(modules)
            finally:
                assert sys.path == original_path
                assert train["data_root"] == "original"
        event("operation_finished")
        return result
    try:
        return original(bundle_path, sha, required, prepared)
    finally:
        assert not any(name in sys.modules for name in (*required, "_synthetic_inputs"))
        event("pinned_modules_cleaned")
bridge.checked_imports = checked
receipt = bridge.run_same_child(
    bundle, digest, "relocated_native_factory_20260920",
    scratch, scratch.parent / "sentinel")
print(json.dumps(receipt))
'''


class NativeFactoryBridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.scratch = self.root / "output"
        self.scratch.mkdir()
        (self.root / "sentinel").write_bytes(b"read-only-sentinel")
        self.scripts = Path(bridge.__file__).parent
        code = self.root / "Cluster"
        documents = {}
        for name in ("migration", "physical", "prior", "registry", "config", "checkpoint"):
            path = self.root / (name + ".json")
            if name == "config":
                path = code / "configs/Quard/ctf_hcg_csort" / (
                    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="ascii")
            documents[name] = self.row(path)
        sources = []
        for name in ("framework/__init__.py", "framework/dataset/__init__.py",
                     "framework/dataset/scannetv2.py"):
            path = code / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# synthetic source\n", encoding="ascii")
            sources.append(self.row(path))
        assets = []
        for name in ("scanrefer/ScanRefer_train_new.json",
                     "scanrefer/scene_graphs_new_train.json",
                     "scannetv2-labels.combined.tsv", "roberta-base/tokenizer_config.json",
                     "roberta-base/vocab.json", "roberta-base/merges.txt"):
            path = self.root / "data" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="ascii")
            assets.append(self.row(path))
        request = dict(contract="relocated-native-factory-v1", code_root=str(code),
                       documents=documents, assets=assets, dataset_sources=sources,
                       capture_id="synthetic3040-3893")
        (self.bundle / "native_factory.json").write_text(json.dumps(request), encoding="ascii")
        for name in (*bridge.REQUIRED, "relocated_native_factory_20260920"):
            (self.bundle / (name + ".py")).write_bytes(
                (self.scripts / (name + ".py")).read_bytes())
        (self.bundle / "_synthetic_inputs.py").write_text(FACTORY, encoding="ascii")

    @staticmethod
    def row(path):
        return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def child(self, mode="success"):
        rows = [dict(self.row(path), path=path.name) for path in self.bundle.iterdir()]
        if mode == "missing_request":
            rows = [row for row in rows if row["path"] != "native_factory.json"]
        manifest = self.bundle / "manifest.json"
        manifest.write_text(json.dumps(dict(files=rows)), encoding="ascii")
        digest = self.row(manifest)["sha256"]
        if mode == "request_tamper":
            (self.bundle / "native_factory.json").write_text("{}")
        if mode == "asset_drift":
            (self.root / "data/roberta-base/vocab.json").write_text("drift")
        if mode == "unlisted_tokenizer":
            (self.root / "data/roberta-base/added_tokens.json").write_text("{}")
        return subprocess.run(
            [sys.executable, "-I", "-B", "-c", CHILD, str(self.scripts),
             str(self.bundle), str(self.scratch), digest, mode],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=""), capture_output=True,
            text=True, timeout=30)

    def events(self):
        path = self.bundle / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def assert_failure(self, mode, message, constructor=False):
        result = self.child(mode)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertFalse((self.scratch / "same_child.json").exists())
        self.assertFalse((self.scratch / "collated/collation.json").exists())
        if not constructor:
            self.assertNotIn("dataset_constructor", [row["name"] for row in self.events()])
        return result

    def test_pinned_entrypoint_constructs_and_collates_in_same_child(self):
        result = self.child()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        events = self.events()
        names = [row["name"] for row in events]
        self.assertEqual(names[:2], ["probe", "pinned_factory_loaded"])
        self.assertLess(names.index("location_verify"), names.index("import_torch"))
        self.assertLess(names.index("dataset_constructor"), names.index("assembly"))
        self.assertEqual(names.count("collate"), 4)
        self.assertEqual(names[-1], "pinned_modules_cleaned")
        self.assertEqual({row["pid"] for row in events}, {receipt["pid"]})
        self.assertNotEqual(receipt["pid"], os.getpid())
        self.assertEqual(receipt["collation"]["original_dataset_indices"], [3040, 3893])
        self.assertEqual(receipt["collation"]["registry_denominator"], 31)
        for key in ("native_execution_verified", "scientific_validation_complete", "admission"):
            self.assertFalse(receipt[key])
        self.assertFalse((self.bundle / "__pycache__").exists())

    def test_missing_pinned_request(self):
        self.assert_failure("missing_request", "active pinned request")

    def test_tampered_request_before_import(self):
        self.assert_failure("request_tamper", "source hash")
        self.assertNotIn("pinned_factory_loaded", [row["name"] for row in self.events()])

    def test_late_request_drift_removes_success_markers(self):
        self.assert_failure("request_drift", "source hash", constructor=True)
        self.assertIn("operation_finished", [row["name"] for row in self.events()])

    def test_source_drift_before_native_import(self):
        self.assert_failure("source_drift", "input hash")
        self.assertNotIn("import_torch", [row["name"] for row in self.events()])

    def test_constructor_asset_drift(self):
        self.assert_failure("asset_drift", "input hash")

    def test_unrecorded_optional_tokenizer_asset(self):
        self.assert_failure("unlisted_tokenizer", "Tokenizer file inventory")

    def test_location_failure(self):
        self.assert_failure("location_failure", "destination mismatch")

    def test_constructor_failure_cleans_modules(self):
        self.assert_failure("constructor_failure", "constructor failure", constructor=True)
        self.assertEqual(self.events()[-1]["name"], "pinned_modules_cleaned")

    def test_validator_failure_after_real_entrypoint(self):
        self.assert_failure("validator_failure", "feature concatenation/dtype", constructor=True)
        self.assertTrue((self.scratch / "collated/failure.json").exists())

    def test_probe_failure_prevents_factory_import(self):
        self.assert_failure("probe_failure", "probe failure")
        self.assertEqual([row["name"] for row in self.events()], ["probe"])


if __name__ == "__main__":
    unittest.main()
