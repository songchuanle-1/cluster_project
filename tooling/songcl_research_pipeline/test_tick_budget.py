"""Offline regressions for bounded admission and explicit research handoff."""
import copy
import contextlib
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import closure
import pipeline_monitor as monitor


class TickBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pipeline = self.root / "pipeline"
        for folder in ("headless", "reports", "admissions"):
            (self.pipeline / folder).mkdir(parents=True, exist_ok=True)
        self.write("pipeline/goal.json", {
            "pipeline_policy": {"research_on_capacity_gap": True}})
        (self.root / "evidence.json").write_text('{"actual_control": "observed"}')
        self.evidence = {"path": "evidence.json", "sha256": closure.digest(self.root / "evidence.json")}
        (self.pipeline / "reports/summary_test.md").write_text(
            "\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.pipeline / "codex_memory.md").write_text("\n".join("## " + s for s in sections))
        self.work = {"candidates": [self.candidate("a", "validation")]}
        self.queue = {"gpu_queues": {"server": []}}
        now = datetime.now(timezone.utc)
        self.context = {
            "generated_at": (now - timedelta(minutes=10)).isoformat(),
            "deadline_at": (now + timedelta(minutes=40)).isoformat(),
            "mode": "design", "preflight": {"monitor_rc": 0, "goal_rc": 0},
            "queue": {"candidate_budget": 1, "target_active": 3, "active_tasks": [],
                      "monitored_active_tasks": [], "recorded_ids": [],
                      "known_experiment_ids": [],
                      "servers": [{"name": "server", "allowed_gpus": [0, 1, 2]}]},
            "research_work": {"candidates": copy.deepcopy(self.work["candidates"])},
        }

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def candidate(self, cid, stage):
        return {"id": cid, "stage": stage, "next_action": "Run the frozen next native test",
                "evidence": [dict(self.evidence)]}

    def admit(self, cid="a", server="server"):
        task = {"id": cid, "config": f"configs/{cid}.yaml", "status": "waiting",
                "code_commit": "a" * 40, "admission_receipt": f"pipeline/admissions/{cid}.json"}
        self.write(task["admission_receipt"], {
            "id": cid, "config": task["config"], "code_commit": task["code_commit"],
            "goal_sha256": closure.digest(self.pipeline / "goal.json"),
            "decision": self.evidence,
            "gates": {name: {"passed": True, "evidence": [self.evidence]}
                      for name in closure.REQUIRED_GATES}})
        self.queue["gpu_queues"].setdefault(server, []).append(task)
        candidates = self.work["candidates"]
        existing = next((c for c in candidates if c["id"] == cid), None)
        if existing:
            existing["stage"] = "admission"
        else:
            candidates.append(self.candidate(cid, "admission"))
        return task

    def backlog(self):
        candidate = self.candidate("next", "diagnosis")
        self.work["candidates"].append(candidate)
        self.context["research_work"]["candidates"].append(copy.deepcopy(candidate))

    def handoff(self, reason="admission_budget_met", ids=None):
        self.work["tick_handoff"] = {
            "tick_started_at": self.context["generated_at"], "reason": reason,
            "candidate_ids": ["next"] if ids is None else ids,
            "resume_condition": "Resume the saved next_action in the next owning tick",
        }

    def finish(self):
        self.write("pipeline/headless/.tick_context.json", self.context)
        self.write("pipeline/research_work.json", self.work)
        self.write("pipeline/queue.json", self.queue)
        return closure.postflight(self.root)

    def test_one_valid_admission_meets_one_tick_budget_not_whole_capacity(self):
        self.admit()
        self.finish()

    def test_budget_met_allows_explicit_handoff_of_unchanged_backlog(self):
        self.backlog()
        self.admit()
        self.handoff()
        self.finish()

    def test_capacity_full_does_not_allow_exceeding_tick_admission_budget(self):
        self.context["queue"]["target_active"] = 2
        self.admit()
        self.admit("b")
        with self.assertRaisesRegex(ValueError, "admission budget"):
            self.finish()

    def test_short_run_archival_cannot_reset_the_admission_budget(self):
        (self.pipeline / "experiments").mkdir()
        self.write("pipeline/experiments/short-run.json", {"id": "short-run", "status": "done_complete"})
        self.admit()
        with self.assertRaisesRegex(ValueError, "admission budget"):
            self.finish()

    def test_old_training_archival_does_not_consume_this_tick_budget(self):
        (self.pipeline / "experiments").mkdir()
        self.context["queue"]["known_experiment_ids"] = ["old-run"]
        self.write("pipeline/experiments/old-run.json", {"id": "old-run", "status": "done_complete"})
        self.admit()
        self.finish()

    def test_known_record_with_legacy_filename_does_not_consume_budget(self):
        (self.pipeline / "experiments").mkdir()
        self.context["queue"].update(candidate_budget=0, known_experiment_ids=["tcff", "tclw"])
        for tid in ("tcff", "tclw"):
            self.write(f"pipeline/experiments/model_base_early_exit_4_tunet_{tid}.json",
                       {"id": tid, "status": "done_earlystop"})
        self.assertEqual(closure.tick_admission_delta(self.root, self.context, self.queue), (0, {}))
        self.assertEqual(closure.new_tick_experiments(self.root, self.context), {})

    def test_new_record_with_legacy_filename_still_consumes_budget(self):
        (self.pipeline / "experiments").mkdir()
        self.context["queue"]["candidate_budget"] = 0
        self.write("pipeline/experiments/model_base_new-run.json",
                   {"id": "new-run", "status": "done_complete"})
        with self.assertRaisesRegex(ValueError, "admission budget"):
            closure.tick_admission_delta(self.root, self.context, self.queue)

    def test_known_filename_cannot_hide_a_new_declared_identity(self):
        (self.pipeline / "experiments").mkdir()
        self.context["queue"].update(candidate_budget=0, known_experiment_ids=["old-run"])
        self.write("pipeline/experiments/old-run.json",
                   {"id": "new-run", "status": "done_complete"})
        with self.assertRaisesRegex(ValueError, "admission budget"):
            closure.tick_admission_delta(self.root, self.context, self.queue)

    def test_duplicate_new_archive_identity_cannot_be_silently_deduplicated(self):
        (self.pipeline / "experiments").mkdir()
        for name in ("first-name", "second-name"):
            self.write(f"pipeline/experiments/{name}.json",
                       {"id": "same-new-run", "status": "done_complete"})
        with self.assertRaisesRegex(ValueError, "Duplicate archived experiment identity"):
            closure.tick_admission_delta(self.root, self.context, self.queue)

    def test_handoff_requires_current_tick_reason_and_exact_preserved_ids(self):
        self.backlog()
        self.admit()
        for issue in ("missing", "old_tick", "bad_reason", "missing_id", "extra_id", "no_resume"):
            self.handoff()
            handoff = self.work["tick_handoff"]
            if issue == "missing":
                del self.work["tick_handoff"]
            elif issue == "old_tick":
                handoff["tick_started_at"] = "2026-01-01T00:00:00+00:00"
            elif issue == "bad_reason":
                handoff["reason"] = "enough_paperwork"
            elif issue == "missing_id":
                handoff["candidate_ids"] = []
            elif issue == "extra_id":
                handoff["candidate_ids"].append("unknown")
            else:
                handoff["resume_condition"] = ""
            with self.subTest(issue=issue), self.assertRaisesRegex(ValueError, "handoff"):
                self.finish()

    def test_handoff_never_skips_evidence_integrity(self):
        self.backlog()
        self.admit()
        self.handoff()
        path = self.root / "backlog_evidence.json"
        path.write_text('{"native_control": "original"}')
        entry = {"path": path.name, "sha256": closure.digest(path)}
        self.work["candidates"][-1]["evidence"] = [entry]
        self.context["research_work"]["candidates"][-1]["evidence"] = [dict(entry)]
        path.write_text('{"native_control": "altered"}')
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.finish()

    def test_handoff_never_silently_removes_candidate(self):
        self.backlog()
        self.admit()
        self.handoff()
        self.work["candidates"].pop()
        with self.assertRaises(ValueError):
            self.finish()

    def test_near_deadline_can_defer_untouched_work_after_real_progress(self):
        self.backlog()
        self.context["deadline_at"] = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
        self.work["candidates"][0]["stage"] = "implementation"
        self.handoff(reason="tick_deadline_near")
        self.finish()

    def test_deadline_handoff_does_not_allow_early_or_zero_progress_close(self):
        self.backlog()
        self.handoff(reason="tick_deadline_near", ids=["a", "next"])
        with self.assertRaises(ValueError):
            self.finish()
        self.context["deadline_at"] = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
        with self.assertRaisesRegex(ValueError, "progress"):
            self.finish()

    def test_ledger_stage_alone_cannot_satisfy_admission_target(self):
        self.backlog()
        self.work["candidates"][0]["stage"] = "admission"
        self.handoff()
        with self.assertRaises(ValueError):
            self.finish()

    def test_new_waiting_task_needs_all_real_admission_gates(self):
        task = self.admit()
        receipt = closure.read(self.root / task["admission_receipt"])
        receipt["gates"]["native_backward"]["passed"] = False
        self.write(task["admission_receipt"], receipt)
        with self.assertRaisesRegex(ValueError, "native_backward"):
            self.finish()

    def test_zero_budget_rejects_new_admission_in_event_mode(self):
        self.context["mode"] = "event"
        self.context["queue"]["candidate_budget"] = 0
        self.admit()
        with self.assertRaisesRegex(ValueError, "admission budget"):
            self.finish()

    def test_reserve_only_cannot_reactivate_an_old_inactive_queue_id(self):
        self.context["research_work"].update(reserve_only=True, reserve_budget=1)
        self.context["queue"].update(candidate_budget=0, recorded_ids=["a"])
        self.admit()
        with self.assertRaisesRegex(ValueError, "Reserve-only|admission budget"):
            self.finish()

    def test_existing_waiting_to_running_does_not_consume_new_budget(self):
        task = self.admit()
        before = dict(task, server="server")
        self.context["queue"].update(candidate_budget=0, recorded_ids=["a"],
                                     active_tasks=[before], monitored_active_tasks=[before])
        self.context["mode"] = "steady"
        task.update(status="running", launch_verified=True)
        self.finish()

    def test_training_without_native_progress_still_cannot_close(self):
        task = self.admit()
        task.update(status="claiming", launch_verification="pending_progress")
        with self.assertRaisesRegex(ValueError, "progress verification"):
            self.finish()

    def test_missing_launch_flag_cannot_disguise_a_new_unverified_run(self):
        task = self.admit()
        for status in ("running", "claiming"):
            task["status"] = status
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "progress verification"):
                self.finish()

    def test_reactivated_history_consumes_new_budget_without_renaming(self):
        self.context["queue"]["recorded_ids"] = ["a", "b"]
        self.admit()
        self.admit("b")
        with self.assertRaisesRegex(ValueError, "admission budget"):
            self.finish()

    def test_duplicate_queue_identity_cannot_fill_quota(self):
        task = self.admit()
        self.queue["gpu_queues"]["server"].append(dict(task))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.finish()

    def test_next_tick_does_not_inherit_old_handoff_permission(self):
        self.backlog()
        self.admit()
        self.handoff()
        self.finish()
        self.context["generated_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        self.context["research_work"]["candidates"] = copy.deepcopy(self.work["candidates"])
        self.context["queue"].update(recorded_ids=["a"], candidate_budget=1,
            monitored_active_tasks=[dict(self.queue["gpu_queues"]["server"][0], server="server")])
        # Refresh only the required report/memory, not the research evidence.
        for path in (self.pipeline / "reports/summary_test.md", self.pipeline / "codex_memory.md"):
            path.write_text(path.read_text())
        with self.assertRaisesRegex(ValueError, "no durable progress"):
            self.finish()

    def test_new_task_on_monitor_only_server_does_not_satisfy_quota(self):
        self.admit(server="monitor-only")
        with self.assertRaisesRegex(ValueError, "authorized|dispatch"):
            self.finish()

    def bind_owner(self):
        self.write("pipeline/headless/.tick_context.json", self.context)
        (self.pipeline / "headless/.foreground.lockdir").mkdir(exist_ok=True)
        self.write("pipeline/headless/.foreground.lockdir/owner.json", {
            "context_sha256": closure.digest(self.pipeline / "headless/.tick_context.json")})

    def test_dispatch_blocks_excess_before_sync_or_launch(self):
        self.admit()
        self.admit("b")
        self.bind_owner()
        with patch.object(monitor, "ssh", return_value="0, 0, 0, 80000"), \
                patch.object(monitor, "load_active_gpu_reservations", return_value={}), \
                patch.object(closure, "enabled", return_value=True), \
                patch.object(closure, "safe_sync") as sync, \
                patch.object(closure, "safe_launch") as launch, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            monitor._process_queue(self.queue, "server", "unused.invalid", "unused",
                                   str(self.root), set(), {"0"}, [])
        sync.assert_not_called()
        launch.assert_not_called()
        self.assertIn("admission budget exceeded", output.getvalue())
        self.assertTrue(all(t["status"] == "waiting" for t in self.queue["gpu_queues"]["server"]))

    def test_dispatch_does_not_reuse_old_snapshot_without_owned_lease(self):
        task = self.admit()
        self.admit("b")
        self.write("pipeline/headless/.tick_context.json", self.context)
        closure.validate_foreground_dispatch_budget(self.root, self.queue, task)
        (self.pipeline / "headless/.foreground.lockdir").mkdir()
        self.write("pipeline/headless/.foreground.lockdir/owner.json", {"token": "fresh-preflight"})
        closure.validate_foreground_dispatch_budget(self.root, self.queue, task)

    def test_dispatch_rejects_changed_bound_snapshot(self):
        task = self.admit()
        self.bind_owner()
        self.context["queue"]["candidate_budget"] = 100
        self.write("pipeline/headless/.tick_context.json", self.context)
        with self.assertRaisesRegex(ValueError, "snapshot"):
            closure.validate_foreground_dispatch_budget(self.root, self.queue, task)

    def test_dispatch_preserves_old_waiting_work_when_new_admissions_exceed_budget(self):
        existing = self.admit("old")
        self.context["queue"].update(recorded_ids=["old"],
            active_tasks=[dict(existing, server="server")],
            monitored_active_tasks=[dict(existing, server="server")])
        self.admit()
        self.admit("b")
        self.bind_owner()
        closure.validate_foreground_dispatch_budget(self.root, self.queue, existing)
        with self.assertRaisesRegex(ValueError, "admission budget"):
            closure.validate_foreground_dispatch_budget(
                self.root, self.queue, self.queue["gpu_queues"]["server"][-1])


if __name__ == "__main__":
    unittest.main()
