"""Contract checks for frozen size-stratified gradient audit."""
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "target_size_interaction", HERE / "m95_target_size_interaction_20260927.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SizeInteractionTests(unittest.TestCase):
    def test_frozen_cohort_and_partition(self):
        data = json.loads(module.SOURCE.read_text(encoding="utf-8"))
        result = module.analyze(data)
        self.assertEqual(sum(a["expressions"] for a in result["arms"].values()), 128)
        self.assertEqual(result["contract"], "m95_target_size_interaction_v1")
        self.assertFalse(result["admission"])

    def test_identity_guard(self):
        data = json.loads(module.SOURCE.read_text(encoding="utf-8"))
        data["target_seed_direction_rows"][0]["ann_id"] = -1
        with self.assertRaises(ValueError):
            module.analyze(data)


if __name__ == "__main__":
    unittest.main()
