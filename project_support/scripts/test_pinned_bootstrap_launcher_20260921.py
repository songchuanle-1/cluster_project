"""Synthetic launcher/bootstrap tests; no Torch, CUDA or native data."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pinned_bootstrap_launcher_20260921 as launcher


DRIVER = r'''
import time

def run(boundary, context):
    if context.get("mode") == "timeout":
        time.sleep(60)
    if context.get("mode") == "overflow":
        print("x" * context["size"])
    return {
        "boundary_type": type(boundary).__name__,
        "boundary_contract": getattr(boundary, "CONTRACT", None),
        "handoff_sha256": boundary.sha256,
        "dependency_modules": sorted(boundary.loader.modules),
        "driver_value": context["value"],
        "admission": False,
        "native_execution_authorized": False,
    }
'''


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scripts = Path(__file__).resolve().parent
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        self.output = self.root / "output"
        self.output.mkdir()
        self.modules = [
            "capture_support_20260916",
            "frozen_capture_contract_20260916",
            "paired_capture_evaluation_20260916",
            "pinned_diagnostic_imports_20260920",
            "preidentity_handoff_20260921",
            "saved_physical_location_20260920",
            "saved_replay_migration_20260920",
            "synthetic_launcher_driver_20260921",
        ]
        sources = {
            name + ".py": self.scripts / (name + ".py")
            for name in self.modules
            if name != "synthetic_launcher_driver_20260921"
        }
        driver_path = self.root / "synthetic_launcher_driver_20260921.py"
        driver_path.write_text(DRIVER, encoding="ascii")
        sources[driver_path.name] = driver_path
        torch = self.root / "torch"
        torch.mkdir()
        torch_init = torch / "__init__.py"
        torch_init.write_text("VERSION='synthetic'\n", encoding="ascii")
        bootstrap = [dict(
            name=name, path=str(self.bundle / (name + ".py")),
            sha256=self.sha((self.scripts / (name + ".py")).read_bytes()))
            for name in self.modules
            if name != "synthetic_launcher_driver_20260921"]
        bootstrap.append(dict(
            name="__main__",
            path=str(self.bundle / launcher.LAUNCHER_NAME),
            sha256=launcher.LAUNCHER_SHA256))
        handoff = dict(
            contract="preidentity-handoff-v1",
            dependencies=[dict(
                name="torch", path=str(torch_init),
                sha256=self.sha(torch_init.read_bytes()), is_package=True)],
            bootstrap=bootstrap)
        self.handoff = self.root / "handoff.json"
        self.handoff.write_text(
            json.dumps(handoff, sort_keys=True, separators=(",", ":")),
            encoding="ascii")
        sources["handoff.json"] = self.handoff
        self.bundle_sha = launcher.produce_launcher_bundle(
            self.bundle, sources, self.modules)
        # Copying replaced the handoff, so refresh its path and source hashes.
        self.handoff = self.bundle / "handoff.json"
        self.handoff_sha = self.sha(self.handoff.read_bytes())
        self.context = self.root / "context.json"
        self.write_context(dict(value=7))
        self.executable = Path(sys.executable).resolve()
        self.executable_sha = self.sha(self.executable.read_bytes())
        self.validator = Mock(return_value=None)

    @staticmethod
    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    def write_context(self, payload):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
        self.context.write_bytes(raw)
        self.context_sha = self.sha(raw)

    def call(self, **changes):
        values = dict(
            executable=self.executable,
            executable_sha256=self.executable_sha,
            bundle=self.bundle,
            manifest_sha256=self.bundle_sha,
            handoff_path=self.handoff,
            handoff_sha256=self.handoff_sha,
            driver_module="synthetic_launcher_driver_20260921",
            driver_entry="run",
            context_path=self.context,
            context_sha256=self.context_sha,
            output=self.output,
            validate_execution=self.validator,
            timeout=20,
            max_output_bytes=1024 * 1024)
        values.update(changes)
        return launcher.launch_pinned_handoff(**values)

    def test_real_isolated_child_publishes_verified_result(self):
        result = self.call()
        self.assertEqual(result["contract"], launcher.CONTRACT)
        self.assertEqual(result["driver_result"]["boundary_type"], "PreIdentityHandoff")
        self.assertEqual(result["driver_result"]["handoff_sha256"], self.handoff_sha)
        self.assertEqual(result["driver_result"]["dependency_modules"], ["torch"])
        self.assertEqual(result["driver_result"]["driver_value"], 7)
        self.validator.assert_called_once()
        self.assertEqual(self.validator.call_args.args[0]["output"], str(self.output))

    def test_missing_validator_blocks_before_child(self):
        self.output.rmdir()
        with self.assertRaisesRegex(ValueError, "validator required"):
            self.call(validate_execution=None)

    def test_validator_true_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "pass flag"):
            self.call(validate_execution=Mock(return_value=True))

    def test_launcher_source_pin_is_required(self):
        with self.assertRaisesRegex(ValueError, "Launcher source"):
            self.call(expected_launcher_sha256="0" * 64)
        self.validator.assert_not_called()

    def test_source_bundle_drift_blocks_before_child(self):
        (self.bundle / "saved_replay_migration_20260920.py").write_bytes(b"drift")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            self.call()
        self.validator.assert_not_called()

    def test_handoff_and_context_pins_are_checked(self):
        with self.assertRaisesRegex(ValueError, "hash differs"):
            self.call(handoff_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "hash differs"):
            self.call(context_sha256="0" * 64)
        self.validator.assert_not_called()

    def test_driver_inventory_and_entry_are_exact(self):
        with self.assertRaisesRegex(ValueError, "driver"):
            self.call(driver_module="absent_driver")
        with self.assertRaisesRegex(ValueError, "driver"):
            self.call(driver_entry="not-callable")
        self.validator.assert_not_called()

    def test_existing_result_is_not_overwritten(self):
        (self.output / "result.json").write_text("{}", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "Fresh result"):
            self.call()
        self.validator.assert_not_called()

    def test_timeout_is_bounded(self):
        self.write_context(dict(value=7, mode="timeout"))
        with self.assertRaisesRegex(TimeoutError, "exceeded timeout"):
            self.call(timeout=0.2)

    def test_output_budget_is_bounded(self):
        self.write_context(dict(value=7, mode="overflow", size=100000))
        with self.assertRaisesRegex(ValueError, "output budget"):
            self.call(max_output_bytes=256)

    def test_positive_claims_are_rejected(self):
        completed = SimpleNamespace(
            returncode=0, stderr="",
            stdout=self.sha(b'{"contract":"x"}') + "\n")
        (self.output / "result.json").write_text(
            '{"contract":"x"}', encoding="ascii")
        with self.assertRaisesRegex(ValueError, "cannot claim"):
            launcher._reject_positive_claims({"admission": True})

    def test_manifest_rejects_duplicate_and_noncanonical_names(self):
        for name in ("../x.py", "nested/x.py", "x.json"):
            with self.subTest(name=name):
                source = self.root / "source"
                source.write_bytes(b"x")
                with self.assertRaises(ValueError):
                    launcher.build_launcher_manifest(
                        {name: source}, ["synthetic_module"])

    def test_manifest_requires_unique_exact_modules(self):
        source = self.root / "synthetic_module.py"
        source.write_bytes(b"x=1\n")
        with self.assertRaises(ValueError):
            launcher.build_launcher_manifest({source.name: source}, [])
        with self.assertRaises(ValueError):
            launcher.build_launcher_manifest(
                {source.name: source}, ["synthetic_module", "synthetic_module"])
        with self.assertRaises(ValueError):
            launcher.build_launcher_manifest({source.name: source}, ["absent"])


if __name__ == "__main__":
    unittest.main()
