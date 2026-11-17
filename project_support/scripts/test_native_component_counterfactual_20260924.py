import math
import unittest

from native_component_counterfactual_20260924 import (
    analyze_expression,
    component_arms,
    summarize,
)
from m95_score_component_control_20260924 import compare


MANIFEST_SHA256 = "a" * 64


def manifest_row(index=7, scene="scene0007_00", ann_id=7):
    return {
        "manifest_index": index,
        "scene_id": scene,
        "ann_id": ann_id,
        "stratum": "ambiguous",
    }


def capture_row():
    return {
        "manifest_index": 7,
        "scene": "scene0007_00",
        "ann_id": 7,
        "scores": [0.8, 0.7, 0.6],
        "native_match_cause": {
            "object_ids": [0, 1],
            "matched_query_gt_pairs": [[0, 0], [1, 1], [2, 0]],
        },
    }


def artifact():
    return {
        "artifact_contract": "m95_manifest_native_query_artifact_v1",
        "manifest_sha256": MANIFEST_SHA256,
        "manifest_index": 7,
        "query_scores": [0.8, 0.7, 0.6],
        "query_mask_logits": [[5.0, -5.0], [-5.0, 5.0], [5.0, -5.0]],
        "query_masks": [[True, False], [False, True], [True, False]],
        "physical_instance_labels": [0, 1],
    }


class NativeComponentCounterfactualTests(unittest.TestCase):
    def test_component_arms_separate_mask_and_label_corrections(self):
        result = compare(
            [(0, 0), (1, 1), (2, 0)],
            [[True, False], [False, True]],
            [[5.0, -5.0], [-5.0, 5.0], [5.0, -5.0]],
            [0.8, 0.7, 0.6],
        )
        arms = component_arms(result)
        self.assertGreater(arms["deltas"]["mask_only_mask_harm"], 0.0)
        self.assertGreater(arms["deltas"]["label_only_score_harm"], 0.0)
        self.assertGreater(arms["deltas"]["coupled_score_harm"], 0.0)
        self.assertGreater(arms["deltas"]["coupled_total_harm"], 0.0)
        self.assertEqual(arms["deltas"]["indicator_change"], 0.0)
        self.assertEqual(
            arms["arms"]["mask_only"]["indicator"],
            arms["arms"]["coupled"]["indicator"],
        )

    def test_expression_replay_reports_four_arms(self):
        row = analyze_expression(
            artifact(),
            capture_row(),
            manifest_row(),
            MANIFEST_SHA256,
        )
        self.assertEqual(row["identity_mismatch_pairs"], 1)
        self.assertEqual(row["changed_mask_pairs"], 1)
        self.assertEqual(row["score_filter_crossings"], 1)
        self.assertEqual(
            set(row["arms"]),
            {"original", "mask_only", "label_only", "coupled"},
        )
        self.assertGreater(row["deltas"]["coupled_total_harm"], 0.0)

    def test_logit_mask_disagreement_fails_closed(self):
        bad = artifact()
        bad["query_masks"][0] = [False, False]
        with self.assertRaisesRegex(ValueError, "disagree"):
            analyze_expression(
                bad,
                capture_row(),
                manifest_row(),
                MANIFEST_SHA256,
            )

    def test_score_axis_disagreement_fails_closed(self):
        bad = artifact()
        bad["query_scores"] = [0.8, 0.7, 0.5]
        with self.assertRaisesRegex(ValueError, "scores differ"):
            analyze_expression(
                bad,
                capture_row(),
                manifest_row(),
                MANIFEST_SHA256,
            )

    def test_summary_is_scene_balanced_and_fail_closed(self):
        row = analyze_expression(
            artifact(),
            capture_row(),
            manifest_row(),
            MANIFEST_SHA256,
        )
        summary = summarize([row], draws=100)
        self.assertEqual(summary["expressions"], 1)
        self.assertEqual(summary["identity_mismatch_pairs"], 1)
        self.assertEqual(
            summary["metrics"]["indicator_change"]["scene_balanced_mean"],
            0.0,
        )
        with self.assertRaisesRegex(ValueError, "No expressions"):
            summarize([])

    def test_zero_indicator_change_is_exact(self):
        result = compare(
            [(0, 0)],
            [[True, False]],
            [[5.0, -5.0]],
            [0.5],
        )
        arms = component_arms(result)
        self.assertAlmostEqual(
            arms["arms"]["original"]["indicator"],
            math.log(1.0 + 1e-6) - math.log(0.5),
            places=8,
        )
        self.assertEqual(arms["deltas"]["indicator_change"], 0.0)


if __name__ == "__main__":
    unittest.main()
