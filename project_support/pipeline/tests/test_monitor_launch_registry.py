import ast
import copy
from datetime import datetime
import os
from pathlib import Path
import unittest


SOURCE = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")


class LaunchRegistryTest(unittest.TestCase):
    def launch(self, existing):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "_process_queue")
        success = next(n for n in ast.walk(function) if isinstance(n, ast.If)
                       and isinstance(n.test, ast.Name) and n.test.id == "success")
        start = next(i for i, n in enumerate(success.body) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "exp_id"
                             for t in n.targets))
        end = next(i for i, n in enumerate(success.body) if isinstance(n, ast.Expr)
                   and isinstance(n.value, ast.Call)
                   and isinstance(n.value.func, ast.Name)
                   and n.value.func.id == "save_experiment")
        saved = []
        task = {"id": "candidate", "config": "configs/candidate.yaml", "gpu": None}
        namespace = {
            "os": os, "datetime": datetime, "task": task,
            "cfg": task["config"], "srv_name": "server-4", "gpu": "1",
            "project_dir": "unused",
            "load_experiment": lambda *_: copy.deepcopy(existing),
            "save_experiment": lambda _, value: saved.append(copy.deepcopy(value)),
        }
        exec(compile(ast.Module(body=success.body[start:end + 1], type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        self.assertIsNone(task["gpu"])
        self.assertEqual(len(saved), 1)
        result = saved[0]
        self.assertEqual((result["server"], result["gpu"], result["status"]),
                         ("server-4", "1", "running"))
        self.assertEqual(result["history"][-1]["action"], "launched")
        self.assertEqual(result["history"][-1]["gpu"], "1")
        self.assertTrue(result["launched"])
        return result

    def test_pre_registered_task_gets_actual_placement_and_keeps_history(self):
        existing = {
            "id": "candidate", "config": "configs/candidate.yaml",
            "server": "server-6", "gpu": None, "status": "waiting",
            "history": [{"action": "metadata_reconciled", "ts": "original"}],
            "validation_report": "retained.json",
        }
        result = self.launch(existing)
        self.assertEqual(result["history"][:-1], existing["history"])
        self.assertEqual(result["validation_report"], "retained.json")

    def test_new_registry_gets_actual_placement(self):
        self.launch(None)


if __name__ == "__main__":
    unittest.main()
