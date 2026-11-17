import ast
from pathlib import Path
import re
import unittest


SOURCE = Path("D:/project/.claude/skills/songcl_research_pipeline/pipeline_monitor.py")


class TerminalMarkerTest(unittest.TestCase):
    def classify(self, tail, cur=27, total=50):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and isinstance(n.test, ast.Call)
                      and "Early stopping at epoch" in ast.unparse(n.test))
        namespace = dict(re=re, tail=tail, cur_ep=cur, total_ep=total,
                         CRASH_KEYWORDS=["Traceback", "CUDA out of memory"])
        exec(compile(ast.Module(body=[branch], type_ignores=[]),
                     str(SOURCE), "exec"), namespace)
        return namespace["state"]

    def test_explicit_normal_stop(self):
        self.assertEqual(self.classify(
            "INFO - Early stopping at epoch 27: no improvement for 10 epochs (best=0.4968)"),
            "done_earlystop")

    def test_crash(self):
        self.assertEqual(self.classify("Traceback"), "crashed")

    def test_unknown(self):
        self.assertEqual(self.classify("validation"), "stopped_unknown")

    def test_complete(self):
        self.assertEqual(self.classify("finished", 50), "done_complete")
