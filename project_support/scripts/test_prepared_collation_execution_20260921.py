"""Synthetic adapter tests only; production execution validator is not supplied."""
from contextlib import ExitStack
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import prepared_collation_execution_20260921 as adapter


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.pin = self.root / "pin"
        self.pin.write_bytes(b"synthetic")
        self.digest = hashlib.sha256(b"synthetic").hexdigest()
        self.prepared = dict(
            run=str(self.root), command=[sys.executable, "-I", "-B", "-c", "print('{}')"],
            pinned_host_inputs=[dict(path=str(self.pin), sha256=self.digest)])
        self.arguments = dict(
            executable="/synthetic/python", executable_sha256="1"*64,
            bwrap="/synthetic/bwrap", bwrap_sha256="2"*64,
            infrastructure="/synthetic/infra", infrastructure_sha256="3"*64,
            bundle="/synthetic/bundle", manifest_sha256="a"*64,
            expected_binding={"capture_id": "original", "nested": {"value": 1}},
            expected_full_binding_sha256="b"*64, expected_indices=[3040, 3893],
            validate_execution=Mock(return_value=None), timeout=13, max_output_bytes=9999)

    def call(self, *, real_completion=False, **changes):
        with ExitStack() as stack:
            self.prepare = stack.enter_context(patch.object(
                adapter, "prepare_handoff", return_value=copy.deepcopy(self.prepared)))
            if not real_completion:
                self.complete = stack.enter_context(patch.object(
                    adapter, "complete_handoff", return_value={"admission": False}))
            return adapter.prepare_and_complete(**dict(self.arguments, **changes))

    def test_exact_contract_and_order(self):
        events = []

        def validate(phase, request, prepared):
            events.append(phase)
            self.assertEqual(request["expected_binding"], self.arguments["expected_binding"])
            self.assertEqual(prepared, None if phase == "before_prepare" else self.prepared)
        self.assertEqual(self.call(validate_execution=validate), {"admission": False})
        self.assertEqual(events, ["before_prepare", "before_launch"])
        self.assertEqual(self.prepare.call_args.args, (
            "/synthetic/python", "1"*64, "/synthetic/bwrap", "2"*64,
            "/synthetic/infra", "3"*64, "/synthetic/bundle", "a"*64))
        self.assertEqual(self.complete.call_args.args, (
            self.prepared["command"], str(self.root), "a"*64,
            self.arguments["expected_binding"], "b"*64, [3040, 3893]))
        self.assertEqual(self.complete.call_args.kwargs,
                         {"timeout": 13, "max_output_bytes": 9999})

    def test_missing_validator_before_provision(self):
        with self.assertRaisesRegex(ValueError, "validator required"):
            self.call(validate_execution=None)
        self.prepare.assert_not_called()
        self.complete.assert_not_called()

    def test_preparation_gate_blocks_before_writes(self):
        with self.assertRaisesRegex(RuntimeError, "unverified"):
            self.call(validate_execution=Mock(side_effect=RuntimeError("unverified")))
        self.prepare.assert_not_called()
        self.complete.assert_not_called()

    def test_launch_gate_failure_preserves_existing_files(self):
        hook = Mock(side_effect=[None, RuntimeError("unverified dependencies")])
        with self.assertRaisesRegex(RuntimeError, "dependencies"):
            self.call(validate_execution=hook)
        self.prepare.assert_called_once()
        self.complete.assert_not_called()
        self.assertEqual(self.pin.read_bytes(), b"synthetic")

    def test_boolean_pass_flag_rejected(self):
        for result in (True, False, {"passed": True}):
            with self.subTest(result=result), self.assertRaisesRegex(ValueError, "pass flag"):
                self.call(validate_execution=Mock(return_value=result))
            self.prepare.assert_not_called()
            self.complete.assert_not_called()

    def test_invalid_expectations_before_provision(self):
        for changes in ({"expected_binding": {}}, {"expected_binding": {"bad": float("nan")}},
                        {"expected_indices": []}, {"expected_indices": [True]},
                        {"expected_indices": [-1]}, {"expected_indices": [3040, 3040]},
                        {"expected_full_binding_sha256": "not-a-digest"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.call(**changes)
            self.prepare.assert_not_called()
            self.complete.assert_not_called()

    def test_invalid_budget_before_provision(self):
        for changes in ({"timeout": True}, {"timeout": float("inf")}, {"timeout": 0},
                        {"max_output_bytes": 0}, {"max_output_bytes": 17000000}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.call(**changes)
            self.prepare.assert_not_called()
            self.complete.assert_not_called()

    def test_each_invalid_input_digest_before_provision(self):
        for name in ("executable_sha256", "bwrap_sha256",
                     "infrastructure_sha256", "manifest_sha256"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.call(**{name: "bad"})
            self.prepare.assert_not_called()

    def test_validator_cannot_rewrite_contract(self):
        def mutate(phase, request, prepared):
            request["expected_binding"]["nested"]["value"] = 99
            request["expected_indices"].clear()
            if prepared:
                prepared["command"].clear()
                prepared["run"] = "/other"
                prepared["pinned_host_inputs"].clear()
        self.call(validate_execution=mutate)
        self.assertEqual(self.complete.call_args.args[0], self.prepared["command"])
        self.assertEqual(self.complete.call_args.args[3]["nested"]["value"], 1)
        self.assertEqual(self.complete.call_args.args[5], [3040, 3893])

    def test_original_caller_mutation_does_not_change_frozen_expectations(self):
        def mutate(phase, request, prepared):
            self.arguments["expected_binding"]["nested"]["value"] = 99
            self.arguments["expected_indices"].clear()
        self.call(validate_execution=mutate)
        self.assertEqual(self.complete.call_args.args[3]["nested"]["value"], 1)
        self.assertEqual(self.complete.call_args.args[5], [3040, 3893])

    def test_pin_drift_during_validator_never_launches(self):
        def drift(phase, request, prepared):
            if phase == "before_launch":
                self.pin.write_bytes(b"drift")
        with self.assertRaisesRegex(ValueError, "digest differs"):
            self.call(validate_execution=drift)
        self.complete.assert_not_called()

    def test_preparation_error_never_launches_or_retries(self):
        with patch.object(adapter, "prepare_handoff", side_effect=OSError("provision")) as p, \
                patch.object(adapter, "complete_handoff") as c:
            with self.assertRaisesRegex(OSError, "provision"):
                adapter.prepare_and_complete(**self.arguments)
        p.assert_called_once()
        c.assert_not_called()

    def test_completion_error_never_retries(self):
        with patch.object(adapter, "prepare_handoff", return_value=self.prepared) as p, \
                patch.object(adapter, "complete_handoff", side_effect=TimeoutError) as c:
            with self.assertRaises(TimeoutError):
                adapter.prepare_and_complete(**self.arguments)
        p.assert_called_once()
        c.assert_called_once()

    def test_real_child_and_receipt_verification(self):
        from test_host_collation_receipts_20260920 import ReceiptTests
        fixture = ReceiptTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.publish()
        self.prepared.update(
            run=str(fixture.root),
            command=[sys.executable, "-I", "-B", "-c",
                     "from pathlib import Path; print(Path('output/same_child.json').read_text())"])
        result = self.call(real_completion=True, expected_binding=fixture.binding)
        self.assertTrue(result["host_artifact_verification_completed"])
        self.assertFalse(result["native_execution_verified"])
        self.assertFalse(result["scientific_validation_complete"])
        self.assertFalse(result["admission"])

    def test_real_child_rejects_child_derived_binding(self):
        from test_host_collation_receipts_20260920 import ReceiptTests
        fixture = ReceiptTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.publish()
        self.prepared.update(
            run=str(fixture.root),
            command=[sys.executable, "-I", "-B", "-c",
                     "from pathlib import Path; print(Path('output/same_child.json').read_text())"])
        with self.assertRaisesRegex(ValueError, "Original saved binding"):
            self.call(real_completion=True)

    def test_real_default_preparation_rejects_windows(self):
        with patch("prepare_collation_handoff_20260921.platform.system", return_value="Windows"), \
                patch.object(adapter, "complete_handoff") as complete:
            with self.assertRaisesRegex(ValueError, "Linux server-4"):
                adapter.prepare_and_complete(**self.arguments)
        complete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
