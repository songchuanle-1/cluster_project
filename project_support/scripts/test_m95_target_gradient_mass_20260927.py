import importlib.util
import unittest
from pathlib import Path

NAME = "m95_target_gradient_mass_20260927"
SPEC = importlib.util.spec_from_file_location(NAME, Path(__file__).with_name(NAME + ".py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TargetGradientMassTest(unittest.TestCase):
    def setUp(self):
        self.data = {"rows": [], "target_seed_direction_rows": []}
        self.old = {"rows": [], "target_seed_direction_rows": []}
        # The cohort guard is deliberately separate from the row checks.
        self.row = {
            "scene": "s", "ann_id": 1, "batch_input_sha256": "a",
            "selected_seed": 0, "selected_mask_iou": 0.0, "topk": [0],
        }
        self.entry = {
            "ann_id": 1, "physical_target_superpoints": 2,
            "scene_superpoints": 10, "valid_fps_count": 3,
            "target_seed_count": 1, "seeds": [[0, 1.0, 0.0, -2.0]],
        }

    def test_different_input_fails_closed(self):
        self.data["rows"] = [self.row] * 128
        self.data["target_seed_direction_rows"] = [self.entry] * 128
        self.old["rows"] = [dict(self.row, batch_input_sha256="changed")] * 128
        self.old["target_seed_direction_rows"] = [self.entry] * 128
        with self.assertRaisesRegex(ValueError, "binding"):
            MODULE.analyze(self.data, self.old)

    def test_different_gradient_fails_closed(self):
        self.data["rows"] = [self.row] * 128
        self.data["target_seed_direction_rows"] = [self.entry] * 128
        self.old["rows"] = [self.row] * 128
        self.old["target_seed_direction_rows"] = [
            dict(self.entry, seeds=[[2, 1.0, 0.0, 2.0]])] * 128
        with self.assertRaisesRegex(ValueError, "seed identity"):
            MODULE.analyze(self.data, self.old)

    def test_invalid_physical_support_fails_closed(self):
        self.data["rows"] = [self.row] * 128
        self.data["target_seed_direction_rows"] = [
            dict(self.entry, physical_target_superpoints=0)] * 128
        self.old["rows"] = [self.row] * 128
        self.old["target_seed_direction_rows"] = [self.entry] * 128
        with self.assertRaisesRegex(ValueError, "physical support"):
            MODULE.analyze(self.data, self.old)


if __name__ == "__main__":
    unittest.main()
