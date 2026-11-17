"""CPU-only tests for scene weighting and paired-bootstrap bookkeeping."""
import ast
from collections import defaultdict
from pathlib import Path
import unittest

import numpy as np

path = Path(__file__).with_name("verify_d1_expansion_20260911.py")
fn = next(n for n in ast.parse(path.read_text()).body
          if isinstance(n, ast.FunctionDef) and n.name == "scene_summary")
ns = dict(np=np, defaultdict=defaultdict)
exec(compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec"), ns)
summary = ns["scene_summary"]
FIELDS = ("selected_iou", "oracle_iou", "bank_limitation", "selection_gap",
          "acc50", "recoverable_failure50", "bank_failure50")


def row(scene, value):
    return dict(scene_id=scene, **{f: value for f in FIELDS})


class SceneTests(unittest.TestCase):
    def test_constant_scene_bootstrap(self):
        result = summary([row(s, .25) for s in ("scene0001_00", "scene0002_00")
                          for _ in range(4)])
        self.assertEqual(result["complete_scenes"], 2)
        self.assertEqual(result["complete_scene_bootstrap95"]["selected_iou"],
                         dict(mean=.25, low=.25, high=.25))

    def test_incomplete_scene_excluded_from_ci(self):
        rows = [row(s, .25) for s in ("scene0001_00", "scene0002_00") for _ in range(4)]
        result = summary(rows + [row("scene0003_00", 1)])
        self.assertEqual(result["descriptions"], 9)
        self.assertEqual(result["incomplete_scenes"], ["scene0003"])
        self.assertEqual(result["complete_scene_bootstrap95"]["selected_iou"]["mean"], .25)
        self.assertAlmostEqual(result["description_mean"]["selected_iou"], 1 / 3)

    def test_repeat_scan_physical_grouping(self):
        rows = [row("scene0001_00", .25), row("scene0001_01", .75)] * 2
        result = summary(rows)
        self.assertEqual(result["physical_scenes"], 1)
        self.assertEqual(result["complete_scene_means"]["scene0001"]["selected_iou"], .5)
        self.assertNotIn("complete_scene_bootstrap95", result)

    def test_negative_paired_delta_and_determinism(self):
        rows = [row(s, v) for s, v in (("scene0001_00", -.2), ("scene0002_00", -.1))
                for _ in range(4)]
        a, b = summary(rows), summary(rows)
        self.assertEqual(a, b)
        interval = a["complete_scene_bootstrap95"]["selected_iou"]
        self.assertAlmostEqual(interval["mean"], -.15)
        self.assertLess(interval["high"], 0)


if __name__ == "__main__":
    unittest.main()
