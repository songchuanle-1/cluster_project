import ast
from pathlib import Path
import unittest
from unittest.mock import Mock


SOURCE = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")


class DispatchHoldTest(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        self.function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                             and n.name == "_process_queue")

    def test_only_held_tasks_do_not_query_or_launch(self):
        ssh = Mock(side_effect=AssertionError("Held tasks must not reach dispatch"))
        namespace = {"ssh": ssh}
        exec(compile(ast.Module(body=[self.function], type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        queue = {"gpu_queues": {"server-4": [
            {"id": "held", "status": "waiting", "dispatch_hold": "profile"}]}}
        namespace["_process_queue"](queue, "server-4", "", "", "", set(), {"0"}, [])
        ssh.assert_not_called()

    def test_eligible_fifo_excludes_holds_and_nonwaiting(self):
        assignment = next(n for n in self.function.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "waiting"
                                  for t in n.targets))
        tasks = [
            {"id": "held", "status": "waiting", "dispatch_hold": "profile"},
            {"id": "first", "status": "waiting"},
            {"id": "active", "status": "running"},
            {"id": "second", "status": "waiting", "dispatch_hold": None},
        ]
        namespace = {"tasks": tasks}
        exec(compile(ast.Module(body=[assignment], type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        self.assertEqual([t["id"] for t in namespace["waiting"]], ["first", "second"])


if __name__ == "__main__":
    unittest.main()
