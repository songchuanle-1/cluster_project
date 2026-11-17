"""Synthetic runtime and actual fresh-child import tests; no native data."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cpu_diagnostic_bootstrap_20260920 as bootstrap


PREFIX = "/home/dl04/anaconda3/envs/project_cluster"
EXECUTABLE = PREFIX + "/bin/python"


def observation():
    paths = {
        p: dict(path=p, resolved=p, directory=p != EXECUTABLE,
                regular_file=p == EXECUTABLE, symlink=False)
        for p in (bootstrap.CODE_ROOT, bootstrap.DATA_ROOT, bootstrap.WORK_ROOT,
                  bootstrap.SCRATCH_ROOT, PREFIX, EXECUTABLE)}
    return dict(
        platform="Linux", addresses=["127.0.0.1", bootstrap.SERVER_ADDRESS],
        user="songcl", conda_env="project_cluster", conda_prefix=PREFIX,
        sys_prefix=PREFIX, executable=EXECUTABLE, cuda_visible_devices="",
        isolated=True, dont_write_bytecode=True, paths=paths)


class RuntimeTest(unittest.TestCase):
    def test_verified_observation_is_not_launch_authorization(self):
        result = bootstrap.validate_runtime(observation(), EXECUTABLE)
        self.assertTrue(result["runtime_preflight_passed"])
        for field in ("native_execution_authorized", "data_bytes_verified",
                      "gpu_occupancy_verified", "scratch_write_enforcement_verified"):
            self.assertIs(result[field], False)

    def test_wrong_host_platform_or_user_rejected(self):
        for key, value in (("platform", "Windows"), ("addresses", ["100.64.3.28"]),
                           ("user", "root"), ("addresses", [])):
            with self.subTest(key=key, value=value):
                data = observation()
                data[key] = value
                with self.assertRaisesRegex(ValueError, "server-4"):
                    bootstrap.validate_runtime(data, EXECUTABLE)

    def test_environment_name_alone_insufficient(self):
        for key, value in (("conda_prefix", "/wrong"), ("sys_prefix", "/wrong"),
                           ("executable", "/usr/bin/python"),
                           ("conda_env", "base")):
            with self.subTest(key=key):
                data = observation()
                data[key] = value
                with self.assertRaisesRegex(ValueError, "executable"):
                    bootstrap.validate_runtime(data, EXECUTABLE)

    def test_expected_executable_must_be_independently_matched(self):
        with self.assertRaises(ValueError):
            bootstrap.validate_runtime(observation(), PREFIX + "/bin/python3")

    def test_traversal_executable_rejected(self):
        data = observation()
        data["executable"] = PREFIX + "/../other/bin/python"
        with self.assertRaisesRegex(ValueError, "Noncanonical"):
            bootstrap.validate_runtime(data, data["executable"])

    def test_cpu_freshness_required(self):
        for key, value in (("cuda_visible_devices", "0"), ("cuda_visible_devices", None),
                           ("isolated", False), ("dont_write_bytecode", False)):
            with self.subTest(key=key):
                data = observation()
                data[key] = value
                with self.assertRaisesRegex(ValueError, "CPU process"):
                    bootstrap.validate_runtime(data, EXECUTABLE)

    def test_each_path_must_exist_and_not_redirect(self):
        for path in observation()["paths"]:
            for field, value in (("resolved", "/elsewhere"), ("symlink", True),
                                 ("regular_file" if path == EXECUTABLE else "directory", False)):
                with self.subTest(path=path, field=field):
                    data = observation()
                    data["paths"][path][field] = value
                    with self.assertRaisesRegex(ValueError, "unverified"):
                        bootstrap.validate_runtime(data, EXECUTABLE)

    def test_missing_path_inventory_rejected(self):
        data = observation()
        del data["paths"][bootstrap.DATA_ROOT]
        with self.assertRaisesRegex(ValueError, "inventory"):
            bootstrap.validate_runtime(data, EXECUTABLE)

    def test_non_linux_probe_does_not_inspect_native_paths(self):
        with patch.object(bootstrap.platform, "system", return_value="Windows"), \
                patch.object(bootstrap, "local_addresses") as probe:
            with self.assertRaisesRegex(ValueError, "Linux"):
                bootstrap.observe_runtime()
            probe.assert_not_called()

    def test_interface_json_parsing_ignores_ipv6(self):
        completed = subprocess.CompletedProcess([], 0, json.dumps([
            {"addr_info": [{"family": "inet", "local": bootstrap.SERVER_ADDRESS},
                           {"family": "inet6", "local": "::1"}]}]), "")
        with patch.object(bootstrap.subprocess, "run", return_value=completed) as run:
            self.assertEqual(bootstrap.local_addresses(), [bootstrap.SERVER_ADDRESS])
            self.assertEqual(run.call_args.args[0], ["ip", "-j", "address", "show"])
            self.assertTrue(run.call_args.kwargs["check"])

    def test_probe_failure_propagates(self):
        with patch.object(bootstrap.subprocess, "run", side_effect=FileNotFoundError("ip")):
            with self.assertRaises(FileNotFoundError):
                bootstrap.local_addresses()

    def test_cli_preflight_does_not_import_producers(self):
        before = set(sys.modules)
        with patch.object(bootstrap, "observe_runtime", return_value=observation()), \
                patch("builtins.print") as output:
            result = bootstrap.main(["--expected-executable", EXECUTABLE])
        self.assertFalse(result["native_execution_authorized"])
        self.assertEqual(set(sys.modules), before)
        output.assert_called_once()


class ChildImportsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "_bootstrap_fixture.py"
        self.source.write_text("VALUE = 31\n", encoding="ascii")
        manifest = {"files": [{
            "path": self.source.name,
            "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest()}]}
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps(manifest), encoding="ascii")
        self.digest = hashlib.sha256(self.manifest.read_bytes()).hexdigest()
        self.scripts = str(Path(bootstrap.__file__).parent)

    def child(self, setup="", operation="lambda m: m['_bootstrap_fixture'].VALUE",
              isolated=True, bytecode=True, cuda="", expected=None):
        code = (
            "import sys, json\n"
            "sys.path.insert(0, " + repr(self.scripts) + ")\n"
            "from cpu_diagnostic_bootstrap_20260920 import checked_imports\n"
            + setup + "\n"
            "result = checked_imports(" + repr(str(self.root)) + ", "
            + repr(expected or self.digest) + ", ['_bootstrap_fixture'], "
            + operation + ")\n"
            "assert '_bootstrap_fixture' not in sys.modules\n"
            "print(json.dumps(result))\n")
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=cuda)
        command = [sys.executable]
        if isolated:
            command.append("-I")
        if bytecode:
            command.append("-B")
        command += ["-c", code]
        return subprocess.run(command, env=env, capture_output=True, text=True, timeout=20)

    def test_actual_isolated_child_import_and_cleanup(self):
        result = self.child()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), 31)
        self.assertFalse((self.root / "__pycache__").exists())

    def test_wrong_manifest_fails_before_source_execution(self):
        result = self.child(expected="0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest hash", result.stderr)

    def test_changed_source_fails(self):
        self.source.write_text("raise RuntimeError('must not execute')", encoding="ascii")
        result = self.child()
        self.assertIn("source hash", result.stderr)
        self.assertNotIn("RuntimeError: must not execute", result.stderr)

    def test_preloaded_producer_rejected(self):
        result = self.child(
            "import types\nsys.modules['_bootstrap_fixture'] = types.ModuleType('_bootstrap_fixture')")
        self.assertIn("already imported", result.stderr)

    def test_preloaded_native_dependency_rejected(self):
        result = self.child("import types\nsys.modules['torch'] = types.ModuleType('torch')")
        self.assertIn("before producer verification", result.stderr)

    def test_missing_isolation_rejected(self):
        result = self.child(isolated=False)
        self.assertIn("Fresh isolated", result.stderr)

    def test_bytecode_enabled_rejected(self):
        result = self.child(bytecode=False)
        # Ignore inherited PYTHONDONTWRITEBYTECODE via -I.
        self.assertIn("Fresh isolated", result.stderr)

    def test_visible_cuda_rejected(self):
        result = self.child(cuda="0")
        self.assertIn("hide CUDA", result.stderr)

    def test_operation_exception_cleans_owned_imports(self):
        setup = (
            "def fail(modules):\n"
            "    raise RuntimeError('operation failed')\n"
            "import atexit\n"
            "def check_cleanup():\n"
            "    assert '_bootstrap_fixture' not in sys.modules\n"
            "atexit.register(check_cleanup)\n")
        result = self.child(setup, "fail")
        self.assertIn("RuntimeError: operation failed", result.stderr)
        self.assertNotIn("AssertionError", result.stderr)


if __name__ == "__main__":
    unittest.main()
