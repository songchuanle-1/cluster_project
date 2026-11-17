import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import foreground_tick as tick


class ForegroundTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {"PROJECT_ROOT": self.temp.name})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.pipeline = Path(self.temp.name) / "sample" / "pipeline"
        self.headless = self.pipeline / "headless"
        self.headless.mkdir(parents=True)
        tick.save(self.pipeline / "execution_mode.json", {
            "mode": "foreground", "target_thread_id": "thread",
        })
        tick.save(self.pipeline / "closure_policy.json", {"enabled": True})

    def prepared_run(self, script, *args):
        if script == "build_tick_context.py":
            tick.save(self.headless / ".tick_context.json", {
                "mode": "design", "deadline_at": "2026-09-27T03:00:00+08:00",
                "generated_at": "2026-09-27T02:00:00+08:00",
            })
            tick.save(self.headless / ".tick_context_state.next.json", {
                "mode": "design", "generated_at": "2026-09-27T02:00:00+08:00",
            })
        return (4 if script == "check_goal.py" else 0), "test output\n"

    def begin(self):
        with patch.object(tick, "run", side_effect=self.prepared_run) as runner:
            self.assertEqual(tick.begin("sample", "thread"), 0)
            self.assertEqual(runner.call_count, 3)
        return tick.load(self.headless / ".foreground.lockdir" / "owner.json")["token"]

    def test_background_lock_blocks_without_mutation(self):
        (self.headless / ".tick.lockdir").mkdir()
        with patch.object(tick, "run") as runner:
            self.assertEqual(tick.begin("sample", "thread"), 75)
            runner.assert_not_called()
        self.assertFalse((self.headless / ".foreground.lockdir").exists())

    def test_wrong_task_cannot_start(self):
        with self.assertRaises(ValueError):
            tick.begin("sample", "other")
        self.assertFalse((self.headless / ".foreground.lockdir").exists())

    def test_duplicate_begin_and_wrong_token(self):
        token = self.begin()
        with patch.object(tick, "run") as runner:
            self.assertEqual(tick.begin("sample", "thread"), 75)
            runner.assert_not_called()
        with self.assertRaises(ValueError):
            tick.complete("sample", "wrong")
        self.assertEqual(tick.complete("sample", token, "interrupted"), 1)
        self.assertFalse((self.headless / ".tick_context_state.next.json").exists())
        self.assertTrue((self.headless / ".tick_unhealthy").exists())

    def test_postflight_failure_retains_lease_then_success_commits(self):
        token = self.begin()
        with patch.object(tick, "run", return_value=(1, "capacity gap")):
            self.assertEqual(tick.complete("sample", token), 1)
        self.assertTrue((self.headless / ".foreground.lockdir").exists())
        self.assertFalse((self.headless / ".tick_context_state.json").exists())
        with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")) as runner:
            self.assertEqual(tick.complete("sample", token), 0)
            runner.assert_called_once_with("closure.py", "sample", "--require-enabled")
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        self.assertEqual(tick.load(self.headless / ".tick_context_state.json")["mode"], "design")
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertEqual(record["status"], "FINALIZED")
        self.assertEqual(record["state_sha256"], tick.digest(self.headless / ".tick_context_state.json"))
        self.assertTrue(record["context_committed"])
        self.assertEqual(record["lease_release"], "released")
        self.assertTrue(record["lease_released_at"])

    def test_preflight_failure_releases_without_context_commit(self):
        with patch.object(tick, "run", return_value=(2, "failed")):
            self.assertEqual(tick.begin("sample", "thread"), 1)
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        self.assertTrue((self.headless / ".tick_unhealthy").exists())

    def test_preflight_exception_releases(self):
        with patch.object(tick, "run", side_effect=RuntimeError("timeout")):
            with self.assertRaises(RuntimeError):
                tick.begin("sample", "thread")
        self.assertFalse((self.headless / ".foreground.lockdir").exists())

    def test_busy_monitor_releases_only_own_lease_without_goal_or_snapshot(self):
        (self.headless / ".tick_unhealthy").write_text("previous failure", encoding="utf-8")
        with patch.object(tick, "run", return_value=(75, "monitor busy")) as runner:
            self.assertEqual(tick.begin("sample", "thread"), 75)
            runner.assert_called_once_with("pipeline_monitor.py", "sample")
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        self.assertFalse((self.headless / ".tick_context.json").exists())
        self.assertFalse((self.headless / ".tick_context_state.json").exists())
        self.assertEqual((self.headless / ".tick_unhealthy").read_text(encoding="utf-8"),
                         "previous failure")
        record = tick.load(next((self.pipeline / "tick_receipts").glob("*.json")))
        self.assertEqual(record["status"], "SKIPPED_BUSY")
        self.assertFalse(record["context_committed"])
        self.assertEqual(record["lease_release"], "released")

    def test_project_path_cannot_escape(self):
        with self.assertRaises(ValueError):
            tick.paths("../escape")

    def test_disabled_or_missing_policy_cannot_start(self):
        for policy in (None, {"enabled": False}):
            with self.subTest(policy=policy):
                path = self.pipeline / "closure_policy.json"
                if policy is None:
                    path.unlink()
                else:
                    tick.save(path, policy)
                with patch.object(tick, "run") as runner:
                    self.assertEqual(tick.begin("sample", "thread"), 2)
                    runner.assert_not_called()
                self.assertFalse((self.headless / ".foreground.lockdir").exists())

    def test_silent_success_is_not_postflight_pass(self):
        token = self.begin()
        with patch.object(tick, "run", return_value=(0, "")):
            self.assertEqual(tick.complete("sample", token), 1)
        self.assertTrue((self.headless / ".foreground.lockdir").exists())
        self.assertFalse((self.headless / ".tick_context_state.json").exists())

    def test_snapshot_tampering_or_loss_cannot_commit(self):
        token = self.begin()
        for name in (".tick_context.json", ".tick_context_state.next.json"):
            path = self.headless / name
            original = path.read_bytes()
            for change in ("missing", "changed"):
                with self.subTest(name=name, change=change):
                    if change == "missing":
                        path.unlink()
                    else:
                        tick.save(path, {"mode": "steady"})
                    with patch.object(tick, "run") as runner:
                        self.assertEqual(tick.complete("sample", token), 1)
                        runner.assert_not_called()
                    self.assertFalse((self.headless / ".tick_context_state.json").exists())
                    path.write_bytes(original)

    def test_receipt_write_failure_does_not_commit(self):
        token = self.begin()
        with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")), \
                patch.object(tick, "receipt", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                tick.complete("sample", token)
        self.assertTrue((self.headless / ".tick_context_state.next.json").exists())
        self.assertFalse((self.headless / ".tick_context_state.json").exists())
        self.assertTrue((self.headless / ".foreground.lockdir").exists())

    def test_release_failure_keeps_durable_finalization_not_false_complete(self):
        token = self.begin()
        with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")), \
                patch.object(tick, "release", side_effect=OSError("locked")):
            with self.assertRaises(OSError):
                tick.complete("sample", token)
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertTrue(record["context_committed"])
        self.assertEqual(record["lease_release"], "retained")
        self.assertEqual(record["lease_release_error"], "OSError")
        self.assertTrue((self.headless / ".foreground.lockdir").exists())
        self.assertEqual(tick.complete("sample", token), 1)
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertTrue(record["context_committed"])
        self.assertEqual(tick.complete("sample", token, "release recovery"), 1)
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertTrue(record["context_committed"])
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertEqual(record["lease_release"], "released")

    def test_policy_removed_after_begin_cannot_finish(self):
        token = self.begin()
        (self.pipeline / "closure_policy.json").unlink()
        self.assertEqual(tick.complete("sample", token), 2)
        self.assertFalse((self.headless / ".tick_context_state.json").exists())
        self.assertTrue((self.headless / ".foreground.lockdir").exists())

    def test_real_closure_subprocess_and_receipt(self):
        token = self.begin()
        context_path = self.headless / ".tick_context.json"
        context = tick.load(context_path)
        context.update({
            "mode": "event", "generated_at": "2026-01-01T00:00:00+00:00",
            "preflight": {"monitor_rc": 0, "goal_rc": 4},
        })
        tick.save(context_path, context)
        owner_path = self.headless / ".foreground.lockdir" / "owner.json"
        owner = tick.load(owner_path)
        owner["context_sha256"] = tick.digest(context_path)
        tick.save(owner_path, owner)
        reports = self.pipeline / "reports"
        reports.mkdir(exist_ok=True)
        (reports / "summary_test.md").write_text(
            "\n".join(f"## {n}. Section" for n in range(6)), encoding="utf-8")
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.pipeline / "codex_memory.md").write_text(
            "\n".join("## " + s for s in sections), encoding="utf-8")
        self.assertEqual(tick.complete("sample", token), 0)
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertEqual(record["postflight"], "PASS")
        self.assertTrue(record["context_committed"])

    def test_auto_steady_finishes_once_and_keeps_full_report(self):
        def runner(script, *args):
            if script == "closure.py":
                return 0, "CLOSURE_POSTFLIGHT_PASS\n"
            result = self.prepared_run(script, *args)
            if script == "build_tick_context.py":
                for name in (".tick_context.json", ".tick_context_state.next.json"):
                    data = tick.load(self.headless / name)
                    data["mode"] = "steady"
                    tick.save(self.headless / name, data)
            return result
        with patch.object(tick, "run", side_effect=runner) as calls:
            self.assertEqual(tick.begin("sample", "thread", auto_steady=True), 0)
        self.assertEqual(calls.call_count, 4)
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        report = next((self.pipeline / "reports").glob("summary_*.md")).read_text(encoding="utf-8")
        for i in range(6):
            self.assertIn(f"## {i}.", report)
        record = tick.load(next((self.pipeline / "tick_receipts").glob("*.json")))
        self.assertEqual(record["usage"]["status"], "unavailable")
        self.assertEqual(record["outcomes"]["changed_candidates"], 0)
        self.assertEqual(record["lease_release"], "released")

    def test_abort_records_release_without_recollecting_usage_or_outcomes(self):
        token = self.begin()
        with patch.object(tick.tick_usage, "collect", return_value={"test": "usage"}) as usage, \
                patch.object(tick.tick_usage, "outcomes", return_value={"test": "outcomes"}) as outcomes:
            self.assertEqual(tick.complete("sample", token, "user_requested_policy_switch"), 1)
        usage.assert_called_once()
        outcomes.assert_called_once()
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertEqual(record["status"], "INCOMPLETE")
        self.assertEqual(record["reason"], "user_requested_policy_switch")
        self.assertEqual(record["lease_release"], "released")
        self.assertEqual(record["usage"], {"test": "usage"})
        self.assertEqual(record["outcomes"], {"test": "outcomes"})
        self.assertFalse(record["context_committed"])

    def test_release_receipt_never_mutates_a_new_lease(self):
        token = self.begin()
        original_release = tick.release
        successor = {"token": "successor", "thread_id": "thread", "started_at": "later"}

        def handover(headless):
            original_release(headless)
            (headless / ".foreground.lockdir").mkdir()
            tick.save(headless / ".foreground.lockdir/owner.json", successor)
            tick.save(headless / ".tick_context_state.next.json", {"new_tick": True})

        with patch.object(tick, "release", side_effect=handover):
            self.assertEqual(tick.complete("sample", token, "requested stop"), 1)
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertEqual(record["lease_release"], "released")
        self.assertEqual(tick.load(self.headless / ".foreground.lockdir/owner.json"), successor)
        self.assertEqual(tick.load(self.headless / ".tick_context_state.next.json"), {"new_tick": True})

    def test_partial_release_failure_is_unknown_not_released(self):
        token = self.begin()

        def partial(headless):
            (headless / ".foreground.lockdir/owner.json").unlink()
            raise PermissionError("directory still locked")

        with patch.object(tick, "release", side_effect=partial):
            with self.assertRaises(tick.LeaseReleaseError):
                tick.complete("sample", token, "stop")
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertEqual(record["lease_release"], "unknown")
        self.assertEqual(record["lease_release_error"], "PermissionError")
        self.assertNotIn("lease_released_at", record)
        self.assertTrue((self.headless / ".foreground.lockdir").exists())

    def test_release_requires_matching_owner_and_receipt(self):
        token = self.begin()
        owner_path = self.headless / ".foreground.lockdir/owner.json"
        owner = tick.load(owner_path)
        record = tick.receipt(self.headless, owner, "INCOMPLETE", lease_release="pending")
        original = record.read_bytes()
        tick.save(owner_path, dict(owner, token="newowner"))
        with patch.object(tick, "release") as release:
            with self.assertRaisesRegex(ValueError, "ownership changed"):
                tick.release_recorded(self.headless, owner, record)
            release.assert_not_called()
        self.assertEqual(record.read_bytes(), original)
        tick.save(owner_path, owner)
        data = tick.load(record)
        tick.save(record, dict(data, token="wrong"))
        with patch.object(tick, "release") as release:
            with self.assertRaisesRegex(ValueError, "receipt does not match"):
                tick.release_recorded(self.headless, owner, record)
            release.assert_not_called()

    def test_postrelease_write_failure_does_not_abort_successor_in_auto_steady(self):
        original_release, original_save = tick.release, tick.save
        successor = {"token": "successor", "thread_id": "thread", "started_at": "later"}

        def runner(script, *args):
            if script == "closure.py":
                return 0, "CLOSURE_POSTFLIGHT_PASS\n"
            result = self.prepared_run(script, *args)
            if script == "build_tick_context.py":
                for name in (".tick_context.json", ".tick_context_state.next.json"):
                    data = tick.load(self.headless / name)
                    tick.save(self.headless / name, dict(data, mode="steady"))
            return result

        def handover(headless):
            original_release(headless)
            (headless / ".foreground.lockdir").mkdir()
            original_save(headless / ".foreground.lockdir/owner.json", successor)
            original_save(headless / ".tick_context_state.next.json", {"new_tick": True})

        def save(path, value):
            if path.parent.name == "tick_receipts" and value.get("lease_release") == "released":
                raise OSError("disk full")
            original_save(path, value)

        with patch.object(tick, "run", side_effect=runner), \
                patch.object(tick, "release", side_effect=handover), \
                patch.object(tick, "save", side_effect=save):
            with self.assertRaisesRegex(tick.LeaseReleaseError, "released but receipt"):
                tick.begin("sample", "thread", auto_steady=True)
        self.assertEqual(tick.load(self.headless / ".foreground.lockdir/owner.json"), successor)
        self.assertEqual(tick.load(self.headless / ".tick_context_state.next.json"), {"new_tick": True})
        record = tick.load(next((self.pipeline / "tick_receipts").glob("*.json")))
        self.assertEqual(record["status"], "FINALIZED")
        self.assertTrue(record["context_committed"])
        self.assertEqual(record["lease_release"], "pending")
        self.assertFalse((self.headless / ".tick_unhealthy").exists())

    def test_busy_background_race_records_own_release(self):
        def snapshot(pipeline):
            (self.headless / ".tick.lockdir").mkdir(exist_ok=True)
            return {}
        with patch.object(tick.tick_usage, "work_snapshot", side_effect=snapshot), \
                patch.object(tick, "run") as runner:
            self.assertEqual(tick.begin("sample", "thread"), 75)
        runner.assert_not_called()
        record = tick.load(next((self.pipeline / "tick_receipts").glob("*.json")))
        self.assertEqual(record["status"], "SKIPPED_BUSY")
        self.assertEqual(record["lease_release"], "released")
        self.assertTrue((self.headless / ".tick.lockdir").exists())

    def test_preflight_exception_cannot_abort_a_different_owner(self):
        def runner(*args):
            owner_path = self.headless / ".foreground.lockdir/owner.json"
            owner = tick.load(owner_path)
            tick.save(owner_path, dict(owner, token="different"))
            raise RuntimeError("interrupted")
        with patch.object(tick, "run", side_effect=runner):
            with self.assertRaises(RuntimeError):
                tick.begin("sample", "thread")
        self.assertEqual(tick.load(self.headless / ".foreground.lockdir/owner.json")["token"],
                         "different")
        self.assertFalse((self.headless / ".tick_unhealthy").exists())

    def test_preflight_release_failure_does_not_retry_cleanup(self):
        with patch.object(tick, "run", return_value=(2, "failed")), \
                patch.object(tick, "release", side_effect=OSError("locked")) as release:
            with self.assertRaises(tick.LeaseReleaseError):
                tick.begin("sample", "thread")
        release.assert_called_once()
        record = tick.load(next((self.pipeline / "tick_receipts").glob("*.json")))
        self.assertEqual(record["lease_release"], "retained")
        self.assertIn("monitor=2", record["reason"])

    def test_renderer_requires_matching_token_and_unchanged_context(self):
        token = self.begin()
        with self.assertRaisesRegex(ValueError, "token"):
            tick.report("sample", "not-owned")
        notes = self.pipeline / "notes.json"
        tick.save(notes, {"actions": ["Executed matched controls"],
                          "decisions": ["Rejected with evidence"]})
        path = tick.report("sample", token, notes)
        self.assertNotIn("RESEARCH_NOTES_PENDING", path.read_text(encoding="utf-8"))
        tick.save(self.headless / ".tick_context.json", {"mode": "steady"})
        with self.assertRaisesRegex(ValueError, "changed snapshot"):
            tick.report("sample", token)

    def test_human_block_cooldown_excludes_closed_and_uses_four_hour_bound(self):
        from datetime import datetime, timedelta, timezone
        token = self.begin()
        now = datetime.now(timezone.utc)
        retry = (now + timedelta(hours=3)).isoformat()
        tick.save(self.pipeline / "research_work.json", {
            "candidates": [
                {"id": "legacy", "stage": "closed"},
                {"id": "human", "stage": "blocked",
                 "blocker_kind": "human_authorization", "retry_after": retry},
            ],
            "design_cycle": {"stop_reason": "external_resource_blocked",
                             "resume_condition": "Scoped commit authorization arrives"},
        })
        with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")):
            self.assertEqual(tick.complete("sample", token), 0)
        hold = tick.load(self.headless / ".research_cooldown.json")
        self.assertEqual(hold["retry_after"], retry)
        self.assertGreater(datetime.fromisoformat(hold["retry_after"]),
                           now + timedelta(hours=2))
        self.assertFalse((self.headless / ".foreground.lockdir").exists())

    def test_resource_cooldown_remains_capped_at_two_hours(self):
        from datetime import datetime, timedelta, timezone
        token = self.begin()
        now = datetime.now(timezone.utc)
        tick.save(self.pipeline / "research_work.json", {
            "candidates": [{"id": "resource", "stage": "blocked",
                            "blocker_kind": "external_resource",
                            "retry_after": (now + timedelta(hours=3)).isoformat()}],
            "design_cycle": {"stop_reason": "external_resource_blocked"},
        })
        with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")):
            self.assertEqual(tick.complete("sample", token), 0)
        hold = tick.load(self.headless / ".research_cooldown.json")
        self.assertLess(datetime.fromisoformat(hold["retry_after"]),
                        now + timedelta(hours=2, seconds=5))

    def test_blocked_cooldown_cannot_hide_executable_candidates(self):
        from datetime import datetime, timedelta, timezone
        token = self.begin()
        tick.save(self.pipeline / "research_work.json", {
            "candidates": [
                {"id": "legacy", "stage": "closed"},
                {"id": "blocked", "stage": "blocked",
                 "blocker_kind": "human_authorization",
                 "retry_after": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()},
                {"id": "active", "stage": "validation"},
            ],
            "design_cycle": {"stop_reason": "external_resource_blocked"},
        })
        with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")):
            self.assertEqual(tick.complete("sample", token), 0)
        self.assertFalse((self.headless / ".research_cooldown.json").exists())

    def test_mixed_cooldown_uses_resource_cap_and_earliest_retry(self):
        from datetime import datetime, timedelta, timezone
        for delay in (3, 0.5):
            with self.subTest(delay=delay):
                token = self.begin()
                now = datetime.now(timezone.utc)
                retry = (now + timedelta(hours=delay)).isoformat()
                tick.save(self.pipeline / "research_work.json", {
                    "candidates": [
                        {"id": "human", "stage": "blocked",
                         "blocker_kind": "human_authorization",
                         "retry_after": (now + timedelta(hours=4)).isoformat()},
                        {"id": "resource", "stage": "blocked",
                         "blocker_kind": "external_resource", "retry_after": retry},
                    ],
                    "design_cycle": {"stop_reason": "external_resource_blocked"},
                })
                with patch.object(tick, "run", return_value=(0, "CLOSURE_POSTFLIGHT_PASS\n")):
                    self.assertEqual(tick.complete("sample", token), 0)
                hold = tick.load(self.headless / ".research_cooldown.json")
                until = datetime.fromisoformat(hold["retry_after"])
                self.assertLessEqual(until, datetime.fromisoformat(retry))
                self.assertLess(until, now + timedelta(hours=2, seconds=5))
                if delay < 2:
                    self.assertEqual(hold["retry_after"], retry)

    def test_pending_limit_real_event_then_auto_steady_without_mutation(self):
        from datetime import datetime, timedelta, timezone
        project = self.pipeline.parent
        (project / "SERVERS.yaml").write_text(
            "servers:\n  gpu:\n    role: gpu_server\n"
            "    allowed_gpus: [0, 1]\n    max_tasks_per_gpu: 1\n",
            encoding="utf-8")
        tick.save(self.pipeline / "goal.json", {
            "pipeline_policy": {"research_on_capacity_gap": True, "research_pending_limit": 2},
        })
        tick.save(self.pipeline / "queue.json", {"gpu_queues": {"gpu": []}})
        evidence = self.pipeline / "native.json"
        evidence.write_text('{"observed": true}', encoding="utf-8")
        entry = {"path": "pipeline/native.json", "sha256": tick.digest(evidence)}
        retry = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        work = {"candidates": [dict(
            id=str(i), stage="blocked", blocker_kind="human_authorization",
            blocker="Scoped commit permission is required", retry_after=retry,
            unblock_condition="Explicit confirmation in the owning chat",
            next_action="Confirm the exact tested file bundle", evidence=[entry],
        ) for i in range(2)]}
        tick.save(self.pipeline / "research_work.json", work)
        original_work = (self.pipeline / "research_work.json").read_bytes()
        original_run = tick.run

        def runner(script, *args):
            if script in ("pipeline_monitor.py", "check_goal.py"):
                return 0, "isolated preflight\n"
            return original_run(script, *args)

        with patch.object(tick, "run", side_effect=runner) as calls:
            self.assertEqual(tick.begin("sample", "thread", auto_steady=True), 0)
            view = tick.load(self.headless / ".tick_model_view.json")
            self.assertEqual(view["mode"], "event")
            self.assertTrue(view["research"]["deferred"])
            self.assertNotIn("design_bootstrap", view)
            owner = tick.load(self.headless / ".foreground.lockdir/owner.json")
            sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                        "Closed Or Failed Directions", "Running And Queue",
                        "Open Questions And Risks", "Last Tick")
            (self.pipeline / "codex_memory.md").write_text(
                "\n".join("## " + s for s in sections), encoding="utf-8")
            notes = self.pipeline / "notes.json"
            tick.save(notes, {"actions": ["Verified evidenced external blockers"],
                              "decisions": ["Wait without new candidates or commits"]})
            tick.report("sample", owner["token"], notes)
            self.assertEqual(tick.complete("sample", owner["token"]), 0)
            memory = (self.pipeline / "codex_memory.md").read_bytes()
            self.assertEqual(tick.begin("sample", "thread", auto_steady=True), 0)
        view = tick.load(self.headless / ".tick_model_view.json")
        self.assertEqual(view["mode"], "steady")
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        self.assertFalse((self.headless / ".tick_context_state.next.json").exists())
        self.assertEqual((self.pipeline / "research_work.json").read_bytes(), original_work)
        self.assertEqual((self.pipeline / "codex_memory.md").read_bytes(), memory)
        self.assertEqual(sum(c.args[0] == "pipeline_monitor.py" for c in calls.call_args_list), 2)
        self.assertEqual(sum(c.args[0] == "closure.py" for c in calls.call_args_list), 2)
        records = [tick.load(path) for path in (self.pipeline / "tick_receipts").glob("*.json")]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(r["status"] == "FINALIZED" and r["context_committed"]
                            for r in records))

    def test_real_early_stop_persists_cooldown_only_after_postflight(self):
        from datetime import datetime, timedelta, timezone
        import closure
        import tick_efficiency
        token = self.begin()
        context_path = self.headless / ".tick_context.json"
        context = tick.load(context_path)
        context.update({
            "generated_at": "2026-01-01T00:00:00+00:00",
            "deadline_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "preflight": {"monitor_rc": 0, "goal_rc": 0},
            "queue": {"candidate_budget": 2, "target_active": 2,
                      "servers": [{"name": "server-1"}]},
        })
        tick.save(context_path, context)
        owner_path = self.headless / ".foreground.lockdir/owner.json"
        owner = tick.load(owner_path)
        owner["context_sha256"] = tick.digest(context_path)
        tick.save(owner_path, owner)
        tick.save(self.pipeline / "goal.json", {"pipeline_policy": {"research_on_capacity_gap": True}})
        tick.save(self.pipeline / "queue.json", {"gpu_queues": {"server-1": []}})
        evidence_path = self.pipeline / "evidence.txt"
        evidence_path.write_text("Executed two distinct matched native controls")
        evidence = {"path": "pipeline/evidence.txt", "sha256": closure.digest(evidence_path)}
        work = {
            "candidates": [{"id": str(i), "stage": "rejected", "evidence": [evidence],
                            "next_action": "Revisit on new independent evidence"} for i in range(2)],
            "design_cycle": {
                "stop_reason": "no_information_gain", "attempted_ids": ["0", "1"],
                "evidence": [evidence], "resume_condition": "New evidence",
                "no_gain_reason": "Both tested controls refute the candidates",
                "retry_after": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                "attempt_results": [{"candidate_id": str(i), "hypothesis_id": str(i),
                                     "test": "matched control", "result": "refuted",
                                     "evidence": [evidence]} for i in range(2)],
            },
        }
        tick.save(self.pipeline / "research_work.json", work)
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.pipeline / "codex_memory.md").write_text("\n".join("## " + s for s in sections))
        # Initial generated reports cannot satisfy a research tick.
        self.assertEqual(tick.complete("sample", token), 1)
        self.assertFalse((self.headless / ".research_cooldown.json").exists())
        notes = self.pipeline / "notes.json"
        tick.save(notes, {"actions": ["Executed two controls"], "decisions": ["Evidence-based stop"]})
        tick.report("sample", token, notes)
        self.assertEqual(tick.complete("sample", token), 0)
        self.assertTrue(tick_efficiency.cooldown_active(self.pipeline.parent))
        self.assertFalse((self.headless / ".foreground.lockdir").exists())
        record = tick.load(self.pipeline / "tick_receipts" / (token + ".json"))
        self.assertEqual(record["outcomes"]["dispositions"]["rejected"], 2)
        tick.save(self.pipeline / "goal.json", {"metric": {"target": 0.7}})
        self.assertFalse(tick_efficiency.cooldown_active(self.pipeline.parent))


if __name__ == "__main__":
    unittest.main()
