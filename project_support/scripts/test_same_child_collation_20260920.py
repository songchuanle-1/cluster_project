"""Actual isolated child + real bridge/callback/validator, synthetic inputs only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import same_child_collation_20260920 as bridge


FACTORY = '''
import copy, json, os, pickle
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from test_relocated_saved_collation_20260920 import CollationTest
from test_native_saved_batch_validation_20260920 import fixture
from frozen_capture_contract_20260916 import fingerprint

EVENTS = Path(__file__).parent / "events.jsonl"
def event(name):
    with EVENTS.open("a") as stream:
        stream.write(json.dumps(dict(name=name, pid=os.getpid())) + "\\n")
event("factory_import")

def build_inputs():
    event("build")
    f = CollationTest()
    f.setUp()
    # Hold the temporary fixture until the entire child exits.
    global keepalive
    keepalive = f
    location_fixture = f.fixture
    item, batch, axes, torch = fixture()
    for index in (3040, 3893):
        payload = location_fixture.payloads["item_%d.pth" % index]
        payload["item"] = copy.deepcopy(item)
        payload["axes"] = [
            dict(axis, dataset_index=index,
                 native_input_sha256=fingerprint(item),
                 original_superpoint_ids=[0, 1, 1], sample_inverse=[0, 1, 1],
                 physical_instance_labels=[1, 2])
            for axis in axes]
    for row in location_fixture.physical["items"]:
        row["native_input_sha256"] = fingerprint(item)
        row["expressions"] = 2
    def collate(items):
        event("collate")
        return copy.deepcopy(batch)
    native = SimpleNamespace(use_xyz=True, collate_fn=collate)
    torch.save.side_effect = lambda value, stream: pickle.dump(value, stream)
    torch.load.side_effect = lambda path, **kw: pickle.loads(Path(path).read_bytes())
    return dict(location=location_fixture.adapter(),
                exporter=location_fixture.exporter, registry_ids=location_fixture.ids,
                read_json=location_fixture.read_json, load_item=location_fixture.load,
                native=native, torch=torch, capture_id="synthetic",
                producer_sha256="a" * 64)
'''


class SameChildTest(unittest.TestCase):
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

    def child(self, factory=FACTORY, setup="", probe="return bridge.PROBE_RECEIPT",
              isolated=True, bytecode=True, cuda="", tamper=False, real_probe=False):
        files = []
        for name in bridge.REQUIRED:
            source = self.scripts / (name + ".py")
            target = self.bundle / source.name
            target.write_bytes(source.read_bytes())
            files.append(dict(path=target.name,
                              sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        target = self.bundle / "_same_child_factory.py"
        target.write_text(factory, encoding="ascii")
        files.append(dict(path=target.name, sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        manifest = self.bundle / "manifest.json"
        manifest.write_text(json.dumps(dict(files=files)), encoding="ascii")
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        if tamper:
            target.write_text("raise RuntimeError('unverified executed')", encoding="ascii")
        code = (
            "import sys, os, json\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, " + repr(str(self.scripts)) + ")\n"
            "import same_child_collation_20260920 as bridge\n"
            "events = Path(" + repr(str(self.bundle / "events.jsonl")) + ")\n"
            "def probe(scratch, sentinel):\n"
            "    assert 'native_frozen_capture_20260916' not in sys.modules\n"
            "    with events.open('a') as stream:\n"
            "        stream.write(json.dumps(dict(name='probe', pid=os.getpid()))+'\\n')\n"
            "    " + probe + "\n"
            + ("" if real_probe else "bridge.filesystem_probe = probe\n")
            + setup + "\n"
            "result = bridge.run_same_child(" + repr(str(self.bundle)) + ", "
            + repr(digest) + ", '_same_child_factory', "
            + repr(str(self.scratch)) + ", " + repr(str(self.root / "sentinel")) + ")\n"
            "assert not any(n in sys.modules for n in bridge.REQUIRED)\n"
            "assert '_same_child_factory' not in sys.modules\n"
            "print(json.dumps(result))\n")
        command = [sys.executable]
        if isolated:
            command.append("-I")
        if bytecode:
            command.append("-B")
        command += ["-c", code]
        return subprocess.run(
            command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=cuda),
            capture_output=True, text=True, timeout=30)

    def events(self):
        path = self.bundle / "events.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def no_success(self):
        self.assertFalse((self.scratch / "same_child.json").exists())
        self.assertFalse((self.scratch / "collated/collation.json").exists())

    def test_probe_import_validator_collation_in_one_actual_child(self):
        result = self.child()
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        events = self.events()
        self.assertEqual([e["name"] for e in events],
                         ["probe", "factory_import", "build"] + ["collate"] * 4)
        self.assertEqual({e["pid"] for e in events}, {receipt["pid"]})
        self.assertNotEqual(receipt["pid"], os.getpid())
        self.assertEqual(receipt["collation"]["original_dataset_indices"], [3040, 3893])
        self.assertEqual(receipt["collation"]["registry_denominator"], 31)
        self.assertFalse(receipt["native_execution_verified"])
        self.assertFalse(receipt["scientific_validation_complete"])
        self.assertFalse(receipt["admission"])
        self.assertEqual(receipt, json.loads((self.scratch / "same_child.json").read_text()))
        self.assertFalse((self.bundle / "__pycache__").exists())

    def test_probe_failure_prevents_all_producer_imports(self):
        result = self.child(probe="raise OSError('probe denied')")
        self.assertIn("probe denied", result.stderr)
        self.assertEqual([e["name"] for e in self.events()], ["probe"])
        self.no_success()

    def test_incomplete_probe_prevents_imports(self):
        result = self.child(probe="return {}")
        self.assertIn("Incomplete same-child", result.stderr)
        self.assertEqual(len(self.events()), 1)
        self.no_success()

    def test_real_probe_fails_on_writable_local_sentinel(self):
        result = self.child(real_probe=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("accepted write access", result.stderr)
        self.assertEqual(self.events(), [])
        self.no_success()

    def test_bad_source_prevents_factory_execution(self):
        result = self.child(tamper=True)
        self.assertIn("source hash", result.stderr)
        self.assertNotIn("unverified executed", result.stderr)
        self.assertEqual(len(self.events()), 1)
        self.no_success()

    def test_preloaded_producer_rejected(self):
        result = self.child(setup="import native_frozen_capture_20260916")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.events(), [])
        self.no_success()

    def test_preloaded_native_dependency_rejected(self):
        result = self.child(setup="import types\nsys.modules['torch'] = types.ModuleType('torch')")
        self.assertIn("before producer verification", result.stderr)
        self.no_success()

    def test_missing_isolation_rejected(self):
        result = self.child(isolated=False)
        self.assertIn("isolated CPU child", result.stderr)
        self.assertEqual(self.events(), [])

    def test_bytecode_enabled_rejected(self):
        result = self.child(bytecode=False)
        self.assertIn("isolated CPU child", result.stderr)
        self.assertEqual(self.events(), [])

    def test_visible_cuda_rejected(self):
        result = self.child(cuda="0")
        self.assertIn("isolated CPU child", result.stderr)
        self.assertEqual(self.events(), [])

    def test_factory_exception_preserves_no_success(self):
        result = self.child(factory=FACTORY.replace('event("build")', 'raise ValueError("factory failed")'))
        self.assertIn("factory failed", result.stderr)
        self.no_success()

    def test_factory_contract_rejected(self):
        result = self.child(factory=FACTORY + "\ndef build_inputs(): return {}\n")
        self.assertIn("input contract differs", result.stderr)
        self.no_success()

    def test_real_validator_failure_prevents_completion(self):
        result = self.child(factory=FACTORY.replace(
            'event("collate")', 'event("collate")\n        batch["feats"] = batch["feats"].astype("float64")'))
        self.assertIn("feature concatenation/dtype differs", result.stderr)
        self.no_success()
        self.assertTrue((self.scratch / "collated/failure.json").exists())

    def test_late_pinned_source_drift_removes_collation_marker(self):
        result = self.child(factory=FACTORY.replace(
            'event("collate")',
            'event("collate")\n        Path(__file__).write_text("changed", encoding="ascii")'))
        self.assertIn("source hash", result.stderr)
        self.no_success()

    def test_existing_output_not_overwritten(self):
        (self.scratch / "collated").mkdir()
        foreign = self.scratch / "collated/keep"
        foreign.write_text("keep")
        result = self.child()
        self.assertIn("Fresh same-child", result.stderr)
        self.assertEqual(foreign.read_text(), "keep")
        self.assertEqual(self.events(), [])


if __name__ == "__main__":
    unittest.main()
