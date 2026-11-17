"""Read-only production audit using disposable projects and simulated SSH."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL))
import pipeline_monitor as monitor
import closure
import check_goal
import tick_efficiency
import render_tick_report


class ClosureGapAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pipeline-closure-audit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "audit_project"
        self.pipeline = self.project / "pipeline"
        (self.pipeline / "experiments").mkdir(parents=True)
        self.write(self.pipeline / "goal.json",
                   {"metric": {"name": "miou", "target": 0.7}})
        (self.project / "SERVERS.yaml").write_text("servers: {}\n", encoding="utf-8")
        self.server = dict(name="test-server", host="unused.invalid", user="unused",
                           remote_code_root="/unused/code", work_dir="/unused/runs",
                           allowed_gpus=[0, 1, 2], max_tasks_per_gpu=1)
        self.task = dict(id="A", config="configs/A.yaml", status="running",
                         gpu="0", pid=4242, launch_verified=True)
        self.queue = {"gpu_queues": {"test-server": [self.task]}}
        self.persist()

    @staticmethod
    def write(path, payload):
        path.write_text(json.dumps(payload), encoding="utf-8")

    def persist(self):
        monitor.save_queue(str(self.project), self.queue)
        monitor.save_running(str(self.project), {"test-server": {"0": "A"}})
        monitor.save_experiment(str(self.project), copy.deepcopy(self.task))

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes()
                for p in self.project.rglob("*") if p.is_file()}

    @contextlib.contextmanager
    def simulated_monitor(self, alive=False, completed=False, stop_result="__PIPELINE_PID_ALIVE__"):
        procs = ({self.task["config"]: ("4242", self.task["config"], "0", None, "train")}
                 if alive else {})

        def ssh(host, user, cmd, *args, **kwargs):
            if cmd == "echo ok":
                return "ok"
            if cmd.startswith("ps -p "):
                return "4242" if alive else ""
            if "__PIPELINE_PID_GONE__" in cmd:
                return stop_result
            return ""

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(monitor, "PROJECT_ROOT", str(self.root)))
            stack.enter_context(patch.object(monitor, "acquire_lock", return_value=io.BytesIO()))
            stack.enter_context(patch.object(monitor, "load_servers",
                                              return_value={"test-server": self.server}))
            stack.enter_context(patch.object(monitor, "find_project_processes",
                                              return_value=procs))
            stack.enter_context(patch.object(monitor, "ssh", side_effect=ssh))
            stack.enter_context(patch.object(closure, "enabled", return_value=False))
            stack.enter_context(patch.object(monitor, "find_log_via_fd",
                                              return_value=["/unused/log"]))
            stack.enter_context(patch.object(monitor, "find_latest_log",
                                              return_value="/unused/log"))
            stack.enter_context(patch.object(monitor, "parse_running_miou",
                                              return_value=([0.5] * 11, 0.5, 10)))
            stack.enter_context(patch.object(monitor, "parse_miou_from_logs",
                                              return_value=([0.5], 0.5, 0)))
            stack.enter_context(patch.object(
                monitor, "get_epoch_info",
                return_value=("100/100", 100, 100, "?") if completed
                else ("20/100", 20, 100, "?")))
            stack.enter_context(patch.object(monitor, "pull_log", return_value=""))
            stack.enter_context(patch.object(monitor, "daily_report", return_value=None))
            stack.enter_context(patch.object(monitor, "log_decision"))
            stack.enter_context(patch.object(monitor, "_process_queue"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            yield

    def dispatch_with_uncertain_first_launch(self, gpu_count, max_tasks=None,
                                             uncertain=True, legacy_observed=True,
                                             stale_launch_proof=False):
        first = dict(id="A", config="configs/A.yaml", status="waiting",
                     code_commit="a" * 40)
        if stale_launch_proof:
            first.update(pid=99, log="/unused/previous-run.log", launch_verified=True,
                         launch_verification="training_progress")
        second = dict(id="B", config="configs/B.yaml", status="waiting",
                      code_commit="a" * 40)
        queue = {"gpu_queues": {"test-server": [first, second]}}
        calls = []
        output = io.StringIO()

        def launch(project, server, task, gpu, ssh):
            calls.append((task["id"], gpu))
            if task["id"] == "A" and uncertain:
                raise OSError("Simulated reply lost after process creation")
            return {"pid": 5000, "log": "/unused/B.log"}

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(
                monitor, "ssh",
                return_value="\n".join(f"{i}, 0, 0, 80000" for i in range(gpu_count))))
            stack.enter_context(patch.object(monitor, "load_active_gpu_reservations",
                                              return_value={}))
            stack.enter_context(patch.object(monitor, "load_servers",
                                              return_value={"test-server": self.server}))
            stack.enter_context(patch.object(monitor, "find_local_code_dir",
                                              return_value=str(self.project)))
            stack.enter_context(patch.object(monitor, "log_decision"))
            stack.enter_context(patch.object(
                monitor, "verify_launched",
                side_effect=lambda host, user, cfg: legacy_observed and cfg == "configs/B.yaml"))
            stack.enter_context(patch.object(closure, "enabled", return_value=True))
            stack.enter_context(patch.object(closure, "admission"))
            stack.enter_context(patch.object(closure, "git", return_value="a" * 40))
            stack.enter_context(patch.object(closure, "safe_sync", return_value=True))
            stack.enter_context(patch.object(closure, "safe_launch", side_effect=launch))
            stack.enter_context(patch.object(closure, "verify_progress", return_value=True))
            stack.enter_context(contextlib.redirect_stdout(output))
            monitor._process_queue(
                queue, "test-server", "unused.invalid", "unused", str(self.project),
                set(), {str(i) for i in range(gpu_count)}, [], max_tasks_total=max_tasks)
        self.dispatched_queue = queue
        self.dispatch_output = output.getvalue()
        return calls

    def test_uncertain_launch_is_not_retried_with_spare_third_gpu(self):
        calls = self.dispatch_with_uncertain_first_launch(3)
        self.assertEqual(sum(tid == "A" for tid, _ in calls), 1,
                         f"One dispatch pass launched held A repeatedly: {calls}")

    def test_control_uncertain_launch_without_spare_gpu_is_once(self):
        calls = self.dispatch_with_uncertain_first_launch(2)
        self.assertEqual(sum(tid == "A" for tid, _ in calls), 1)

    def test_failed_early_stop_keeps_live_task_active(self):
        with self.simulated_monitor(alive=True):
            monitor.monitor_project("audit_project")
        tasks = monitor.load_queue(str(self.project))["gpu_queues"]["test-server"]
        record = monitor.load_experiment(str(self.project), "A")
        self.assertEqual([task["id"] for task in tasks], ["A"],
                         f"Process 4242 remained alive but archival state={record['status']}")

    def test_control_dead_completed_task_is_archived(self):
        self.write(self.pipeline / "deathwatch.json",
                   {"test-server": {"A": {"missed": 2}}})
        with self.simulated_monitor(completed=True):
            monitor.monitor_project("audit_project")
        self.assertEqual(monitor.load_experiment(str(self.project), "A")["status"],
                         "done_complete")
        self.assertEqual(monitor.load_queue(str(self.project))["gpu_queues"]["test-server"],
                         [])

    def test_read_only_reconcile_combination_cannot_write(self):
        self.write(self.pipeline / "deathwatch.json",
                   {"test-server": {"A": {"missed": 2}}})
        before = self.snapshot()
        with self.simulated_monitor(completed=True):
            monitor.monitor_project("audit_project", read_only=True, reconcile_only=True)
        after = self.snapshot()
        changed = sorted(k for k in before.keys() | after.keys()
                         if before.get(k) != after.get(k))
        self.assertEqual(changed, [], f"Read-only invocation modified {changed}")

    def test_control_read_only_alone_does_not_write(self):
        self.write(self.pipeline / "deathwatch.json",
                   {"test-server": {"A": {"missed": 2}}})
        before = self.snapshot()
        with self.simulated_monitor(completed=True):
            monitor.monitor_project("audit_project", read_only=True)
        self.assertEqual(self.snapshot(), before)

    def test_busy_monitor_is_not_successful_preflight(self):
        lock = monitor.acquire_lock(str(self.project))
        self.assertIsNotNone(lock)
        try:
            result = subprocess.run(
                [sys.executable, "-B", str(SKILL / "pipeline_monitor.py"), "audit_project"],
                env={**os.environ, "PROJECT_ROOT": str(self.root),
                     "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
                capture_output=True, text=True, encoding="utf-8", timeout=15)
        finally:
            lock.close()
        self.assertIn("[\u8df3\u8fc7]", result.stdout)
        self.assertNotEqual(
            result.returncode, 0,
            f"Busy monitor returned success; operational issues="
            f"{tick_efficiency.monitor_issues(result.stdout)}")

    def archive(self, remote_log=""):
        monitor.finalize_task(
            str(self.project), self.queue, "test-server", "unused.invalid", "unused",
            self.task, "A", "done_complete", 0.8, "100/100", "0", remote_log, [])

    def champion(self):
        return check_goal.find_champion(check_goal.load_experiments_csv(str(self.project)),
                                        check_goal.load_analyses(str(self.project)))

    def test_archive_interruption_is_recovered_for_goal_evaluation(self):
        with patch.object(monitor, "ledger_append",
                          side_effect=OSError("Simulated failure after queue removal")):
            with self.assertRaisesRegex(OSError, "after queue removal"):
                self.archive()
        self.assertEqual(monitor.load_experiment(str(self.project), "A")["status"],
                         "done_complete")
        with self.simulated_monitor():
            monitor.monitor_project("audit_project")
        self.assertIsNotNone(
            self.champion(),
            "A is durable done_complete=0.8, but the next monitor never repairs the "
            "missing goal ledger/analysis because the task was removed from the queue")

    def test_control_uninterrupted_archive_enters_goal_evaluation(self):
        self.archive()
        self.assertEqual(self.champion()["miou"], 0.8)

    def pending_archive(self):
        with patch.object(monitor, "ledger_append", side_effect=OSError("interrupted ledger")):
            with self.assertRaisesRegex(OSError, "interrupted ledger"):
                self.archive()
        return next((self.pipeline / "archive_pending").glob("*.json"))

    def replay(self, servers=None, read_only=False):
        with patch.object(monitor, "ssh", side_effect=AssertionError("Replay cannot use SSH")):
            return monitor.recover_archives(
                str(self.project), monitor.load_queue(str(self.project)),
                {"test-server": self.server} if servers is None else servers,
                read_only=read_only)

    def test_uncertain_launch_reserves_the_project_concurrency_slot(self):
        self.assertEqual(self.dispatch_with_uncertain_first_launch(3, max_tasks=1), [("A", "0")])
        self.assertEqual(self.dispatched_queue["gpu_queues"]["test-server"][0]["status"],
                         "claiming")

    def test_verified_native_progress_is_not_downgraded_by_legacy_probe(self):
        calls = self.dispatch_with_uncertain_first_launch(3, uncertain=False, legacy_observed=False)
        self.assertEqual([tid for tid, _ in calls], ["A", "B"])
        self.assertTrue(all(t["status"] == "running" for t in
                            self.dispatched_queue["gpu_queues"]["test-server"]))

    def test_old_launch_proof_cannot_certify_a_failed_new_attempt(self):
        self.dispatch_with_uncertain_first_launch(3, max_tasks=1, stale_launch_proof=True)
        task = self.dispatched_queue["gpu_queues"]["test-server"][0]
        self.assertEqual(task["status"], "claiming")
        self.assertFalse(task["launch_verified"])
        self.assertEqual(task["launch_verification"], "pending_progress")
        self.assertNotIn("pid", task)
        self.assertNotIn("log", task)

    def test_uncertain_launch_is_reported_as_reconciliation_not_failure(self):
        self.dispatch_with_uncertain_first_launch(3, max_tasks=1)
        issues = tick_efficiency.monitor_issues(self.dispatch_output)
        self.assertEqual([item["reason"] for item in issues], ["claim_uncertain"])
        self.assertEqual(issues[0]["task"], "A")

    def test_unknown_stop_probe_keeps_active_record_and_dependency_unsatisfied(self):
        with self.simulated_monitor(alive=True, stop_result=""):
            monitor.monitor_project("audit_project")
        queue = monitor.load_queue(str(self.project))
        self.assertEqual(monitor.dependency_states(str(self.project), queue, {"A"})["A"],
                         "running")
        self.assertEqual(monitor.load_running(str(self.project)), {"test-server": {"0": "A"}})

    def test_explicit_gone_probe_allows_early_stop_archival(self):
        with self.simulated_monitor(alive=True, stop_result="__PIPELINE_PID_GONE__"):
            monitor.monitor_project("audit_project")
        self.assertEqual(monitor.load_experiment(str(self.project), "A")["status"],
                         "done_earlystop")

    def test_pending_archive_is_never_replayed_by_combined_read_only_flags(self):
        self.pending_archive()
        before = self.snapshot()
        with self.simulated_monitor():
            self.assertEqual(monitor.monitor_project(
                "audit_project", read_only=True, reconcile_only=True), 0)
        self.assertEqual(self.snapshot(), before)

    def test_unknown_experiment_read_does_not_create_directory(self):
        root = self.root / "query_only"
        (root / "pipeline").mkdir(parents=True)
        self.assertIsNone(monitor.load_experiment(str(root), "unknown"))
        self.assertFalse((root / "pipeline/experiments").exists())

    def test_archive_replay_is_idempotent_after_csv_write(self):
        append = monitor.ledger_append
        def interrupted(*args, **kwargs):
            append(*args, **kwargs)
            raise OSError("after CSV publication")
        with patch.object(monitor, "ledger_append", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "CSV publication"):
                self.archive()
        self.assertTrue(self.replay())
        self.assertTrue(self.replay())
        self.assertEqual(len(check_goal.load_experiments_csv(str(self.project))), 1)
        history = monitor.load_experiment(str(self.project), "A")["history"]
        self.assertEqual(len(history), 1)

    def test_archive_replay_after_queue_cleanup_does_not_repeat_ledger(self):
        save = monitor.save_queue
        def interrupted(*args, **kwargs):
            save(*args, **kwargs)
            raise OSError("after queue publication")
        with patch.object(monitor, "save_queue", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "queue publication"):
                self.archive()
        self.assertEqual(monitor.load_queue(str(self.project))["gpu_queues"]["test-server"], [])
        self.assertTrue(self.replay())
        self.assertEqual(len(check_goal.load_experiments_csv(str(self.project))), 1)
        self.assertEqual(list((self.pipeline / "archive_pending").glob("*.json")), [])

    def test_archive_replay_after_running_cleanup_preserves_other_jobs(self):
        monitor.save_running(str(self.project), {"test-server": {"0": ["A", "B"]}})
        save = monitor.save_running
        def interrupted(*args, **kwargs):
            save(*args, **kwargs)
            raise OSError("after running publication")
        with patch.object(monitor, "save_running", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "running publication"):
                self.archive()
        self.assertTrue(self.replay())
        self.assertEqual(monitor.load_running(str(self.project)), {"test-server": {"0": ["B"]}})

    def test_experiment_write_failure_keeps_valid_json_and_replays(self):
        previous = (self.pipeline / "experiments/A.json").read_bytes()
        replace = os.replace
        def interrupted(source, target):
            if Path(target) == self.pipeline / "experiments/A.json":
                raise OSError("experiment replacement failed")
            return replace(source, target)
        with patch.object(monitor.os, "replace", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "replacement failed"):
                self.archive()
        self.assertEqual((self.pipeline / "experiments/A.json").read_bytes(), previous)
        self.assertEqual(list(self.project.rglob("*.tmp")), [])
        self.assertTrue(self.replay())
        self.assertEqual(self.champion()["miou"], 0.8)

    def test_journal_failure_leaves_all_lifecycle_ledgers_unchanged(self):
        before = self.snapshot()
        with patch.object(monitor, "_save_json", side_effect=OSError("journal unavailable")):
            with self.assertRaisesRegex(OSError, "journal unavailable"):
                self.archive()
        self.assertEqual(self.snapshot(), before)

    def test_csv_replacement_failure_preserves_existing_history(self):
        monitor.ledger_append(str(self.project), id="older", state="done_complete", best_miou="0.4")
        previous = (self.pipeline / "experiments.csv").read_bytes()
        replace = os.replace
        def interrupted(source, target):
            if Path(target) == self.pipeline / "experiments.csv":
                raise OSError("CSV replacement failed")
            return replace(source, target)
        with patch.object(monitor.os, "replace", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "CSV replacement failed"):
                self.archive()
        self.assertEqual((self.pipeline / "experiments.csv").read_bytes(), previous)
        self.assertTrue(self.replay())
        self.assertEqual([r["id"] for r in check_goal.load_experiments_csv(str(self.project))],
                         ["older", "A"])

    def test_analysis_replay_has_stable_path_and_no_duplicate_rows(self):
        log = self.project / "downloaded.log"
        log.write_text("spAcc_50: 0.9\nspmIOU: 0.8\n", encoding="utf-8")
        write = monitor.write_analysis_md
        def interrupted(*args, **kwargs):
            write(*args, **kwargs)
            raise OSError("after analysis publication")
        with patch.object(monitor, "pull_log", return_value=str(log)), \
                patch.object(monitor, "write_analysis_md", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "analysis publication"):
                self.archive(remote_log="/unused/remote.log")
        paths = list((self.pipeline / "analyses").glob("*.md"))
        self.assertEqual(len(paths), 1)
        self.assertTrue(self.replay())
        self.assertEqual(list((self.pipeline / "analyses").glob("*.md")), paths)
        self.assertEqual(len(check_goal.load_experiments_csv(str(self.project))), 1)

    def test_replay_cannot_overwrite_a_newer_experiment(self):
        self.pending_archive()
        newer = dict(self.task, pid=9999, launched="new-run")
        monitor.save_experiment(str(self.project), newer)
        before = self.snapshot()
        self.assertFalse(self.replay())
        self.assertEqual(self.snapshot(), before)

    def test_replay_cannot_delete_a_changed_queue_entry(self):
        self.pending_archive()
        self.queue["gpu_queues"]["test-server"][0]["pid"] = 9999
        monitor.save_queue(str(self.project), self.queue)
        before = self.snapshot()
        self.assertFalse(self.replay())
        self.assertEqual(self.snapshot(), before)

    def test_replay_respects_current_server_and_gpu_authorization(self):
        self.pending_archive()
        before = self.snapshot()
        for servers in ({}, {"test-server": dict(self.server, allowed_gpus=[])}):
            with self.subTest(servers=list(servers)):
                self.assertFalse(self.replay(servers=servers))
                self.assertEqual(self.snapshot(), before)

    def test_finalization_does_not_remove_another_id_with_the_same_config(self):
        self.queue["gpu_queues"]["test-server"].append(
            dict(self.task, id="B", status="waiting"))
        monitor.save_queue(str(self.project), self.queue)
        self.archive()
        self.assertEqual([t["id"] for t in monitor.load_queue(str(self.project))[
            "gpu_queues"]["test-server"]], ["B"])

    def test_corrupt_archive_stops_before_observation_or_dispatch(self):
        journal = self.pending_archive()
        journal.write_text("{invalid", encoding="utf-8")
        before = self.snapshot()
        with self.simulated_monitor(), patch.object(monitor, "find_project_processes") as probe:
            self.assertEqual(monitor.monitor_project("audit_project"), 1)
            probe.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_monitor_lock_is_released_when_observation_raises(self):
        handle = io.BytesIO()
        with patch.object(monitor, "PROJECT_ROOT", str(self.root)), \
                patch.object(monitor, "acquire_lock", return_value=handle), \
                patch.object(monitor, "load_servers", side_effect=ValueError("invalid server config")):
            with self.assertRaisesRegex(ValueError, "invalid server config"):
                monitor.monitor_project("audit_project")
        self.assertTrue(handle.closed)

    def test_recovery_faults_have_specific_report_labels(self):
        issues = tick_efficiency.monitor_issues(
            "--- test-server (unused) ---\n"
            "[\u505c\u6b62\u5f85\u6838\u9a8c] [A] process still alive\n"
            "[\u5f52\u6863\u5f85\u6062\u590d] [B] pending local replay\n"
            "[\u8df3\u8fc7] monitor owns .pipeline.lock\n")
        self.assertEqual([i["reason"] for i in issues],
                         ["stop_unconfirmed", "archive_pending", "monitor_busy"])
        self.assertEqual([i["task"] for i in issues[:2]], ["A", "B"])
        self.assertIsNone(issues[-1]["task"])
        for issue in issues:
            self.assertIn(issue["reason"], render_tick_report.ISSUE_LABELS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
