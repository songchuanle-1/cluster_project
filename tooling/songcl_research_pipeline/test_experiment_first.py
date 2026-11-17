import copy
import json
import os
import unittest
from datetime import datetime, timedelta, timezone

import closure
import experiment_first
import test_closure
import test_tick_context
import tick_efficiency


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return {"path": path.name, "sha256": closure.digest(path)}


def enable(root, **bounds):
    entry = write(root / "approval.json", {
        "scope": experiment_first.SCOPE, "project": root.name,
        "authorization_granted": True, "source_thread_id": "human-chat",
        "human_reply": "Use experiment-first", "resource_expansion": False})
    policy = dict(enabled=True, authorization=entry, **bounds)
    write(root / "pipeline/closure_policy.json", dict(enabled=True, experiment_first=policy))
    return experiment_first.effective(root)


class PolicyAndAdmissionTests(unittest.TestCase):
    setUp = test_closure.ClosureTests.setUp
    save = test_closure.ClosureTests.save

    def prepare(self):
        self.policy = enable(self.root)
        self.receipt.update(profile="experiment_first",
                            authorization=self.policy["authorization"])
        self.receipt["gates"] = {k: self.receipt["gates"][k] for k in experiment_first.GATES}
        self.smoke = {k: self.receipt[k] for k in ("id", "config", "code_commit", "goal_sha256")}
        self.smoke.update(steps=2, losses=[1.2, 1.1], native_data_loaded=True,
                          backward_finite=True, intended_path_observed=True,
                          split="train", command="native training smoke",
                          data_source="existing train dataset", evidence=[self.evidence])
        self.save_smoke()

    def save_smoke(self):
        self.receipt["native_smoke"] = write(self.root / "smoke.json", self.smoke)
        self.save()

    def test_approved_native_smoke_does_not_require_efficacy_gates(self):
        self.prepare()
        self.assertEqual(closure.admission(self.root, self.task)["profile"], "experiment_first")
        for name in experiment_first.GATES:
            previous = self.receipt["gates"].pop(name)
            self.save()
            with self.subTest(gate=name), self.assertRaisesRegex(ValueError, "Incomplete"):
                closure.admission(self.root, self.task)
            self.receipt["gates"][name] = previous

    def test_legacy_receipt_is_not_reinterpreted_by_opt_in(self):
        enable(self.root)
        del self.receipt["gates"]["diagnosis"]
        self.save()
        with self.assertRaisesRegex(ValueError, "diagnosis"):
            closure.admission(self.root, self.task)

    def test_native_smoke_rejects_unobserved_or_nonfinite_execution(self):
        self.prepare()
        baseline = copy.deepcopy(self.smoke)
        for field, bad in [("steps", 1), ("steps", True), ("losses", [1, float("nan")]),
                           ("losses", [True, 1]), ("backward_finite", False),
                           ("native_data_loaded", False), ("intended_path_observed", False),
                           ("split", "test"), ("split", "validation"), ("command", ""),
                           ("data_source", ""), ("evidence", []), ("code_commit", "b" * 40)]:
            self.smoke = dict(baseline, **{field: bad})
            self.save_smoke()
            with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                closure.admission(self.root, self.task)

    def test_authorization_is_project_bound_and_hash_checked(self):
        self.prepare()
        self.receipt["authorization"] = {"path": "another.json", "sha256": "a" * 64}
        self.save()
        with self.assertRaisesRegex(ValueError, "not authorized"):
            closure.admission(self.root, self.task)
        policy = enable(self.root)
        grant = closure.read(self.root / "approval.json")
        grant["project"] = "other_project"
        policy["authorization"] = write(self.root / "approval.json", grant)
        with self.assertRaisesRegex(ValueError, "scoped human"):
            experiment_first.validate_policy(self.root, policy)
        policy = enable(self.root)
        (self.root / "approval.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            experiment_first.validate_policy(self.root, policy)

    def test_inflight_legacy_snapshot_stays_legacy(self):
        self.prepare()
        headless = self.root / "pipeline/headless"
        context = headless / ".tick_context.json"
        write(context, {"mode": "design"})
        write(headless / ".foreground.lockdir/owner.json",
              {"context_sha256": closure.digest(context)})
        self.assertEqual(experiment_first.effective(self.root), {})
        with self.assertRaisesRegex(ValueError, "not authorized"):
            closure.admission(self.root, self.task)

    def test_snapshot_policy_is_immutable_but_artifact_must_still_match(self):
        policy = enable(self.root)
        headless = self.root / "pipeline/headless"
        context = headless / ".tick_context.json"
        write(context, {"experiment_first": policy})
        write(headless / ".foreground.lockdir/owner.json",
              {"context_sha256": closure.digest(context)})
        write(self.root / "pipeline/closure_policy.json", {"enabled": True})
        self.assertEqual(experiment_first.effective(self.root), policy)
        write(context, {"experiment_first": {}})
        with self.assertRaisesRegex(ValueError, "snapshot"):
            experiment_first.effective(self.root)

    def test_bad_bounds_fail_closed(self):
        for key in ("waiting_target", "actionable_limit", "max_new_candidates"):
            for bad in (-1, True, "2"):
                with self.subTest(key=key, value=bad), self.assertRaises(ValueError):
                    enable(self.root, **{key: bad})

    def test_new_profile_cannot_reopen_rejection_or_erase_revision_history(self):
        self.prepare()
        candidate = dict(id="test", stage="admission", next_action="dispatch", evidence=[self.evidence])
        context = {"experiment_first": self.policy, "research_work": {
            "candidates": [dict(candidate, stage="rejected")]}}
        with self.assertRaisesRegex(ValueError, "reopen authorization"):
            closure.validate_work(self.root, context, [candidate], {"gpu_queues": {}})

    def test_unknown_profile_is_not_accepted(self):
        self.receipt["profile"] = "skip_checks"
        self.save()
        with self.assertRaisesRegex(ValueError, "Unknown admission"):
            closure.admission(self.root, self.task)

    def test_task_config_remains_yaml_and_matches_the_tested_config(self):
        self.prepare()
        self.smoke["config"] = "configs/other.yaml"
        self.save_smoke()
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            closure.admission(self.root, self.task)
        for suffix in (".json", ".py", ""):
            self.smoke["config"] = self.receipt["config"] = self.task["config"] = "configs/test" + suffix
            self.save_smoke()
            with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError, "native YAML"):
                closure.admission(self.root, self.task)


class ContextTests(unittest.TestCase):
    setUp = test_tick_context.TickContextTest.setUp
    tearDown = test_tick_context.TickContextTest.tearDown
    build = test_tick_context.TickContextTest.build
    set_tasks = test_tick_context.TickContextTest.set_tasks
    set_capacity = test_tick_context.TickContextTest.set_capacity
    set_pipeline_policy = test_tick_context.TickContextTest.set_pipeline_policy
    commit = test_tick_context.TickContextTest.commit

    def test_full_gpus_still_prepare_two_waiting_experiments(self):
        enable(self.project)
        self.set_capacity(2)
        self.set_tasks([dict(id="running1", status="running"), dict(id="running2", status="running")])
        context = self.build()
        self.assertEqual(context["mode"], "design")
        self.assertEqual(context["queue"]["capacity"], 2)
        self.assertEqual(context["queue"]["candidate_budget"], 2)
        self.assertEqual(context["queue"]["target_active"], 4)
        self.assertFalse(context["research_work"]["reserve_only"])
        self.assertEqual(context["research_work"]["creation_budget"], 2)

    def test_many_blocked_candidates_do_not_fill_actionable_limit(self):
        enable(self.project)
        blocked = [dict(id=f"held{i}", stage="blocked", blocker_kind="human_authorization",
                        blocker="held", next_action="wait", unblock_condition="external reply",
                        retry_after=(datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
                        evidence=[{"path": "evidence.json", "sha256": "a" * 64}])
                   for i in range(9)]
        write(self.pipeline / "research_work.json", {"candidates": blocked})
        context = self.build()
        self.assertEqual(context["mode"], "design")
        self.assertEqual(context["research_work"]["pending_count"], 0)
        self.assertEqual(context["research_work"]["total_pending_count"], 9)
        self.assertEqual(context["research_work"]["creation_budget"], 2)
        self.assertEqual(context["research_work"]["parked_count"], 9)

    def test_waiting_holds_and_unmet_dependencies_do_not_count_as_ready(self):
        enable(self.project)
        self.set_tasks([dict(id="held", status="waiting", dispatch_hold="review"),
                        dict(id="bad", status="waiting", admission_error="bad evidence"),
                        dict(id="dep", status="waiting", depends_on=["absent"]),
                        dict(id="ready", status="waiting")])
        context = self.build()
        self.assertEqual(context["queue"]["waiting_count"], 4)
        self.assertEqual(context["queue"]["ready_waiting_count"], 1)
        self.assertEqual(context["queue"]["candidate_budget"], 2)
        self.assertEqual(context["research_work"]["pending_count"], 1)

    def test_completed_dependency_counts_as_ready(self):
        enable(self.project)
        self.set_tasks([dict(id="parent", status="done_complete"),
                        dict(id="child", status="waiting", depends_on=["parent"])])
        context = self.build()
        self.assertEqual(context["queue"]["ready_waiting_count"], 1)
        self.assertEqual(context["research_work"]["pending_count"], 1)

    def test_actionable_cap_bounds_new_creation_not_existing_progress(self):
        enable(self.project)
        write(self.pipeline / "research_work.json", {"candidates": [
            dict(id=f"work{i}", stage="implementation") for i in range(4)]})
        context = self.build()
        self.assertEqual(context["research_work"]["pending_count"], 4)
        self.assertEqual(context["research_work"]["creation_budget"], 0)
        self.assertGreater(context["queue"]["candidate_budget"], 0)
        self.assertEqual(context["mode"], "design")

    def test_respects_phase_capacity_and_explicit_project_limits(self):
        for settings in ({"max_candidates_per_design_tick": 0}, {"fill_to_capacity": False}):
            enable(self.project)
            self.set_pipeline_policy(**settings)
            context = self.build()
            self.assertEqual(context["queue"]["candidate_budget"], 0)
            self.assertEqual(context["research_work"]["creation_budget"], 0)
        self.set_pipeline_policy()
        for phase in (1, 4):
            context = self.build(goal_rc=phase)
            self.assertNotEqual(context["mode"], "design")
            self.assertEqual(context["queue"]["candidate_budget"], 0)
        self.set_capacity(0)
        context = self.build()
        self.assertEqual(context["queue"]["candidate_budget"], 0)
        self.assertEqual(context["research_work"]["creation_budget"], 0)

    def test_old_cooldown_does_not_suppress_new_opt_in(self):
        enable(self.project)
        self.build()
        self.commit()
        write(self.headless / ".research_cooldown.json", {
            "retry_after": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
            "signature": tick_efficiency.research_signature(self.project)})
        context = self.build()
        self.assertEqual(context["mode"], "design")
        self.assertFalse(context["changes"]["research_cooldown"])

    def test_full_ready_backlog_allows_quiet_polling(self):
        enable(self.project)
        self.set_tasks([dict(id="live", status="running"),
                        dict(id="next1", status="waiting"), dict(id="next2", status="waiting")])
        self.build()
        self.commit()
        context = self.build()
        self.assertEqual(context["mode"], "steady")
        self.assertEqual(context["queue"]["candidate_budget"], 0)
        view = tick_efficiency.compact_view(context)
        self.assertNotIn("design_bootstrap", view)
        self.assertIn("workflow", view)
        self.assertLessEqual(tick_efficiency.encoded_size(view), tick_efficiency.VIEW_LIMIT)


class OutcomeTests(unittest.TestCase):
    setUp = test_closure.ClosureTests.setUp

    def prepare(self):
        policy = enable(self.root)
        self.candidate = dict(id="test", stage="implementation", next_action="Fix implementation",
                              evidence=[self.evidence])
        old = dict(self.candidate, evidence=[])
        self.context = dict(mode="design", generated_at=(
            datetime.now(timezone.utc) - timedelta(seconds=2)).isoformat(),
            experiment_first=policy,
            research_work=dict(creation_budget=2, progress_baselines={
                "test": closure.candidate_progress(old)}, candidates=[old]))
        self.queue = {"gpu_queues": {}}
        self.attempt = dict(tick_started_at=self.context["generated_at"], candidate_id="test",
                            kind="implementation_test", result="failed", command="native test",
                            observation="shape mismatch on actual training input", evidence=[self.evidence])
        write(self.root / "pipeline/research_work.json",
              dict(candidates=[self.candidate], tick_attempt=self.attempt))

    def test_one_real_failure_finishes_without_exhausting_routes(self):
        self.prepare()
        experiment_first.validate_outcome(self.root, self.context, [self.candidate], self.queue)

    def test_stage_only_change_or_recycled_evidence_is_not_success(self):
        self.prepare()
        for field in ("tick_started_at", "candidate_id", "command", "observation", "evidence"):
            bad = dict(self.attempt, **{field: None})
            write(self.root / "pipeline/research_work.json", dict(tick_attempt=bad))
            with self.subTest(field=field), self.assertRaises(ValueError):
                experiment_first.validate_outcome(self.root, self.context, [self.candidate], self.queue)
        write(self.root / "pipeline/research_work.json", dict(tick_attempt=self.attempt))
        os.utime(self.root / "evidence.json", (1, 1))
        with self.assertRaisesRegex(ValueError, "old results"):
            experiment_first.validate_outcome(self.root, self.context, [self.candidate], self.queue)

    def test_untouched_backlog_need_not_be_rewritten(self):
        self.prepare()
        unchanged = dict(id="later", stage="validation", next_action="Next native test",
                         evidence=[self.evidence])
        self.context["research_work"]["candidates"].append(unchanged)
        closure.validate_work(self.root, self.context, [self.candidate, unchanged], self.queue)
        del self.context["experiment_first"]
        with self.assertRaisesRegex(ValueError, "no durable progress"):
            closure.validate_work(self.root, self.context, [self.candidate, unchanged], self.queue)

    def test_new_failed_candidates_are_also_bounded(self):
        self.prepare()
        candidates = [dict(self.candidate, id=str(i), stage="blocked") for i in range(3)]
        with self.assertRaisesRegex(ValueError, "creation budget"):
            experiment_first.validate_outcome(self.root, self.context, candidates, self.queue)

    def test_pending_limit_still_rejects_new_actionable_overflow(self):
        self.prepare()
        self.context["research_work"].update(
            pending_limit=1, pending_scope="actionable", pending_ids=["test"])
        candidates = [self.candidate, dict(self.candidate, id="blocked", stage="blocked")]
        closure.validate_pending_limit(self.context, candidates, self.queue)
        candidates.append(dict(self.candidate, id="extra"))
        with self.assertRaisesRegex(ValueError, "Pending candidate limit"):
            closure.validate_pending_limit(self.context, candidates, self.queue)

    def test_postflight_accepts_bounded_failure_but_not_fake_completion(self):
        self.prepare()
        self.context.update(preflight={"monitor_rc": 0, "goal_rc": 0})
        write(self.root / "pipeline/headless/.tick_context.json", self.context)
        write(self.root / "pipeline/queue.json", self.queue)
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text(
            "\n".join(f"## {i}. verified test" for i in range(6)), encoding="utf-8")
        names = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                 "Closed Or Failed Directions", "Running And Queue", "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text(
            "\n".join("## " + n for n in names), encoding="utf-8")
        closure.postflight(self.root)
        write(self.root / "pipeline/research_work.json", dict(candidates=[self.candidate]))
        with self.assertRaisesRegex(ValueError, "real current test"):
            closure.postflight(self.root)
        self.context["preflight"]["monitor_rc"] = 75
        write(self.root / "pipeline/headless/.tick_context.json", self.context)
        with self.assertRaisesRegex(ValueError, "Preflight failed"):
            closure.postflight(self.root)

    def test_pending_limit_rechecks_dependencies_completed_during_tick(self):
        self.prepare()
        self.context["research_work"].update(
            pending_limit=1, pending_scope="actionable", pending_ids=["test"])
        self.context["queue"] = {"dependency_states": {"parent": "running"}}
        self.queue["gpu_queues"]["server"] = [
            dict(id="next", status="waiting", depends_on=["parent"])]
        write(self.root / "pipeline/experiments/parent.json",
              dict(id="parent", status="done_complete"))
        with self.assertRaisesRegex(ValueError, "Pending candidate limit"):
            closure.validate_pending_limit(
                self.context, [self.candidate], self.queue, self.root)


if __name__ == "__main__":
    unittest.main()
