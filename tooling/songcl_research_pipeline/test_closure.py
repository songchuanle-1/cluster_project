import json
import os
import tempfile
import unittest
import copy
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

    def revision(self, number=1, result="pending"):
        return dict(
            revision=number, failure_scope="implementation",
            reason="The original validity mask was bypassed",
            change="Move the same residual after its validity mask",
            prediction="Invalid positions stay unchanged, native gradients remain",
            preregistered_at="2026-01-01T00:00:00+00:00",
            failure_evidence=[self.evidence], result=result,
            evidence=[] if result == "pending" else [self.evidence])

    def test_revision_preserves_hypothesis_and_completed_negative_evidence(self):
        candidate = dict(id="test", stage="validation", hypothesis="same mechanism",
                         revision_history=[self.revision(result="failed")])
        closure.validate_revisions(self.root, candidate)
        previous = copy.deepcopy(candidate)
        candidate["revision_history"].append(self.revision(2))
        closure.validate_revisions(self.root, candidate, previous)
        candidate["hypothesis"] = "a renamed replacement"
        with self.assertRaisesRegex(ValueError, "core hypothesis"):
            closure.validate_revisions(self.root, candidate, previous)
        candidate["hypothesis"] = previous["hypothesis"]
        candidate["revision_history"][0]["result"] = "passed"
        with self.assertRaisesRegex(ValueError, "rewritten"):
            closure.validate_revisions(self.root, candidate, previous)
        candidate["revision_history"] = []
        with self.assertRaisesRegex(ValueError, "removed"):
            closure.validate_revisions(self.root, candidate, previous)

    def test_revision_can_finish_but_not_rewrite_its_frozen_protocol(self):
        previous = dict(id="test", stage="implementation",
                        revision_history=[self.revision()])
        candidate = copy.deepcopy(previous)
        candidate["revision_history"][0].update(result="passed", evidence=[self.evidence])
        closure.validate_revisions(self.root, candidate, previous)
        candidate["revision_history"][0]["prediction"] = "changed after seeing results"
        with self.assertRaisesRegex(ValueError, "protocol"):
            closure.validate_revisions(self.root, candidate, previous)

    def authorized_third_revision(self):
        candidate = dict(id="test", stage="implementation",
                         revision_history=[self.revision(i, "failed") for i in (1, 2)])
        (self.root / "pipeline/execution_mode.json").write_text(
            json.dumps(dict(target_thread_id="verified-owner")))
        authorization = dict(
            scope="implementation_revision", authorization_granted=True,
            candidate_id="test", base_revision_count=2, additional_revisions=1,
            human_reply="Continue the scoped repair", owner_thread_id="verified-owner",
            goal_sha256=closure.digest(self.root / "pipeline/goal.json"),
            base_revision_history_sha256=closure.revision_digest(candidate["revision_history"]))
        path = self.root / "permission.json"
        path.write_text(json.dumps(authorization))
        candidate["implementation_revision_authorization"] = dict(
            path=path.name, sha256=closure.digest(path))
        candidate["revision_history"].append(self.revision(3))
        return candidate, authorization

    def test_scoped_third_revision_does_not_raise_the_default_budget(self):
        candidate, _ = self.authorized_third_revision()
        before = closure.digest(self.root / "pipeline/goal.json")
        closure.validate_revisions(self.root, candidate)
        candidate["revision_history"][-1].update(result="failed", evidence=[self.evidence])
        closure.validate_revisions(self.root, candidate)
        candidate["revision_history"].append(self.revision(4))
        with self.assertRaisesRegex(ValueError, "budget exceeded"):
            closure.validate_revisions(self.root, candidate)
        candidate["revision_history"].pop()
        del candidate["implementation_revision_authorization"]
        with self.assertRaisesRegex(ValueError, "budget exceeded"):
            closure.validate_revisions(self.root, candidate)
        self.assertEqual(before, closure.digest(self.root / "pipeline/goal.json"))

    def test_scoped_revision_authorization_is_bound_to_owner_goal_id_and_history(self):
        for field in ("scope", "authorization_granted", "candidate_id", "base_revision_count",
                      "additional_revisions", "human_reply", "owner_thread_id",
                      "goal_sha256", "base_revision_history_sha256"):
            candidate, authorization = self.authorized_third_revision()
            authorization[field] = None
            path = self.root / "permission.json"
            path.write_text(json.dumps(authorization))
            candidate["implementation_revision_authorization"]["sha256"] = closure.digest(path)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "candidate-scoped"):
                closure.validate_revisions(self.root, candidate)
        candidate, _ = self.authorized_third_revision()
        (self.root / "permission.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            closure.validate_revisions(self.root, candidate)

    def test_revision_limits_scope_order_evidence_and_reopen_authorization(self):
        for issue in ("budget", "hypothesis", "pending", "missing", "naive", "reopen"):
            candidate = dict(id="test", stage="validation",
                             revision_history=[self.revision()])
            previous = None
            if issue == "budget":
                candidate["revision_history"] = [self.revision(i, "failed") for i in (1, 2, 3)]
            elif issue == "hypothesis":
                candidate["revision_history"][0]["failure_scope"] = "hypothesis"
            elif issue == "pending":
                candidate["revision_history"].append(self.revision(2))
            elif issue == "missing":
                candidate["revision_history"][0].update(result="passed", evidence=[])
            elif issue == "naive":
                candidate["revision_history"][0]["preregistered_at"] = "2026-01-01T00:00:00"
            else:
                previous = dict(id="test", stage="rejected")
            with self.subTest(issue=issue), self.assertRaises(ValueError):
                closure.validate_revisions(self.root, candidate, previous)

    def test_revised_receipt_requires_latest_passed_revision_and_all_six_gates(self):
        candidate = dict(id="test", stage="admission",
                         revision_history=[self.revision(result="passed")])
        work_path = self.root / "pipeline/research_work.json"
        work_path.write_text(json.dumps(dict(candidates=[candidate])))
        self.save()
        with self.assertRaisesRegex(ValueError, "current passed"):
            closure.admission(self.root, self.task)
        self.receipt.update(candidate_id="test",
                            implementation_revision_sha256=closure.revision_digest(
                                candidate["revision_history"][-1]))
        self.save()
        closure.admission(self.root, self.task)
        del self.receipt["gates"]["native_backward"]
        self.save()
        with self.assertRaisesRegex(ValueError, "native_backward"):
            closure.admission(self.root, self.task)
        self.receipt["gates"]["native_backward"] = dict(passed=True, evidence=[self.evidence])
        candidate["revision_history"][0]["change"] = "untested new connection"
        work_path.write_text(json.dumps(dict(candidates=[candidate])))
        self.save()
        with self.assertRaisesRegex(ValueError, "current passed"):
            closure.admission(self.root, self.task)

    def test_revision_result_cannot_predate_registration(self):
        from datetime import datetime
        candidate = dict(id="test", revision_history=[self.revision(result="passed")])
        timestamp = datetime.fromisoformat("2026-01-01T00:00:00+00:00").timestamp() - 1
        os.utime(self.root / "evidence.json", (timestamp, timestamp))
        with self.assertRaisesRegex(ValueError, "pre-registration"):
            closure.validate_revisions(self.root, candidate)

    def mixed_revision(self):
        from datetime import datetime
        source = self.root / "frozen_source.py"
        source.write_text("# frozen input before the preregistration\n")
        timestamp = datetime.fromisoformat("2026-01-01T00:00:00+00:00").timestamp() - 1
        os.utime(source, (timestamp, timestamp))
        entry = {"path": source.name, "sha256": closure.digest(source)}
        previous = dict(id="test", stage="implementation",
                        revision_history=[dict(self.revision(), evidence=[entry])])
        current = copy.deepcopy(previous)
        current["revision_history"][0].update(
            result="failed", evidence=[entry, self.evidence], result_evidence=[self.evidence])
        return previous, current

    def test_revision_results_can_preserve_older_frozen_inputs(self):
        previous, current = self.mixed_revision()
        before = (self.root / "frozen_source.py").stat().st_mtime_ns
        closure.validate_revisions(self.root, current, previous)
        self.assertEqual(current["revision_history"][0]["result"], "failed")
        self.assertEqual((self.root / "frozen_source.py").stat().st_mtime_ns, before)
        self.assertIn(previous["revision_history"][0]["evidence"][0],
                      current["revision_history"][0]["evidence"])

    def test_explicit_revision_results_must_be_nonempty_fresh_and_referenced(self):
        for issue in ("empty", "not_list", "stale", "not_referenced", "bad_input_hash"):
            previous, current = self.mixed_revision()
            revision = current["revision_history"][0]
            if issue == "empty":
                revision["result_evidence"] = []
            elif issue == "not_list":
                revision["result_evidence"] = self.evidence
            elif issue == "stale":
                revision["result_evidence"] = [revision["evidence"][0]]
            elif issue == "not_referenced":
                revision["evidence"] = previous["revision_history"][0]["evidence"]
            else:
                (self.root / "frozen_source.py").write_text("# altered after freeze\n")
            with self.subTest(issue=issue), self.assertRaises(ValueError):
                closure.validate_revisions(self.root, current, previous)

    def test_completed_revision_cannot_reclassify_or_remove_results(self):
        previous, current = self.mixed_revision()
        closure.validate_revisions(self.root, current, previous)
        completed = copy.deepcopy(current)
        current["revision_history"][0]["result_evidence"].append(
            current["revision_history"][0]["evidence"][0])
        with self.assertRaises(ValueError):
            closure.validate_revisions(self.root, current, completed)
        partial = copy.deepcopy(completed)
        partial["revision_history"][0]["result"] = "pending"
        current = copy.deepcopy(partial)
        current["revision_history"][0]["result_evidence"] = []
        with self.assertRaisesRegex(ValueError, "removed"):
            closure.validate_revisions(self.root, current, partial)

    def test_revision_baselines_cover_terminal_records_not_only_due_work(self):
        previous = dict(id="old", stage="rejected", hypothesis="original mechanism")
        current = dict(previous, stage="implementation", next_action="Run frozen repair",
                       evidence=[self.evidence], revision_history=[self.revision()])
        context = dict(research_work=dict(candidates=[], revision_baselines={"old": previous}))
        with self.assertRaisesRegex(ValueError, "reopen authorization"):
            closure.validate_work(self.root, context, [current], dict(gpu_queues={}))
        current["reopen_authorization"] = self.evidence
        closure.validate_work(self.root, context, [current], dict(gpu_queues={}))
        passed = dict(id="closed-revision", stage="complete", hypothesis="same",
                      next_action="Preserve result", evidence=[self.evidence],
                      revision_history=[self.revision(result="failed")])
        context["research_work"]["revision_baselines"] = {passed["id"]: copy.deepcopy(passed)}
        passed["revision_history"][0]["result"] = "passed"
        with self.assertRaisesRegex(ValueError, "rewritten"):
            closure.validate_work(self.root, context, [passed], dict(gpu_queues={}))

    def test_reserve_only_postflight_needs_progress_and_forbids_queue_growth(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text("\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text("\n".join("## " + s for s in sections))
        historical = dict(id="old-rejected", stage="rejected", next_action="Preserve evidence",
                          evidence=[self.evidence])
        context = dict(generated_at="2026-01-01T00:00:00+00:00", mode="design",
                       preflight=dict(monitor_rc=0, goal_rc=0),
                       queue=dict(candidate_budget=0, recorded_ids=["already-running"]),
                       research_work=dict(candidates=[], reserve_only=True, reserve_budget=1,
                                          progress_baselines={
                                              historical["id"]: closure.candidate_progress(historical)}))
        (headless / ".tick_context.json").write_text(json.dumps(context))
        queue = dict(gpu_queues={"server": [
            dict(id="already-running", status="running")]})
        queue_path = self.root / "pipeline/queue.json"
        queue_path.write_text(json.dumps(queue))
        work_path = self.root / "pipeline/research_work.json"
        work_path.write_text(json.dumps(dict(candidates=[historical])))
        with self.assertRaisesRegex(ValueError, "no durable candidate progress"):
            closure.postflight(self.root)
        candidate = dict(id="reserve", stage="diagnosis", next_action="Run matched control",
                         evidence=[self.evidence])
        work_path.write_text(json.dumps(dict(candidates=[historical, candidate])))
        closure.postflight(self.root)
        queue["gpu_queues"]["server"].append(dict(id="unauthorized-new", status="waiting"))
        queue_path.write_text(json.dumps(queue))
        with self.assertRaisesRegex(ValueError, "Reserve-only"):
            closure.postflight(self.root)
        queue["gpu_queues"]["server"].pop()
        queue_path.write_text(json.dumps(queue))
        work_path.write_text(json.dumps(dict(candidates=[
            historical, candidate, dict(candidate, id="extra")])))
        with self.assertRaisesRegex(ValueError, "creation budget"):
            closure.postflight(self.root)

    def test_pending_excludes_historical_closed_but_keeps_actionable_work(self):
        candidates = [
            {"id": "historical", "stage": "closed"},
            {"id": "rejected", "stage": "rejected"},
            {"id": "complete", "stage": "complete"},
            {"id": "training", "stage": "training"},
            {"id": "diagnosis", "stage": "diagnosis"},
            {"id": "retry", "stage": "blocked"},
        ]
        (self.root / "pipeline/research_work.json").write_text(
            json.dumps({"candidates": candidates}))
        self.assertEqual(
            [candidate["id"] for candidate in closure.pending(self.root)],
            ["diagnosis", "retry"])

    def test_valid_admission(self):
        self.save()
        self.assertEqual(closure.admission(self.root, self.task)["id"], "test")

    def test_cli_requires_enabled_policy_when_requested(self):
        with patch.dict(os.environ, {"PROJECT_ROOT": str(self.root.parent)}):
            with patch.object(closure, "postflight") as check:
                self.assertEqual(closure.main([self.root.name, "--require-enabled"]), 2)
                self.assertEqual(closure.main([self.root.name]), 0)
                check.assert_not_called()
                (self.root / "pipeline/closure_policy.json").write_text('{"enabled":true}')
                self.assertEqual(closure.main([self.root.name, "--require-enabled"]), 0)
                check.assert_called_once_with(self.root)

    def test_deadline_does_not_bypass_durable_integrity(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text("\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text("\n".join("## " + s for s in sections))
        (self.root / "pipeline/goal.json").write_text(json.dumps(
            {"pipeline_policy": {"research_on_capacity_gap": True}}))
        context = dict(generated_at="2026-01-01T00:00:00+00:00", mode="design",
                       deadline_at="2026-01-01T01:00:00+00:00",
                       preflight=dict(monitor_rc=0, goal_rc=0),
                       queue=dict(candidate_budget=2, target_active=2),
                       research_work=dict(candidates=[]))
        (headless / ".tick_context.json").write_text(json.dumps(context))
        active = dict(id="active", stage="diagnosis", next_action="Run native test",
                      evidence=[self.evidence])
        work = self.root / "pipeline/research_work.json"
        cases = [
            ([dict(active, evidence=[dict(self.evidence, sha256="0" * 64)])], "hash mismatch"),
            ([active, active], "Duplicate"),
            ([dict(active, next_action="")], "actionable"),
            ([active, dict(active, id="blocked", stage="blocked")], "retry"),
            ([active, dict(active, id="training", stage="training")], "verified launch"),
        ]
        for candidates, error in cases:
            with self.subTest(error=error):
                work.write_text(json.dumps(dict(candidates=candidates)))
                with self.assertRaisesRegex(ValueError, error):
                    closure.postflight(self.root)
        work.write_text(json.dumps(dict(candidates=[active])))
        closure.postflight(self.root)

    def test_missing_gate(self):
        del self.receipt["gates"]["native_backward"]
        self.save()
        with self.assertRaises(ValueError):
            closure.admission(self.root, self.task)

    def test_optional_research_gates_do_not_block_admission(self):
        del self.receipt["gates"]["derivation"]
        del self.receipt["gates"]["literature"]
        self.save()
        self.assertEqual(closure.admission(self.root, self.task)["id"], "test")

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
        with patch.object(closure, "git", return_value="a" * 40) as git, \
                patch.object(closure.source_integrity, "verify_git") as verify:
            self.assertTrue(closure.safe_sync(self.root, "/code", server, ssh))
        self.assertEqual(verify.call_count, 2)
        commands = " ".join(str(c) for c in ssh.call_args_list + git.call_args_list)
        self.assertIn("--ff-only", commands)
        for bad in ("reset --hard", "stash -u", "clean -fd", "add -A"):
            self.assertNotIn(bad, commands)

    def test_sync_mismatch_fails(self):
        server = {"host": "h", "user": "u", "remote_code_root": "/code"}
        with patch.object(closure, "git", return_value="a" * 40), \
                patch.object(closure.source_integrity, "verify_git"):
            with self.assertRaises(ValueError):
                closure.safe_sync(self.root, "/code", server, Mock(return_value="b" * 40))

    def test_adares_marker_sync_is_restricted(self):
        (self.root / "pipeline/closure_policy.json").write_text(
            '{"sync_strategy":"adares_additive_marker"}')
        server = dict(name="server-2", host="h", user="u", remote_code_root="/code")
        with patch.object(closure, "git", return_value="a" * 40):
            with self.assertRaisesRegex(ValueError, "another project"):
                closure.safe_sync(self.root, self.root, server, Mock())

    def test_adares_marker_sync_verifies_script_and_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "AdaRES_project"
            (root / "pipeline").mkdir(parents=True)
            (root / "scripts").mkdir()
            (root / "scripts/sync.sh").write_text("#!/bin/sh\n")
            (root / "pipeline/closure_policy.json").write_text(
                '{"sync_strategy":"adares_additive_marker"}')
            server = dict(name="server-2", host="h", user="u", remote_code_root="/code")
            remote = Mock(side_effect=["b" * 40, "a" * 40])
            with patch.object(closure, "git", return_value="a" * 40), \
                    patch.object(closure.source_integrity, "verify_marker") as verify:
                with patch("pipeline_monitor.bash_executable", return_value="/bin/bash"):
                    with patch.object(closure.subprocess, "run", return_value=Mock(
                            returncode=0)) as run:
                        self.assertTrue(closure.safe_sync(root, root, server, remote))
            self.assertEqual(verify.call_count, 2)
            self.assertEqual(run.call_args.args[0], [
                "/bin/bash", str(root / "scripts/sync.sh"), "server-2"])
            self.assertEqual(remote.call_count, 2)
            with patch.object(closure, "git", return_value="a" * 40):
                with self.assertRaisesRegex(ValueError, "marker unavailable"):
                    closure.safe_sync(root, root, server, Mock(return_value=""))

    def test_adares_native_launcher_is_restricted(self):
        (self.root / "pipeline/closure_policy.json").write_text(
            '{"launcher":"adares_native"}')
        server = dict(name="server-2", host="h", user="u", remote_code_root="/code")
        with self.assertRaisesRegex(ValueError, "restricted"):
            closure.safe_launch(self.root, server, self.task, 0, Mock())

    def test_adares_native_launcher_uses_single_gpu_native_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "AdaRES_project"
            (root / "pipeline").mkdir(parents=True)
            (root / "pipeline/closure_policy.json").write_text(
                '{"launcher":"adares_native"}')
            server = dict(name="server-2", host="h", user="u", remote_code_root="/code",
                          python="/conda/bin/python", site_packages="/conda/site",
                          pointnet_egg="/pointnet.egg")
            task = dict(self.task, config="configs_song/model_paper5/test.yaml")

            def respond(host, user, command):
                import shlex
                program = shlex.split(command)[-1]
                self.assertIn("'--num_gpus','1'", program)
                self.assertIn("'-S','tools/train.py'", program)
                self.assertIn("/pointnet.egg", command)
                self.assertIn(".codex_source_commit", command)
                import re
                log = re.search(r"/code/logs/train_test_\d{8}_\d{6}\.log", program).group()
                return json.dumps(dict(pid=123, log=log))

            self.assertEqual(closure.safe_launch(root, server, task, 1, respond)["pid"], 123)
            with self.assertRaisesRegex(ValueError, "outside authorized"):
                closure.safe_launch(root, server, task, 7, Mock())

    def test_frozen_legacy_terminal_records_do_not_admit_changed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "AdaRES_project"
            (root / "pipeline").mkdir(parents=True)
            historical = dict(id="old", stage="closed", next_action="Keep history",
                              evidence=[dict(path="missing.json")])
            snapshot = root / "pipeline/legacy.json"
            snapshot.write_text(json.dumps(dict(
                research_work=dict(candidates=[historical]))))
            (root / "pipeline/closure_policy.json").write_text(json.dumps(dict(
                legacy_terminal_snapshot=dict(
                    path="pipeline/legacy.json", sha256=closure.digest(snapshot)))))
            queue = dict(gpu_queues={})
            closure.validate_work(root, {}, [historical], queue)
            closure.validate_work(root, dict(
                research_work=dict(candidates=[historical])), [historical], queue)
            with self.assertRaisesRegex(ValueError, "invalid stage"):
                closure.validate_work(root, {}, [dict(historical, next_action="Changed")], queue)
            with self.assertRaisesRegex(ValueError, "Missing"):
                closure.validate_work(root, {}, [dict(historical, stage="complete")], queue)
            snapshot.write_text("{}")
            with self.assertRaisesRegex(ValueError, "snapshot hash mismatch"):
                closure.validate_work(root, {}, [historical], queue)

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

    def test_postflight_accepts_phase1_goal_status(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text("\n".join(f"## {n}. Section" for n in range(6)))
        (headless / ".tick_context.json").write_text(json.dumps({
            "generated_at": "2026-01-01T00:00:00+00:00", "mode": "event",
            "preflight": {"monitor_rc": 0, "goal_rc": 4}}))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue", "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text("\n".join("## " + s for s in sections))
        closure.postflight(self.root)

    def test_postflight_rejects_unknown_goal_status(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        (headless / ".tick_context.json").write_text(json.dumps({
            "preflight": {"monitor_rc": 0, "goal_rc": 2}}))
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

    def test_resource_block_requires_occupied_authorized_gpu(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        (self.root / "pipeline/reports").mkdir()
        (self.root / "pipeline/reports/summary_test.md").write_text(
            "\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text(
            "\n".join("## " + s for s in sections))
        context = dict(generated_at="2026-01-01T00:00:00+00:00", mode="event",
                       preflight=dict(monitor_rc=0, goal_rc=0),
                       queue=dict(servers=[dict(name="server-1", allowed_gpus=[0],
                                                max_tasks_per_gpu=1)],
                                  active_tasks=[dict(server="server-1", gpu=0)]))
        (headless / ".tick_context.json").write_text(json.dumps(context))
        candidate = dict(id="probe", stage="blocked", blocker="training occupies GPU",
                         blocker_kind="exclusive_gpu_slot", required_server="server-1",
                         retry_after="2026-01-01T01:00:00+00:00",
                         unblock_condition="GPU idle with lease",
                         next_action="Run task probe", evidence=[self.evidence])
        work = self.root / "pipeline/research_work.json"
        work.write_text(json.dumps(dict(candidates=[candidate])))
        closure.postflight(self.root)
        context["queue"]["active_tasks"] = []
        (headless / ".tick_context.json").write_text(json.dumps(context))
        with self.assertRaisesRegex(ValueError, "queue opening"):
            closure.postflight(self.root)
        context["queue"]["active_tasks"] = [dict(server="server-1", gpu=None)]
        (headless / ".tick_context.json").write_text(json.dumps(context))
        closure.postflight(self.root)
        context["queue"]["active_tasks"] = [dict(server="server-1", gpu=99)]
        (headless / ".tick_context.json").write_text(json.dumps(context))
        closure.postflight(self.root)
        context["queue"]["active_tasks"] = [dict(server="server-1", gpu=0)]
        (headless / ".tick_context.json").write_text(json.dumps(context))
        candidate["retry_after"] = "2026-01-01T01:00:00"
        work.write_text(json.dumps(dict(candidates=[candidate])))
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            closure.postflight(self.root)

    def test_capacity_gap_design_requires_durable_candidate_progress(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text(
            "\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text(
            "\n".join("## " + s for s in sections))
        previous = dict(id="existing", stage="rejected", next_action="Do not retry",
                        evidence=[self.evidence])
        context = dict(generated_at="2026-01-01T00:00:00+00:00", mode="design",
                       preflight=dict(monitor_rc=0, goal_rc=0),
                       queue=dict(candidate_budget=1),
                       research_work=dict(candidates=[previous]))
        (headless / ".tick_context.json").write_text(json.dumps(context))
        work_path = self.root / "pipeline/research_work.json"
        work_path.write_text(json.dumps(dict(candidates=[previous])))
        with self.assertRaisesRegex(ValueError, "no durable candidate progress"):
            closure.postflight(self.root)
        candidate = dict(id="new-diagnostic", stage="diagnosis",
                         next_action="Run native control", evidence=[self.evidence])
        work_path.write_text(json.dumps(dict(candidates=[previous, candidate])))
        closure.postflight(self.root)

    def test_capacity_gap_reject_only_requires_continuation_or_evidenced_stop(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text(
            "\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text(
            "\n".join("## " + s for s in sections))
        (self.root / "pipeline/goal.json").write_text(json.dumps(
            {"pipeline_policy": {"research_on_capacity_gap": True}}))
        (headless / ".tick_context.json").write_text(json.dumps(dict(
            generated_at="2026-01-01T00:00:00+00:00", mode="design",
            preflight=dict(monitor_rc=0, goal_rc=0),
            queue=dict(candidate_budget=2, target_active=2),
            research_work=dict(candidates=[]))))
        rejected = dict(id="failed", stage="rejected", next_action="Preserve evidence",
                        evidence=[self.evidence])
        work_path = self.root / "pipeline/research_work.json"
        work_path.write_text(json.dumps(dict(candidates=[rejected])))
        with self.assertRaisesRegex(ValueError, "Capacity gap remains"):
            closure.postflight(self.root)
        active = dict(id="next", stage="diagnosis",
                      next_action="Run native test", evidence=[self.evidence])
        work_path.write_text(json.dumps(dict(candidates=[rejected, active])))
        with self.assertRaisesRegex(ValueError, "executable research"):
            closure.postflight(self.root)
        context = json.loads((headless / ".tick_context.json").read_text())
        context["deadline_at"] = "2026-01-01T01:00:00+00:00"
        (headless / ".tick_context.json").write_text(json.dumps(context))
        closure.postflight(self.root)
        work_path.write_text(json.dumps(dict(
            candidates=[rejected],
            design_cycle=dict(
                stop_reason="independent_routes_exhausted",
                attempted_ids=["failed"],
                resume_condition="New independent task evidence",
                evidence=[self.evidence]))))
        context["deadline_at"] = "2099-01-01T00:00:00+00:00"
        (headless / ".tick_context.json").write_text(json.dumps(context))
        with self.assertRaisesRegex(ValueError, "Early stop"):
            closure.postflight(self.root)
        context = json.loads((headless / ".tick_context.json").read_text())
        context["deadline_at"] = "2026-01-01T01:00:00+00:00"
        (headless / ".tick_context.json").write_text(json.dumps(context))
        closure.postflight(self.root)
        work_path.write_text(json.dumps(dict(
            candidates=[rejected],
            design_cycle=dict(
                stop_reason="independent_routes_exhausted",
                attempted_ids=["failed"],
                resume_condition="New evidence"))))
        with self.assertRaisesRegex(ValueError, "hashed evidence"):
            closure.postflight(self.root)
        work_path.write_text(json.dumps(dict(
            candidates=[rejected],
            design_cycle=dict(
                stop_reason="independent_routes_exhausted",
                attempted_ids=["old-unrelated"],
                resume_condition="New evidence", evidence=[self.evidence]))))
        with self.assertRaisesRegex(ValueError, "this tick's candidate progress"):
            closure.postflight(self.root)
        work_path.write_text(json.dumps(dict(
            candidates=[rejected],
            design_cycle=dict(
                stop_reason="tick_deadline_near",
                attempted_ids=["failed"],
                resume_condition="Resume independent diagnosis",
                evidence=[self.evidence]))))
        context.pop("deadline_at")
        (headless / ".tick_context.json").write_text(json.dumps(context))
        with self.assertRaisesRegex(ValueError, "scheduler deadline"):
            closure.postflight(self.root)
        context = json.loads((headless / ".tick_context.json").read_text())
        context["deadline_at"] = "2099-01-01T00:00:00+00:00"
        (headless / ".tick_context.json").write_text(json.dumps(context))
        with self.assertRaisesRegex(ValueError, "not near"):
            closure.postflight(self.root)
        context["deadline_at"] = "2026-01-01T01:00:00+00:00"
        (headless / ".tick_context.json").write_text(json.dumps(context))
        closure.postflight(self.root)
        work_path.write_text(json.dumps(dict(
            candidates=[rejected],
            design_cycle=dict(
                stop_reason="external_resource_blocked",
                attempted_ids=["failed"],
                resume_condition="GPU available",
                evidence=[self.evidence]))))
        with self.assertRaisesRegex(ValueError, "blocked candidate"):
            closure.postflight(self.root)

    def test_completed_candidate_does_not_require_fake_progress(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text("\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue", "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text("\n".join("## " + s for s in sections))
        candidate = dict(id="test", stage="complete", next_action="Preserve result", evidence=[self.evidence])
        (self.root / "pipeline/research_work.json").write_text(json.dumps(dict(candidates=[candidate])))
        (headless / ".tick_context.json").write_text(json.dumps(dict(
            generated_at="2026-01-01T00:00:00+00:00", mode="event",
            preflight=dict(monitor_rc=0, goal_rc=4),
            research_work=dict(candidates=[candidate]))))
        closure.postflight(self.root)

    def test_training_hypothesis_resolves_explicit_experiment(self):
        headless = self.root / "pipeline/headless"
        headless.mkdir()
        reports = self.root / "pipeline/reports"
        reports.mkdir()
        (reports / "summary_test.md").write_text("\n".join(f"## {n}. Section" for n in range(6)))
        sections = ("Goal And Phase", "Champion And Baseline", "Active Hypotheses",
                    "Closed Or Failed Directions", "Running And Queue",
                    "Open Questions And Risks", "Last Tick")
        (self.root / "pipeline/codex_memory.md").write_text("\n".join("## " + s for s in sections))
        (headless / ".tick_context.json").write_text(json.dumps(dict(
            generated_at="2026-01-01T00:00:00+00:00", mode="event",
            preflight=dict(monitor_rc=0, goal_rc=0))))
        candidate = dict(id="hypothesis", experiment_id="M197-PIRS", stage="training",
                         next_action="Evaluate terminal outputs", evidence=[self.evidence])
        (self.root / "pipeline/research_work.json").write_text(json.dumps(
            dict(candidates=[candidate])))
        queue_path = self.root / "pipeline/queue.json"
        for task_id, verified, expected in (
                ("M197-PIRS", True, True), ("M197-PIRS", False, False),
                ("hypothesis", True, False), ("unrelated", True, False)):
            with self.subTest(task_id=task_id, verified=verified):
                queue_path.write_text(json.dumps(dict(gpu_queues={
                    "7": [dict(id=task_id, launch_verified=verified)]})))
                if expected:
                    closure.postflight(self.root)
                else:
                    with self.assertRaisesRegex(ValueError, "verified launch"):
                        closure.postflight(self.root)
        candidate.pop("experiment_id")
        (self.root / "pipeline/research_work.json").write_text(json.dumps(
            dict(candidates=[candidate])))
        queue_path.write_text(json.dumps(dict(gpu_queues={
            "7": [dict(id="hypothesis", launch_verified=True)]})))
        closure.postflight(self.root)
        queue_path.write_text(json.dumps(dict(gpu_queues={
            "7": [dict(id="hypothesis", launch_verified=True)] * 2})))
        with self.assertRaisesRegex(ValueError, "verified launch"):
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

    def launch_tmpdir_fragment(self):
        import ast
        import shlex
        captured = []
        (self.root / "pipeline/closure_policy.json").write_text('{"path_mappings":[]}')
        server = dict(host="h", user="u", remote_code_root="/code",
                      conda_source="/conda.sh", conda_env="env")

        def respond(host, user, command):
            import re
            captured.append(shlex.split(command)[-1])
            log = re.search(r"/code/logs/train_test_\d{8}_\d{6}\.log", command).group()
            return json.dumps(dict(pid=123, log=log))

        closure.safe_launch(self.root, server, self.task, 0, respond)
        nodes = ast.parse(captured[0]).body
        start = next(i for i, node in enumerate(nodes) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == "_td" for target in node.targets))
        fragment = ast.Module(body=nodes[start:start + 3], type_ignores=[])
        return compile(ast.fix_missing_locations(fragment), "native_tmpdir_fragment", "exec")

    def test_native_launch_preserves_configured_short_tmpdir(self):
        import pathlib
        configured = self.root / "short-ipc"
        env = {"TMPDIR": str(configured)}
        exec(self.launch_tmpdir_fragment(), dict(env=env, root=str(self.root / "deep/code"),
                                                os=os, pathlib=pathlib))
        self.assertEqual(env["TMPDIR"], str(configured))
        self.assertTrue(configured.is_dir())

    def test_native_launch_keeps_project_local_default_without_override(self):
        import pathlib
        env = {}
        code = self.root / "deployment/code"
        exec(self.launch_tmpdir_fragment(), dict(env=env, root=str(code), os=os, pathlib=pathlib))
        self.assertEqual(env["TMPDIR"], str(code.parent / "pipeline/tmp"))
        self.assertTrue(Path(env["TMPDIR"]).is_dir())


class PendingLimitTests(unittest.TestCase):
    def test_steady_postflight_cannot_hide_new_pending_overflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pipeline = root / "pipeline"
            (pipeline / "headless").mkdir(parents=True)
            (pipeline / "reports").mkdir()
            context = {"mode": "steady", "generated_at": "2026-01-01T00:00:00+00:00",
                       "preflight": {"monitor_rc": 0, "goal_rc": 0},
                       "research_work": {"pending_limit": 0, "pending_ids": []}}
            (pipeline / "headless/.tick_context.json").write_text(json.dumps(context))
            (pipeline / "reports/summary_test.md").write_text(
                "\n".join(f"## {i}. Section" for i in range(6)))
            (pipeline / "research_work.json").write_text(json.dumps({
                "candidates": [dict(id="unexpected", stage="blocked")]}))
            with self.assertRaisesRegex(ValueError, "Pending candidate limit"):
                closure.postflight(root)

    def test_limit_counts_parked_and_queued_candidates_once(self):
        context = {"research_work": {"pending_limit": 1, "pending_ids": []}}
        candidates = [dict(id="stable", experiment_id="queued", stage="blocked")]
        queue = {"gpu_queues": {"gpu": [dict(id="queued", status="waiting")]}}
        closure.validate_pending_limit(context, candidates, queue)
        candidates.append(dict(id="extra", stage="blocked"))
        with self.assertRaisesRegex(ValueError, "Pending candidate limit"):
            closure.validate_pending_limit(context, candidates, queue)

    def test_legacy_overflow_is_preserved_but_cannot_grow(self):
        context = {"research_work": {"pending_limit": 1, "pending_ids": ["a", "b"]}}
        candidates = [dict(id=name, stage="blocked") for name in ("a", "b")]
        queue = {"gpu_queues": {}}
        closure.validate_pending_limit(context, candidates, queue)
        candidates.append(dict(id="c", stage="diagnosis"))
        with self.assertRaisesRegex(ValueError, "Pending candidate limit"):
            closure.validate_pending_limit(context, candidates, queue)
        for c in candidates[:2]:
            c["stage"] = "rejected"
        closure.validate_pending_limit(context, candidates, queue)

    def test_in_flight_legacy_context_is_not_retroactively_capped(self):
        closure.validate_pending_limit({}, [dict(id=str(i), stage="blocked")
                                            for i in range(10)], {"gpu_queues": {}})
        for limit in (-1, True, "8"):
            with self.assertRaisesRegex(ValueError, "Invalid pending"):
                closure.validate_pending_limit({"research_work": {"pending_limit": limit}},
                                               [], {"gpu_queues": {}})


if __name__ == "__main__":
    unittest.main()
