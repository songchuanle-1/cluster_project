"""Real stdlib subprocesses and synthetic receipts only."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from bounded_collation_process_20260921 import bounded_process, complete_handoff


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_child(self, source, **kwargs):
        return bounded_process(
            [sys.executable, "-I", "-B", "-c", source], self.root, **kwargs)

    def test_both_pipes_and_exit_code(self):
        result = self.run_child(
            "import sys; print('out'); print('err', file=sys.stderr); sys.exit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout.strip(), "out")
        self.assertEqual(result.stderr.strip(), "err")

    def test_timeout_reaps_child(self):
        import bounded_collation_process_20260921 as module
        original = subprocess.Popen
        children = []

        def capture(*args, **kwargs):
            child = original(*args, **kwargs)
            children.append(child)
            return child

        with patch.object(module.subprocess, "Popen", side_effect=capture):
            with self.assertRaises(TimeoutError):
                self.run_child("import time; time.sleep(60)", timeout=0.15)
        self.assertIsNotNone(children[0].returncode)

    def test_stdout_limit(self):
        with self.assertRaisesRegex(ValueError, "output budget"):
            self.run_child("print('x' * 100000)", max_output_bytes=100)

    def test_stderr_limit(self):
        with self.assertRaisesRegex(ValueError, "output budget"):
            self.run_child("import sys; sys.stderr.write('x' * 100000)",
                           max_output_bytes=100)

    def test_combined_limit(self):
        with self.assertRaisesRegex(ValueError, "output budget"):
            self.run_child("import os; os.write(1,b'x'*60); os.write(2,b'x'*60)",
                           max_output_bytes=100)

    def test_exact_limit(self):
        result = self.run_child("import os; os.write(1,b'x'*100)", max_output_bytes=100)
        self.assertEqual(len(result.stdout), 100)

    def test_invalid_utf8_fails_closed(self):
        with self.assertRaises(UnicodeDecodeError):
            self.run_child("import os; os.write(1,b'\\xff')")

    def test_stdin_closed_and_environment_not_inherited(self):
        with patch.dict(os.environ, {"DIAGNOSTIC_TEST_SECRET": "hidden"}):
            result = self.run_child(
                "import os,sys; assert 'DIAGNOSTIC_TEST_SECRET' not in os.environ; "
                "assert sys.stdin.read() == ''; print('ok')")
        self.assertEqual(result.returncode, 0)

    def test_bad_limits_before_launch(self):
        for kwargs in (dict(timeout=True), dict(timeout=float("nan")),
                       dict(timeout=0), dict(timeout=3601),
                       dict(max_output_bytes=True), dict(max_output_bytes=0)):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.run_child("raise RuntimeError", **kwargs)

    def test_reject_shell_strings_and_relative_executable(self):
        for argv in ("echo hello", ["python", "-c", "pass"], [], [sys.executable, "\x00"]):
            with self.subTest(argv=argv), self.assertRaises(ValueError):
                bounded_process(argv, self.root)

    def test_spawn_failure(self):
        with self.assertRaises(OSError):
            bounded_process([str(self.root / "absent.exe")], self.root)

    def test_completion_verifier_receives_exact_contract(self):
        with patch("bounded_collation_process_20260921.verify_completion",
                   return_value={"admission": False}) as verify:
            result = complete_handoff(
                [sys.executable, "-I", "-B", "-c", "print('{}')"],
                self.root, "a"*64, {"capture": "synthetic"}, "b"*64, [3040, 3893])
        self.assertFalse(result["admission"])
        args = verify.call_args.args
        self.assertEqual(args[0].returncode, 0)
        self.assertEqual(args[1:], (self.root / "output", "a"*64,
                                   {"capture": "synthetic"}, "b"*64, [3040, 3893]))

    def test_timeout_never_reaches_receipt_verifier(self):
        with patch("bounded_collation_process_20260921.verify_completion") as verify:
            with self.assertRaises(TimeoutError):
                complete_handoff(
                    [sys.executable, "-I", "-B", "-c", "import time; time.sleep(60)"],
                    self.root, "a"*64, {}, "b"*64, [3040], timeout=0.15)
        verify.assert_not_called()

    def test_real_verifier_rejects_nonzero_exit(self):
        with self.assertRaisesRegex(ValueError, "Child did not"):
            complete_handoff(
                [sys.executable, "-I", "-B", "-c", "raise SystemExit(2)"],
                self.root, "a"*64, {"capture": "synthetic"}, "b"*64, [3040])

    def test_real_process_to_real_synthetic_receipt_verifier(self):
        from test_host_collation_receipts_20260920 import ReceiptTests

        fixture = ReceiptTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.publish()
        result = complete_handoff(
            [sys.executable, "-I", "-B", "-c",
             "from pathlib import Path; print(Path('output/same_child.json').read_text())"],
            fixture.root, "a"*64, fixture.binding, "b"*64, fixture.indices)
        self.assertTrue(result["host_artifact_verification_completed"])
        self.assertFalse(result["native_execution_verified"])
        self.assertFalse(result["admission"])

    def test_zero_exit_without_artifacts_is_not_completion(self):
        with self.assertRaisesRegex(ValueError, "output directory"):
            complete_handoff(
                [sys.executable, "-I", "-B", "-c", "print('{}')"],
                self.root, "a"*64, {"capture": "synthetic"}, "b"*64, [3040])

    @unittest.skipUnless(os.name == "posix", "Linux process-group cleanup needs Linux")
    def test_descendant_pipe_is_closed_after_leader_exit(self):
        result = self.run_child(
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
            "print('leader done')", timeout=2)
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
