"""Factory contract tests with generated registry/native objects, no Torch/data."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from frozen_capture_contract_20260916 import file_sha256, fingerprint
from referent_registry_binding_20260919 import BindingExporter
from relocated_factory_core_20260920 import assemble_inputs
from relocated_producer_closure_20260920 import producer_closure
from saved_replay_migration_20260920 import DESTINATION_DATA


class SyntheticNative:
    training = True
    use_xyz = True
    data_root = str(DESTINATION_DATA)

    def __getitem__(self, index):
        raise AssertionError("Saved-only factory must never sample")

    def collate_fn(self, items):
        raise AssertionError("Factory must not collate")


class FactoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.native = SyntheticNative()
        self.native.scene_inputs = [[dict(
            scene_id="scene%d" % i, ann_id=str(i), object_id="1")] for i in range(31)]
        registry = dict(pairs=[dict(
            pair_id="scene%d:0:%d" % (i, i), scene="scene%d" % i,
            expression_slot=0, ann_id=i, target_object_id=1,
            observed_control_object_id=2, primary_same_class_pair_eligible=True,
            same_class_control_pool=[2]) for i in range(31)])
        self.registry_bytes = json.dumps(registry).encode("ascii")
        self.source_path = Path(__file__).absolute()
        binding = dict(
            producer_sha256="a"*64, checkpoint_sha256="b"*64,
            model_source_sha256="c"*64, config_sha256="d"*64,
            dataset_source_sha256=file_sha256(self.source_path),
            registry_sha256=hashlib.sha256(self.registry_bytes).hexdigest())
        source = {k: v for k, v in binding.items()
                  if k not in ("dataset_source_sha256", "registry_sha256")}
        self.joins = BindingExporter(
            registry, binding["registry_sha256"], self.native.scene_inputs,
            source, binding["dataset_source_sha256"]).manifest()
        self.join_path = self.root / "physical_bindings.json"
        self.join_path.write_text(json.dumps(self.joins), encoding="ascii")
        self.location = Mock()
        self.location.contract = dict(original_binding=binding,
                                      original_dataset_indices=[3040, 3893])
        self.location.locations = {
            "physical_bindings.json": str(self.join_path),
            "item_3040.pth": str(self.root / "item_3040.pth"),
            "item_3893.pth": str(self.root / "item_3893.pth")}
        self.torch = Mock()
        self.torch.cuda.is_initialized.return_value = False

    def assemble(self, **overrides):
        inputs = dict(location=self.location, registry_bytes=self.registry_bytes,
                      native=self.native, torch=self.torch, capture_id="saved",
                      dataset_source_path=self.source_path)
        return assemble_inputs(**dict(inputs, **overrides))

    def test_real_exporter_complete_plan_no_sampling_or_tensor_load(self):
        before = copy.deepcopy(self.native.scene_inputs)
        result = self.assemble()
        self.assertIsInstance(result["exporter"], BindingExporter)
        self.assertEqual(len(result["registry_ids"]), 31)
        self.assertEqual(result["exporter"].plan["counts"], {"planned": 31})
        self.assertEqual(before, self.native.scene_inputs)
        self.torch.load.assert_not_called()
        self.location.validate_denominator.assert_called_once()
        self.assertEqual(set(result), {
            "location", "exporter", "registry_ids", "read_json", "load_item",
            "native", "torch", "capture_id", "producer_sha256"})

    def test_original_registry_bytes_required(self):
        with self.assertRaisesRegex(ValueError, "registry bytes"):
            self.assemble(registry_bytes=self.registry_bytes+b" ")
        self.location.verify.assert_not_called()

    def test_full_denominator_required(self):
        registry = json.loads(self.registry_bytes)
        registry["pairs"].pop()
        data = json.dumps(registry).encode()
        self.location.contract["original_binding"]["registry_sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError, "Full31"):
            self.assemble(registry_bytes=data)

    def test_actual_dataset_source_hash_required(self):
        self.location.contract["original_binding"]["dataset_source_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "class source"):
            self.assemble()

    def test_actual_dataset_source_identity_required(self):
        with self.assertRaisesRegex(ValueError, "class source"):
            self.assemble(dataset_source_path=self.join_path)

    def test_native_configuration_and_cuda_fail_closed(self):
        for name, value in (("training", False), ("use_xyz", 1),
                            ("data_root", "/data3/songcl/data/data_cluster"),
                            ("collate_fn", None)):
            native = copy.copy(self.native)
            setattr(native, name, value)
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.assemble(native=native)
        self.torch.cuda.is_initialized.return_value = True
        with self.assertRaisesRegex(ValueError, "CUDA"):
            self.assemble()

    def test_changed_metadata_plan_rejected(self):
        self.native.scene_inputs[0][0]["object_id"] = "9"
        with self.assertRaisesRegex(ValueError, "metadata plan"):
            self.assemble()
        self.torch.load.assert_not_called()

    def test_location_verification_before_loading(self):
        self.location.verify.side_effect = ValueError("destination bytes")
        with self.assertRaisesRegex(ValueError, "destination bytes"):
            self.assemble()
        self.torch.load.assert_not_called()

    def test_original_bound_dispositions_accepted_without_imputing_capture(self):
        self.joins["dispositions"][0]["status"] = "bound"
        self.join_path.write_text(json.dumps(self.joins))
        result = self.assemble()
        self.assertEqual(result["exporter"].manifest()["bindings"], [])

    def test_loader_is_cpu_only_scoped_and_reverified(self):
        result = self.assemble()
        path = self.location.locations["item_3040.pth"]
        value = result["load_item"](path)
        self.assertIs(value, self.torch.load.return_value)
        self.torch.load.assert_called_once_with(path, map_location="cpu", weights_only=False)
        self.assertEqual(self.location.verify.call_count, 4)
        with self.assertRaisesRegex(ValueError, "tensor location"):
            result["load_item"](self.root / "other.pth")
        with self.assertRaisesRegex(ValueError, "JSON location"):
            result["read_json"](self.root / "other.json")

    def test_late_metadata_change_blocks_loader(self):
        result = self.assemble()
        self.native.scene_inputs[0][0]["ann_id"] = "99"
        with self.assertRaisesRegex(ValueError, "metadata changed"):
            result["load_item"](self.location.locations["item_3040.pth"])
        self.torch.load.assert_not_called()

    def test_invalid_capture_id(self):
        for value in (None, "", " "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.assemble(capture_id=value)


class ClosureTest(unittest.TestCase):
    def test_real_static_closure_covers_transitive_local_imports(self):
        result = producer_closure()
        names = {row["path"] for row in result["files"]}
        self.assertTrue({
            "saved_physical_location_20260920.py",
            "referent_registry_binding_20260919.py",
            "capture_support_20260916.py",
        }.issubset(names))
        self.assertIn("torch", result["external_imports"])
        self.assertFalse(result["deployment_ready"])
        self.assertEqual(result["closure_sha256"], fingerprint(result["files"]))

    def test_transitive_cycles_and_function_local_imports_without_execution(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / "a.py").write_text("raise RuntimeError('do not execute')\nimport b\n")
            (root / "b.py").write_text("def f():\n import a\n import json\n")
            result = producer_closure(root, ["a.py"])
            self.assertEqual([r["path"] for r in result["files"]], ["a.py", "b.py"])
            self.assertEqual(result["external_imports"], ["json"])

    def test_duplicate_empty_and_nonlocal_entry_rejected(self):
        for entries in ([], ["a.py", "a.py"], ["../outside.py"]):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                producer_closure(entries=entries)


if __name__ == "__main__":
    unittest.main()
