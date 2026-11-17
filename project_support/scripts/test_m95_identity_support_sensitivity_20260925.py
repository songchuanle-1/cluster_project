import unittest

from m95_identity_support_sensitivity_20260925 import (
    exclusion_category,
    filter_pair_rows,
    make_floor_pair_rows,
    make_nearest_peer_pair_rows,
    pair_keys,
    remaining_support_counts,
    validate_pair_rows,
)


class SupportSensitivityTest(unittest.TestCase):
    def test_remaining_counts_and_category(self):
        stats = {
            1: {"count": 4, "sum": [0.0]},
            2: {"count": 2, "sum": [0.0]},
        }
        excluded = {
            1: {"count": 3, "sum": [0.0]},
            2: {"count": 0, "sum": [0.0]},
        }
        counts = remaining_support_counts(stats, excluded)
        self.assertEqual(counts, {1: 1, 2: 2})
        self.assertEqual(
            exclusion_category({1: 1}, {2: 2}, 2),
            "target_below_floor",
        )
        self.assertEqual(
            exclusion_category({1: 1}, {2: 2}, 1),
            "both_available",
        )

    def test_common_pair_filter_uses_exact_pair_key(self):
        rows = [
            {"pair_key": [0, 1, 2], "value": "a"},
            {"pair_key": [0, 1, 3], "value": "b"},
        ]
        self.assertEqual(pair_keys(rows), {(0, 1, 2), (0, 1, 3)})
        self.assertEqual(
            filter_pair_rows(rows, {(0, 1, 3)})[0]["value"],
            "b",
        )

    def test_pair_construction_is_order_independent(self):
        target = {
            "manifest_index": 0,
            "scene_id": "scene",
            "query": 1,
            "truth": "target",
            "native_positive": True,
            "score": 0.5,
            "iou": 1.0,
            "identity": {"margin": 0.2},
        }
        peer = {
            "manifest_index": 0,
            "scene_id": "scene",
            "query": 2,
            "truth": "peer",
            "native_positive": False,
            "score": 0.45,
            "iou": 0.0,
            "identity": {"margin": -0.2},
        }
        forward = make_floor_pair_rows([target, peer])
        reverse = make_floor_pair_rows([peer, target])
        self.assertEqual(pair_keys(forward), pair_keys(reverse))
        validate_pair_rows(forward)

    def test_duplicate_pairs_are_rejected(self):
        row = {
            "manifest_index": 0,
            "pair_key": [0, 1, 2],
        }
        with self.assertRaisesRegex(ValueError, "duplicates"):
            validate_pair_rows([row, dict(row)])

    def test_nearest_peer_is_order_independent(self):
        target = {
            "manifest_index": 0,
            "scene_id": "scene",
            "query": 1,
            "truth": "target",
            "native_positive": True,
            "score": 0.5,
            "iou": 1.0,
            "identity": {"margin": 0.2},
        }
        closer = {
            "manifest_index": 0,
            "scene_id": "scene",
            "query": 2,
            "truth": "peer",
            "native_positive": False,
            "score": 0.55,
            "iou": 0.0,
            "identity": {"margin": -0.2},
        }
        farther = {
            **closer,
            "query": 3,
            "score": 0.58,
        }
        forward = make_nearest_peer_pair_rows([target, closer, farther])
        reverse = make_nearest_peer_pair_rows([farther, closer, target])
        self.assertEqual(pair_keys(forward), {(0, 1, 2)})
        self.assertEqual(pair_keys(forward), pair_keys(reverse))


if __name__ == "__main__":
    unittest.main()
