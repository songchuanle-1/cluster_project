import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

import closure
import tick_efficiency as efficiency
import tick_usage
import render_tick_report


class EfficiencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pipeline = self.root / "pipeline"
        (self.pipeline / "headless").mkdir(parents=True)

    def test_actual_pretty_serialization_fits_bound_and_pagination(self):
        candidates = [{"id": str(i), "stage": "design",
                       "next_action": "\u7814" * 10000, "evidence": [{}] * 20}
                      for i in range(40)]
        context = {"mode": "design", "mode_reason": "x" * 15000,
                   "goal": {"metric": {"name": "\u7814" * 5000}},
                   "research_work": {"due_ids": [c["id"] for c in candidates],
                                     "candidates": candidates}}
        view = efficiency.compact_view(context)
        self.assertLessEqual(efficiency.encoded_size(view), efficiency.VIEW_LIMIT)
        self.assertEqual(view["research"]["due_count"], 40)
        self.assertEqual(view["research"]["omitted_due_count"] +
                         len(view["research"]["shown"]), 40)
        ids, offset = [], 0
        while offset is not None:
            page = efficiency.candidate_page(context, offset)
            ids += page["ids"]
            offset = page["next_offset"]
        self.assertEqual(ids, [c["id"] for c in candidates])
        with self.assertRaises(ValueError):
            efficiency.candidate_page(context, -1)

    def test_design_bootstrap_is_explicit_when_no_due_candidates(self):
        context = {
            "mode": "design",
            "queue": {"candidate_budget": 2},
            "research_work": {"due_ids": [], "candidates": []},
        }
        view = efficiency.compact_view(context)
        bootstrap = view["design_bootstrap"]
        self.assertTrue(bootstrap["required"])
        self.assertEqual(bootstrap["candidate_budget"], 2)
        self.assertIn("before broad route review", bootstrap["rule"])

        context["research_work"]["due_ids"] = ["pending"]
        context["research_work"]["candidates"] = [
            {"id": "pending", "stage": "diagnosis",
             "next_action": "Run test", "evidence": [{}]}]
        self.assertNotIn("design_bootstrap", efficiency.compact_view(context))

        context["mode"] = "steady"
        context["research_work"] = {"due_ids": [], "candidates": []}
        self.assertNotIn("design_bootstrap", efficiency.compact_view(context))

    def test_human_handoff_is_bounded_visible_and_not_authorization(self):
        actions = [{"id": str(i), "next_action": "Confirm exact tested files " * 1000,
                    "retry_after": "2099-01-01T00:00:00+00:00"} for i in range(20)]
        context = {"project": "demo", "mode": "steady", "research_work": {
            "due_ids": [], "candidates": [], "deferred": True,
            "deferred_until": actions[0]["retry_after"], "human_actions": actions}}
        view = efficiency.compact_view(context)
        self.assertTrue(view["research"]["deferred"])
        self.assertEqual(len(view["research"]["human_actions"]), efficiency.MAX_DUE)
        self.assertEqual(view["research"]["omitted_human_action_count"], 16)
        self.assertLessEqual(efficiency.encoded_size(view), efficiency.VIEW_LIMIT)
        self.assertTrue(all(len(a["next_action"]) <= 400
                            for a in view["research"]["human_actions"]))
        self.assertNotIn("design_bootstrap", view)
        text = render_tick_report.render(context)
        self.assertIn("待人工确认", text)
        self.assertIn("不代表已授权", text)
        for i in range(6):
            self.assertIn(f"## {i}.", text)

    def test_cooldown_wakes_on_goal_queue_evidence_and_expiry(self):
        evidence = self.root / "test-result.txt"
        evidence.write_text("initial")
        (self.pipeline / "research_work.json").write_text(json.dumps({
            "candidates": [{"evidence": [{"path": evidence.name}]}]}))
        hold_path = self.pipeline / "headless/.research_cooldown.json"
        def reset():
            hold_path.write_text(json.dumps({
                "retry_after": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                "signature": efficiency.research_signature(self.root)}))
        reset()
        self.assertTrue(efficiency.cooldown_active(self.root))
        (self.pipeline / "reports").mkdir()
        (self.pipeline / "reports/summary_a.md").write_text("routine report")
        self.assertTrue(efficiency.cooldown_active(self.root))
        for path in (self.pipeline / "goal.json", self.pipeline / "queue.json", evidence):
            reset()
            path.write_text('{"changed": true}')
            self.assertFalse(efficiency.cooldown_active(self.root))
        reset()
        self.assertFalse(efficiency.cooldown_active(
            self.root, datetime.now(timezone.utc) + timedelta(hours=5)))

    def test_monitor_failures_remain_visible_and_are_bound_to_dispatch(self):
        output = (
            "--- server-4 (example) ---\n  [\u4e0d\u53ef\u8fbe]\n"
            "--- server-2 (example) ---\n"
            "  >>> \u961f\u5217\u63a8\u9001: [Y52 fixed30] on server-2 gpu0\n"
            "  [\u540c\u6b65\u963b\u6b62] Remote source marker unavailable\n"
            "  >>> \u4ee3\u7801\u540c\u6b65\u5931\u8d25\n"
            "  >>> \u961f\u5217\u63a8\u9001: [Y54 fixed30] on server-2 gpu1\n"
            "  [\u540c\u6b65\u963b\u6b62] Remote source marker unavailable\n")
        issues = efficiency.monitor_issues(output)
        self.assertEqual(len(issues), 3)
        self.assertEqual(issues[0]["server"], "server-4")
        self.assertEqual(issues[1]["task"], "Y52 fixed30")
        self.assertEqual(issues[2]["task"], "Y54 fixed30")
        self.assertEqual(issues[1]["reason"], "source_marker")
        self.assertEqual(efficiency.monitor_issues(""), [])
        context = {"project": "demo", "mode": "steady", "queue": {"active_tasks": []},
                   "preflight": {"monitor_rc": 0, "operational_issues": issues}}
        view = efficiency.compact_view(context)
        self.assertEqual(view["preflight"]["operational_issues"], issues)
        text = render_tick_report.render(context)
        self.assertIn("\u4e0d\u662f\u65b0\u6388\u6743\u8bf7\u6c42", text)
        self.assertIn("\u8fdc\u7aef\u8fdb\u7a0b\u987b\u53e6\u6838\u5b9e", text)
        self.assertNotIn("\u5feb\u7167\u5185\u65e0\u8fd0\u884c\u4efb\u52a1", text)

    def test_operational_issue_overflow_is_explicit(self):
        issues = [{"server": str(i), "kind": "connectivity", "reason": "unreachable"}
                  for i in range(10)]
        view = efficiency.compact_view({"mode": "steady", "preflight": {
            "operational_issues": issues}})
        self.assertEqual(len(view["preflight"]["operational_issues"]), 6)
        self.assertEqual(view["preflight"]["omitted_issue_count"], 4)
        self.assertLessEqual(efficiency.encoded_size(view), efficiency.VIEW_LIMIT)

    def test_bootstrap_never_demands_new_id_when_pending_limit_is_full(self):
        context = {"mode": "design", "queue": {"candidate_budget": 2},
                   "research_work": {"pending_limit": 8, "reserve_budget": 0,
                                     "due_ids": [], "candidates": []}}
        self.assertNotIn("design_bootstrap", efficiency.compact_view(context))

    def test_only_evidenced_typed_holds_leave_actionable_reserve(self):
        valid = dict(stage="blocked", blocker_kind="human_revision_authorization",
                     blocker="Revision limit", next_action="Review genuine confirmation",
                     evidence=[{"path": "result.json", "sha256": "a" * 64}],
                     retry_after="2099-01-01T00:00:00+00:00", unblock_condition="Human consent")
        self.assertTrue(efficiency.external_block(valid))
        for change in (dict(evidence=[]), dict(next_action=""),
                       dict(blocker_kind="unknown"), dict(retry_after="2099-01-01"),
                       dict(stage="validation")):
            self.assertFalse(efficiency.external_block(dict(valid, **change)))

    def test_numerical_hold_is_visible_and_never_labelled_human_permission(self):
        hold = dict(stage="blocked", blocker_kind="numerical_control_failure",
                    failure_scope="inconclusive", blocker="Repeated controls disagree",
                    next_action="Use new discriminating numerical evidence",
                    evidence=[{"path": "result.json", "sha256": "a" * 64}],
                    retry_after="2099-01-01T00:00:00+00:00",
                    unblock_condition="A control-preserving measurement repair")
        self.assertTrue(efficiency.parkable_block(hold))
        self.assertFalse(efficiency.external_block(hold))
        context = {"mode": "design", "research_work": {
            "research_wait_count": 2, "pending_count": 2, "pending_limit": 8}}
        view = efficiency.compact_view(context)
        self.assertEqual(view["research"]["research_wait_count"], 2)
        self.assertEqual(view["research"]["human_actions"], [])
        self.assertIn("\u6570\u503c\u8bca\u65ad\u5f85\u89e3 2", render_tick_report.render(context))

    def test_pending_identity_deduplicates_queue_and_excludes_terminal_history(self):
        candidates = [dict(id="stable", experiment_id="run-name", stage="blocked"),
                      dict(id="old", stage="closed"), dict(id="done", stage="rejected"),
                      dict(id="training", stage="training")]
        queued = [dict(id="run-name", status="waiting"), dict(id="claim", status="claiming"),
                  dict(id="training", status="running")]
        self.assertEqual(efficiency.pending_ids(candidates, queued), {"run-name", "claim"})

    def early_fixture(self):
        evidence = self.root / "evidence.txt"
        evidence.write_text("two actual independent test results")
        entry = {"path": evidence.name, "sha256": closure.digest(evidence)}
        candidates = [{"id": str(i), "stage": "rejected", "evidence": [entry],
                       "next_action": "Revisit only with new evidence"} for i in range(2)]
        cycle = {
            "stop_reason": "no_information_gain", "no_gain_reason": "Both controls refute routes",
            "resume_condition": "New dataset evidence",
            "retry_after": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "attempted_ids": ["0", "1"], "evidence": [entry],
            "attempt_results": [{"candidate_id": str(i), "hypothesis_id": str(i),
                                 "test": "matched native control", "result": "refuted",
                                 "evidence": [entry]} for i in range(2)],
        }
        context = {"generated_at": "2026-01-01T00:00:00+00:00"}
        return candidates, cycle, context

    def test_early_stop_evidence_and_no_abandoned_work(self):
        candidates, cycle, context = self.early_fixture()
        closure.validate_early_stop(self.root, context, candidates, cycle)
        candidates.append({"id": "pending", "stage": "diagnosis"})
        with self.assertRaisesRegex(ValueError, "executable"):
            closure.validate_early_stop(self.root, context, candidates, cycle)
        candidates.pop()
        cycle["attempt_results"][1]["hypothesis_id"] = "0"
        with self.assertRaisesRegex(ValueError, "independently"):
            closure.validate_early_stop(self.root, context, candidates, cycle)

    def test_early_stop_rejects_invalid_retry_recycled_and_tampered_evidence(self):
        for issue in ("retry", "old", "tampered"):
            candidates, cycle, context = self.early_fixture()
            if issue == "retry":
                cycle["retry_after"] = "2099-01-01T00:00:00+00:00"
            elif issue == "old":
                context["research_work"] = {"candidates": candidates}
            else:
                (self.root / "evidence.txt").write_text("tampered")
            with self.assertRaises(ValueError):
                closure.validate_early_stop(self.root, context, candidates, cycle)

    def test_early_stop_cannot_recycle_terminal_baselines_from_full_ledger(self):
        candidates, cycle, context = self.early_fixture()
        context["research_work"] = dict(
            candidates=[],
            progress_baselines={c["id"]: closure.candidate_progress(c) for c in candidates})
        with self.assertRaisesRegex(ValueError, "recycle unchanged"):
            closure.validate_early_stop(self.root, context, candidates, cycle)

    def test_usage_deduplicates_response_not_cumulative_totals(self):
        path = self.root / "rollout.jsonl"
        usage = {"input_tokens": 100, "cached_input_tokens": 80,
                 "output_tokens": 8, "reasoning_output_tokens": 3, "total_tokens": 108}
        event = {"type": "token_usage_record", "payload": {
            "thread_id": "t", "response_id": "r", "usage": usage,
            "thread_token_usage": {"total_tokens": 99999}}}
        path.write_text((json.dumps(event) + "\n") * 2)
        start = {"path": str(path), "offset": 0, "inode": path.stat().st_ino, "thread_id": "t"}
        got = tick_usage.collect(start)
        self.assertEqual(got["calls"], 1)
        self.assertEqual(got["total_tokens"], 108)
        self.assertEqual(got["uncached_input_tokens"], 20)
        self.assertEqual(tick_usage.collect(None)["status"], "unavailable")
        start["offset"] = path.stat().st_size
        self.assertIsNone(tick_usage.collect(start)["calls"])
        start["offset"] += 10
        self.assertEqual(tick_usage.collect(start)["reason"], "log_replaced_or_truncated")

    def test_report_complete_and_unknown_not_zero(self):
        text = render_tick_report.render({"project": "demo", "mode": "steady"})
        for i in range(6):
            self.assertIn(f"## {i}.", text)
        self.assertIn("| ID | Config | Server | GPU | Epoch | Best mIoU | Acc@50 | spmIOU | No-Impr | Status |", text)
        self.assertIn("本轮未检查", text)
        self.assertNotIn("0 active", text)
        self.assertNotIn("0% ", text)
        self.assertIn("Next tick:", text)

    def test_reserve_and_funnel_are_visible_without_claiming_training_success(self):
        context = dict(project="demo", mode="design", queue=dict(candidate_budget=0),
                       research_work=dict(reserve_only=True, reserve_target=2,
                                          reserve_count=1, reserve_budget=1),
                       research_funnel=dict(observed=True, candidate_records=3,
                                            stages=dict(rejected=2, validation=1),
                                            rejected_scopes=dict(unclassified=2),
                                            implementation_revisions=1, receipt_files=2))
        text = render_tick_report.render(context)
        self.assertIn("研究储备 1 / 2", text)
        self.assertIn("不代表成功率", text)
        view = efficiency.compact_view(context)
        self.assertTrue(view["research"]["reserve_only"])
        self.assertEqual(view["research_funnel"]["candidate_records"], 3)
        self.assertLessEqual(efficiency.encoded_size(view), efficiency.VIEW_LIMIT)


if __name__ == "__main__":
    unittest.main()
