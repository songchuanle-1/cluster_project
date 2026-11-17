import unittest
from diagnostic_identity import attach_description, manifest_index, same_target_donors


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.index = manifest_index([
            {"scene": "a", "selected": [{"ann_id": "1", "object_id": "2", "description": "A"}]},
            {"scene": "b", "selected": [{"ann_id": "1", "object_id": "3", "description": "B"}]},
        ])

    def test_shuffled_order(self):
        rows = [{"scene": "b", "ann_id": 1, "target_ids": [3]},
                {"scene": "a", "ann_id": 1, "target_ids": [2]}]
        self.assertEqual([attach_description(r, self.index)["utterance"] for r in rows], ["B", "A"])

    def test_target_mismatch(self):
        with self.assertRaises(ValueError):
            attach_description({"scene": "a", "ann_id": 1, "target_ids": [3]}, self.index)

    def test_duplicate(self):
        with self.assertRaises(ValueError):
            manifest_index([{"scene": "a", "selected": [
                {"ann_id": 1, "object_id": 2, "description": "A"},
                {"ann_id": 1, "object_id": 2, "description": "A"}]}])

    def test_no_mutation(self):
        row = {"scene": "a", "ann_id": 1, "target_ids": [2], "before": .3}
        self.assertEqual(attach_description(row, self.index)["before"], .3)
        self.assertNotIn("utterance", row)

    def test_segment_isolation(self):
        self.assertEqual(same_target_donors([[2], [2], [2], [2]], [2, 2]), [1, 0, 3, 2])

    def test_singleton_and_multitarget(self):
        self.assertEqual(same_target_donors([[2], [3], [2, 3], [2, 3]], [4]), [0, 1, 2, 3])

    def test_bad_lengths(self):
        for lengths in ([1], [0, 2], [3]):
            with self.assertRaises(ValueError):
                same_target_donors([[2], [2]], lengths)


if __name__ == "__main__":
    unittest.main()
