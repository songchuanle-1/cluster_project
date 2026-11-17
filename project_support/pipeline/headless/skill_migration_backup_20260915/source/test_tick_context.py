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
    ) -> dict:
        command = [
            sys.executable,
            str(BUILDER),
            "demo_project",
            "--monitor-file",
            str(self.monitor),
            "--goal-file",
            str(self.goal),
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

    def test_empty_four_slot_project_budgets_four_candidates(self) -> None:
        self.set_capacity(4)
        third = self.advance_to_design_check()
        self.assertEqual(third["mode"], "design")
        self.assertEqual(third["queue"]["candidate_budget"], 4)

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


if __name__ == "__main__":
    unittest.main()
