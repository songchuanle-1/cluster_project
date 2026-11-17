import copy
import unittest

from analyze_m95_native_routes_20261002 import repeat_check


class RepeatContractTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"repeat": 0, "id": 1, "batch_input_sha256": "bound", "metric": [1.0, None]},
            {"repeat": 1, "id": 1, "batch_input_sha256": "bound", "metric": [1.0, None]},
        ]

    def check(self, rows):
        return repeat_check(rows, lambda row: row["id"])

    def test_exact_repeat(self):
        self.assertEqual(self.check(self.rows)["max_absolute_metric_drift"], 0)

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            self.check(self.rows + [self.rows[0]])

    def test_missing_repeat_rejected(self):
        with self.assertRaises(ValueError):
            self.check(self.rows[:1])

    def test_input_drift_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["batch_input_sha256"] = "changed"
        with self.assertRaises(ValueError):
            self.check(rows)

    def test_numeric_drift_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["metric"][0] += 0.01
        with self.assertRaises(ValueError):
            self.check(rows)

    def test_nonfinite_rejected(self):
        rows = copy.deepcopy(self.rows)
        rows[1]["metric"][0] = float("nan")
        with self.assertRaises(ValueError):
            self.check(rows)


if __name__ == "__main__":
    unittest.main()
