import unittest

from m95_instance_identity_discriminability_20260925 import (
    balanced_accuracy,
    classify_pair,
    cosine,
    instance_prototypes,
    maximum_similarity,
    query_identity,
    summarize_pairs,
    summarize_query_classification,
)


class InstanceIdentityDiscriminabilityTests(unittest.TestCase):
    def test_cosine_rejects_zero_and_shape_mismatch(self):
        self.assertIsNone(cosine([0.0, 0.0], [1.0, 0.0]))
        self.assertIsNone(cosine([1.0], [1.0, 0.0]))
        self.assertAlmostEqual(cosine([1.0, 0.0], [1.0, 0.0]), 1.0)

    def test_instance_prototypes_enforce_minimum_support(self):
        rows = [
            [1.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ]
        labels = [1, 1, 1, 2, 2]
        prototypes = instance_prototypes(rows, labels, [1, 2])
        self.assertEqual(set(prototypes), {1})

    def test_maximum_similarity_selects_nearest_instance(self):
        self.assertAlmostEqual(
            maximum_similarity([1.0, 0.0], {1: [1.0, 0.0], 2: [0.0, 1.0]}),
            1.0,
        )

    def test_query_identity_prefers_closer_target_prototype(self):
        rows = [
            [1.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ]
        labels = [1, 1, 1, 2, 2, 2]
        result = query_identity(
            rows, [True, True, False, False, False, False],
            labels, [1], [2],
        )
        self.assertGreater(result["target_similarity"], result["peer_similarity"])
        self.assertGreater(result["margin"], 0.0)

    def test_pair_classification_separates_identity_and_score(self):
        result = classify_pair(
            {"margin": 0.5, "score": 0.1, "iou": 0.8},
            {"margin": -0.2, "score": 0.2, "iou": 0.1},
        )
        self.assertTrue(result["identity_matches_iou"])
        self.assertFalse(result["score_matches_iou"])
        self.assertTrue(result["identity_disagrees_with_score"])

    def test_summaries_are_bounded_and_count_disagreements(self):
        query_rows = [
            {
                "manifest_index": 0, "scene_id": "s1",
                "truth": "target", "prediction": "target",
            },
            {
                "manifest_index": 0, "scene_id": "s1",
                "truth": "peer", "prediction": "target",
            },
            {
                "manifest_index": 1, "scene_id": "s2",
                "truth": "target", "prediction": "peer",
            },
            {
                "manifest_index": 1, "scene_id": "s2",
                "truth": "peer", "prediction": "peer",
            },
        ]
        query_summary = summarize_query_classification(query_rows)
        self.assertEqual(query_summary["queries"], 4)
        self.assertAlmostEqual(query_summary["accuracy"], 0.5)
        self.assertAlmostEqual(query_summary["balanced_accuracy"], 0.5)
        self.assertAlmostEqual(balanced_accuracy(query_rows), 0.5)

        pair_summary = summarize_pairs(
            [
                {
                    "manifest_index": 0,
                    "scene_id": "s1",
                    "identity_matches_iou": True,
                    "score_matches_iou": False,
                    "identity_disagrees_with_score": True,
                },
                {
                    "manifest_index": 1,
                    "scene_id": "s2",
                    "identity_matches_iou": False,
                    "score_matches_iou": True,
                    "identity_disagrees_with_score": True,
                },
            ]
        )
        self.assertEqual(pair_summary["identity_only_matches_iou"], 1)
        self.assertEqual(pair_summary["score_only_matches_iou"], 1)
        self.assertEqual(pair_summary["identity_disagrees_with_score"], 2)
        self.assertAlmostEqual(pair_summary["identity_accuracy"], 0.5)
        self.assertAlmostEqual(pair_summary["score_accuracy"], 0.5)
        self.assertAlmostEqual(pair_summary["identity_minus_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
