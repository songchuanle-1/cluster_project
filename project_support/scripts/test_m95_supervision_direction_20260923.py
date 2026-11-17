import copy
import math
import unittest

from m95_supervision_direction_20260923 import analyze, indicator_direction


def query(label, score=0.8, iou=0.8):
    return {
        "query": 1, "score": score, "iou": iou, "native_positive": label,
        "target_seed": label, "identity": "target_dominant", "dominant_instance": 2,
    }


def fixture():
    return {
        "contract": "m95_failure_followup_v1", "admission": False,
        "supervision_focus": [{
            "manifest_index": 1, "scene_id": "s",
            "partition": "recoverable_positive_set_excludes_acceptable",
            "seed": None, "positive": query(True, iou=0.1),
            "acceptable": [query(False)],
        }],
    }


class DirectionTests(unittest.TestCase):
    def test_derivative_matches_finite_difference(self):
        for label in (False, True):
            for z in (-3.0, 0.0, 2.0):
                probability = 1 / (1 + math.exp(-z))
                loss = lambda x: math.log1p(math.exp(x)) - int(label) * x
                finite = (loss(z + 1e-5) - loss(z - 1e-5)) / 2e-5
                actual = indicator_direction(query(label, probability))
                self.assertAlmostEqual(
                    finite, actual["positive_logit_derivative_before_weight_normalization"], places=8)

    def test_exclusion_is_not_positive_ranking(self):
        result = analyze(fixture())
        row = result["rows"][0]
        self.assertEqual(row["acceptable_negative_queries"], 1)
        self.assertEqual(row["acceptable"][0]["gradient_descent_direction"], "decrease")
        self.assertEqual(row["positive_selector"]["gradient_descent_direction"], "increase")
        self.assertFalse(result["analytic_contract"]["native_backward_executed"])

    def test_within_positive_has_no_ordering_label(self):
        doc = fixture()
        row = doc["supervision_focus"][0]
        row["partition"] = "recoverable_within_positive_score_failure"
        row["acceptable"] = [query(True), query(False)]
        result = analyze(doc)["rows"][0]
        self.assertEqual(result["acceptable_positive_queries"], 1)
        self.assertEqual(result["acceptable"][0]["gradient_descent_direction"], "increase")

    def test_invalid_partition_and_duplicates_fail(self):
        doc = fixture()
        doc["supervision_focus"].append(copy.deepcopy(doc["supervision_focus"][0]))
        with self.assertRaises(ValueError):
            analyze(doc)
        doc = fixture()
        doc["supervision_focus"][0]["acceptable"] = [query(True)]
        with self.assertRaises(ValueError):
            analyze(doc)

    def test_invalid_probability_and_seed_fail(self):
        for p in (float("nan"), float("inf"), -0.01, 1.01):
            with self.assertRaises(ValueError):
                indicator_direction(query(True, p))
        q = query(False)
        q["target_seed"] = True
        with self.assertRaises(ValueError):
            indicator_direction(q)

    def test_strict_iou_and_empty_set(self):
        for acceptable in ([], [query(False, iou=0.5)]):
            doc = fixture()
            doc["supervision_focus"][0]["acceptable"] = acceptable
            with self.assertRaises(ValueError):
                analyze(doc)


if __name__ == "__main__":
    unittest.main()
