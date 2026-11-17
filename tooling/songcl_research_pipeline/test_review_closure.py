"""Offline regressions for historical permissions and same-tick archival."""
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

import closure
import pipeline_monitor as monitor
import test_closure as revision_fixtures
import test_tick_budget as budget_fixtures
import test_tick_context as context_fixtures


class HistoricalPermissionTests(unittest.TestCase):
    def setUp(self):
        self.case = revision_fixtures.ClosureTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def validate(self, candidate, previous):
        context = {"research_work": {
            "candidates": [], "revision_baselines": {previous["id"]: previous}}}
        closure.validate_work(self.case.root, context, [candidate], {"gpu_queues": {}})

    def completed(self):
        candidate, _ = self.case.authorized_third_revision()
        candidate.update(stage="complete", next_action="Preserve the tested outcome",
                         evidence=[self.case.evidence])
        candidate["revision_history"][-1].update(
            result="failed", evidence=[self.case.evidence])
        self.validate(candidate, copy.deepcopy(candidate))
        return candidate, copy.deepcopy(candidate)

    def change_goal(self, **policy):
        (self.case.root / "pipeline/goal.json").write_text(json.dumps(
            {"description": "Updated description", "pipeline_policy": policy}))

    def test_rejected_without_revisions_still_needs_reopen_authorization(self):
        before = dict(id="old", stage="rejected", failure_scope="hypothesis",
                      hypothesis="original", next_action="Keep negative evidence",
                      evidence=[self.case.evidence])
        for stage in ("diagnosis", "implementation", "admission", "complete", "blocked"):
            with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, "reopen authorization"):
                self.validate(dict(before, stage=stage), before)
        current = dict(before, stage="implementation", reopen_authorization=self.case.evidence)
        self.validate(current, before)
        self.validate(before, before)

    def test_closed_without_revisions_still_needs_reopen_authorization(self):
        previous = dict(id="old", stage="closed")
        with self.assertRaisesRegex(ValueError, "reopen authorization"):
            closure.validate_revisions(self.case.root, dict(previous, stage="diagnosis"), previous)

    def test_dispatch_admission_checks_reopening_before_launch(self):
        c = self.case
        candidate = dict(id="test", stage="admission", next_action="Run verified candidate",
                         evidence=[c.evidence])
        (c.root / "pipeline/research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        headless = c.root / "pipeline/headless"
        (headless / ".foreground.lockdir").mkdir(parents=True)
        context = {"research_work": {"revision_baselines": {
            "test": dict(candidate, stage="rejected")}}}
        (headless / ".tick_context.json").write_text(json.dumps(context))
        (headless / ".foreground.lockdir/owner.json").write_text(json.dumps({
            "context_sha256": closure.digest(headless / ".tick_context.json")}))
        c.save()
        with self.assertRaisesRegex(ValueError, "reopen authorization"):
            closure.admission(c.root, c.task)
        candidate["reopen_authorization"] = c.evidence
        (c.root / "pipeline/research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        closure.admission(c.root, c.task)

    def test_rejected_candidate_cannot_admit_without_revision_history(self):
        c = self.case
        (c.root / "pipeline/research_work.json").write_text(json.dumps(
            {"candidates": [{"id": "test", "stage": "rejected"}]}))
        c.save()
        with self.assertRaisesRegex(ValueError, "candidate stage"):
            closure.admission(c.root, c.task)

    def test_completed_grant_survives_goal_owner_and_default_changes(self):
        candidate, previous = self.completed()
        self.change_goal(max_implementation_revisions=1)
        (self.case.root / "pipeline/execution_mode.json").write_text(
            json.dumps({"target_thread_id": "new-owner"}))
        self.validate(candidate, previous)

    def test_preserved_grant_does_not_allow_new_revision_or_stage(self):
        candidate, previous = self.completed()
        self.change_goal()
        for change in ("revision", "stage", "pending", "missing_baseline"):
            current, before = copy.deepcopy(candidate), copy.deepcopy(previous)
            if change == "revision":
                current["revision_history"].append(self.case.revision(4))
            elif change == "stage":
                current["stage"] = "implementation"
            elif change == "pending":
                current["revision_history"][-1]["result"] = "pending"
                before = copy.deepcopy(current)
            else:
                before.pop("implementation_revision_authorization")
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(current, before)
        # Admission callers do not have a historical preservation exception.
        with self.assertRaises(ValueError):
            closure.validate_revisions(self.case.root, candidate)

    def test_preserved_grant_still_checks_content_history_and_hypothesis(self):
        candidate, previous = self.completed()
        self.change_goal()
        for change in ("result", "hypothesis", "authorization"):
            current = copy.deepcopy(candidate)
            if change == "result":
                current["revision_history"][-1]["result"] = "passed"
            elif change == "hypothesis":
                current["hypothesis"] = "replacement mechanism"
            else:
                (self.case.root / "permission.json").write_text("{}")
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.validate(current, previous)

    def test_context_binds_historical_authorization_reference(self):
        fixture = context_fixtures.TickContextTest()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        candidate, _ = self.completed()
        (fixture.pipeline / "research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        context = fixture.build()
        previous = context["research_work"]["revision_baselines"][candidate["id"]]
        self.assertEqual(previous.get("implementation_revision_authorization"),
                         candidate["implementation_revision_authorization"])


class ArchivedAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.case = budget_fixtures.TickBudgetTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def archive(self, state="done_complete", current_proof=True):
        c = self.case
        task = c.admit()
        task.update(status="running", launch_verified=True,
                    launch_verification="training_progress", gpu="0")
        c.write("pipeline/research_work.json", c.work)
        closure.admission(c.root, task)
        monitor.save_experiment(str(c.root), dict(
            id="a", config=task["config"], server="server", gpu="0",
            status="running", launch_verified=True,
            launch_verification="training_progress", history=[]))
        if not current_proof:
            task.pop("launch_verified")
            task.pop("launch_verification")
        with patch.object(monitor, "ledger_append"), patch.object(monitor, "write_analysis_md"):
            monitor.finalize_task(
                str(c.root), c.queue, "server", "unused.invalid", "unused", task, "a",
                state, 0.7, "1/1", "0", "", [])
        c.work["candidates"][0]["stage"] = "complete"
        c.write("pipeline/research_work.json", c.work)
        return closure.read(c.pipeline / "experiments/a.json")

    def test_successful_archive_credits_quota_and_preserves_budget(self):
        c = self.case
        c.backlog()
        archive = self.archive()
        self.assertEqual(archive.get("code_commit"), "a" * 40)
        self.assertEqual(archive.get("admission_receipt"), "pipeline/admissions/a.json")
        self.assertTrue(closure.validate_tick_admissions(c.root, c.context, c.queue))
        c.handoff()
        c.finish()
        c.admit("b")
        with self.assertRaisesRegex(ValueError, "admission budget exceeded"):
            c.finish()

    def test_earlystop_counts_but_crash_and_unknown_do_not(self):
        c = self.case
        archive = self.archive()
        for state in ("done_earlystop", "crashed", "stopped_unknown"):
            archive["status"] = state
            c.write("pipeline/experiments/a.json", archive)
            with self.subTest(state=state):
                self.assertEqual(closure.validate_tick_admissions(c.root, c.context, c.queue),
                                 state == "done_earlystop")

    def test_archive_requires_verified_identity_receipt_and_authorized_server(self):
        c = self.case
        archive = self.archive()
        for key, value in (("id", "other"), ("archive_id", None),
                           ("launch_verified", False), ("admission_receipt", None),
                           ("code_commit", "b" * 40), ("server", "monitor-only")):
            c.write("pipeline/experiments/a.json", dict(archive, **{key: value}))
            with self.subTest(field=key), self.assertRaises(ValueError):
                closure.validate_tick_admissions(c.root, c.context, c.queue)

    def test_incomplete_archive_cannot_credit_a_successful_tick(self):
        c = self.case
        self.archive()
        journal = c.pipeline / "archive_pending" / (
            hashlib.sha256(b"a").hexdigest() + ".json")
        journal.write_text("{}")
        with self.assertRaisesRegex(ValueError, "archiv"):
            closure.validate_tick_admissions(c.root, c.context, c.queue)

    def test_old_run_proof_cannot_certify_a_different_current_run(self):
        c = self.case
        archive = self.archive(current_proof=False)
        self.assertNotIn("launch_verified", archive)
        with self.assertRaisesRegex(ValueError, "verified launch"):
            closure.validate_tick_admissions(c.root, c.context, c.queue)

    def test_archive_keeps_all_gate_hash_checks(self):
        c = self.case
        self.archive()
        (c.root / "evidence.json").write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            closure.validate_tick_admissions(c.root, c.context, c.queue)

    def test_completed_revised_candidate_can_credit_but_cannot_relaunch(self):
        c = self.case
        self.archive()
        revision = dict(
            revision=1, failure_scope="implementation", reason="Frozen defect",
            change="Frozen local repair", prediction="Native control holds",
            preregistered_at="2026-01-01T00:00:00+00:00",
            failure_evidence=[c.evidence], result="passed", evidence=[c.evidence])
        c.work["candidates"][0]["revision_history"] = [revision]
        c.write("pipeline/research_work.json", c.work)
        receipt = closure.read(c.pipeline / "admissions/a.json")
        receipt.update(candidate_id="a",
                       implementation_revision_sha256=closure.revision_digest(revision))
        c.write("pipeline/admissions/a.json", receipt)
        self.assertTrue(closure.validate_tick_admissions(c.root, c.context, c.queue))
        task = closure.read(c.pipeline / "experiments/a.json")
        with self.assertRaisesRegex(ValueError, "current passed"):
            closure.admission(c.root, dict(task, status="waiting"))

    def test_archive_and_live_queue_entry_do_not_double_count(self):
        c = self.case
        archive = self.archive()
        c.queue["gpu_queues"]["server"].append(archive)
        self.assertTrue(closure.validate_tick_admissions(c.root, c.context, c.queue))

    def test_old_archive_is_not_a_new_admission(self):
        c = self.case
        self.archive()
        c.context["queue"]["known_experiment_ids"] = ["a"]
        self.assertFalse(closure.validate_tick_admissions(c.root, c.context, c.queue))


if __name__ == "__main__":
    unittest.main()
