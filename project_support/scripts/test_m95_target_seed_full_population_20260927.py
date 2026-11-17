import unittest

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, analyze,
)


def fixture():
    rows = []
    for index in range(256):
        rows.append({
            "manifest_index": index, "scene": f"scene{index // 4:04d}",
            "ann_id": index, "selected_query": 0,
            "sampled_seed_indices": [0] * 128,
            "fps_superpoints": [0], "physical_instance_labels": [1],
            "target_instances": [1], "ious": [0.8] * 128,
        })
    rows[0]["ious"][0] = 0.5
    return {
        "producer_sha256": PRODUCER_SHA, "checkpoint_sha256": CHECKPOINT_SHA,
        "manifest": {"sha256": MANIFEST_SHA}, "capture_mode": "full_train_scan",
        "rows": rows,
    }


class FullPopulationTest(unittest.TestCase):
    def setUp(self):
        self.capture = fixture()

    def test_matched_target(self):
        result = analyze(self.capture)
        self.assertEqual(result["failures_with_same_target_control"], 1)
        self.assertEqual(result["same_target_paired_scenes"], 1)
        self.assertEqual(result["target_seed_failures"], 1)

    def test_different_physical_target_not_matched(self):
        for row in self.capture["rows"][1:4]:
            row["target_instances"] = [2]
            row["physical_instance_labels"] = [2]
        result = analyze(self.capture)
        self.assertEqual(result["failures_with_same_scene_control"], 1)
        self.assertEqual(result["failures_with_same_target_control"], 0)

    def test_reject_duplicate_manifest(self):
        self.capture["rows"][1]["manifest_index"] = 0
        with self.assertRaises(ValueError):
            analyze(self.capture)

    def test_reject_invalid_seed_axis(self):
        self.capture["rows"][0]["fps_superpoints"] = [3]
        with self.assertRaises(ValueError):
            analyze(self.capture)

    def test_reject_provenance(self):
        self.capture["checkpoint_sha256"] = "different"
        with self.assertRaises(ValueError):
            analyze(self.capture)


if __name__ == "__main__":
    unittest.main()
