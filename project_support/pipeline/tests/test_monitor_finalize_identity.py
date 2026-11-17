import ast
from datetime import datetime
import os
from pathlib import Path
import unittest
from unittest.mock import Mock


SOURCE = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")


class FinalizeIdentityTest(unittest.TestCase):
    def finalize(self, slot, gpu="0", recorded=None):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef)
                        and node.name == "finalize_task")
        running = {"server-4": {"0": slot}}
        namespace = {
            "os": os, "datetime": datetime,
            "pull_log": Mock(return_value=""),
            "load_experiment": Mock(return_value=recorded),
            "save_experiment": Mock(),
            "load_running": Mock(return_value=running),
            "save_running": Mock(),
            "save_queue": Mock(),
            "ledger_append": Mock(),
        }
        exec(compile(ast.Module(body=[function], type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        task = {"id": "old", "config": "old.yaml"}
        successor = {"id": "new", "config": "new.yaml", "status": "running"}
        queue = {"gpu_queues": {"server-4": [task, successor]}}
        namespace["finalize_task"](
            "project", queue, "server-4", "host", "user", task, "old",
            "done_earlystop", 0.49, "27/50", gpu, "", [])
        self.assertEqual(queue["gpu_queues"]["server-4"], [successor])
        return running

    def test_preserves_successor_on_same_gpu(self):
        self.assertEqual(self.finalize("new"), {"server-4": {"0": "new"}})

    def test_removes_matching_single_owner(self):
        self.assertEqual(self.finalize("old"), {})

    def test_preserves_other_shared_slot_owners(self):
        self.assertEqual(self.finalize(["old", "new"]),
                         {"server-4": {"0": ["new"]}})

    def test_removes_empty_shared_slot(self):
        self.assertEqual(self.finalize(["old"]), {})

    def test_null_preference_uses_recorded_gpu_and_retains_peer(self):
        self.assertEqual(self.finalize(["old", "new"], gpu=None,
                                      recorded={"id": "old", "gpu": "0"}),
                         {"server-4": {"0": ["new"]}})

    def test_unknown_preference_uses_recorded_gpu(self):
        self.assertEqual(self.finalize("old", gpu="?",
                                      recorded={"id": "old", "gpu": "0"}), {})


if __name__ == "__main__":
    unittest.main()
