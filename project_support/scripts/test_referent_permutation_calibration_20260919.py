import unittest

from referent_permutation_calibration_20260919 import (
    ALPHA,
    REFERENT_ENDPOINTS,
    _summarize_arm,
    run_calibration,
)


class ReferentPermutationCalibrationTest(unittest.TestCase):
    def test_familywise_summary_rejects_when_any_endpoint_rejects(self):
        p_values = [
            {
                "referent_top1": ALPHA,
                "referent_normalized_excess": 1.0,
                "objectness_top1": 1.0,
                "objectness_normalized_excess": 1.0,
                "paired_top1_lift": 1.0,
                "paired_normalized_excess_difference": 1.0,
            },
            {
                "referent_top1": 1.0,
                "referent_normalized_excess": 1.0,
                "objectness_top1": 1.0,
                "objectness_normalized_excess": 1.0,
                "paired_top1_lift": 1.0,
                "paired_normalized_excess_difference": 1.0,
            },
        ]

        summary = _summarize_arm(p_values)

        self.assertEqual(
            summary["holm_familywise_any"]["rejections"],
            1,
        )

    def test_calibration_is_deterministic(self):
        first = run_calibration(simulations=6, draws=99)
        second = run_calibration(simulations=6, draws=99)
        self.assertEqual(first, second)

    def test_planted_signal_has_referent_power(self):
        result = run_calibration(simulations=20, draws=199)
        for endpoint in REFERENT_ENDPOINTS:
            self.assertGreaterEqual(
                result["planted_signal"]["summary"][endpoint][
                    "rejection_rate"
                ],
                0.80,
            )
        self.assertLessEqual(
            result["planted_signal"]["summary"]["objectness_top1"][
                "rejection_rate"
            ],
            0.10,
        )

    def test_null_has_bounded_familywise_rate(self):
        result = run_calibration(simulations=20, draws=199)
        self.assertLessEqual(
            result["null"]["summary"]["holm_familywise_any"][
                "rejection_rate"
            ],
            0.10,
        )


if __name__ == "__main__":
    unittest.main()
