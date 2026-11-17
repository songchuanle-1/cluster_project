import copy
import unittest

from referent_target_rank_evaluator_20260919 import evaluate_capture
from referent_within_scene_permutation_20260919 import (
    evaluate_permutation_control,
)
from test_referent_target_rank_evaluator_20260919 import (
    capture_fixture,
    registry_fixture,
)


class ReferentWithinScenePermutationTest(unittest.TestCase):
    def setUp(self):
        self.registry = registry_fixture()
        self.capture = capture_fixture(self.registry)

    def test_control_is_deterministic(self):
        first = evaluate_permutation_control(
            self.registry,
            self.capture,
            draws=128,
        )
        second = evaluate_permutation_control(
            self.registry,
            self.capture,
            draws=128,
        )
        self.assertEqual(first, second)

    def test_observed_metrics_match_frozen_rank_evaluator(self):
        reference = evaluate_capture(self.registry, self.capture)
        control = evaluate_permutation_control(
            self.registry,
            self.capture,
            draws=64,
        )
        for score_name in ("referent", "objectness"):
            expected = reference["score_summaries"][score_name]
            self.assertAlmostEqual(
                control["observed"][score_name + "_top1"],
                expected["scene_balanced_top1_success"],
            )
            self.assertAlmostEqual(
                control["observed"][score_name + "_normalized_excess"],
                expected["scene_balanced_normalized_rank_excess"],
            )

    def test_p_values_and_holm_adjustment_are_bounded(self):
        control = evaluate_permutation_control(
            self.registry,
            self.capture,
            draws=128,
        )
        self.assertEqual(set(control["p_values"]), set(control["observed"]))
        self.assertTrue(
            all(0.0 < value <= 1.0 for value in control["p_values"].values())
        )
        self.assertTrue(
            all(
                0.0 < value <= 1.0
                for value in control["holm_adjusted_p_values"].values()
            )
        )
        raw_min = min(control["p_values"].values())
        adjusted_max = max(control["holm_adjusted_p_values"].values())
        self.assertGreaterEqual(adjusted_max, raw_min)

    def test_tied_scores_reject_expression_without_imputation(self):
        capture = copy.deepcopy(self.capture)
        score_map = capture["rows"][0]["scores"]["referent"]
        score_map["2"] = score_map["0"]
        control = evaluate_permutation_control(
            self.registry,
            capture,
            draws=32,
        )
        self.assertEqual(
            control["cohort"]["rejected_rank_eligible_expressions"],
            1,
        )
        self.assertIn(
            "Native score ties are not admissible",
            control["rejected"][0]["reason"],
        )

    def test_invalid_draw_count_is_rejected(self):
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                evaluate_permutation_control(
                    self.registry,
                    self.capture,
                    draws=value,
                )


if __name__ == "__main__":
    unittest.main()
