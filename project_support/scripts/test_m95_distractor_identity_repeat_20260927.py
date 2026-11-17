import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_distractor_identity_repeat_20260927.py")
spec = importlib.util.spec_from_file_location("identity_repeat", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IdentityRepeatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first = json.loads(module.FIRST.read_text(encoding="utf-8"))
        cls.second = json.loads(module.SECOND.read_text(encoding="utf-8"))

    def test_frozen_capture(self):
        result = module.analyze(self.first, self.second)
        self.assertFalse(result["admission"])

    def test_changed_target_fails(self):
        second = copy.deepcopy(self.second)
        second["rows"][0]["target_instances"] = [-100]
        with self.assertRaisesRegex(ValueError, "Target physical"):
            module.analyze(self.first, second)

    def test_identity_drift_fails(self):
        second = copy.deepcopy(self.second)
        second["rows"][0]["scene"] = "unseen"
        with self.assertRaisesRegex(ValueError, "identity set"):
            module.analyze(self.first, second)


if __name__ == "__main__":
    unittest.main()
