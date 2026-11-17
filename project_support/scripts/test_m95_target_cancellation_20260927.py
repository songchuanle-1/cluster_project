import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "target_cancellation",
    Path(__file__).with_name("m95_target_cancellation_20260927.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CancellationTest(unittest.TestCase):
    def setUp(self):
        self.rows = []
        self.entries = []
        for scene in range(32):
            for ann in range(4):
                self.rows.append({
                    "scene": str(scene), "ann_id": scene * 4 + ann,
                    "selected_mask_iou": 0.0 if ann == 0 and scene < 20 else 1.0,
                })
                self.entries.append({
                    "ann_id": scene * 4 + ann, "target_seed_count": 2,
                    "seeds": [[0, 1, 0, -2.0], [1, 1, 0, 1.0]]
                    if ann == 0 else [[0, 1, 0, -2.0], [1, 1, 0, -1.0]],
                })

    def test_scene_not_seed_is_unit(self):
        result = MODULE.analyze({
            "rows": self.rows, "target_seed_direction_rows": self.entries})
        self.assertEqual(result["failure_lower_coherence"], 20)
        self.assertEqual(result["paired_defined_scenes"], 20)

    def test_mismatched_identity_fails(self):
        self.entries[0]["ann_id"] = -1
        with self.assertRaisesRegex(ValueError, "binding"):
            MODULE.analyze({
                "rows": self.rows, "target_seed_direction_rows": self.entries})


if __name__ == "__main__":
    unittest.main()
