import importlib.util
import json
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("m95_cause_role_overlap_20260927.py")
spec = importlib.util.spec_from_file_location("m95_cause_role_overlap", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CauseRoleOverlapTests(unittest.TestCase):
    def setUp(self):
        self.source = [json.loads(p.read_text(encoding="utf-8"))
                       for p in (module.CAUSE, module.SEED, module.ROLE)]

    def test_frozen_bindings(self):
        result = module.analyze(*self.source)
        self.assertEqual(result["arms"]["covered"]["expressions"], 20)
        self.assertEqual(result["arms"]["uncovered"]["expressions"], 108)
        self.assertFalse(result["admission"])

    def test_selected_iou_drift_fails_closed(self):
        self.source[1]["rows"][0]["selected_mask_iou"] = -1
        with self.assertRaises(ValueError):
            module.analyze(*self.source)

    def test_role_binding_fails_closed(self):
        self.source[2]["role_gradient_rows"][0]["target_ann"] = -1
        with self.assertRaises(ValueError):
            module.analyze(*self.source)


if __name__ == "__main__":
    unittest.main()
