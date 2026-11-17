import unittest

from m95_mask_limited_match_contract_20260927 import analyze
from test_m95_target_seed_full_population_20260927 import fixture


def sources():
    capture = fixture()
    indices = (0, 4, 8, 12)
    for row in capture["rows"]:
        row["native_positive"] = [True] + [False] * 127
        row["native_match_cause"] = {
            "native_positive": row["native_positive"][:],
            "nearest_query_per_gt": [0],
            "member_queries_per_gt": [[]],
        }
    prior = {
        "capture_sha256": "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a",
        "residual_expressions": 4,
        "with_adequate_non_target_seed_query": 0,
        "rows": [],
    }
    for index in indices:
        row = capture["rows"][index]
        row["ious"] = [.5] * 128
        prior["rows"].append({
            "manifest_index": index, "scene": row["scene"],
            "ann_id": index, "selected_iou": .5,
        })
    return capture, prior


class MatcherContractTest(unittest.TestCase):
    def setUp(self):
        self.capture, self.prior = sources()

    def test_four_positive_selected(self):
        result = analyze(self.capture, self.prior)
        self.assertEqual(result["failure_expressions"], 4)
        self.assertEqual(result["selected_matcher_positive"], 4)

    def test_negative_selected(self):
        row = self.capture["rows"][0]
        row["native_positive"][0] = False
        row["native_match_cause"]["native_positive"][0] = False
        self.assertEqual(analyze(self.capture, self.prior)["selected_matcher_positive"], 3)

    def test_mismatch_cause_guard(self):
        self.capture["rows"][0]["native_match_cause"]["native_positive"][0] = False
        with self.assertRaises(ValueError):
            analyze(self.capture, self.prior)

    def test_prior_identity_guard(self):
        self.prior["rows"][0]["ann_id"] = -1
        with self.assertRaises(ValueError):
            analyze(self.capture, self.prior)

    def test_adequate_query_guard(self):
        self.capture["rows"][0]["ious"][1] = .8
        with self.assertRaises(ValueError):
            analyze(self.capture, self.prior)


if __name__ == "__main__":
    unittest.main()
