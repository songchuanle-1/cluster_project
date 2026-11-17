import unittest

from m95_target_positive_cardinality_control_20260925 import (
    analyze_document,
    analyze_rows,
)


def row(
    manifest_index=0,
    scene_id="scene0000_00",
    scores=None,
    ious=None,
    positive=None,
):
    return {
        "manifest_index": manifest_index,
        "scene_id": scene_id,
        "scores": scores or [0.9, 0.8, 0.7],
        "ious": ious or [0.1, 0.9, 0.8],
        "native_positive": positive or [False, True, False],
    }


class TargetPositiveCardinalityControlTests(unittest.TestCase):
    def test_target_specific_set_beats_topk_and_random_control(self):
        rows = [
            row(
                scores=[0.99, 0.9, 0.8, 0.7],
                ious=[0.0, 0.9, 0.0, 0.0],
                positive=[False, True, False, False],
            )
        ]
        result = analyze_rows(
            rows, random_draws=200, bootstrap_draws=100, seed=1999
        )
        control = result["paired_controls"]["native_positive_minus_topk"]
        self.assertAlmostEqual(control["pooled_mean"], 0.9)
        self.assertGreater(
            result["paired_controls"]["native_positive_minus_random_mean"][
                "pooled_mean"
            ],
            0.0,
        )
        self.assertGreater(result["positive_set_quantile"]["mean"], 0.5)

    def test_topk_equal_positive_set_gives_zero_delta(self):
        rows = [
            row(
                scores=[0.9, 0.8, 0.7],
                ious=[0.1, 0.9, 0.8],
                positive=[True, True, False],
            )
        ]
        result = analyze_rows(
            rows, random_draws=100, bootstrap_draws=100, seed=1999
        )
        self.assertEqual(result["topk_selector_changed_rows"], 0)
        self.assertEqual(
            result["paired_controls"]["native_positive_minus_topk"]["pooled_mean"],
            0.0,
        )

    def test_cardinality_control_is_deterministic(self):
        rows = [
            row(
                scores=[0.9, 0.8, 0.7, 0.6],
                ious=[0.1, 0.9, 0.8, 0.7],
                positive=[False, True, True, False],
            )
        ]
        first = analyze_rows(rows, random_draws=101, bootstrap_draws=100)
        second = analyze_rows(rows, random_draws=101, bootstrap_draws=100)
        self.assertEqual(
            first["selectors"]["random_mean_iou"],
            second["selectors"]["random_mean_iou"],
        )

    def test_empty_positive_set_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "no native-positive"):
            analyze_rows(
                [row(positive=[False, False, False])],
                random_draws=10,
                bootstrap_draws=10,
            )

    def test_wrong_contract_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "contract"):
            analyze_document({"contract": "wrong", "rows": [row()]})


if __name__ == "__main__":
    unittest.main()
