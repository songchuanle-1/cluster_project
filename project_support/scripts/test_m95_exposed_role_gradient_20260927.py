import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_exposed_role_gradient_20260927.py")
spec = importlib.util.spec_from_file_location("exposed_role", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExposedRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = json.loads(module.SEED.read_text(encoding="utf-8"))
        cls.role = json.loads(module.ROLE.read_text(encoding="utf-8"))

    def test_frozen_capture(self):
        result = module.analyze(self.seed, self.role)
        self.assertEqual(sum(g["expressions"] for g in result["groups"].values()), 20)
        self.assertFalse(result["admission"])

    def test_input_drift_fails(self):
        role = copy.deepcopy(self.role)
        role["rows"][0]["batch_input_sha256"] = "invalid"
        with self.assertRaisesRegex(ValueError, "drift"):
            module.analyze(self.seed, role)

    def test_missing_role_target_fails(self):
        role = copy.deepcopy(self.role)
        role["role_gradient_rows"][0]["target_ann"] = -1
        with self.assertRaisesRegex(ValueError, "binding"):
            module.analyze(self.seed, role)


if __name__ == "__main__":
    unittest.main()
