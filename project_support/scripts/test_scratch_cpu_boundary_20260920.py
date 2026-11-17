"""Static and mocked tests only; Windows tests do not verify Linux mounts."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import scratch_cpu_boundary_20260920 as boundary
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE, observation


RUN = boundary.SCRATCH_ROOT + "/cpu-probe-fixture"


class CommandTest(unittest.TestCase):
    def command(self, **kw):
        return boundary.probe_command(
            kw.get("executable", EXECUTABLE), kw.get("bwrap", "/usr/bin/bwrap"),
            kw.get("run", RUN))

    def test_only_scratch_host_mounts_are_writable(self):
        args = self.command()
        mounts = [args[i+1:i+3] for i, arg in enumerate(args) if arg == "--bind"]
        self.assertEqual(mounts, [[RUN + "/output", RUN + "/output"],
                                 [RUN + "/output/tmp", "/tmp"]])
        index = args.index("--ro-bind")
        self.assertEqual(args[index+1:index+3], ["/", "/"])
        self.assertLess(index, args.index("--bind"))

    def test_namespace_failure_is_not_optional(self):
        args = self.command()
        for flag in ("--unshare-user", "--disable-userns", "--unshare-all",
                     "--new-session", "--die-with-parent"):
            self.assertIn(flag, args)
        self.assertNotIn("--unshare-user-try", args)
        self.assertNotIn("--share-net", args)
        self.assertEqual(args[args.index("--cap-drop")+1], "ALL")

    def test_no_host_devices_or_daemon_sockets_mounted(self):
        args = self.command()
        self.assertNotIn("--dev-bind", args)
        targets = [args[i+1] for i, a in enumerate(args) if a == "--remount-ro"]
        self.assertEqual(targets, ["/proc", "/dev/pts", "/dev", "/run"])

    def test_child_is_isolated_cpu_and_bytecode_disabled(self):
        args = self.command()
        i = args.index("--")
        self.assertEqual(args[i+1:i+5], [EXECUTABLE, "-I", "-B", "-c"])
        self.assertEqual(args[i+5], boundary.PROBE)
        env = {args[i+1]: args[i+2] for i, a in enumerate(args) if a == "--setenv"}
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(env["HOME"], RUN + "/output/home")
        self.assertIn("--clearenv", args)

    def test_canonical_paths(self):
        for value in ("relative", "//tmp/a", "/tmp/../a", "/tmp/./a",
                      "/tmp//a", "/tmp/a/", "/tmp\\a", "/tmp/\x00a", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                boundary.canonical(value)

    def test_unapproved_scratch_rejected(self):
        for run in ("/tmp/cpu-probe-x", boundary.SCRATCH_ROOT,
                    RUN + "/nested", boundary.SCRATCH_ROOT + "/other"):
            with self.subTest(run=run), self.assertRaises(ValueError):
                self.command(run=run)

    def test_executable_in_scratch_rejected(self):
        for key in ("bwrap", "executable"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.command(**{key: RUN + "/bin/python"})

    def test_probe_program_compiles_without_execution(self):
        compile(boundary.PROBE, "<probe>", "exec")


class ExecutionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.binary = self.root / "bwrap"
        self.binary.write_bytes(b"synthetic-binary")
        self.digest = hashlib.sha256(self.binary.read_bytes()).hexdigest()

    def test_windows_refuses_before_host_probe_or_writes(self):
        with patch.object(boundary.platform, "system", return_value="Windows"), \
                patch.object(boundary, "observe_runtime") as observe:
            with self.assertRaisesRegex(ValueError, "Linux"):
                boundary.run_probe(EXECUTABLE, "/usr/bin/bwrap", self.digest)
            observe.assert_not_called()

    def launch(self, run, digest=None):
        def checked(value, directory=False):
            return self.root if directory else self.binary

        with patch.object(boundary.platform, "system", return_value="Linux"), \
                patch.object(boundary, "observe_runtime", return_value=observation()), \
                patch.object(boundary, "checked_path", side_effect=checked), \
                patch.object(boundary, "probe_command", return_value=["synthetic-bwrap"]), \
                patch.object(boundary.subprocess, "run", side_effect=run):
            return boundary.run_probe(EXECUTABLE, "/usr/bin/bwrap", digest or self.digest)

    @staticmethod
    def success(args, **kwargs):
        root = Path(kwargs["cwd"])
        (root / "output/probe-output").write_bytes(b"scratch-write-ok")
        return subprocess.CompletedProcess(args, 0, json.dumps(dict(
            contract="scratch-probe-v1", denied_opens=3, denied_mkdir=True,
            scratch_write=True, native_imports=False)), "")

    def test_mocked_success_is_not_native_authorization(self):
        calls = []

        def run(args, **kwargs):
            calls.append(kwargs)
            return self.success(args, **kwargs)

        result = self.launch(run)
        self.assertTrue(result["boundary_probe_passed"])
        self.assertFalse(result["native_execution_authorized"])
        self.assertFalse(result["native_execution"])
        self.assertEqual(calls[0]["env"], {"PATH": "/usr/bin:/bin"})
        self.assertTrue(calls[0]["close_fds"])
        self.assertTrue(calls[0]["check"])
        self.assertNotIn("shell", calls[0])
        self.assertEqual(calls[0]["stdin"], subprocess.DEVNULL)

    def test_changed_binary_rejected_before_process_or_scratch(self):
        with self.assertRaisesRegex(ValueError, "digest"):
            self.launch(lambda *a, **k: self.fail("must not launch"), "0" * 64)
        self.assertEqual(list(self.root.iterdir()), [self.binary])

    def test_missing_bwrap_has_no_unsandboxed_retry(self):
        calls = []

        def run(*args, **kwargs):
            calls.append(args)
            raise FileNotFoundError("bwrap")

        with self.assertRaises(FileNotFoundError):
            self.launch(run)
        self.assertEqual(len(calls), 1)

    def test_kernel_failure_propagates(self):
        def run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0], stderr="namespace denied")
        with self.assertRaises(subprocess.CalledProcessError):
            self.launch(run)

    def test_timeout_propagates(self):
        def run(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], 30)
        with self.assertRaises(subprocess.TimeoutExpired):
            self.launch(run)

    def test_incomplete_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, "receipt"):
            self.launch(lambda *a, **k: subprocess.CompletedProcess([], 0, "{}", ""))

    def test_sentinel_mutation_rejected(self):
        def run(args, **kwargs):
            result = self.success(args, **kwargs)
            (Path(kwargs["cwd"]) / "sentinel").write_bytes(b"changed")
            return result
        with self.assertRaisesRegex(ValueError, "bytes"):
            self.launch(run)

    def test_missing_output_rejected(self):
        def run(args, **kwargs):
            result = self.success(args, **kwargs)
            (Path(kwargs["cwd"]) / "output/probe-output").unlink()
            return result
        with self.assertRaises(FileNotFoundError):
            self.launch(run)

    def test_checked_path_missing_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing"):
            boundary.checked_path(self.root / "absent")

    def test_checked_regular_file_and_directory(self):
        self.assertEqual(boundary.checked_path(self.binary), self.binary)
        self.assertEqual(boundary.checked_path(self.root, directory=True), self.root)


if __name__ == "__main__":
    unittest.main()
