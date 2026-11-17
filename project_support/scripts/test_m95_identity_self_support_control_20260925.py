import unittest

from m95_identity_self_support_control_20260925 import (
    identity_from_stats,
    nearest_prototype_similarity,
    prototype_stats,
    support_stats,
)


class IdentitySelfSupportControlTests(unittest.TestCase):
    def test_prototype_stats_match_selected_points(self):
        rows = [[1.0, 0.0], [1.0, 2.0], [0.0, 3.0]]
        labels = [1, 1, 2]
        stats = prototype_stats(rows, labels, [1, 2])
        self.assertEqual(stats[1]["count"], 2)
        self.assertEqual(stats[1]["sum"], [2.0, 2.0])
        self.assertEqual(stats[2]["count"], 1)
        self.assertEqual(stats[2]["sum"], [0.0, 3.0])

    def test_support_stats_subtract_query_points(self):
        rows = [[1.0, 0.0], [1.0, 2.0], [0.0, 3.0]]
        labels = [1, 1, 2]
        stats = prototype_stats(rows, labels, [1, 2])
        excluded = support_stats(rows, labels, [1, 2], [True, False, True])
        similar = nearest_prototype_similarity(
            [1.0, 0.0],
            {1: stats[1]},
            excluded=excluded,
            minimum_points=1,
        )
        self.assertAlmostEqual(similar, 1.0 / (5.0 ** 0.5))

    def test_self_inclusion_can_be_removed(self):
        rows = [
            [1.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ]
        labels = [1, 1, 1, 2, 2, 2]
        target_stats = prototype_stats(rows, labels, [1])
        peer_stats = prototype_stats(rows, labels, [2])
        excluded = support_stats(
            rows,
            labels,
            [1, 2],
            [True, True, True, False, False, False],
        )
        baseline = identity_from_stats(
            [1.0, 0.0],
            target_stats,
            peer_stats,
        )
        self.assertGreater(baseline["margin"], 0.0)
        self.assertIsNone(
            identity_from_stats(
                [1.0, 0.0],
                target_stats,
                peer_stats,
                excluded=excluded,
            )
        )

    def test_control_can_preserve_identity_when_support_remains(self):
        rows = [
            [1.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ]
        labels = [1, 1, 1, 1, 2, 2, 2, 2]
        target_stats = prototype_stats(rows, labels, [1])
        peer_stats = prototype_stats(rows, labels, [2])
        excluded = support_stats(rows, labels, [1, 2], [True, False, False, False,
                                                       False, False, False, False])
        result = identity_from_stats(
            [1.0, 0.0],
            target_stats,
            peer_stats,
            excluded=excluded,
        )
        self.assertGreater(result["margin"], 0.0)


if __name__ == "__main__":
    unittest.main()
