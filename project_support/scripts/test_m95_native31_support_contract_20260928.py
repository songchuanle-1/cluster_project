"""CPU-only fail-closed checks for a future native intervention capture."""
import importlib.util
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("m95_native31_support_contract_20260928.py")
SPEC = importlib.util.spec_from_file_location("m95_support_contract", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SupportContractTest(unittest.TestCase):
    def setUp(self):
        self.original = [1.0, 0.0, 0.0, 0.0, 0.25]
        self.treated = [1.0, 0.25, 0.0, 0.0, 0.25]
        self.placebo = [1.0, 0.0, 0.25, 0.0, 0.25]

    def test_equal_final_seed_changes(self):
        result = MODULE.check_final_targets(
            self.original, self.treated, self.placebo, {0}, {1}, {2})
        self.assertEqual(result["final_target_delta"], [0.25])

    def test_overwritten_seed_is_not_reported_as_effect(self):
        with self.assertRaisesRegex(ValueError, "No final"):
            MODULE.check_final_targets(
                self.original, self.original, self.placebo, {0}, {1}, {2})

    def test_protected_seed_mutation_fails(self):
        with self.assertRaisesRegex(ValueError, "Protected"):
            MODULE.check_final_targets(
                self.original, [0.25, 0.25, 0, 0, 0.25],
                self.placebo, {0}, {1}, {2})

    def test_off_target_mutation_fails(self):
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            MODULE.check_final_targets(
                self.original, [1, 0.25, 0, 0.25, 0.25],
                self.placebo, {0}, {1}, {2})

    def test_unequal_count_and_magnitude_fail(self):
        with self.assertRaisesRegex(ValueError, "counts differ"):
            MODULE.check_final_targets(
                self.original, self.treated, [1, 0, 0.25, 0.25, 0.25],
                {0}, {1}, {2, 3})
        with self.assertRaisesRegex(ValueError, "magnitudes differ"):
            MODULE.check_final_targets(
                self.original, self.treated, [1, 0, 0.5, 0, 0.25],
                {0}, {1}, {2})

    def test_other_criterion_components_invariant(self):
        base = {"sample_loss": .1, "mask_bce_loss": .3, "indi_loss": .2}
        other = dict(base, sample_loss=.2)
        self.assertTrue(MODULE.check_non_sample_losses(base, other, other))
        with self.assertRaisesRegex(ValueError, "Non-sample loss changed"):
            MODULE.check_non_sample_losses(
                base, other, dict(other, mask_bce_loss=.31))


if __name__ == "__main__":
    unittest.main()
