import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_role_selected_context_20260927.py")
spec = importlib.util.spec_from_file_location("role_selected_context", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RoleSelectedContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = json.loads(module.SEED.read_text(encoding="utf-8"))
        cls.role = json.loads(module.ROLE.read_text(encoding="utf-8"))

    def test_frozen_population(self):
        result = module.analyze(self.seed, self.role)
        self.assertEqual(sum(r["expressions"] for r in result["arms"].values()), 128)
        self.assertEqual(len(result["exposed"]), 17)
        self.assertFalse(result["admission"])

    def test_input_drift_fails_closed(self):
        role = copy.deepcopy(self.role)
        role["rows"][0]["batch_input_sha256"] = "invalid"
        with self.assertRaisesRegex(ValueError, "drift"):
            module.analyze(self.seed, role)

    def test_outcome_drift_fails_closed(self):
        role = copy.deepcopy(self.role)
        role["rows"][0]["selected_mask_iou"] = -1.0
        with self.assertRaisesRegex(ValueError, "drift"):
            module.analyze(self.seed, role)


if __name__ == "__main__":
    unittest.main()
