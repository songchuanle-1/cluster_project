import unittest

from m95_identity_actionability_20260925 import (
    action_pair,
    actionability_rows,
    cluster_bootstrap,
    leave_one_cluster_out,
    make_actionability_rows,
    metric_summary,
    percentile,
    summarize_actionability,
)


def query(index, truth, positive, score, iou, margin):
    return {
        "manifest_index": 0,
        "scene_id": "scene-0",
        "query": index,
        "score": score,
        "iou": iou,
        "native_positive": positive,
        "truth": truth,
        "identity": {"margin": margin},
    }


def action_row(index, target_query, peer_query, iou, margin):
    return {
        "manifest_index": index,
        "scene_id": "scene-%d" % index,
        "target_query": target_query,
        "peer_query": peer_query,
        "target_iou": 0.8,
        "peer_iou": 0.2,
        "target_score": 0.6,
        "peer_score": 0.5,
        "target_identity_margin": margin + 0.1,
        "peer_identity_margin": margin,
        "identity_tie": False,
        "score_tie": False,
        "iou_tie": False,
        "identity_target": True,
        "score_target": False,
        "identity_correct": True,
        "score_correct": False,
        "identity_disagrees_with_score": True,
        "identity_choice_iou": iou,
        "score_choice_iou": 1.0 - iou,
        "identity_minus_score_iou": 2.0 * iou - 1.0,
        "identity_margin_gap": 0.1,
    }


class IdentityActionabilityTest(unittest.TestCase):
    def test_action_pair_uses_identity_choice_iou(self):
        row = action_pair(
            query(1, "target", True, 0.5, 0.8, 1.3),
            query(2, "peer", True, 0.6, 0.2, 1.0),
        )
        self.assertTrue(row["identity_disagrees_with_score"])
        self.assertAlmostEqual(row["identity_choice_iou"], 0.8)
        self.assertAlmostEqual(row["score_choice_iou"], 0.2)
        self.assertAlmostEqual(row["identity_minus_score_iou"], 0.6)

    def test_action_pair_excludes_score_ties(self):
        row = action_pair(
            query(1, "target", True, 0.5, 0.8, 1.3),
            query(2, "peer", True, 0.5, 0.2, 1.0),
        )
        self.assertFalse(row["identity_disagrees_with_score"])
        self.assertNotIn("identity_minus_score_iou", row)

    def test_pair_construction_requires_native_positive_target(self):
        rows = [
            query(0, "target", False, 0.6, 0.8, 1.3),
            query(1, "peer", True, 0.5, 0.2, 1.0),
            query(2, "target", True, 0.6, 0.8, 1.3),
        ]
        pairs = make_actionability_rows(0, "scene-0", rows)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["target_query"], 2)

    def test_metric_summary_balances_gain_and_loss(self):
        rows = [
            action_row(0, 0, 1, 0.8, 1.0),
            action_row(1, 0, 1, 0.2, 1.0),
        ]
        summary = metric_summary(rows, rows)
        self.assertEqual(summary["non_tied_disagreement_pairs"], 2)
        self.assertAlmostEqual(summary["mean_identity_minus_score_iou"], 0.0)
        self.assertEqual(summary["positive_deltas"], 1)
        self.assertEqual(summary["negative_deltas"], 1)

    def test_actionability_rows_are_unique(self):
        row = action_row(0, 0, 1, 0.8, 1.0)
        with self.assertRaises(ValueError):
            actionability_rows([row, dict(row)])

    def test_bootstrap_is_deterministic(self):
        rows = [
            action_row(0, 0, 1, 0.8, 1.0),
            action_row(1, 0, 1, 0.7, 1.0),
            action_row(2, 0, 1, 0.4, 1.0),
        ]
        first = cluster_bootstrap(
            rows,
            lambda row: row["manifest_index"],
            "expression",
            100,
            7,
        )
        second = cluster_bootstrap(
            rows,
            lambda row: row["manifest_index"],
            "expression",
            100,
            7,
        )
        self.assertEqual(first, second)
        self.assertEqual(first["cluster_count"], 3)

    def test_leave_one_cluster_out_detects_sign_flip(self):
        rows = [
            action_row(0, 0, 1, 0.9, 1.0),
            action_row(1, 0, 1, 0.2, 1.0),
            action_row(2, 0, 1, 0.2, 1.0),
        ]
        result = leave_one_cluster_out(
            rows,
            lambda row: row["manifest_index"],
            "expression",
        )
        self.assertFalse(result["all_positive"])
        self.assertEqual(result["most_influential_cluster"], [0])

    def test_percentile_interpolates(self):
        self.assertAlmostEqual(percentile([0.0, 1.0], 0.25), 0.25)
        self.assertAlmostEqual(percentile([0.0, 1.0], 0.75), 0.75)

    def test_summary_reports_fixed_margin_strata(self):
        rows = [
            action_row(index, 0, 1, iou, 1.0 + index)
            for index, iou in enumerate((0.2, 0.4, 0.6, 0.8))
        ]
        result = summarize_actionability(rows, draws=50)
        self.assertEqual(len(result["identity_margin_gap_strata"]), 4)
        self.assertEqual(
            sum(
                row["pairs"]
                for row in result["identity_margin_gap_strata"]
            ),
            4,
        )


if __name__ == "__main__":
    unittest.main()
