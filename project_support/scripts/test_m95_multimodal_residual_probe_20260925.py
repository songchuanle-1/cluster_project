"""Tests for the M95 multimodal residual probe."""
import unittest

import numpy as np

from m95_multimodal_residual_probe_20260925 import (
    bootstrap_scene,
    fit_ridge_predictions,
    group_fold_indices,
    masked_mean_features,
    scene_balanced,
    top1_metrics,
)


class ResidualProbeTest(unittest.TestCase):
    def test_group_folds_do_not_leak_scenes(self):
        scenes = np.asarray(
            ["scene_a"] * 3 + ["scene_b"] * 3 + ["scene_c"] * 3
            + ["scene_d"] * 3 + ["scene_e"] * 3
        )
        folds = group_fold_indices(scenes, n_splits=5)
        self.assertEqual(len(folds), 5)
        for train_index, test_index in folds:
            self.assertFalse(set(scenes[train_index]) & set(scenes[test_index]))

    def test_single_holdout_does_not_leak_scenes(self):
        scenes = np.asarray(
            ["scene_a"] * 2 + ["scene_b"] * 2 + ["scene_c"] * 2
            + ["scene_d"] * 2 + ["scene_e"] * 2
        )
        folds = group_fold_indices(scenes, n_splits=1)
        self.assertEqual(len(folds), 1)
        train_index, test_index = folds[0]
        self.assertFalse(set(scenes[train_index]) & set(scenes[test_index]))
        self.assertTrue(len(train_index) > len(test_index) > 0)

    def test_scene_balanced_and_bootstrap_are_finite(self):
        values = {"a": [0.0, 1.0], "b": [1.0]}
        self.assertEqual(scene_balanced(values), 0.75)
        result = bootstrap_scene(values, draws=200, seed=7)
        self.assertEqual(result["point_estimate"], 0.75)
        self.assertLessEqual(result["lo"], result["point_estimate"])
        self.assertGreaterEqual(result["hi"], result["point_estimate"])

    def test_top1_uses_score_and_reports_iou(self):
        expression_ids = np.asarray([0, 0, 1, 1])
        labels = np.asarray([0, 1, 1, 0], dtype=np.int8)
        ious = np.asarray([0.1, 0.8, 0.7, 0.2])
        scores = np.asarray([0.2, 0.9, 0.9, 0.1])
        success, selected_iou = top1_metrics(
            expression_ids, labels, ious, scores
        )
        self.assertEqual(success, {0: 1.0, 1: 1.0})
        self.assertEqual(selected_iou, {0: 0.8, 1: 0.7})

    def test_masked_mean_features(self):
        masks = np.asarray([[1, 1, 0], [0, 1, 1], [0, 0, 0]], dtype=bool)
        features = np.asarray([[1.0, 3.0], [3.0, 1.0], [5.0, -1.0]])
        result = masked_mean_features(masks, features)
        np.testing.assert_allclose(
            result, [[2.0, 2.0], [4.0, 0.0], [0.0, 0.0]]
        )

    def test_ridge_predictions_are_finite(self):
        x_train = np.asarray([[0.0], [1.0], [2.0], [3.0]], dtype=np.float32)
        y_train = np.asarray([0.0, 0.0, 1.0, 1.0], dtype=np.float32)
        prediction = fit_ridge_predictions(x_train, y_train, x_train)
        self.assertTrue(np.isfinite(prediction).all())
        self.assertGreater(prediction[-1], prediction[0])


if __name__ == "__main__":
    unittest.main()
