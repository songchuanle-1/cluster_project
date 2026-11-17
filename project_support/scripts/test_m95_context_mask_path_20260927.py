import copy
import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_context_mask_path_20260927.py")
spec = importlib.util.spec_from_file_location("context_mask", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContextMaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(module.SOURCE.read_text(encoding="utf-8"))

    def test_native_capture(self):
        result = module.analyze(self.source)
        self.assertEqual(sum(x["expressions"] for x in result["arms"].values()), 128)
        self.assertFalse(result["admission"])

    def test_identity_fails(self):
        source = copy.deepcopy(self.source)
        source["rows"][0]["scene"] = source["rows"][1]["scene"]
        source["rows"][0]["ann_id"] = source["rows"][1]["ann_id"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.analyze(source)

    def test_outside_mask_is_counted(self):
        source = copy.deepcopy(self.source)
        source["rows"][0]["selected_seed_in_selected_mask"] = False
        result = module.analyze(source)
        self.assertGreaterEqual(
            sum(x["selected_seed_outside_mask"] for x in result["arms"].values()), 1)


if __name__ == "__main__":
    unittest.main()
