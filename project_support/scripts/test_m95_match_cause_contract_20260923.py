import copy
import unittest

from m95_match_cause_contract_20260923 import check_row


ROW = {
    "sampled_pos": [[0, 0, 0], [10, 0, 0], [6, 0, 0], [11, 0, 0]],
    "obj_pos": [[0, 0, 0], [10, 0, 0]],
    "sampled_instance_labels": [20, 20, -1, 20],
    "object_ids": [10, 20],
    "nearest_query_per_gt": [0, 1],
    "member_queries_per_gt": [[], [3]],
    "native_positive": [True, True, False, True],
}


class MatchCauseContractTest(unittest.TestCase):
    def test_nearest_outside_seed_and_member_are_distinct(self):
        self.assertEqual(
            check_row(ROW),
            {"nearest_gt": 2, "instance_member": 1, "negative": 1},
        )

    def test_rejects_hierarchy_coordinate_substitution(self):
        row = copy.deepcopy(ROW)
        row["sampled_pos"][0] = [30, 0, 0]
        with self.assertRaisesRegex(ValueError, "nearest"):
            check_row(row)

    def test_rejects_missing_membership(self):
        row = copy.deepcopy(ROW)
        row["member_queries_per_gt"][1] = []
        with self.assertRaisesRegex(ValueError, "membership"):
            check_row(row)

    def test_rejects_label_only_assertion(self):
        row = copy.deepcopy(ROW)
        row["native_positive"][2] = True
        with self.assertRaisesRegex(ValueError, "Positive vector"):
            check_row(row)

    def test_rejects_missing_geometry(self):
        row = copy.deepcopy(ROW)
        row["obj_pos"] = []
        with self.assertRaisesRegex(ValueError, "nonempty query axis"):
            check_row(row)


if __name__ == "__main__":
    unittest.main()
