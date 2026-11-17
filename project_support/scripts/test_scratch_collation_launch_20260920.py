"""Synthetic bootstrap handoff tests, not Linux sandbox/native validation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import scratch_collation_launch_20260920 as launch
from test_cpu_diagnostic_bootstrap_20260920 import EXECUTABLE
from test_scratch_cpu_boundary_20260920 import RUN


class CommandTest(unittest.TestCase):
    def command(self, **kw):
        params = dict(executable=EXECUTABLE, bwrap="/usr/bin/bwrap", run=RUN,
                      infrastructure="/inputs/bootstrap", infrastructure_sha256="a"*64,
                      bundle="/inputs/producers", manifest_sha256="b"*64)
        params.update(kw)
        return launch.collation_command(**params)

    def test_preserves_mounts_isolation_and_single_child(self):
        args = self.command()
        base = launch.probe_command(EXECUTABLE, "/usr/bin/bwrap", RUN)
        i = args.index("--")
        self.assertEqual(args[:i+5], base[:i+5])
        self.assertEqual(args[i+5], launch.CHILD)
        self.assertEqual(args[-2:], [RUN + "/output", RUN + "/sentinel"])
        self.assertEqual(args.count("-c"), 1)

    def test_rejects_writable_or_shared_inputs(self):
        for kw in (dict(bundle=RUN), dict(infrastructure=RUN + "/output/source"),
                   dict(bundle="/inputs/bootstrap"), dict(bundle="/"),
                   dict(bundle="/inputs/../source")):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                self.command(**kw)

    def test_rejects_unpinned_manifests(self):
        for key in ("infrastructure_sha256", "manifest_sha256"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.command(**{key: "x"*64})

    def test_exact_bootstrap_inventory(self):
        with self.assertRaises(ValueError):
            launch.bootstrap_manifest({})


class BootstrapTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.infra = self.root / "infrastructure"
        self.bundle = self.root / "bundle"
        self.scratch = self.root / "output"
        for path in (self.infra, self.bundle, self.scratch):
            path.mkdir()
        (self.root / "sentinel").write_bytes(b"read-only-sentinel")
        self.sources = {
            name: (Path(launch.__file__).parent / (name + ".py")).read_bytes()
            for name in launch.INFRASTRUCTURE}

    def child(self, mode="success", isolated=True):
        # The real bootstrap/bridge are used, but replace producer execution and
        # the successful filesystem probe. No native data or model is imported.
        suffix = r'''
def synthetic_probe(scratch, sentinel):
    (scratch / "probe-order").write_text("probe", encoding="ascii")
    return PROBE_RECEIPT
filesystem_probe = synthetic_probe
def synthetic_imports(bundle, digest, required, operation):
    scratch = Path(__file__).parent.parent / "output"
    assert (scratch / "probe-order").read_text() == "probe"
    assert "torch" not in sys.modules
    (scratch / "collated").mkdir()
    (scratch / "collated/collation.json").write_text("{}")
    return dict(callback_collation_completed=True, registry_denominator=31,
                native_execution_verified=False, scientific_validation_complete=False)
checked_imports = synthetic_imports
'''
        if mode == "probe_failure":
            suffix += '\ndef filesystem_probe(*args): raise ValueError("synthetic probe failed")\n'
        if mode == "late_drift":
            suffix += r'''
original = run_same_child
def run_same_child(*args):
    result = original(*args)
    Path(__file__).write_text("changed")
    return result
'''
        self.sources[launch.INFRASTRUCTURE[-1]] += suffix.encode("ascii")
        manifest = launch.bootstrap_manifest(self.sources)
        for name, raw in self.sources.items():
            (self.infra / (name + ".py")).write_bytes(raw)
        raw = json.dumps(manifest).encode("ascii")
        (self.infra / "bootstrap.json").write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        producer = dict(files=[])
        if mode == "overlap":
            producer["files"].append(dict(path=launch.INFRASTRUCTURE[0]+".py", sha256="a"*64))
        producer_raw = json.dumps(producer).encode("ascii")
        (self.bundle / "manifest.json").write_bytes(producer_raw)
        producer_sha = hashlib.sha256(producer_raw).hexdigest()
        if mode == "source_drift":
            (self.infra / (launch.INFRASTRUCTURE[0]+".py")).write_text("raise RuntimeError('executed')")
        if mode == "manifest_drift":
            (self.infra / "bootstrap.json").write_text("{}")
        if mode == "producer_drift":
            (self.bundle / "manifest.json").write_text("{}")
        return subprocess.run(
            [sys.executable, *(["-I"] if isolated else []), "-B", "-c", launch.CHILD,
             str(self.infra), digest, str(self.bundle), producer_sha,
             str(self.scratch), str(self.root / "sentinel")],
            env=dict(os.environ, CUDA_VISIBLE_DEVICES=""),
            capture_output=True, text=True, timeout=30)

    def test_real_bootstrap_bridge_handoff(self):
        result = self.child()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertNotEqual(receipt["pid"], os.getpid())
        self.assertTrue(receipt["same_child_integration_completed"])
        self.assertFalse(receipt["native_execution_verified"])
        self.assertFalse(receipt["admission"])
        self.assertFalse((self.infra / "__pycache__").exists())

    def test_bootstrap_source_drift_prevents_execution(self):
        result = self.child("source_drift")
        self.assertIn("Bootstrap source hash", result.stderr)
        self.assertNotIn("RuntimeError: executed", result.stderr)

    def test_bootstrap_manifest_drift_rejected(self):
        self.assertIn("Bootstrap manifest hash", self.child("manifest_drift").stderr)

    def test_producer_manifest_drift_rejected_before_probe(self):
        self.assertIn("Producer manifest hash", self.child("producer_drift").stderr)
        self.assertFalse((self.scratch / "probe-order").exists())

    def test_overlapping_inventories_rejected_before_import(self):
        self.assertIn("inventories overlap", self.child("overlap").stderr)
        self.assertFalse((self.scratch / "probe-order").exists())

    def test_probe_failure_leaves_no_success(self):
        self.assertIn("synthetic probe failed", self.child("probe_failure").stderr)
        self.assertFalse((self.scratch / "same_child.json").exists())

    def test_late_bootstrap_drift_removes_success_markers(self):
        result = self.child("late_drift")
        self.assertIn("Bootstrap bytes or module identity changed", result.stderr)
        self.assertFalse((self.scratch / "same_child.json").exists())
        self.assertFalse((self.scratch / "collated/collation.json").exists())

    def test_nonisolated_child_rejected(self):
        self.assertIn("Isolated bytecode-disabled", self.child(isolated=False).stderr)

    def test_existing_output_preserved(self):
        output = self.scratch / "collated"
        output.mkdir()
        marker = output / "collation.json"
        marker.write_text("foreign")
        self.assertIn("Fresh bootstrap output", self.child().stderr)
        self.assertEqual(marker.read_text(), "foreign")


if __name__ == "__main__":
    unittest.main()
