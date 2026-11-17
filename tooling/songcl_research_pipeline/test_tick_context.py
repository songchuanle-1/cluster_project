#!/usr/bin/env python
"""Focused tests for compact tick context mode transitions."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone
import tick_efficiency
import build_tick_context as builder


SKILL_DIR = Path(__file__).resolve().parent
BUILDER = SKILL_DIR / "build_tick_context.py"
REPORTER = SKILL_DIR / "render_steady_report.py"


class TickContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.project = self.root / "demo_project"
        self.pipeline = self.project / "pipeline"
        self.headless = self.pipeline / "headless"
        for name in (
            "headless",
            "reports",
            "decisions",
            "analyses",
            "designs",
            "reviews",
            "bugfixes",
        ):
            (self.pipeline / name).mkdir(parents=True, exist_ok=True)
        (self.project / "SERVERS.yaml").write_text(
            "servers:\n"
            "  server-1:\n"
            "    role: gpu_server\n"
            "    allowed_gpus: [0]\n"
            "    max_tasks_per_gpu: 1\n",
            encoding="utf-8",
        )
        (self.pipeline / "goal.json").write_text(
            json.dumps(
                {
                    "metric": {"name": "mIoU", "target": 0.5},
                    "description": "test",
                    "constraints": [],
                    "banned": [],
                }
            ),
            encoding="utf-8",
        )
        (self.pipeline / "queue.json").write_text(
            json.dumps({"gpu_queues": {"server-1": []}}),
            encoding="utf-8",
        )
        (self.pipeline / "running.json").write_text("{}\n", encoding="utf-8")
        (self.pipeline / "experiments.csv").write_text(
            "id,config,server,gpu,state,best_miou,epochs,finished_at\n",
            encoding="utf-8",
        )
        (self.pipeline / "codex_memory.md").write_text(
            "# Codex Research Memory\n", encoding="utf-8"
        )
        self.monitor = self.headless / "monitor.txt"
        self.goal = self.headless / "goal.txt"
        self.monitor.write_text("monitor ok\n", encoding="utf-8")
        self.goal.write_text("goal ok\n", encoding="utf-8")
        self.env = dict(os.environ, PROJECT_ROOT=str(self.root))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def build(
        self,
        force_design: bool = False,
        design_interval_hours: float | None = None,
        goal_rc: int = 0,
    ) -> dict:
        command = [
            sys.executable,
            str(BUILDER),
            "demo_project",
            "--monitor-file",
            str(self.monitor),
            "--goal-file",
            str(self.goal),
            "--goal-rc", str(goal_rc),
        ]
        if force_design:
            command.append("--force-design")
        if design_interval_hours is not None:
            command.extend(
                ["--design-interval-hours", str(design_interval_hours)]
            )
        subprocess.run(
            command,
            check=True,
            env=self.env,
            capture_output=True,
            text=True,
        )
        return json.loads(
            (self.headless / ".tick_context.json").read_text(encoding="utf-8")
        )

    def set_capacity(self, capacity: int) -> None:
        allowed = ", ".join(str(index) for index in range(capacity))
        (self.project / "SERVERS.yaml").write_text(
            "servers:\n"
            "  server-1:\n"
            "    role: gpu_server\n"
            f"    allowed_gpus: [{allowed}]\n"
            "    max_tasks_per_gpu: 1\n",
            encoding="utf-8",
        )

    def set_tasks(self, tasks: list[dict]) -> None:
        (self.pipeline / "queue.json").write_text(
            json.dumps({"gpu_queues": {"server-1": tasks}}),
            encoding="utf-8",
        )

    def set_pipeline_policy(self, **policy: object) -> None:
        goal = json.loads(
            (self.pipeline / "goal.json").read_text(encoding="utf-8")
        )
        goal["pipeline_policy"] = policy
        (self.pipeline / "goal.json").write_text(
            json.dumps(goal),
            encoding="utf-8",
        )

    def commit(self) -> None:
        shutil.move(
            self.headless / ".tick_context_state.next.json",
            self.headless / ".tick_context_state.json",
        )

    def test_valid_cooldown_uses_steady_but_due_work_and_goal_changes_wake(self):
        self.set_pipeline_policy(research_on_capacity_gap=True)
        self.build()
        self.commit()
        (self.pipeline / "closure_policy.json").write_text('{"enabled": true}')
        work = {"candidates": [{"id": "blocked", "stage": "blocked",
                               "retry_after": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()}]}
        (self.pipeline / "research_work.json").write_text(json.dumps(work))
        def cooldown():
            (self.headless / ".research_cooldown.json").write_text(json.dumps({
                "retry_after": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                "signature": tick_efficiency.research_signature(self.project)}))
        cooldown()
        context = self.build()
        self.assertEqual(context["mode"], "steady")
        self.assertTrue(context["changes"]["research_cooldown"])
        self.assertEqual(context["changes"]["steady_ticks"], 1)
        # Even a matching signature may not suppress a retry that is already due.
        work["candidates"][0]["retry_after"] = "2026-01-01T00:00:00+00:00"
        (self.pipeline / "research_work.json").write_text(json.dumps(work))
        cooldown()
        self.assertEqual(self.build()["mode"], "design")
        (self.pipeline / "research_work.json").write_text('{"candidates": []}')
        cooldown()
        self.assertEqual(self.build()["mode"], "steady")
        self.set_pipeline_policy(research_on_capacity_gap=True, design_buffer=1)
        self.assertEqual(self.build()["mode"], "design")

    def test_historical_closed_records_do_not_bypass_valid_cooldown(self):
        self.set_pipeline_policy(research_on_capacity_gap=True)
        self.build()
        self.commit()
        (self.pipeline / "closure_policy.json").write_text('{"enabled": true}')
        (self.pipeline / "research_work.json").write_text(json.dumps({
            "candidates": [{"id": "legacy", "stage": "closed",
                            "next_action": "Preserve terminal record"}],
        }))
        (self.headless / ".research_cooldown.json").write_text(json.dumps({
            "retry_after": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "signature": tick_efficiency.research_signature(self.project),
        }))
        context = self.build()
        self.assertEqual(context["research_work"]["due_ids"], [])
        self.assertEqual(context["mode"], "steady")
        self.assertTrue(context["changes"]["research_cooldown"])

    def test_same_goal_phase_four_does_not_trigger_endless_events(self):
        self.build()
        self.commit()
        state_path = self.headless / ".tick_context_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["goal_rc"] = 4
        state_path.write_text(json.dumps(state))
        subprocess.run([sys.executable, "-B", str(BUILDER), "demo_project", "--goal-rc", "4"],
                       env=self.env, check=True, capture_output=True)
        context = json.loads((self.headless / ".tick_context.json").read_text(encoding="utf-8"))
        self.assertEqual(context["mode"], "steady")

    def test_bootstrap_steady_design_and_report(self) -> None:
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.commit()

        second = self.build()
        self.assertEqual(second["mode"], "steady")
        self.assertEqual(second["changes"]["steady_ticks"], 1)
        subprocess.run(
            [sys.executable, str(REPORTER), "demo_project"],
            check=True,
            env=self.env,
            capture_output=True,
            text=True,
        )
        report = max((self.pipeline / "reports").glob("summary_*.md"))
        report_text = report.read_text(encoding="utf-8")
        for section in range(6):
            self.assertIn(f"## {section}.", report_text)
        self.commit()

        third = self.build()
        self.assertEqual(third["mode"], "design")
        self.assertEqual(third["changes"]["steady_ticks"], 2)
        self.assertEqual(third["queue"]["candidate_budget"], 1)

    def test_uncommitted_state_replays_event(self) -> None:
        first = self.build()
        self.assertEqual(first["mode"], "event")
        second = self.build()
        self.assertEqual(second["mode"], "event")
        self.assertIn("context_bootstrap", second["changes"]["reasons"])

    def test_force_design_skips_steady_wait_and_cooldown(self) -> None:
        context = self.build(force_design=True)
        self.assertEqual(context["mode"], "design")
        self.assertTrue(context["changes"]["force_design"])
        self.assertEqual(context["queue"]["candidate_budget"], 1)
        self.assertIn("user-forced design", context["mode_reason"])

    def test_project_policy_overrides_global_design_interval(self) -> None:
        self.set_pipeline_policy(
            steady_ticks_before_design=1,
            design_interval_hours=1,
        )
        first = self.build(design_interval_hours=6)
        self.assertEqual(first["mode"], "event")
        self.commit()

        second = self.build(design_interval_hours=6)
        self.assertEqual(second["mode"], "design")
        self.assertEqual(second["changes"]["design_interval_hours"], 1.0)

    def advance_to_design_check(self) -> dict:
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.commit()
        second = self.build()
        self.assertEqual(second["mode"], "steady")
        self.commit()
        return self.build()

    def test_full_capacity_with_running_task_needs_no_design(self) -> None:
        self.set_tasks(
            [
                {
                    "id": "active-1",
                    "config": "configs/active.yaml",
                    "status": "running",
                    "gpu": 0,
                }
            ]
        )
        third = self.advance_to_design_check()
        self.assertEqual(third["mode"], "steady")
        self.assertEqual(third["queue"]["active_count"], 1)
        self.assertEqual(third["queue"]["candidate_budget"], 0)
        self.assertFalse(third["changes"]["design_due"])

    def test_full_capacity_prepares_reserve_without_increasing_admission_budget(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        self.set_pipeline_policy(research_on_capacity_gap=True)
        self.set_tasks([{"id": "run", "status": "running", "gpu": 0}])
        context = self.build()
        self.assertEqual(context["mode"], "design")
        self.assertEqual(context["queue"]["candidate_budget"], 0)
        self.assertEqual(context["research_work"]["reserve_budget"], 1)
        self.assertTrue(context["research_work"]["reserve_only"])
        self.assertEqual(context["queue"]["recorded_ids"], ["run"])
        view = tick_efficiency.compact_view(context)
        self.assertTrue(view["design_bootstrap"]["reserve_only"])
        self.assertEqual(view["research"]["reserve_target"], 2)

    def test_reserve_counts_blocked_and_queued_candidates_once(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        self.set_pipeline_policy(research_on_capacity_gap=True)
        self.set_tasks([{"id": "waiting", "status": "waiting", "gpu": 0}])
        (self.pipeline / "research_work.json").write_text(json.dumps(dict(candidates=[
            dict(id="stable", experiment_id="waiting", stage="admission"),
            dict(id="blocked", stage="blocked",
                 retry_after="2099-01-01T00:00:00+00:00") ])))
        context = self.build()
        self.assertEqual(context["research_work"]["reserve_count"], 2)
        self.assertEqual(context["research_work"]["reserve_budget"], 0)
        self.assertFalse(context["research_work"]["reserve_only"])

    def test_reserve_respects_explicit_zero_phase_hold_and_disabled_closure(self):
        self.set_pipeline_policy(research_on_capacity_gap=True)
        self.set_tasks([{"id": "run", "status": "running", "gpu": 0}])
        self.assertEqual(self.build()["research_work"]["reserve_target"], 0)
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        self.assertEqual(self.build(goal_rc=4)["research_work"]["reserve_target"], 0)
        self.set_pipeline_policy(research_on_capacity_gap=True, research_reserve_target=0)
        context = self.build()
        self.assertEqual(context["research_work"]["reserve_target"], 0)
        self.assertNotEqual(context["mode"], "design")

    def prepare_blocked_reserve(self, pending_limit=2):
        self.set_capacity(2)
        self.set_pipeline_policy(research_on_capacity_gap=True,
                                 research_pending_limit=pending_limit)
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        (self.pipeline / "authorizations").mkdir(exist_ok=True)
        evidence = self.pipeline / "analyses/native.json"
        evidence.write_text('{"observed": true}', encoding="utf-8")
        entry = {"path": "pipeline/analyses/native.json",
                 "sha256": builder.hash_file(evidence)}
        retry = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        candidates = [dict(id=f"legacy-{i}", stage="closed") for i in range(12)]
        candidates += [dict(
            id=f"ready-{i}", stage="blocked", blocker_kind="human_authorization",
            blocker="Exact tested code needs scoped commit authorization",
            retry_after=retry, unblock_condition="Explicit scoped authorization",
            next_action=f"Authorize only the tested files for ready-{i}",
            wake_paths=[f"pipeline/authorizations/ready-{i}.json"],
            evidence=[entry]) for i in range(2)]
        (self.pipeline / "research_work.json").write_text(
            json.dumps({"candidates": candidates}), encoding="utf-8")
        return candidates

    def test_pending_limit_waits_without_bootstrap_or_history_changes(self):
        self.prepare_blocked_reserve()
        work_path = self.pipeline / "research_work.json"
        original = work_path.read_bytes()
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.assertTrue(first["research_work"]["deferred"])
        self.assertEqual(first["queue"]["candidate_budget"], 2)
        self.assertEqual(first["research_work"]["reserve_budget"], 0)
        self.assertEqual(first["research_work"]["due_ids"], [])
        self.assertEqual(len(first["research_work"]["human_actions"]), 2)
        self.assertNotIn("design_bootstrap", tick_efficiency.compact_view(first))
        self.commit()
        second = self.build()
        self.assertEqual(second["mode"], "steady")
        self.assertTrue(second["research_work"]["deferred"])
        self.assertFalse(second["changes"]["design_due"])
        self.assertEqual(work_path.read_bytes(), original)

    def test_blocked_wait_does_not_turn_old_unhealthy_marker_into_design(self):
        self.prepare_blocked_reserve()
        (self.headless / ".tick_unhealthy").write_text("old no-progress abort")
        context = self.build()
        self.assertEqual(context["mode"], "event")
        self.assertTrue(context["research_work"]["deferred"])
        self.assertIn("previous_tick_unhealthy", context["changes"]["reasons"])
        self.assertNotIn("design_bootstrap", tick_efficiency.compact_view(context))

    def test_blocked_wait_wakes_on_authorization_intake(self):
        self.prepare_blocked_reserve()
        self.build()
        self.commit()
        (self.pipeline / "authorizations/ready-0.json").write_text('{"confirmed":true}')
        context = self.build()
        self.assertFalse(context["research_work"]["deferred"])
        self.assertEqual(context["research_work"]["due_ids"], ["ready-0"])
        self.assertEqual(context["mode"], "event")
        self.assertNotIn("design_bootstrap", tick_efficiency.compact_view(context))

    def test_blocked_wait_wakes_on_due_retry(self):
        candidates = self.prepare_blocked_reserve()
        self.build()
        self.commit()
        candidates[-2]["retry_after"] = "2026-01-01T00:00:00+00:00"
        (self.pipeline / "research_work.json").write_text(json.dumps({"candidates": candidates}))
        context = self.build()
        self.assertFalse(context["research_work"]["deferred"])
        self.assertEqual(context["research_work"]["due_ids"], ["ready-0"])
        self.assertEqual(context["mode"], "event")

    def test_blocked_wait_wakes_on_goal_and_server_changes(self):
        self.prepare_blocked_reserve()
        self.build()
        self.commit()
        self.set_pipeline_policy(research_on_capacity_gap=True, design_buffer=1,
                                 research_pending_limit=2)
        goal_change = self.build()
        self.assertEqual(goal_change["research_work"]["due_ids"], ["ready-0", "ready-1"])
        self.assertEqual(goal_change["mode"], "event")
        self.commit()
        self.set_capacity(1)
        server_change = self.build()
        self.assertEqual(server_change["research_work"]["due_ids"], ["ready-0", "ready-1"])
        self.assertEqual(server_change["mode"], "event")

    def test_blocked_wait_surfaces_changed_evidence_even_without_wake_path(self):
        self.prepare_blocked_reserve()
        self.build()
        self.commit()
        self.assertEqual(self.build()["mode"], "steady")
        self.commit()
        (self.pipeline / "analyses/native.json").write_text('{"observed": false}')
        context = self.build()
        self.assertEqual(context["mode"], "event")
        self.assertIn("blocked_wait_changed", context["changes"]["reasons"])

    def test_blocked_wait_cannot_hide_unknown_or_executable_work(self):
        candidates = self.prepare_blocked_reserve()
        candidates[-1]["blocker_kind"] = "unknown"
        path = self.pipeline / "research_work.json"
        path.write_text(json.dumps({"candidates": candidates}))
        unknown = self.build()
        self.assertFalse(unknown["research_work"]["deferred"])
        self.assertEqual(unknown["mode"], "design")
        candidates[-1]["stage"] = "validation"
        path.write_text(json.dumps({"candidates": candidates}))
        executable = self.build()
        self.assertFalse(executable["research_work"]["deferred"])
        self.assertEqual(executable["research_work"]["due_ids"], ["ready-1"])

    def test_force_design_cannot_bypass_pending_limit(self):
        self.prepare_blocked_reserve()
        context = self.build(force_design=True)
        self.assertTrue(context["research_work"]["deferred"])
        self.assertEqual(context["mode"], "event")
        self.assertNotIn("design_bootstrap", tick_efficiency.compact_view(context))

    def test_scope_holds_do_not_fill_actionable_reserve(self):
        candidates = self.prepare_blocked_reserve()
        self.set_pipeline_policy(research_on_capacity_gap=True)
        candidates += [dict(candidates[-1], id=f"scope-{i}") for i in range(2)]
        path = self.pipeline / "research_work.json"
        path.write_text(json.dumps({"candidates": candidates}))
        original = path.read_bytes()
        context = self.build()
        research = context["research_work"]
        self.assertEqual(context["mode"], "design")
        self.assertEqual((research["reserve_count"], research["reserve_budget"]), (0, 2))
        self.assertEqual((research["pending_count"], research["pending_limit"]), (4, 8))
        self.assertEqual(research["human_wait_count"], 4)
        self.assertEqual(research["due_ids"], [])
        self.assertFalse(research["deferred"])
        self.assertTrue(tick_efficiency.compact_view(context)["design_bootstrap"]["required"])
        self.assertEqual(path.read_bytes(), original)

    def test_numerical_holds_do_not_fill_actionable_reserve(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        candidates += [dict(candidates[-1], id=f"scope-{i}") for i in range(3)]
        candidates += [dict(candidates[-1], id=f"numeric-{i}",
                            blocker_kind="numerical_control_failure",
                            failure_scope="implementation") for i in range(2)]
        path = self.pipeline / "research_work.json"
        path.write_text(json.dumps({"candidates": candidates}))
        original = path.read_bytes()
        context = self.build()
        research = context["research_work"]
        self.assertEqual(research["reserve_count"], 0)
        self.assertEqual(research["reserve_budget"], 1)
        self.assertEqual(research["pending_count"], 7)
        self.assertEqual(research["research_wait_count"], 2)
        self.assertEqual(research["unclassified_block_count"], 0)
        self.assertTrue(tick_efficiency.compact_view(context)["design_bootstrap"]["required"])
        self.assertEqual(path.read_bytes(), original)

    def test_due_human_checks_do_not_suppress_independent_design_bootstrap(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        for candidate in candidates[-2:]:
            candidate["retry_after"] = "2026-01-01T00:00:00+00:00"
        (self.pipeline / "research_work.json").write_text(json.dumps({"candidates": candidates}))
        context = self.build()
        self.assertEqual(context["research_work"]["due_ids"], ["ready-0", "ready-1"])
        self.assertTrue(tick_efficiency.compact_view(context)["design_bootstrap"]["required"])

    def test_executable_due_candidates_precede_blocked_rechecks(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        for candidate in candidates[-2:]:
            candidate["retry_after"] = "2026-01-01T00:00:00+00:00"
        candidates += [dict(candidates[-1], id="first-test", stage="diagnosis"),
                       dict(candidates[-1], id="near-admission", stage="validation")]
        (self.pipeline / "research_work.json").write_text(json.dumps({"candidates": candidates}))
        context = self.build()
        expected = ["near-admission", "first-test", "ready-0", "ready-1"]
        self.assertEqual(context["research_work"]["due_ids"], expected)
        view = tick_efficiency.compact_view(context)
        self.assertEqual(view["research"]["shown"][0]["id"], "near-admission")
        self.assertEqual(tick_efficiency.candidate_page(context)["ids"], expected)
        self.assertNotIn("design_bootstrap", view)

    def test_numerical_holds_require_valid_evidence_and_local_failure_scope(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        candidate = dict(candidates[-1], blocker_kind="numerical_control_failure",
                         failure_scope="implementation")
        for change in (dict(failure_scope="hypothesis"), dict(evidence=[]),
                       dict(evidence=[{"path": "missing.json", "sha256": "a" * 64}])):
            with self.subTest(change=change):
                candidates[-1] = dict(candidate, **change)
                (self.pipeline / "research_work.json").write_text(
                    json.dumps({"candidates": candidates}))
                context = self.build()
                self.assertEqual(context["research_work"]["reserve_count"], 1)
                self.assertEqual(context["research_work"]["unclassified_block_count"], 1)

    def test_numerical_hold_rechecks_back_off_but_new_evidence_wakes(self):
        candidate = self.prepare_blocked_reserve(pending_limit=8)[-1]
        candidate.update(blocker_kind="numerical_control_failure",
                         failure_scope="inconclusive",
                         retry_after="2026-01-01T00:00:00+00:00")
        now = datetime.now(timezone.utc)
        signals = dict(goal="goal", servers="servers", queue=[])
        due, state = builder.blocked_recheck(self.project, candidate, {}, signals, now)
        self.assertTrue(due)
        self.assertFalse(builder.blocked_recheck(
            self.project, candidate, state, signals, now + timedelta(hours=1))[0])
        new_result = self.pipeline / "analyses/new.json"
        new_result.write_text('{"new_discriminating_observation": true}')
        candidate["evidence"].append({"path": "pipeline/analyses/new.json",
                                      "sha256": builder.hash_file(new_result)})
        self.assertTrue(builder.blocked_recheck(
            self.project, candidate, state, signals, now + timedelta(minutes=1))[0])

    def test_numerical_holds_still_obey_pending_limit_and_wait_without_fake_progress(self):
        candidates = self.prepare_blocked_reserve(pending_limit=2)
        for candidate in candidates[-2:]:
            candidate.update(blocker_kind="numerical_control_failure",
                             failure_scope="implementation")
        path = self.pipeline / "research_work.json"
        path.write_text(json.dumps({"candidates": candidates}))
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.assertEqual(first["research_work"]["reserve_budget"], 0)
        self.assertEqual(first["research_work"]["deferred_reason"], "pending_limit")
        self.commit()
        self.assertEqual(self.build()["mode"], "steady")
        for candidate in candidates[-2:]:
            candidate["retry_after"] = "2026-01-01T00:00:00+00:00"
        path.write_text(json.dumps({"candidates": candidates}))
        recheck = self.build()
        self.assertEqual(recheck["mode"], "event")
        self.assertEqual(len(recheck["research_work"]["due_ids"]), 2)
        self.assertNotIn("design_bootstrap", tick_efficiency.compact_view(recheck))
        for goal_rc in (1, 4):
            self.assertNotEqual(self.build(goal_rc=goal_rc)["mode"], "design")

    def test_revision_authorization_wait_leaves_room_for_independent_work(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        candidates += [dict(candidates[-1], id=f"revision-{i}",
                            blocker_kind="human_revision_authorization") for i in range(3)]
        candidates.append(dict(candidates[-1], id="annotation", blocker_kind="human_review"))
        path = self.pipeline / "research_work.json"
        path.write_text(json.dumps({"candidates": candidates}))
        context = self.build()
        self.assertEqual(context["research_work"]["human_wait_count"], 6)
        self.assertEqual(context["research_work"]["reserve_budget"], 2)
        self.assertEqual(context["mode"], "design")
        self.assertEqual(len(context["research_work"]["human_actions"]), 6)
        candidates += [dict(candidates[-1], id=f"parked-{i}") for i in range(2)]
        path.write_text(json.dumps({"candidates": candidates}))
        capped = self.build()
        self.assertEqual(capped["research_work"]["pending_count"], 8)
        self.assertEqual(capped["research_work"]["reserve_budget"], 0)
        self.assertEqual(capped["research_work"]["deferred_reason"], "pending_limit")
        self.assertEqual(capped["mode"], "event")
        self.commit()
        self.assertEqual(self.build()["mode"], "steady")
        candidates[-1]["stage"] = "rejected"
        path.write_text(json.dumps({"candidates": candidates}))
        opened = self.build()
        self.assertEqual(opened["research_work"]["reserve_budget"], 1)
        self.assertEqual(opened["mode"], "design")

    def test_queued_blocked_candidates_still_reserve_admission_slots(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        for c in candidates[-2:]:
            c["blocker_kind"] = "external_resource"
        (self.pipeline / "research_work.json").write_text(json.dumps({"candidates": candidates}))
        self.set_tasks([dict(id=c["id"], status="waiting", gpu=i)
                        for i, c in enumerate(candidates[-2:])])
        context = self.build()
        self.assertEqual(context["queue"]["candidate_budget"], 0)
        self.assertEqual(context["research_work"]["pending_count"], 2)
        self.assertEqual(context["research_work"]["reserve_count"], 2)
        self.assertEqual(context["research_work"]["parked_count"], 0)
        self.assertEqual(context["research_work"]["resource_wait_count"], 2)
        self.assertEqual(context["research_work"]["reserve_budget"], 0)
        self.assertEqual(context["research_work"]["deferred_reason"], "queued_work")

    def test_resource_block_without_queue_allows_bounded_cpu_preparation(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        for c in candidates[-2:]:
            c["blocker_kind"] = "external_resource"
        (self.pipeline / "research_work.json").write_text(json.dumps({"candidates": candidates}))
        self.set_tasks([dict(id=f"run-{i}", status="running", gpu=i) for i in range(2)])
        context = self.build()
        self.assertEqual(context["queue"]["candidate_budget"], 0)
        self.assertTrue(context["research_work"]["reserve_only"])
        self.assertEqual(context["research_work"]["reserve_budget"], 2)

    def test_blocked_cooldown_cannot_freeze_available_independent_reserve(self):
        candidates = self.prepare_blocked_reserve(pending_limit=8)
        self.build()
        self.commit()
        for reason, expected in (("external_resource_blocked", "design"),
                                 ("no_information_gain", "steady")):
            with self.subTest(reason=reason):
                (self.pipeline / "research_work.json").write_text(json.dumps({
                    "candidates": candidates, "design_cycle": {"stop_reason": reason}}))
                (self.headless / ".research_cooldown.json").write_text(json.dumps({
                    "retry_after": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                    "signature": tick_efficiency.research_signature(self.project)}))
                self.assertEqual(self.build()["mode"], expected)

    def test_zero_pending_limit_and_phase_holds_do_not_force_new_research(self):
        self.prepare_blocked_reserve(pending_limit=0)
        (self.pipeline / "research_work.json").write_text('{"candidates": []}')
        self.assertNotEqual(self.build(force_design=True)["mode"], "design")
        self.set_pipeline_policy(research_on_capacity_gap=True)
        for rc in (1, 4, 2):
            self.assertNotEqual(self.build(force_design=True, goal_rc=rc)["mode"], "design")

    def test_operational_failure_and_recovery_wake_without_queue_changes(self):
        self.set_tasks([dict(id="waiting", status="waiting", gpu=0)])
        self.build()
        self.commit()
        self.monitor.write_text(
            "--- server-1 (example) ---\n  [\u4e0d\u53ef\u8fbe]\n", encoding="utf-8")
        failed = self.build()
        self.assertEqual(failed["mode"], "event")
        self.assertIn("operational_issues_changed", failed["changes"]["reasons"])
        self.assertEqual(failed["preflight"]["monitor_rc"], 0)
        view = tick_efficiency.compact_view(failed)
        self.assertEqual(view["preflight"]["operational_issues"][0]["kind"], "connectivity")
        self.commit()
        self.assertEqual(self.build()["mode"], "steady")
        self.commit()
        self.monitor.write_text("monitor ok\n")
        recovered = self.build()
        self.assertEqual(recovered["mode"], "event")
        self.assertEqual(recovered["preflight"]["operational_issues"], [])

    def test_mixed_blocked_reserve_wakes_resource_on_queue_change(self):
        candidates = self.prepare_blocked_reserve()
        candidates[-1]["blocker_kind"] = "external_resource"
        (self.pipeline / "research_work.json").write_text(json.dumps({"candidates": candidates}))
        self.build()
        self.commit()
        self.assertEqual(self.build()["mode"], "steady")
        self.commit()
        self.set_tasks([{"id": "running", "status": "running", "gpu": 0}])
        context = self.build()
        self.assertFalse(context["research_work"]["deferred"])
        self.assertEqual(context["research_work"]["due_ids"], ["ready-1"])

    def test_invalid_blocker_fields_do_not_defer_design(self):
        candidates = self.prepare_blocked_reserve()
        path = self.pipeline / "research_work.json"
        for key, value in (("retry_after", "invalid"),
                           ("retry_after", "2099-01-01T00:00:00"),
                           ("wake_paths", ["../../outside.json"]),
                           ("evidence", []), ("next_action", ""),
                           ("unblock_condition", ""), ("blocker", "")):
            with self.subTest(key=key, value=value):
                changed = [dict(c) for c in candidates]
                changed[-1][key] = value
                path.write_text(json.dumps({"candidates": changed}))
                context = self.build()
                self.assertFalse(context["research_work"]["deferred"])
                self.assertEqual(context["mode"], "design")

    def test_disabled_reserve_does_not_suppress_capacity_gap_design(self):
        self.prepare_blocked_reserve()
        self.set_pipeline_policy(research_on_capacity_gap=True, research_reserve_target=0)
        context = self.build()
        self.assertFalse(context["research_work"]["deferred"])
        self.assertEqual(context["mode"], "design")

    def test_unchanged_external_blocks_back_off_and_real_signals_wake(self):
        now = datetime.now(timezone.utc)
        candidate = dict(id="human", stage="blocked", blocker_kind="human_review",
                         retry_after=(now - timedelta(days=1)).isoformat(),
                         unblock_condition="Actual sealed responses arrive",
                         wake_paths=["pipeline/intake.json"])
        signals = dict(goal="goal", servers="servers", queue=[])
        due, state = builder.blocked_recheck(self.project, candidate, {}, signals, now)
        self.assertTrue(due)
        self.assertFalse(builder.blocked_recheck(
            self.project, candidate, state, signals, now + timedelta(hours=1))[0])
        (self.pipeline / "intake.json").write_text('{"real_responses":1}')
        self.assertTrue(builder.blocked_recheck(
            self.project, candidate, state, signals, now + timedelta(minutes=1))[0])
        candidate["wake_paths"] = ["../../outside.json"]
        self.assertTrue(builder.blocked_recheck(
            self.project, candidate, state, signals, now)[0])
        candidate.update(blocker_kind="live_external_gpu_occupation", wake_paths=[])
        _, state = builder.blocked_recheck(self.project, candidate, {}, signals, now)
        self.assertFalse(builder.blocked_recheck(
            self.project, candidate, state, signals, now + timedelta(minutes=20))[0])
        self.assertTrue(builder.blocked_recheck(
            self.project, candidate, state, signals, now + timedelta(hours=1))[0])
        changed = dict(signals, queue=[["opening", "done_complete"]])
        self.assertTrue(builder.blocked_recheck(
            self.project, candidate, state, changed, now + timedelta(minutes=1))[0])

    def test_external_block_backoff_persists_across_committed_contexts(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        self.set_tasks([{"id": "run", "status": "running", "gpu": 0}])
        candidate = dict(id="human", stage="blocked", blocker_kind="human_review",
                         retry_after="2026-01-01T00:00:00+00:00",
                         unblock_condition="Actual sealed responses arrive",
                         wake_paths=["pipeline/intake.json"])
        (self.pipeline / "research_work.json").write_text(json.dumps(dict(candidates=[candidate])))
        first = self.build()
        self.assertEqual(first["research_work"]["due_ids"], ["human"])
        self.commit()
        second = self.build()
        self.assertEqual(second["research_work"]["due_ids"], [])
        self.assertEqual(second["mode"], "steady")
        self.commit()
        (self.pipeline / "intake.json").write_text('{"responses":1}')
        self.assertEqual(self.build()["research_work"]["due_ids"], ["human"])

    def test_funnel_does_not_treat_legacy_rejections_as_falsified_hypotheses(self):
        rows = [dict(id="legacy", stage="rejected"),
                dict(id="realization", stage="rejected", failure_scope="implementation"),
                dict(id="pending", stage="validation")]
        funnel = builder.research_funnel(self.project, rows, True)
        self.assertEqual(funnel["candidate_records"], 3)
        self.assertEqual(funnel["rejected_scopes"], dict(unclassified=1, implementation=1))
        self.assertNotIn("acceptance_rate", funnel)
        self.assertEqual(builder.research_funnel(self.project, [], False), {"observed": False})

    def test_one_running_task_leaves_one_candidate_slot(self) -> None:
        self.set_capacity(2)
        self.set_tasks(
            [
                {
                    "id": "active-1",
                    "config": "configs/active.yaml",
                    "status": "running",
                    "gpu": 0,
                }
            ]
        )
        third = self.advance_to_design_check()
        self.assertEqual(third["mode"], "design")
        self.assertEqual(third["queue"]["active_count"], 1)
        self.assertEqual(third["queue"]["target_active"], 2)
        self.assertEqual(third["queue"]["candidate_budget"], 1)

    def test_monitor_only_server_does_not_add_capacity_or_consume_slots(self) -> None:
        (self.project / "SERVERS.yaml").write_text(
            "servers:\n"
            "  dispatch:\n"
            "    role: gpu_server\n"
            "    allowed_gpus: [0, 1]\n"
            "    max_tasks_per_gpu: 1\n"
            "  legacy:\n"
            "    role: gpu_server\n"
            "    allowed_gpus: [7]\n"
            "    max_tasks_per_gpu: 2\n"
            "    dispatch_enabled: false\n",
            encoding="utf-8",
        )
        (self.pipeline / "queue.json").write_text(
            json.dumps(
                {
                    "gpu_queues": {
                        "dispatch": [],
                        "legacy": [
                            {
                                "id": "legacy-running",
                                "status": "running",
                                "gpu": 7,
                            }
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        context = self.build(force_design=True)
        self.assertEqual(context["queue"]["capacity"], 2)
        self.assertEqual(context["queue"]["active_count"], 0)
        self.assertEqual(context["queue"]["candidate_budget"], 2)
        self.assertEqual(context["queue"]["active_tasks"], [])
        self.assertEqual(
            context["queue"]["monitored_active_tasks"][0]["id"],
            "legacy-running",
        )

    def test_empty_four_slot_project_budgets_four_candidates(self) -> None:
        self.set_capacity(4)
        third = self.advance_to_design_check()
        self.assertEqual(third["mode"], "design")
        self.assertEqual(third["queue"]["candidate_budget"], 4)

    def test_server_wide_task_cap_limits_aggregate_capacity(self) -> None:
        (self.project / "SERVERS.yaml").write_text(
            "servers:\n"
            "  server-many-gpus:\n"
            "    role: gpu_server\n"
            "    allowed_gpus: [0, 1, 2, 3, 4, 5, 6, 7]\n"
            "    max_tasks_per_gpu: 2\n"
            "    max_tasks: 2\n",
            encoding="utf-8",
        )
        (self.pipeline / "queue.json").write_text(
            json.dumps({"gpu_queues": {"server-many-gpus": []}}),
            encoding="utf-8",
        )
        context = self.build(force_design=True)
        self.assertEqual(context["queue"]["capacity"], 2)
        self.assertEqual(context["queue"]["candidate_budget"], 2)

    def test_waiting_claiming_and_running_all_consume_capacity(self) -> None:
        self.set_capacity(4)
        self.set_tasks(
            [
                {"id": "wait-1", "status": "waiting"},
                {"id": "claim-1", "status": "claiming"},
                {"id": "run-1", "status": "running"},
            ]
        )
        third = self.advance_to_design_check()
        self.assertEqual(third["mode"], "design")
        self.assertEqual(third["queue"]["waiting_count"], 1)
        self.assertEqual(third["queue"]["claiming_count"], 1)
        self.assertEqual(third["queue"]["running_count"], 1)
        self.assertEqual(third["queue"]["candidate_budget"], 1)

    def test_new_analysis_triggers_event(self) -> None:
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.commit()
        second = self.build()
        self.assertEqual(second["mode"], "steady")
        self.commit()
        (self.pipeline / "analyses" / "new_result.md").write_text(
            "# New result\n", encoding="utf-8"
        )
        third = self.build()
        self.assertEqual(third["mode"], "event")
        self.assertIn(
            "research_artifact_changed", third["changes"]["reasons"]
        )

    def test_terminal_removed_from_queue_is_detected_from_durable_state(self) -> None:
        self.set_tasks(
            [
                {
                    "id": "crash-1",
                    "config": "configs/crash.yaml",
                    "status": "running",
                    "gpu": 0,
                }
            ]
        )
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.commit()

        self.set_tasks([])
        experiment = {
            "id": "crash-1",
            "config": "configs/crash.yaml",
            "status": "crashed",
        }
        experiments_dir = self.pipeline / "experiments"
        experiments_dir.mkdir(exist_ok=True)
        (experiments_dir / "crash-1.json").write_text(
            json.dumps(experiment),
            encoding="utf-8",
        )
        with (self.pipeline / "experiments.csv").open(
            "a", encoding="utf-8"
        ) as handle:
            handle.write(
                "crash-1,configs/crash.yaml,server-1,0,crashed,,,2026-09-15\n"
            )

        second = self.build()
        self.assertEqual(second["mode"], "event")
        self.assertEqual(second["changes"]["new_terminal_ids"], ["crash-1"])
        self.assertIn("new_terminal:crash-1", second["changes"]["reasons"])
        self.assertEqual(
            second["manifests"]["terminal_experiments"][0]["state"],
            "crashed",
        )


    def test_pending_work_resumes_without_design_cooldown(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        candidate = {"id": "native-capture", "stage": "validation",
                     "next_action": "capture native batches", "evidence": []}
        (self.pipeline / "research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        context = self.build()
        self.assertEqual(context["mode"], "event")
        self.assertEqual(context["research_work"]["due_ids"], ["native-capture"])

    def test_due_work_and_capacity_gap_continue_design_in_same_tick(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        self.set_pipeline_policy(research_on_capacity_gap=True)
        candidate = {"id": "native-capture", "stage": "validation",
                     "next_action": "capture native batches", "evidence": []}
        (self.pipeline / "research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        context = self.build()
        self.assertEqual(context["mode"], "design")
        self.assertEqual(context["research_work"]["due_ids"], ["native-capture"])
        self.assertEqual(context["queue"]["candidate_budget"], 1)
        self.assertIn("resume unfinished candidate stages", context["mode_reason"])

    def test_due_work_does_not_preempt_cooled_down_design(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        candidate = {"id": "native-capture", "stage": "validation",
                     "next_action": "capture native batches", "evidence": []}
        (self.pipeline / "research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        first = self.build()
        self.assertEqual(first["mode"], "event")
        self.commit()
        second = self.build()
        self.assertEqual(second["mode"], "event")
        self.commit()
        third = self.build()
        self.assertEqual(third["mode"], "design")
        self.assertEqual(third["research_work"]["due_ids"], ["native-capture"])

    def test_exclusive_gpu_block_waits_for_queue_opening_not_retry_timer(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        self.set_pipeline_policy(research_on_capacity_gap=True, research_reserve_target=1)
        candidate = {
            "id": "depth-probe", "stage": "blocked",
            "blocker_kind": "exclusive_gpu_slot", "required_server": "server-1",
            "blocker": "Training occupies the authorized card",
            "retry_after": "2099-01-01T00:00:00+00:00",
            "unblock_condition": "Authorized card opens; recheck live lease",
            "next_action": "Run native diagnostic after lease", "evidence": [],
        }
        (self.pipeline / "research_work.json").write_text(
            json.dumps({"candidates": [candidate]}))
        self.set_tasks([{"id": "training", "status": "running", "gpu": 0}])
        first = self.build()
        self.assertEqual(first["research_work"]["due_ids"], [])
        self.commit()
        second = self.build()
        self.assertEqual(second["mode"], "steady")
        self.assertEqual(second["research_work"]["due_ids"], [])
        self.commit()
        self.set_tasks([{"id": "training", "status": "done_earlystop", "gpu": 0}])
        opened = self.build()
        self.assertEqual(opened["research_work"]["due_ids"], ["depth-probe"])
        self.assertEqual(opened["mode"], "design")

    def test_unknown_gpu_assignment_does_not_fake_exclusive_opening(self):
        (self.pipeline / "closure_policy.json").write_text('{"enabled":true}')
        (self.pipeline / "research_work.json").write_text(json.dumps({
            "candidates": [{
                "id": "depth-probe", "stage": "blocked",
                "blocker_kind": "exclusive_gpu_slot", "required_server": "server-1",
                "retry_after": "2099-01-01T00:00:00+00:00",
            }]
        }))
        self.set_tasks([{"id": "claim", "status": "claiming"}])
        self.assertEqual(self.build()["research_work"]["due_ids"], [])
        self.set_tasks([{"id": "claim", "status": "claiming", "gpu": 99}])
        self.assertEqual(self.build()["research_work"]["due_ids"], [])

    def test_capacity_gap_research_immediate(self):
        goal_path = self.pipeline / "goal.json"
        goal = json.loads(goal_path.read_text())
        goal["pipeline_policy"] = {"research_on_capacity_gap": True}
        goal_path.write_text(json.dumps(goal))
        context = self.build()
        self.assertEqual(context["mode"], "design")
        self.assertTrue(context["changes"]["design_due"])


if __name__ == "__main__":
    unittest.main()
