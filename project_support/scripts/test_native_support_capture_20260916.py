import unittest

from native_support_capture_20260916 import exact_rows, physical_join


class Tests(unittest.TestCase):
    def setUp(self):
        self.axis = dict(capture_id="native", producer_sha256="a" * 64,
                         scene="s", scene_occurrence=0, dataset_index=3, ann_id=4,
                         expression_slot=0, original_superpoint_ids=[4, 8],
                         sample_inverse=[0, 1, 0])

    def test_equal(self):
        self.assertTrue(physical_join(self.axis, dict(self.axis)))

    def test_identity_changes(self):
        for key in ("capture_id", "producer_sha256", "scene", "scene_occurrence",
                    "dataset_index", "ann_id", "expression_slot"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                physical_join(self.axis, dict(self.axis, **{key: "different"}))

    def test_missing_occurrence_or_producer(self):
        for key in ("scene_occurrence", "producer_sha256"):
            row = dict(self.axis)
            row.pop(key)
            with self.assertRaises(ValueError):
                physical_join(row, row)

    def test_reordered_rows(self):
        with self.assertRaises(ValueError):
            physical_join(self.axis, dict(self.axis, original_superpoint_ids=[8, 4]))

    def test_changed_point_support(self):
        with self.assertRaises(ValueError):
            physical_join(self.axis, dict(self.axis, sample_inverse=[1, 0, 1]))

    def test_no_truncation(self):
        self.assertEqual(exact_rows(self.axis, [[1], [2]]), [[1], [2]])
        with self.assertRaises(ValueError):
            exact_rows(self.axis, [[1], [2], [3]])


if __name__ == "__main__":
    unittest.main()
