import unittest

from m95_target_seed_query_counterfactual_20260927 import analyze
from test_m95_target_seed_full_population_20260927 import fixture


class QueryAlternativeTest(unittest.TestCase):
    def setUp(self):
        self.capture = fixture()
        for row in self.capture["rows"]:
            row["scores"] = [1.0] + [0.0] * 127
        first = self.capture["rows"][0]
        first["ious"][1] = .8

    def test_adequate_alternative(self):
        result = analyze(self.capture)
        self.assertEqual(result["target_seed_failures"], 1)
        self.assertEqual(result["with_adequate_target_seed_alternative"], 1)
        self.assertEqual(result["rows"][0]["best_alternative"]["score_rank"], 2)

    def test_only_non_target_seed_alternative(self):
        self.capture["rows"][0]["ious"][2:] = [.5] * 126
        self.capture["rows"][0]["sampled_seed_indices"][1] = 1
        self.capture["rows"][0]["fps_superpoints"].append(1)
        self.capture["rows"][0]["physical_instance_labels"].append(2)
        self.assertEqual(analyze(self.capture)["with_adequate_target_seed_alternative"], 0)

    def test_no_adequate_alternative(self):
        self.capture["rows"][0]["ious"][1:] = [0.5] * 127
        self.assertEqual(analyze(self.capture)["with_adequate_target_seed_alternative"], 0)

    def test_invalid_seed_axis(self):
        self.capture["rows"][0]["sampled_seed_indices"][1] = 5
        with self.assertRaises(ValueError):
            analyze(self.capture)

    def test_provenance(self):
        self.capture["capture_mode"] = "other"
        with self.assertRaises(ValueError):
            analyze(self.capture)


if __name__ == "__main__":
    unittest.main()
