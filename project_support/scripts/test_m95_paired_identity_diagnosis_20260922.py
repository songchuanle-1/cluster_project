import unittest

import torch

import m95_paired_identity_diagnosis_20260922 as diagnosis


class RankTests(unittest.TestCase):
    def test_rankdata_handles_ties(self):
        self.assertEqual(diagnosis.rankdata([3.0, 1.0, 3.0]), [2.5, 1.0, 2.5])

    def test_spearman_detects_monotonic_relation(self):
        self.assertAlmostEqual(
            diagnosis.spearman([1.0, 2.0, 3.0], [3.0, 5.0, 8.0]), 1.0
        )
        self.assertAlmostEqual(
            diagnosis.spearman([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]), -1.0
        )


class FeatureTests(unittest.TestCase):
    def test_centroids_exclude_sparse_instances(self):
        features = torch.tensor(
            [[1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0],
             [0.0, 1.0], [1.0, 1.0]]
        )
        labels = torch.tensor([0, 0, 0, 1, 1, 1, 2])
        centroids = diagnosis.instance_centroids(features, labels)
        self.assertEqual(sorted(centroids), [0, 1])

    def test_missing_semantic_class_is_unknown(self):
        labels = [0, 0, 1, 1]
        semantics = [-100, -100, 3, 3]
        self.assertIsNone(diagnosis.dominant_class(labels, semantics, 0))
        self.assertEqual(diagnosis.dominant_class(labels, semantics, 1), 3)

    def test_identity_rank_finds_target_nearest_to_wrong(self):
        centroids = {
            0: torch.tensor([1.0, 0.0]),
            1: torch.tensor([0.9, 0.1]),
            2: torch.tensor([-1.0, 0.0]),
        }
        centroids = {
            key: torch.nn.functional.normalize(value, dim=0)
            for key, value in centroids.items()
        }
        metrics = diagnosis.identity_metrics(
            centroids, target_ids=[1], wrong_id=0,
            class_by_id={0: 1, 1: 1, 2: 2},
        )
        self.assertEqual(metrics["target_rank_to_wrong"], 1)
        self.assertTrue(metrics["target_nearest_to_wrong"])
        self.assertEqual(metrics["margin_over_nearest_other"], 0.0)

    def test_modality_preservation_has_perfect_agreement(self):
        centroids = {
            0: torch.tensor([1.0, 0.0]),
            1: torch.tensor([0.9, 0.1]),
            2: torch.tensor([-1.0, 0.0]),
        }
        centroids = {
            key: torch.nn.functional.normalize(value, dim=0)
            for key, value in centroids.items()
        }
        measured = diagnosis.modality_preservation(centroids, centroids)
        self.assertAlmostEqual(measured["spearman"], 1.0)
        self.assertEqual(measured["nearest_agreement"], 1.0)


if __name__ == "__main__":
    unittest.main()
