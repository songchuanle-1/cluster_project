import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import closure


class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "pipeline").mkdir()
        (self.root / "pipeline/goal.json").write_text("{}")
        (self.root / "evidence.json").write_text('{"passed":true}')
        self.evidence = {"path": "evidence.json", "sha256": closure.digest(self.root / "evidence.json")}
        self.task = {"id": "test", "config": "configs/test.yaml", "code_commit": "a" * 40,
                     "admission_receipt": "receipt.json"}
        self.receipt = dict(id="test", config="configs/test.yaml", code_commit="a" * 40,
                            goal_sha256=closure.digest(self.root / "pipeline/goal.json"),
                            decision=self.evidence,
                            gates={g: dict(passed=True, evidence=[self.evidence]) for g in closure.GATES})

    def save(self):
        (self.root / "receipt.json").write_text(json.dumps(self.receipt))

    def test_valid_admission(self):
        self.save()
        self.assertEqual(closure.admission(self.root, self.task)["id"], "test")

    def test_missing_gate(self):
        del self.receipt["gates"]["native_backward"]
        self.save()
        with self.assertRaises(ValueError):
            closure.admission(self.root, self.task)

    def test_changed_evidence(self):
        self.save()
        (self.root / "evidence.json").write_text("changed")
        with self.assertRaises(ValueError):
            closure.admission(self.root, self.task)

    def test_changed_goal(self):
        self.save()
        (self.root / "pipeline/goal.json").write_text('{"target":1}')
        with self.assertRaises(ValueError):
            closure.admission(self.root, self.task)

    def test_missing_receipt(self):
        with self.assertRaises(ValueError):
            closure.admission(self.root, {"id": "x"})

    def test_progress_not_pid(self):
        server = {"host": "h", "user": "u"}
        task = {"pid": 12, "log": "/logs/x"}
        self.assertFalse(closure.verify_progress(server, task, Mock(return_value="alive"), wait_s=0))
        log = "Train[1/50]: 0%| | 1/4686\rTrain[1/50]: 0%| | 2/4686"
        self.assertTrue(closure.verify_progress(server, task, Mock(return_value=log), wait_s=0))
        self.assertFalse(closure.verify_progress(server, task, Mock(return_value=log + "\nTraceback"), wait_s=0))

    def test_safe_sync_uses_only_ff(self):
        server = {"host": "h", "user": "u", "remote_code_root": "/code path"}
        ssh = Mock(side_effect=["b" * 40, "", "a" * 40])
        with patch.object(closure, "git", return_value="a" * 40) as git:
            self.assertTrue(closure.safe_sync(self.root, "/code", server, ssh))
        commands = " ".join(str(c) for c in ssh.call_args_list + git.call_args_list)
        self.assertIn("--ff-only", commands)
        for bad in ("reset --hard", "stash -u", "clean -fd", "add -A"):
            self.assertNotIn(bad, commands)

    def test_sync_mismatch_fails(self):
        server = {"host": "h", "user": "u", "remote_code_root": "/code"}
        with patch.object(closure, "git", return_value="a" * 40):
            with self.assertRaises(ValueError):
                closure.safe_sync(self.root, "/code", server, Mock(return_value="b" * 40))

    def test_postflight_rejects_missing_report(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        (self.root / "pipeline/reports").mkdir()
        (headless / ".tick_context.json").write_text(json.dumps({
            "generated_at": "2026-01-01T00:00:00+00:00", "mode": "steady",
            "preflight": {"monitor_rc": 0, "goal_rc": 0}}))
        with self.assertRaisesRegex(ValueError, "report"):
            closure.postflight(self.root)

    def test_postflight_preflight_failure_not_hidden(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        (headless / ".tick_context.json").write_text(json.dumps({
            "preflight": {"monitor_rc": 1, "goal_rc": 0}}))
        with self.assertRaisesRegex(ValueError, "Preflight"):
            closure.postflight(self.root)

    def test_postflight_no_progress_and_timestamp_only_rejected(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text("\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue", "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text("\n".join("## " + s for s in sections))
        candidate = dict(id="test", stage="validation", next_action="native check", evidence=[self.evidence])
        context = dict(generated_at="2026-01-01T00:00:00+00:00", mode="event",
                       preflight=dict(monitor_rc=0, goal_rc=0),
                       research_work=dict(candidates=[candidate]))
        (headless / ".tick_context.json").write_text(json.dumps(context))
        candidate = dict(candidate, updated_at="2026-09-15", next_action="reworded native check")
        (self.root / "pipeline/research_work.json").write_text(json.dumps(dict(candidates=[candidate])))
        with self.assertRaisesRegex(ValueError, "no durable progress"):
            closure.postflight(self.root)
        candidate["stage"] = "rejected"
        (self.root / "pipeline/research_work.json").write_text(json.dumps(dict(candidates=[candidate])))
        closure.postflight(self.root)

    def test_safe_launch_does_not_call_legacy_scripts(self):
        (self.root / "pipeline/closure_policy.json").write_text('{"path_mappings":[]}')
        server = dict(host="h", user="u", remote_code_root="/code",
                      conda_source="/conda.sh", conda_env="env")
        def respond(host, user, command):
            self.assertIn("subprocess.Popen", command)
            self.assertNotIn("sync.sh", command)
            self.assertNotIn("remote_train.sh", command)
            self.assertNotIn("git add", command)
            # The unique log path is encoded in the generated Python command.
            import re
            log = re.search(r"/code/logs/train_test_\d{8}_\d{6}\.log", command).group()
            return json.dumps(dict(pid=123, log=log))
        result = closure.safe_launch(self.root, server, self.task, 0, respond)
        self.assertEqual(result["pid"], 123)


if __name__ == "__main__":
    unittest.main()
