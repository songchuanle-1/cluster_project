"""Synthetic host observations and scratch files only; no native execution."""
from contextlib import ExitStack
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import prepare_collation_handoff_20260921 as handoff
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE, observation


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scratch = self.root / "scratch"
        self.scratch.mkdir()
        self.infra = self.root / "infra"
        self.bundle = self.root / "bundle"
        self.infra.mkdir()
        self.bundle.mkdir()
        self.python = self.root / "python"
        self.bwrap = self.root / "bwrap"
        self.files = [self.python, self.bwrap, self.infra / "bootstrap.json",
                      self.bundle / "manifest.json"]
        for index, path in enumerate(self.files):
            path.write_bytes(("synthetic-input-%d" % index).encode("ascii"))
        self.digests = [hashlib.sha256(path.read_bytes()).hexdigest() for path in self.files]
        self.bwrap_name = "/usr/bin/bwrap"
        self.infra_name = "/synthetic/infra"
        self.bundle_name = "/synthetic/bundle"

    def prepare(self, observation_override=None, after_provision=None, command_error=None):
        original = handoff.checked_path
        mapping = {handoff.SCRATCH_ROOT: self.scratch, EXECUTABLE: self.python,
                   self.bwrap_name: self.bwrap, self.infra_name: self.infra,
                   self.bundle_name: self.bundle}

        def check(value, directory=False):
            return original(mapping.get(str(value), value), directory)

        real_private = handoff.private_directory

        def provision(path):
            real_private(path)
            if after_provision:
                after_provision(path)

        with ExitStack() as stack:
            stack.enter_context(patch.object(handoff.platform, "system", return_value="Linux"))
            stack.enter_context(patch.object(handoff, "observe_runtime",
                                            return_value=observation_override or observation()))
            stack.enter_context(patch.object(handoff, "checked_path", side_effect=check))
            stack.enter_context(patch.object(handoff, "private_directory", side_effect=provision))
            # POSIX argv has separate static coverage. No Windows path is sent to Linux.
            command = stack.enter_context(patch.object(
                handoff, "collation_command", side_effect=command_error,
                return_value=["/synthetic/bwrap", "--", EXECUTABLE, "-I", "-B"]))
            result = handoff.prepare_handoff(
                EXECUTABLE, self.digests[0], self.bwrap_name, self.digests[1],
                self.infra_name, self.digests[2], self.bundle_name, self.digests[3])
            return result, command.call_args.args

    def test_real_private_scratch_and_exact_handoff_arguments(self):
        result, args = self.prepare()
        run = Path(result["run"])
        self.assertEqual(run.parent, self.scratch)
        self.assertTrue(run.name.startswith("cpu-probe-"))
        self.assertEqual((run / "sentinel").read_bytes(), b"read-only-sentinel")
        self.assertEqual(sorted(p.name for p in (run / "output").iterdir()),
                         ["cache", "home", "tmp"])
        self.assertEqual(args, (
            EXECUTABLE, self.bwrap_name, str(run), self.infra_name,
            self.digests[2], self.bundle_name, self.digests[3]))
        self.assertTrue(result["host_preparation_completed"])
        for key in ("external_dependency_attestation", "scratch_write_enforcement_verified",
                    "native_execution_verified", "scientific_validation_complete",
                    "execution_authorized", "admission"):
            self.assertIs(result[key], False)

    def test_each_run_is_fresh(self):
        first, _ = self.prepare()
        second, _ = self.prepare()
        self.assertNotEqual(first["run"], second["run"])
        self.assertEqual(len(list(self.scratch.iterdir())), 2)

    def test_non_linux_rejected_before_observation(self):
        with patch.object(handoff.platform, "system", return_value="Windows"), \
                patch.object(handoff, "observe_runtime") as observe:
            with self.assertRaisesRegex(ValueError, "Linux"):
                handoff.prepare_handoff(*([None] * 8))
            observe.assert_not_called()

    def test_unauthorized_host_before_writes(self):
        data = observation()
        data["addresses"] = ["100.64.3.28"]
        with self.assertRaisesRegex(ValueError, "server-4"):
            self.prepare(data)
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_each_digest_checked_before_provision(self):
        for index in range(4):
            old = self.digests[index]
            self.digests[index] = "0" * 64
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "digest"):
                self.prepare()
            self.digests[index] = old
            self.assertEqual(list(self.scratch.iterdir()), [])

    def test_missing_manifest_before_provision(self):
        self.files[-1].unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            self.prepare()
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_invalid_command_before_provision(self):
        with self.assertRaisesRegex(ValueError, "invalid argv"):
            self.prepare(command_error=ValueError("invalid argv"))
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_late_input_drift_never_returns_prepared_receipt(self):
        def drift(path):
            if path.name == "cache":
                self.python.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "digest"):
            self.prepare(after_provision=drift)
        runs = list(self.scratch.iterdir())
        self.assertEqual(len(runs), 1)
        self.assertFalse((runs[0] / "output/same_child.json").exists())

    def test_collision_preserves_existing_run(self):
        with patch.object(handoff.uuid, "uuid4") as identifier:
            identifier.return_value.hex = "fixed"
            first, _ = self.prepare()
            marker = Path(first["run"]) / "foreign"
            marker.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                self.prepare()
            self.assertEqual(marker.read_bytes(), b"preserve")

    def test_partial_provision_failure_does_not_launch(self):
        def fail(path):
            if path.name == "home":
                raise OSError("synthetic provisioning failure")
        with patch("subprocess.Popen") as launch:
            with self.assertRaisesRegex(OSError, "provisioning"):
                self.prepare(after_provision=fail)
            launch.assert_not_called()
        self.assertEqual(len(list(self.scratch.iterdir())), 1)

    def test_success_does_not_launch_or_load_native_dependencies(self):
        with patch("subprocess.Popen") as launch:
            self.prepare()
            launch.assert_not_called()

    def test_hardlinked_pinned_input_rejected(self):
        import os
        alias = self.root / "alias"
        os.link(self.python, alias)
        with self.assertRaisesRegex(ValueError, "Hardlinked"):
            self.prepare()
        self.assertEqual(list(self.scratch.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
