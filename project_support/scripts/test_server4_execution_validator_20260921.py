"""Synthetic tests for the production execution guard and child driver."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import production_saved_collation_driver_20260921 as production_driver
import server4_execution_validator_20260921 as validator
from test_cpu_diagnostic_bootstrap_20260920 import observation
from test_gpu_runtime_validation_20260921 import UUID


class Clock:
    def __init__(self, now=1000):
        self.now = now

    def __call__(self):
        return self.now


class Lease:
    def __init__(self, gpu=0):
        self.proof = dict(
            owner_pid=os.getpid(), token="a" * 64,
            server="server-4", gpu=gpu)
        self.held = True
        self.released = False

    def assert_held(self):
        return self.held

    def release(self):
        self.released = True
        self.held = False


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.runtime = dict(observation(), cuda_visible_devices=UUID)
        self.capacity = dict(
            server="server-4", gpu=0, gpu_uuid=UUID, observed_at=1000,
            memory_total_mib=32000, memory_used_mib=500,
            utilization_percent=0, process_count=0)
        self.clock = Clock()
        self.lease = Lease()
        self.dependencies = self.evidence("dependencies")
        self.assets = self.evidence("assets")
        self.isolation = self.evidence("isolation")
        self.host_validator = Mock(return_value=None)
        self.capacity_validator = Mock(return_value=None)

    def evidence(self, name):
        path = self.root / (name + ".json")
        raw = json.dumps({"name": name}).encode("ascii")
        path.write_bytes(raw)
        return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())

    def make_guard(self, **changes):
        arguments = dict(
            expected_executable="/opt/project_cluster/bin/python",
            expected_executable_sha256="b" * 64,
            gpu=0,
            expected_gpu_uuid=UUID,
            required_memory_mib=20000,
            acquire_slot=lambda server, gpu: self.lease,
            observe_capacity=lambda gpu: copy.deepcopy(self.capacity),
            verify_dependencies=lambda: copy.deepcopy(self.dependencies),
            verify_assets=lambda: copy.deepcopy(self.assets),
            verify_isolation=lambda: copy.deepcopy(self.isolation),
            runtime_observer=lambda: copy.deepcopy(self.runtime),
            host_validator=self.host_validator,
            capacity_validator=self.capacity_validator,
            clock=self.clock)
        arguments.update(changes)
        return validator.ProductionExecutionGuard(**arguments)

    def prepared(self):
        guard = self.make_guard()
        guard.__enter__()
        path, sha = guard.write_context(self.root / "context.json")
        request = dict(
            executable="/opt/project_cluster/bin/python",
            executable_sha256="b" * 64,
            bundle="/srv/bundle", manifest_sha256="c" * 64,
            handoff_path="/srv/bundle/handoff.json",
            handoff_sha256="d" * 64,
            driver_module="production_saved_collation_driver_20260921",
            driver_entry="run",
            context_path=str(path), context_sha256=sha,
            output="/srv/output", timeout=300, max_output_bytes=1000000)
        return guard, path, sha, request

    def test_external_checks_freeze_one_valid_context(self):
        guard, path, _, request = self.prepared()
        try:
            self.assertEqual(
                set(guard.receipt),
                validator.RECEIPT_KEYS)
            context = json.loads(path.read_text(encoding="ascii"))
            config = validator.validate_driver_context(context)
            self.assertEqual(config["receipt"]["slot"]["owner_pid"], os.getpid())
            self.assertEqual(config["gpu_uuid"], UUID)
            self.assertIsNone(guard(copy.deepcopy(request)))
            self.host_validator.assert_called()
            self.capacity_validator.assert_called()
        finally:
            guard.__exit__(None, None, None)
        self.assertTrue(self.lease.released)

    def test_truthy_or_unhashed_external_evidence_is_rejected(self):
        for name in ("verify_dependencies", "verify_assets", "verify_isolation"):
            before = self.lease.released
            with self.subTest(name=name), self.assertRaises(ValueError):
                with self.make_guard(**{name: lambda: None}):
                    pass
            self.assertFalse(before)
            self.assertTrue(self.lease.released)
            self.lease = Lease()

    def test_slot_identity_and_uuid_must_match(self):
        self.lease.proof = dict(
            owner_pid=os.getpid() + 1, token="a" * 64,
            server="server-4", gpu=0)
        with self.assertRaisesRegex(ValueError, "owned"):
            with self.make_guard():
                pass
        self.assertTrue(self.lease.released)
        self.lease = Lease()
        self.runtime["cuda_visible_devices"] = "GPU-" + UUID[4:-1] + "c"
        with self.assertRaisesRegex(ValueError, "UUID"):
            with self.make_guard():
                pass

    def test_context_is_fresh_write_once_and_request_pinned(self):
        guard, path, sha, request = self.prepared()
        try:
            with self.assertRaises(FileExistsError):
                guard.write_context(path)
            bad = dict(request, context_sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "context differs"):
                guard(bad)
            raw = path.read_bytes()
            path.write_bytes(raw + b" ")
            with self.assertRaisesRegex(ValueError, "context changed"):
                guard(request)
            self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        finally:
            guard.__exit__(None, None, None)

    def test_stale_receipt_and_slot_loss_block_before_launch(self):
        guard, _, _, request = self.prepared()
        try:
            self.clock.now = 1401
            with self.assertRaisesRegex(ValueError, "stale"):
                guard(request)
            self.clock.now = 1001
            self.lease.held = False
            with self.assertRaisesRegex(ValueError, "slot"):
                guard(request)
        finally:
            guard.__exit__(None, None, None)

    def test_capacity_and_evidence_drift_reject_launch(self):
        guard, path, _, request = self.prepared()
        try:
            self.capacity_validator.side_effect = ValueError("busy")
            with self.assertRaisesRegex(ValueError, "busy"):
                guard(request)
            self.capacity_validator.side_effect = None
            self.dependencies["sha256"] = "0" * 64
            (self.root / "dependencies.json").write_bytes(b"drift")
            with self.assertRaisesRegex(ValueError, "hash"):
                guard(request)
        finally:
            guard.__exit__(None, None, None)

    def test_child_callbacks_recheck_runtime_parent_and_evidence(self):
        guard, path, _, _ = self.prepared()
        try:
            document = json.loads(path.read_text(encoding="ascii"))
            slot, execution = validator.make_child_checks(
                document, runtime_observer=lambda: copy.deepcopy(self.runtime),
                parent_pid=lambda: os.getpid(), clock=lambda: 1001)
            self.assertIs(slot("server-4", 0), True)
            self.assertIs(execution("server-4", 0), True)
            with self.assertRaisesRegex(ValueError, "parent"):
                _, bad_execution = validator.make_child_checks(
                    document,
                    runtime_observer=lambda: copy.deepcopy(self.runtime),
                    parent_pid=lambda: os.getpid() + 1,
                    clock=lambda: 1001)
                bad_execution("server-4", 0)
            changed = copy.deepcopy(self.runtime)
            changed["user"] = "root"
            with self.assertRaisesRegex(ValueError, "runtime"):
                _, bad_runtime = validator.make_child_checks(
                    document, runtime_observer=lambda: changed,
                    parent_pid=lambda: os.getpid(),
                    clock=lambda: 1001)
                bad_runtime("server-4", 0)
        finally:
            guard.__exit__(None, None, None)

    def test_production_driver_delegates_and_preserves_false_claims(self):
        guard, path, _, _ = self.prepared()
        try:
            document = json.loads(path.read_text(encoding="ascii"))
            boundary = Mock()
            boundary.collect.return_value = {
                "native_execution_authorized": False,
                "scientific_validation_complete": False,
                "admission": False,
                "training_launch": False,
                "identity": {"device": {"logical_uuid": UUID}},
            }
            with patch.object(
                    validator, "observe_runtime",
                    return_value=copy.deepcopy(self.runtime)), \
                    patch.object(validator, "_parent_pid", return_value=os.getpid()):
                result = production_driver.run(boundary, document)
            self.assertFalse(result["admission"])
            arguments = boundary.collect.call_args
            self.assertEqual(arguments.args, ("/opt/project_cluster/bin/python",))
            self.assertEqual(arguments.kwargs["gpu"], 0)
            self.assertEqual(arguments.kwargs["required_memory_mib"], 20000)
            self.assertTrue(callable(arguments.kwargs["slot_check"]))
            self.assertTrue(callable(arguments.kwargs["execution_check"]))
        finally:
            guard.__exit__(None, None, None)

    def test_production_driver_rejects_positive_claim(self):
        guard, path, _, _ = self.prepared()
        try:
            document = json.loads(path.read_text(encoding="ascii"))
            boundary = Mock()
            boundary.collect.return_value = {"admission": True}
            with patch.object(
                    validator, "observe_runtime",
                    return_value=copy.deepcopy(self.runtime)), \
                    patch.object(validator, "_parent_pid", return_value=os.getpid()):
                with self.assertRaisesRegex(ValueError, "cannot claim"):
                    production_driver.run(boundary, document)
        finally:
            guard.__exit__(None, None, None)

    def test_invalid_driver_schema_and_evidence_are_rejected(self):
        guard, path, _, _ = self.prepared()
        try:
            document = json.loads(path.read_text(encoding="ascii"))
            document["gpu"] = 7
            with self.assertRaisesRegex(ValueError, "GPU0/1"):
                validator.validate_driver_context(document)
            document["gpu"] = 0
            document["execution_receipt"]["dependencies"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "hash"):
                validator.validate_driver_context(document)
        finally:
            guard.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
