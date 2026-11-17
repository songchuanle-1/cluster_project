import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("native_registry_coverage_runner_20260921.py")
SPEC = importlib.util.spec_from_file_location("coverage_runner", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SelectionTest(unittest.TestCase):
    def test_accepts_planned_subset(self):
        self.assertEqual(
            MODULE.validate_selection([1524, 1097], [1097, 1524, 2690]),
            (1524, 1097),
        )

    def test_rejects_empty_or_oversized(self):
        for value in ([], [1, 2, 3]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.validate_selection(value, [1, 2, 3])

    def test_rejects_duplicate_or_unplanned(self):
        for value in ([1097, 1097], [1097, 9999]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.validate_selection(value, [1097, 1524])

    def test_rejects_noninteger(self):
        for value in ([True], [1.0]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.validate_selection(value, [1])


if __name__ == "__main__":
    unittest.main()
