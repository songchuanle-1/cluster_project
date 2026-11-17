"""Run the real tick wrapper with an isolated fake CLI, never a live Codex call."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


RUNNER = Path("D:/project/.claude/skills/songcl_research_pipeline/codex_tick_exec.sh")
THREAD = "11111111-1111-1111-1111-111111111111"


@unittest.skipUnless(shutil.which("bash"), "bash is required")
class TickExecFailureTest(unittest.TestCase):
    def invoke(self, mode, previous_log=""):
        with tempfile.TemporaryDirectory(prefix="cluster_tick_test_") as tmp:
            root = Path(tmp)
            headless = root / "test_project/pipeline/headless"
            headless.mkdir(parents=True)
            (headless / ".codex_target_thread_id").write_text(THREAD, encoding="ascii")
            (headless / ".codex_thread_ticks").write_text("7", encoding="ascii")
            prompt = root / "prompt.txt"
            prompt.write_text("Isolated test; do not execute work.", encoding="ascii")
            log = headless / "tick_test.log"
            log.write_text(previous_log, encoding="utf-8")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            cli = bin_dir / "codex"
            cli.write_text(
                """#!/usr/bin/env bash
case "$MOCK_MODE" in
  busy)
    echo 'Error: thread already has an active writer' >&2
    exit 1 ;;
  quoted)
    echo '{"type":"thread.started","thread_id":"11111111-1111-1111-1111-111111111111"}'
    echo '{"type":"item.completed","item":{"aggregated_output":"already has an active writer"}}'
    echo '{"type":"turn.failed","error":{"message":"auth_unavailable"}}'
    exit 1 ;;
  started_conflict)
    echo '{"type":"thread.started","thread_id":"11111111-1111-1111-1111-111111111111"}'
    echo 'Error: thread already has an active writer' >&2
    exit 1 ;;
  auth)
    echo 'Error: auth_unavailable' >&2
    exit 1 ;;
  success)
    echo '{"type":"thread.started","thread_id":"11111111-1111-1111-1111-111111111111"}'
    echo '{"type":"turn.completed"}'
    exit 0 ;;
esac
exit 99
""", encoding="ascii")
            cli.chmod(0o755)
            env = os.environ.copy()
            env.update(PROJECT_ROOT=root.as_posix(), MOCK_BIN=bin_dir.as_posix(),
                       MOCK_MODE=mode, RUNNER=RUNNER.as_posix(),
                       PROMPT=prompt.as_posix(), TICK_LOG=log.as_posix())
            command = """
bin="$MOCK_BIN"
if command -v cygpath >/dev/null 2>&1; then bin=$(cygpath -u "$bin"); fi
export PATH="$bin:$PATH"
exec bash "$RUNNER" test_project "$PROMPT" "$TICK_LOG" 10
"""
            result = subprocess.run(["bash", "--noprofile", "--norc", "-c", command],
                                    env=env, capture_output=True, text=True,
                                    encoding="utf-8", timeout=20)
            content = log.read_text(encoding="utf-8")
            count_path = headless / ".codex_thread_ticks"
            count = count_path.read_text() if count_path.exists() else None
            self.assertEqual((headless / ".codex_target_thread_id").read_text(), THREAD)
            self.assertFalse(list(headless.glob(".codex_prompt_*")))
            self.assertFalse(list(headless.glob(".codex_events_*")))
            self.assertFalse(list(headless.glob(".codex_stderr_*")))
            return result.returncode, content, count

    def test_prestart_stderr_conflict_remains_a_skip(self):
        code, log, count = self.invoke("busy")
        self.assertEqual(code, 0)
        self.assertIn("skip this tick", log)
        self.assertEqual(count, "7")

    def test_quoted_historical_conflict_does_not_hide_auth_failure(self):
        code, log, count = self.invoke("quoted")
        self.assertEqual(code, 1)
        self.assertNotIn("skip this tick", log)
        self.assertIn("auth_unavailable", log)
        self.assertIn("retaining pinned target", log)
        self.assertIsNone(count)

    def test_stderr_conflict_after_events_is_not_a_skip(self):
        code, log, count = self.invoke("started_conflict")
        self.assertEqual(code, 1)
        self.assertNotIn("skip this tick", log)
        self.assertIsNone(count)

    def test_existing_log_conflict_does_not_hide_failure(self):
        code, log, count = self.invoke("auth", "old: already has an active writer\n")
        self.assertEqual(code, 1)
        self.assertNotIn("skip this tick", log)
        self.assertIsNone(count)

    def test_success_keeps_normal_thread_count(self):
        code, log, count = self.invoke("success")
        self.assertEqual(code, 0)
        self.assertNotIn("skip this tick", log)
        self.assertEqual(count.strip(), "8")


if __name__ == "__main__":
    unittest.main()
