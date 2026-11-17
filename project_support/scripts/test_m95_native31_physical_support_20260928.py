"""Synthetic source-boundary checks; not a native GPU intervention."""
import importlib.util
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location(
    "m95_physical_support", Path(__file__).with_name(
        "m95_native31_physical_support_20260928.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PhysicalSupportTest(unittest.TestCase):
    def setUp(self):
        self.args = ([0, 0, 1, 1, 2, 2, 3], [6, 6, 1, 9, 9, 9, 7],
                     [2, 2, 13, 4, 4, 4, 17], {6}, {4}, {1},
                     [1.0, .25, .5, 0.0])

    def test_mixed_superpoint_and_target_preserved(self):
        result = MODULE.physical_support(*self.args)
        self.assertEqual(result["baseline"], [1.0, .25, .5, 0.0])
        self.assertEqual(result["treated"], [1.0, .5, .5, 0.0])
        self.assertEqual(result["mixed_changed"], [1])
        self.assertEqual(result["placebo_pool"], [3])

    def test_original_native_support_mismatch_rejected(self):
        args = list(self.args)
        args[-1] = [1.0, 0.0, .5, 0.0]
        with self.assertRaisesRegex(ValueError, "Native support differs"):
            MODULE.physical_support(*args)

    def test_physical_identity_and_class_fail_closed(self):
        args = list(self.args)
        args[2] = [2, 2, 11, 4, 4, 17, 17]
        with self.assertRaisesRegex(ValueError, "physical class"):
            MODULE.physical_support(*args)
        args = list(self.args)
        args[5] = {6}
        with self.assertRaisesRegex(ValueError, "Target and physical"):
            MODULE.physical_support(*args)

    def test_crop_and_missing_labels_fail(self):
        args = list(self.args)
        args[5] = {100}
        args[-1] = [1, .25, .5, 0]
        with self.assertRaisesRegex(ValueError, "Curtain cropped"):
            MODULE.physical_support(*args)
        args = list(self.args)
        args[2] = args[2][:-1]
        with self.assertRaisesRegex(ValueError, "axes differ"):
            MODULE.physical_support(*args)

    def test_no_new_support_fails(self):
        args = list(self.args)
        args[4] = {4, 13}
        args[-1] = [1.0, .5, .5, 0.0]
        with self.assertRaisesRegex(ValueError, "No physical"):
            MODULE.physical_support(*args)

    def test_mixed_instance_class_fails_closed(self):
        args = list(self.args)
        args[2] = [2, 2, 13, 4, 4, 17, 17]
        with self.assertRaisesRegex(ValueError, "Instance class differs"):
            MODULE.physical_support(*args)


if __name__ == "__main__":
    unittest.main()
