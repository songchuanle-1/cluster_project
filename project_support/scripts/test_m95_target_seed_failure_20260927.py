import copy
import unittest

from m95_target_seed_failure_20260927 import analyze


def capture(seed, iou, instance, target=1):
    rows = []
    for i in range(128):
        rows.append({
            "scene": f"scene{i // 4:04d}_00", "ann_id": i,
            "batch_input_sha256": f"{seed}-{i}", "target_instances": [target],
            "selected_seed_instance": instance if i == 0 else target,
            "selected_seed_matches_target_instance": instance == target if i == 0 else True,
            "selected_seed_is_context": False,
            "selected_mask_iou": iou if i == 0 else 0.8,
            "selected_seed_final_target": 0.8,
        })
    return {
        "checkpoint_sha256": "fixed", "population_manifest_sha256": "fixed",
        "transform_seed": seed, "rows": rows,
    }


class TargetSeedFailureTest(unittest.TestCase):
    def setUp(self):
        self.a = capture(1999, 0.5, 1)
        self.b = capture(2000, 0.4, 1)

    def test_persistent_boundary(self):
        result = analyze(self.a, self.b)
        self.assertEqual(result["arms"]["target_seed_failure"]["persistent_expressions"], 1)
        self.assertEqual(result["arms"]["target_seed_failure"]["persistent_scenes"], 1)

    def test_changed_identity_is_reported(self):
        self.b["rows"][0]["selected_seed_instance"] = 2
        self.b["rows"][0]["selected_seed_matches_target_instance"] = False
        result = analyze(self.a, self.b)
        self.assertEqual(result["arms"]["target_seed_failure"]["persistent_expressions"], 0)
        self.assertTrue(any(t["first"] == "target_seed_failure"
                            and t["second"] == "other_failure"
                            for t in result["transitions"]))

    def test_reject_duplicate_identity(self):
        self.b["rows"][1]["ann_id"] = 0
        with self.assertRaises(ValueError):
            analyze(self.a, self.b)

    def test_reject_unchanged_input(self):
        self.b["rows"][0]["batch_input_sha256"] = self.a["rows"][0]["batch_input_sha256"]
        with self.assertRaises(ValueError):
            analyze(self.a, self.b)

    def test_reject_inconsistent_target_binding(self):
        self.b["rows"][0]["selected_seed_matches_target_instance"] = False
        with self.assertRaises(ValueError):
            analyze(self.a, self.b)


if __name__ == "__main__":
    unittest.main()
