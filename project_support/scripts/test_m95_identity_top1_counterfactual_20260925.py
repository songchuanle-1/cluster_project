import unittest

from m95_identity_top1_counterfactual_20260925 import (
    expression_result,
    leave_one_scene_out,
    permutation_null,
    summarize,
    top_query,
)


def query(index, score, iou, margin):
    return {
        "query": index,
        "score": score,
        "iou": iou,
        "identity_margin": margin,
    }


def result(index, scene, delta, same=False):
    return {
        "manifest_index": index,
        "scene_id": scene,
        "eligible_queries": 2,
        "score_query": 0,
        "identity_query": 0 if same else 1,
        "oracle_query": 1,
        "score_iou": 0.4,
        "identity_iou": 0.4 + delta,
        "oracle_iou": 0.9,
        "identity_minus_score_iou": delta,
        "oracle_minus_score_iou": 0.5,
        "same_query": same,
        "score_success": False,
        "identity_success": 0.4 + delta > 0.5,
        "identity_margin": 1.0,
        "score": 0.8,
        "query_rows": [
            query(0, 0.8, 0.4, 0.5),
            query(1, 0.7, 0.4 + delta, 1.0),
        ],
    }


class TopQueryTest(unittest.TestCase):
    def test_top_query_uses_lowest_index_for_ties(self):
        rows = [query(4, 1.0, 0.0, 0.0), query(2, 1.0, 0.0, 0.0)]
        self.assertEqual(top_query(rows, "score")["query"], 2)

    def test_expression_result_shares_query_universe(self):
        result = expression_result(
            3,
            "scene",
            [
                query(0, 0.9, 0.2, 0.1),
                query(1, 0.8, 0.8, 0.2),
            ],
        )
        self.assertEqual(result["score_query"], 0)
        self.assertEqual(result["identity_query"], 1)
        self.assertEqual(result["oracle_query"], 1)
        self.assertAlmostEqual(result["identity_minus_score_iou"], 0.6)

    def test_summary_reports_paired_and_success_metrics(self):
        rows = [
            result(0, "a", 0.2, same=False),
            result(1, "a", -0.1, same=False),
            result(2, "b", 0.3, same=True),
        ]
        summary = summarize(rows)
        self.assertEqual(summary["expressions"], 3)
        self.assertEqual(summary["same_query"], 1)
        self.assertEqual(summary["positive_deltas"], 2)
        self.assertAlmostEqual(
            summary["paired_effects"]["identity_minus_score"][
                "scene_balanced_mean"
            ],
            0.175,
        )

    def test_leave_one_scene_out_detects_sign_flip(self):
        summary = leave_one_scene_out(
            [
                result(0, "a", 1.0),
                result(1, "b", -0.1),
                result(2, "c", -0.1),
            ],
            "identity_minus_score_iou",
        )
        self.assertFalse(summary["all_positive"])
        self.assertEqual(summary["most_influential_scene"], "a")

    def test_permutation_null_is_deterministic(self):
        rows = [
            result(0, "a", 0.2, same=False),
            result(1, "b", 0.3, same=False),
        ]
        first = permutation_null(rows, draws=100, seed=7)
        second = permutation_null(rows, draws=100, seed=7)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first["two_sided_empirical_p"], 0.0)
        self.assertLessEqual(first["two_sided_empirical_p"], 1.0)
        self.assertLess(
            first["null_mean"],
            rows[0]["oracle_minus_score_iou"],
        )


if __name__ == "__main__":
    unittest.main()
