"""Synthetic handoff/coordinator checks; no installed Torch or CUDA execution."""
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest
from unittest.mock import Mock

import preidentity_handoff_20260921 as handoff
from pinned_diagnostic_imports_20260920 import digest
import test_preidentity_torch_imports_20260921 as imports_fixture
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE
from test_gpu_runtime_validation_20260921 import UUID
import test_logical_gpu_identity_20260921 as identity_fixture


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.imports = imports_fixture.PreIdentityImportsTests()
        self.imports.setUp()
        self.addCleanup(self.imports.doCleanups)
        self.identity = identity_fixture.LogicalIdentityTests()
        self.identity.setUp()
        self.addCleanup(self.identity.doCleanups)
        self.imports.change(
            "torch", "from types import SimpleNamespace as S\n"
            "version=S(cuda='12.8', hip=None)\n"
            "cuda=S(is_initialized=lambda: False, is_available=lambda: True,\n"
            "device_count=lambda: 1, current_device=lambda: 0,\n"
            "get_device_properties=lambda i: S(uuid=" + repr(UUID[4:]) + "))\n")
        self.path = self.imports.root / "handoff.json"
        self.payload = dict(
            contract=handoff.CONTRACT, dependencies=self.imports.rows,
            bootstrap=[
                dict(name=name, path=module.__file__,
                     sha256=digest(Path(module.__file__).read_bytes()))
                for name, module in handoff._bootstrap_modules().items()])
        self.slot = Mock(return_value=True)
        self.execution = Mock(return_value=True)

    def build(self):
        self.path.write_text(json.dumps(self.payload), encoding="ascii")
        return handoff.PreIdentityHandoff(
            self.path, digest(self.path.read_bytes()))

    def collect(self, boundary=None, **kwargs):
        return (boundary or self.build()).collect(
            EXECUTABLE, **dict(dict(
                gpu=0, capacity=self.identity.capacity, required_memory_mib=20000,
                slot_check=self.slot, execution_check=self.execution), **kwargs))

    def test_end_to_end_pinned_synthetic_identity(self):
        boundary = self.build()
        result = self.collect(boundary)
        self.assertEqual(result["identity"]["device"]["logical_uuid"], UUID)
        self.assertIn("torch", result["dependency_modules"])
        self.assertEqual(self.slot.call_count, 4)
        self.assertFalse(boundary.loader.active)
        self.assertIs(sys.modules["torch"], boundary.loader.loaded["torch"])
        for name in ("admission", "training_launch", "native_execution_authorized"):
            self.assertIs(result[name], False)
        with self.assertRaisesRegex(ValueError, "single-use"):
            self.collect(boundary)

    def test_independent_digest_required(self):
        self.build()
        with self.assertRaisesRegex(ValueError, "hash"):
            handoff.PreIdentityHandoff(self.path, "0" * 64)

    def test_missing_bootstrap_row(self):
        self.payload["bootstrap"].pop()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.build()

    def test_duplicate_bootstrap_row(self):
        self.payload["bootstrap"].append(self.payload["bootstrap"][0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.build()

    def test_bootstrap_hash_drift(self):
        self.payload["bootstrap"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            self.build()

    def test_manifest_changed_before_collect(self):
        boundary = self.build()
        self.path.write_bytes(self.path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "handoff changed"):
            self.collect(boundary)
        self.assertNotIn("torch", sys.modules)

    def test_initial_or_preload_slot_loss_blocks_import(self):
        self.slot.side_effect = [True, False]
        with self.assertRaisesRegex(ValueError, "Held slot"):
            self.collect()
        self.assertNotIn("torch", sys.modules)

    def test_execution_failure_before_import(self):
        self.execution.return_value = False
        with self.assertRaisesRegex(ValueError, "execution verification"):
            self.collect()
        self.assertNotIn("torch", sys.modules)

    def test_slot_loss_after_import_blocks_identity_and_reuse(self):
        boundary = self.build()
        self.slot.side_effect = [True, True, False]
        with self.assertRaisesRegex(ValueError, "Held slot"):
            self.collect(boundary)
        self.assertTrue(boundary.loader.failed)
        self.assertFalse(boundary.loader.active)
        self.assertEqual(self.identity.clock.call_count, 1)
        with self.assertRaisesRegex(ValueError, "single-use"):
            self.collect(boundary)

    def test_slot_loss_after_identity_prevents_success(self):
        self.slot.side_effect = [True, True, True, False]
        with self.assertRaisesRegex(ValueError, "Held slot"):
            self.collect()
        self.assertEqual(self.identity.clock.call_count, 2)

    def test_bootstrap_replacement(self):
        boundary = self.build()
        name = self.payload["bootstrap"][0]["name"]
        sys.modules[name] = ModuleType(name)
        with self.assertRaisesRegex(ValueError, "Bootstrap"):
            self.collect(boundary)

    def test_unlisted_bootstrap_import(self):
        boundary = self.build()
        sys.modules["synthetic_late_bootstrap"] = ModuleType("synthetic_late_bootstrap")
        with self.assertRaisesRegex(ValueError, "Untracked bootstrap"):
            self.collect(boundary)

    def test_deferred_dependency_failure_removes_finder(self):
        self.imports.change("torch", "import synthetic_missing\n")
        boundary = self.build()
        with self.assertRaisesRegex(ImportError, "Undeclared"):
            self.collect(boundary)
        self.assertNotIn(boundary.loader, sys.meta_path)

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        for raw in (b'{"contract":1,"contract":2}', b'{"contract":NaN}'):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                handoff.PreIdentityHandoff(self.path, digest(raw))

    def test_noncanonical_bootstrap_path_and_schema_rejected(self):
        self.payload["bootstrap"][0]["path"] = "relative.py"
        with self.assertRaisesRegex(ValueError, "Canonical"):
            self.build()
        self.payload["extra"] = True
        with self.assertRaisesRegex(ValueError, "schema"):
            self.build()

    def test_wrong_gpu_and_truthy_checks_rejected(self):
        with self.assertRaisesRegex(ValueError, "GPU0/1"):
            self.collect(gpu=7)
        self.slot.return_value = 1
        with self.assertRaisesRegex(ValueError, "Held slot"):
            self.collect()
        self.assertNotIn("torch", sys.modules)


if __name__ == "__main__":
    unittest.main()
