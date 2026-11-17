import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_target_zero_failure_20260927.py")
spec = importlib.util.spec_from_file_location("target_zero_failure", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TargetZeroTests(unittest.TestCase):
    def setUp(self):
        self.seeds = json.loads(module.SEEDS.read_text(encoding="utf-8"))
        self.roles = json.loads(module.ROLES.read_text(encoding="utf-8"))

    def test_frozen_join_and_denominators(self):
        result = module.analyze(self.seeds, self.roles)
        self.assertEqual(result["physical_positions"], 139)
        self.assertEqual(result["paired_scenes"], len(result["detail"]))
        self.assertFalse(result["admission"])

    def test_identity_failure_closed(self):
        self.roles["role_gradient_rows"][0]["target_ann"] = -1
        with self.assertRaises(ValueError):
            module.analyze(self.seeds, self.roles)


if __name__ == "__main__":
    unittest.main()
