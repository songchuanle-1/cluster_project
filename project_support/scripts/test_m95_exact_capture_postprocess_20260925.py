"""Tests for the exact-capture post-processing gate."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import m95_exact_capture_postprocess_20260925 as postprocess


class CompletionGateTest(unittest.TestCase):
    def report(self):
        return {
            "native_capture_completed": True,
            "native_match_cause_completed": True,
            "identity_query_completed": True,
            "capture_mode": "full_train_scan",
            "producer_sha256": "a" * 64,
            "selected_expressions": 256,
            "rows": [
                {"manifest_index": index, "native_match_cause": {}}
                for index in range(256)
            ],
        }

    def test_complete_report_passes(self):
        postprocess.validate_completion_report(self.report(), "a" * 64)

    def test_incomplete_or_wrong_mode_fails(self):
        for key in (
            "native_capture_completed",
            "native_match_cause_completed",
            "identity_query_completed",
        ):
            report = self.report()
            report[key] = False
            with self.assertRaisesRegex(ValueError, key):
                postprocess.validate_completion_report(report, "a" * 64)

        report = self.report()
        report["capture_mode"] = "manifest_subset"
        with self.assertRaisesRegex(ValueError, "full-train"):
            postprocess.validate_completion_report(report, "a" * 64)

    def test_missing_match_cause_fails(self):
        report = self.report()
        del report["rows"][17]["native_match_cause"]
        with self.assertRaisesRegex(ValueError, "native_match_cause"):
            postprocess.validate_completion_report(report, "a" * 64)

    def test_duplicate_or_incomplete_indices_fail(self):
        report = self.report()
        report["rows"][17]["manifest_index"] = 16
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            postprocess.validate_completion_report(report, "a" * 64)


class CompositeHashTest(unittest.TestCase):
    def test_composite_hash_is_concatenated_file_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.py").write_bytes(b"a")
            (root / "b.py").write_bytes(b"bc")
            expected = hashlib.sha256(b"abc").hexdigest()
            self.assertEqual(
                postprocess.composite_sha256(root, ("a.py", "b.py")),
                expected,
            )


class CommandTest(unittest.TestCase):
    def test_analyzer_order_and_arguments(self):
        commands = postprocess.build_analyzer_commands(
            "component.py",
            "identity.py",
            "capture.json",
            "manifest.json",
            "component-out.json",
            "identity-out.json",
            "identity-analysis.json",
            python_executable="python",
        )
        self.assertEqual(commands[0][1], "component.py")
        self.assertEqual(commands[1][1], "identity.py")
        self.assertEqual(
            Path(commands[2][1]).name,
            "analyze_m95_manifest_identity_controls_20260922.py",
        )
        self.assertIn("--manifest", commands[0])
        self.assertNotIn("--manifest", commands[1])
        self.assertIn("--manifest", commands[2])
        self.assertIn("identity-analysis.json", commands[2])

    def test_runner_stops_after_first_failure(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return SimpleNamespace(
                returncode=1 if len(calls) == 1 else 0,
                stdout="",
                stderr="failed",
            )

        with self.assertRaisesRegex(RuntimeError, "exit code 1"):
            postprocess.run_commands(
                [["python", "one.py"], ["python", "two.py"]],
                cwd=".",
                runner=runner,
            )
        self.assertEqual(calls, [["python", "one.py"]])

    def test_runner_records_both_successes(self):
        def runner(command, **kwargs):
            return SimpleNamespace(returncode=0, stdout=command[1], stderr="")

        results = postprocess.run_commands(
            [["python", "one.py"], ["python", "two.py"]],
            cwd=".",
            runner=runner,
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["stderr_tail"], "")


class OutputTest(unittest.TestCase):
    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            path.write_text("original", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "already exists"):
                postprocess.write_json(path, {"new": True})
            self.assertEqual(path.read_text(encoding="ascii"), "original")

    def test_json_output_is_ascii_and_sorted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            postprocess.write_json(path, {"b": 2, "a": 1})
            self.assertEqual(
                path.read_text(encoding="ascii"),
                '{\n  "a": 1,\n  "b": 2\n}\n',
            )
            self.assertEqual(json.loads(path.read_text(encoding="ascii")), {"a": 1, "b": 2})


if __name__ == "__main__":
    unittest.main()
