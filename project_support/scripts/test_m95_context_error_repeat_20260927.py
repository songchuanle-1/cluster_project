import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_context_error_repeat_20260927.py")
spec = importlib.util.spec_from_file_location("context_repeat", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContextRepeatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first = json.loads(module.FIRST.read_text(encoding="utf-8"))
        cls.second = json.loads(module.SECOND.read_text(encoding="utf-8"))

    def test_frozen_population(self):
        result = module.analyze(self.first, self.second)
        self.assertEqual(result["expressions"], 128)
        self.assertFalse(result["admission"])

    def test_duplicate_fails(self):
        second = copy.deepcopy(self.second)
        second["rows"][1]["ann_id"] = second["rows"][0]["ann_id"]
        second["rows"][1]["scene"] = second["rows"][0]["scene"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.analyze(self.first, second)

    def test_nonindependent_input_fails(self):
        second = copy.deepcopy(self.second)
        second["rows"][0]["batch_input_sha256"] = self.first["rows"][0]["batch_input_sha256"]
        with self.assertRaisesRegex(ValueError, "unchanged"):
            module.analyze(self.first, second)


if __name__ == "__main__":
    unittest.main()
