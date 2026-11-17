import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_role_capture_coverage_20260927.py")
spec = importlib.util.spec_from_file_location("role_capture_coverage", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RoleCoverageTests(unittest.TestCase):
    def setUp(self):
        self.seed = json.loads(module.SEED.read_text(encoding="utf-8"))
        self.role = json.loads(module.ROLE.read_text(encoding="utf-8"))

    def test_frozen_denominators(self):
        result = module.audit(self.seed, self.role)
        self.assertEqual(result["arms"]["covered"]["expressions"], 20)
        self.assertEqual(result["arms"]["uncovered"]["expressions"], 108)
        self.assertFalse(result["admission"])

    def test_unbound_role_fails_closed(self):
        self.role["role_gradient_rows"][0]["target_ann"] = -1
        with self.assertRaises(ValueError):
            module.audit(self.seed, self.role)

    def test_target_size_binding_fails_closed(self):
        self.seed["target_seed_direction_rows"][0]["ann_id"] = -1
        with self.assertRaises(ValueError):
            module.audit(self.seed, self.role)


if __name__ == "__main__":
    unittest.main()
