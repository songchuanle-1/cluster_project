import ast
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock


SOURCE = (
    Path(os.environ.get("PROJECT_ROOT", "D:/project"))
    / ".claude/skills/songcl_research_pipeline/pipeline_monitor.py"
)


class MiouFallbackTest(unittest.TestCase):
    def parse(self, text):
        # Isolate the parser from the monitor's process and filesystem setup.
        tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "parse_miou_from_logs"
        )

        def ssh(host, user, command, timeout=15):
            command = command.replace("'fixture.log'", "-")
            result = subprocess.run(
                ["bash", "-c", command], input=text, text=True,
                encoding="utf-8", capture_output=True, timeout=timeout,
            )
            return result.stdout.strip()

        namespace = {"ssh": ssh, "parse_overall_miou": lambda text: ""}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"),
             namespace)
        return namespace["parse_miou_from_logs"](["fixture.log"], "", "")

    def test_excludes_superpoint_metrics(self):
        result = self.parse(
            "mIOU: 0.493. Acc_50: 0.548\nspmIOU: 0.457\n"
            "mIOU: 0.489. Acc_50: 0.543\nspmIOU: 0.453\n"
            "mIOU: 0.490. Acc_50: 0.543\nspmIOU: 0.453\n"
        )
        self.assertEqual(result, ([0.493, 0.489, 0.490], 0.493, 2))

    def test_preserves_precise_primary_format(self):
        result = self.parse("mIoU : 0.49349165\nmIoU : 0.49053207\n")
        self.assertEqual(result, ([0.49349165, 0.49053207], 0.49349165, 1))

    def test_precise_improvement_hidden_by_rounding(self):
        result = self.parse(
            "mIoU : 0.4955331683\nmIOU: 0.496. Acc_50: 0.547\n"
            "spmIOU: 0.459\n"
            "mIoU : 0.4962787926\nmIOU: 0.496. Acc_50: 0.548\n"
            "spmIOU: 0.459\n"
        )
        self.assertEqual(result, ([0.4955331683, 0.4962787926], 0.4962787926, 0))


class LiveMetricLogTest(unittest.TestCase):
    def run_parser(self, targets, precise=None, resume_path=None, logs=None):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "parse_running_miou"
        )
        rounded = ([0.496, 0.493, 0.496], 0.496, 2)
        parser = Mock(side_effect=[rounded, precise])
        ssh = Mock(return_value=targets)
        namespace = {"ssh": ssh, "parse_miou_from_logs": parser}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), "exec"),
             namespace)
        result = namespace["parse_running_miou"](
            logs or ["/code/logs/train_model.log"], 123, "model",
            "/work dir", "host", "user", resume_path,
        )
        return result, parser, ssh

    def test_uses_only_logger_opened_by_same_pid(self):
        precise = ([0.4955331683, 0.4933, 0.4962787926], 0.4962787926, 0)
        result, parser, ssh = self.run_parser(
            "/code/logs/train_model.log\n/work dir/model/run/run.log\n"
            "/work dir/model/run/run.log\n/work dir/model_other/run/run.log\n",
            precise,
        )
        self.assertEqual(result, precise)
        self.assertEqual(parser.call_args.args[0], ["/work dir/model/run/run.log"])
        self.assertIn("/proc/123/fd/*", ssh.call_args.args[2])

    def test_no_matching_live_logger_preserves_fallback(self):
        result, parser, _ = self.run_parser(
            "/work dir/model_other/run/run.log\n"
            "/work dir/model/run/run.log (deleted)\n"
        )
        self.assertEqual(result[2], 2)
        self.assertEqual(parser.call_count, 1)

    def test_ambiguous_live_loggers_are_not_combined(self):
        result, parser, _ = self.run_parser(
            "/work dir/model/old/old.log\n/work dir/model/new/new.log\n"
        )
        self.assertEqual(result[2], 2)
        self.assertEqual(parser.call_count, 1)

    def test_resume_lineage_is_not_replaced(self):
        result, parser, ssh = self.run_parser(
            "/work dir/model/run/run.log\n", resume_path="/old/last.pth"
        )
        self.assertEqual(result[2], 2)
        self.assertEqual(parser.call_count, 1)
        ssh.assert_not_called()

    def test_multiple_log_lineages_are_not_replaced(self):
        result, parser, ssh = self.run_parser(
            "/work dir/model/run/run.log\n", logs=["old.log", "current.log"]
        )
        self.assertEqual(result[2], 2)
        self.assertEqual(parser.call_count, 1)
        ssh.assert_not_called()

    def test_incomplete_or_mismatched_logger_defers_early_stop(self):
        for precise in [
            ([0.4955331683], 0.4955331683, 0),
            ([0.4955331683, 0.4900, 0.4962787926], 0.4962787926, 0),
            (None, None, None),
        ]:
            with self.subTest(precise=precise):
                result, _, _ = self.run_parser("/work dir/model/run/run.log", precise)
                self.assertEqual(result, (None, None, None))


if __name__ == "__main__":
    unittest.main()
