import unittest

from m95_seed_coverage_residual_20260927 import analyze
from test_m95_target_seed_full_population_20260927 import fixture


def sources():
    capture = fixture()
    for row in capture["rows"]:
        row["scores"] = [1.0] + [0.0] * 127
    for index in (0, 4, 8, 12):
        capture["rows"][index]["ious"][1:] = [.5] * 127
    prior = {
        "capture_sha256": "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a",
        "target_seed_failures": 8,
        "with_adequate_target_seed_alternative": 4,
        "rows": [
            {"manifest_index": index, "scene": capture["rows"][index]["scene"],
             "ann_id": index, "selected_iou": capture["rows"][index]["ious"][0],
             "adequate_alternatives": 0 if index in (0, 4, 8, 12) else 1}
            for index in (0, 4, 8, 12, 16, 20, 24, 28)],
    }
    return capture, prior


class ResidualTest(unittest.TestCase):
    def setUp(self):
        self.capture, self.prior = sources()

    def test_no_alternative(self):
        result = analyze(self.capture, self.prior)
        self.assertEqual(result["residual_expressions"], 4)
        self.assertEqual(result["with_adequate_non_target_seed_query"], 0)

    def test_non_target_alternative(self):
        row = self.capture["rows"][0]
        row["physical_instance_labels"].append(2)
        row["fps_superpoints"].append(1)
        row["sampled_seed_indices"][1] = 1
        row["ious"][1] = .8
        result = analyze(self.capture, self.prior)
        self.assertEqual(result["with_adequate_non_target_seed_query"], 1)
        self.assertEqual(result["rows"][0]["best"]["physical_seed_instance"], 2)

    def test_target_alternative_invalidates_prior(self):
        self.capture["rows"][0]["ious"][1] = .8
        with self.assertRaises(ValueError):
            analyze(self.capture, self.prior)

    def test_prior_identity_guard(self):
        self.prior["rows"][0]["ann_id"] = -1
        with self.assertRaises(ValueError):
            analyze(self.capture, self.prior)

    def test_provenance_guard(self):
        self.capture["checkpoint_sha256"] = "other"
        with self.assertRaises(ValueError):
            analyze(self.capture, self.prior)


if __name__ == "__main__":
    unittest.main()
