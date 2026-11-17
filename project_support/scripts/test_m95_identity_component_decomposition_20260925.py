import math
import unittest

from m95_identity_component_decomposition_20260925 import (
    decomposition_rows,
    method_choice,
    summarize_decomposition,
    summarize_selector,
)


def pair(
    target_target_similarity,
    target_peer_similarity,
    target_score,
    target_iou,
    peer_target_similarity,
    peer_peer_similarity,
    peer_score,
    peer_iou,
):
    return {
        "manifest_index": 0,
        "scene_id": "scene0001_00",
        "target_query": 1,
        "peer_query": 2,
        "target": {
            "target_similarity": target_target_similarity,
            "peer_similarity": target_peer_similarity,
            "score": target_score,
            "iou": target_iou,
        },
        "peer": {
            "target_similarity": peer_target_similarity,
            "peer_similarity": peer_peer_similarity,
            "score": peer_score,
            "iou": peer_iou,
        },
    }


class IdentityComponentDecompositionTest(unittest.TestCase):
    def test_component_choices(self):
        row = pair(0.9, 0.1, 0.5, 0.8, 0.2, 0.3, 0.4, 0.2)
        self.assertEqual(
            method_choice(row, "target_similarity"),
            "target",
        )
        self.assertEqual(
            method_choice(row, "peer_rejection"),
            "target",
        )
        self.assertEqual(
            method_choice(row, "identity_margin"),
            "target",
        )

    def test_component_choice_ties(self):
        row = pair(0.5, 0.2, 0.5, 0.8, 0.5, 0.2, 0.4, 0.2)
        self.assertIsNone(method_choice(row, "target_similarity"))
        self.assertIsNone(method_choice(row, "peer_rejection"))
        self.assertIsNone(method_choice(row, "identity_margin"))

    def test_decomposition_is_additive(self):
        row = pair(0.9, 0.3, 0.4, 0.8, 0.2, 0.6, 0.5, 0.2)
        result = decomposition_rows([row])[0]
        self.assertAlmostEqual(
            result["identity_margin_delta"],
            result["target_similarity_delta"]
            - result["peer_similarity_delta"],
        )
        self.assertGreater(result["target_similarity_delta"], 0.0)
        self.assertLess(result["peer_similarity_delta"], 0.0)
        self.assertGreater(result["identity_minus_score_iou"], 0.0)

    def test_decomposition_category(self):
        row = pair(0.9, 0.3, 0.4, 0.8, 0.2, 0.2, 0.5, 0.2)
        result = summarize_decomposition([row])
        category = result["categories"]["target_assisted_only"]
        self.assertEqual(category["pairs"], 1)
        self.assertEqual(category["identity_better"], 1)

    def test_selector_summary_reproduces_score_comparison(self):
        rows = [
            pair(0.9, 0.3, 0.5, 0.8, 0.2, 0.6, 0.4, 0.2),
            pair(0.1, 0.7, 0.6, 0.1, 0.8, 0.2, 0.5, 0.9),
        ]
        result = summarize_selector(rows, "identity_margin")
        self.assertEqual(result["pairs"], 2)
        self.assertAlmostEqual(result["component_accuracy"], 1.0)
        self.assertAlmostEqual(result["score_accuracy"], 0.5)
        self.assertAlmostEqual(result["component_minus_score"], 0.5)

    def test_selector_summary_is_finite(self):
        row = pair(0.5, 0.2, 0.5, 0.8, 0.5, 0.2, 0.4, 0.2)
        result = summarize_selector([row], "identity_margin")
        self.assertTrue(
            math.isfinite(result["component_minus_score"])
        )


if __name__ == "__main__":
    unittest.main()
