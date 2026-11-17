import unittest

from m95_group_local_stack_20260926 import local_peer


class LocalStackTest(unittest.TestCase):
    def test_horizontal_neighbor_does_not_use_z_or_outcome(self):
        row = {"target": 1, "peers": [3, 2], "failed": True,
               "instances": {
                   "1": {"centroid": [0, 0, 0]},
                   "2": {"centroid": [0.1, 0, 9]},
                   "3": {"centroid": [1, 0, -1]},
               }}
        self.assertEqual(local_peer(row), 2)

    def test_tie_and_no_peers(self):
        row = {"target": 1, "peers": [3, 2],
               "instances": {"1": {"centroid": [0, 0, 0]},
                             "2": {"centroid": [1, 0, 0]},
                             "3": {"centroid": [-1, 0, 0]}}}
        self.assertEqual(local_peer(row), 2)
        row["peers"] = []
        self.assertIsNone(local_peer(row))


if __name__ == "__main__":
    unittest.main()
