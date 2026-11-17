import unittest

import numpy as np

from m95_group_all_instance_20260926 import nearest


class CandidateNeighborhoodTests(unittest.TestCase):
    def test_excludes_target_and_breaks_ties(self):
        centers = {7: np.array([0, 0, 0]), 2: np.array([1, 0, 1]),
                   3: np.array([-1, 0, 2])}
        self.assertEqual(nearest(centers[7], centers, 7)[1], 2)
        self.assertIsNone(nearest(centers[7], {7: centers[7]}, 7))


if __name__ == "__main__":
    unittest.main()
