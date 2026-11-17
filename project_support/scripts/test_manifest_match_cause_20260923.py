import unittest

from native_manifest_capture_20260922 import (
    matcher_cause_record,
    native_matcher_cause_record,
)


class MatcherCauseRecordTest(unittest.TestCase):
    def setUp(self):
        self.positions = [[0, 0, 0], [10, 0, 0], [11, 0, 0]]
        self.centroids = [[0, 0, 0], [10, 0, 0]]
        self.labels = [20, 20, 20]
        self.objects = [10, 20]
        self.result = ([0, 1], [[], [2]], ([0, 1, 2], [0, 1, 1]), [1, 2])
        self.positive = [True, True, True]

    def test_source_bound_match_and_positive(self):
        row, counts = matcher_cause_record(
            self.positions, self.centroids, self.labels, self.objects,
            self.result, self.positive
        )
        self.assertEqual(row["nearest_query_per_gt"], [0, 1])
        self.assertEqual(counts, {"nearest_gt": 2, "instance_member": 1})

    def test_native_matcher_argument_order(self):
        row, counts = native_matcher_cause_record(
            (self.labels, self.objects, self.positions, self.centroids),
            self.result,
            self.positive,
        )
        self.assertEqual(row["sampled_pos"], self.positions)
        self.assertEqual(row["object_ids"], self.objects)
        self.assertEqual(counts, {"nearest_gt": 2, "instance_member": 1})

    def test_rejects_pair_axis_mismatch(self):
        result = (self.result[0], self.result[1],
                  ([0, 1, 2], [0, 0, 1]), self.result[3])
        with self.assertRaisesRegex(ValueError, "matched pair"):
            matcher_cause_record(
                self.positions, self.centroids, self.labels, self.objects,
                result, self.positive
            )

    def test_rejects_positive_mismatch(self):
        with self.assertRaisesRegex(ValueError, "Positive vector"):
            matcher_cause_record(
                self.positions, self.centroids, self.labels, self.objects,
                self.result, [True, False, True]
            )


if __name__ == "__main__":
    unittest.main()
