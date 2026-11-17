import unittest

from m95_identity_expression_dependence_20260925 import (
    deterministic_one_pair_per_expression,
    expression_balanced_summary,
    expression_cluster_bootstrap,
    leave_one_expression_out,
    leave_one_target_query_out,
    make_pair_rows,
    metric_summary,
    pair_digest,
    summarize_dependence,
    target_query_cluster_bootstrap,
)


def pair(index, target, peer, identity, score, scene=None):
    return {
        "manifest_index": index,
        "scene_id": scene or "scene-%d" % index,
        "pair_key": [index, target, peer],
        "identity_matches_iou": identity,
        "score_matches_iou": score,
        "identity_disagrees_with_score": identity != score,
    }


class ExpressionDependenceTest(unittest.TestCase):
    def test_pair_construction_requires_target_truth_and_native_positive(self):
        def query(index, truth, positive, score):
            return {
                "manifest_index": 0,
                "scene_id": "scene-0",
                "query": index,
                "score": score,
                "iou": 0.5,
                "native_positive": positive,
                "truth": truth,
                "identity": {
                    "target_similarity": 1.0,
                    "peer_similarity": 0.0,
                    "margin": 1.0,
                },
            }

        rows = [
            query(0, "target", True, 0.5),
            query(1, "peer", True, 0.6),
            query(2, "peer", False, 0.55),
        ]
        pairs = make_pair_rows(0, "scene-0", rows)
        self.assertEqual(
            [row["pair_key"] for row in pairs],
            [[0, 0, 1], [0, 0, 2]],
        )

    def test_metric_summary_counts_pairwise_differences(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 2, 3, False, True),
            pair(1, 0, 1, True, True),
        ]
        summary = metric_summary(rows)
        self.assertEqual(summary["pairs"], 3)
        self.assertEqual(summary["identity_only_matches_iou"], 1)
        self.assertEqual(summary["score_only_matches_iou"], 1)
        self.assertAlmostEqual(summary["identity_minus_score"], 0.0)

    def test_expression_balanced_is_not_pair_pooled(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 2, 3, True, False),
            pair(1, 0, 1, False, True),
        ]
        pooled = metric_summary(rows)["identity_minus_score"]
        balanced = expression_balanced_summary(rows)[
            "expression_balanced_identity_minus_score"
        ]
        self.assertAlmostEqual(pooled, 1 / 3)
        self.assertAlmostEqual(balanced, 0.0)

    def test_expression_cluster_bootstrap_is_deterministic(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 2, 3, True, False),
            pair(1, 0, 1, False, True),
            pair(2, 0, 1, True, True),
        ]
        first = expression_cluster_bootstrap(rows, draws=100, seed=7)
        second = expression_cluster_bootstrap(rows, draws=100, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(first["unit"], "expression")
        self.assertLessEqual(first["lo"], first["point_estimate"])
        self.assertGreaterEqual(first["hi"], first["point_estimate"])

    def test_target_query_cluster_bootstrap_is_deterministic(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 0, 2, True, False),
            pair(0, 3, 4, False, True),
            pair(1, 0, 1, True, True),
        ]
        first = target_query_cluster_bootstrap(rows, draws=100, seed=11)
        second = target_query_cluster_bootstrap(rows, draws=100, seed=11)
        self.assertEqual(first, second)
        self.assertEqual(first["unit"], "target_query")
        self.assertEqual(first["target_query_count"], 3)

    def test_leave_one_expression_out_detects_sign_flip(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 2, 3, True, False),
            pair(1, 0, 1, False, True),
        ]
        result = leave_one_expression_out(rows)
        self.assertFalse(result["all_positive"])
        self.assertEqual(result["most_influential_manifest_index"], 0)

    def test_leave_one_target_query_out_detects_concentration(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 0, 2, True, False),
            pair(0, 3, 4, False, True),
        ]
        result = leave_one_target_query_out(rows)
        self.assertEqual(result["most_influential_cluster"], [0, 0])
        self.assertLess(
            result["minimum_identity_minus_score"],
            result["maximum_identity_minus_score"],
        )

    def test_one_pair_selection_ignores_metric_fields(self):
        rows = [
            pair(0, 0, 1, True, False),
            pair(0, 2, 3, False, True),
            pair(1, 0, 1, True, True),
        ]
        selected = deterministic_one_pair_per_expression(rows)
        by_key = {(row["manifest_index"], tuple(row["pair_key"])): row for row in selected}
        changed = [dict(row) for row in rows]
        changed[0]["identity_matches_iou"] = False
        changed[0]["score_matches_iou"] = True
        changed_selected = deterministic_one_pair_per_expression(changed)
        self.assertEqual(
            {
                (row["manifest_index"], tuple(row["pair_key"]))
                for row in selected
            },
            {
                (row["manifest_index"], tuple(row["pair_key"]))
                for row in changed_selected
            },
        )
        for row in selected:
            self.assertEqual(row, by_key[(row["manifest_index"], tuple(row["pair_key"]))])

    def test_pair_digest_excludes_metric_fields(self):
        left = pair(3, 7, 9, True, False)
        right = pair(3, 7, 9, False, True)
        self.assertEqual(pair_digest(left), pair_digest(right))

    def test_empty_or_duplicate_pairs_fail_closed(self):
        with self.assertRaises(ValueError):
            summarize_dependence([])
        duplicate = pair(0, 0, 1, True, False)
        with self.assertRaises(ValueError):
            summarize_dependence([duplicate, dict(duplicate)])


if __name__ == "__main__":
    unittest.main()
