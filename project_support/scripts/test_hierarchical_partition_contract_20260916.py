import copy
import json
import unittest

from hierarchical_partition_contract_20260916 import (
    partition_rows_from_observations,
    validate_hierarchical_row,
    validate_hierarchical_partition,
)


def valid_observation():
    positions = [
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
        [[0.0, 0.0, 0.0]],
        [[0.0, 0.0, 0.0]],
    ]
    ids = [
        [0, 0, 1, 1],
        [0, 0],
        [0],
    ]
    maps = [
        {0: [0]},
        {0: [0]},
    ]
    digest = validate_hierarchical_partition(4, positions, ids, maps)
    return dict(
        original_superpoint_ids=[10, 11, 12, 13],
        fps_superpoints=[0, 2],
        hierarchical_fps_positions=positions,
        hierarchical_cluster_ids=ids,
        hierarchical_child_maps=maps,
        hierarchical_partition_sha256=digest)


class HierarchyContractTests(unittest.TestCase):
    def test_valid_row(self):
        row = valid_observation()
        self.assertEqual(validate_hierarchical_row(row),
                         row["hierarchical_partition_sha256"])

    def test_json_round_trip_child_map_keys_are_canonical(self):
        row = valid_observation()
        restored = json.loads(json.dumps(row, ensure_ascii=True))
        self.assertEqual(validate_hierarchical_row(restored),
                         row["hierarchical_partition_sha256"])

    def test_fps_position_change_changes_hash(self):
        left = valid_observation()
        right = copy.deepcopy(left)
        right["hierarchical_fps_positions"][2][0][0] = 0.25
        with self.assertRaisesRegex(ValueError, "hash differs"):
            validate_hierarchical_row(right)

    def test_cluster_id_range_is_checked(self):
        row = valid_observation()
        row["hierarchical_cluster_ids"][0][0] = 2
        with self.assertRaisesRegex(ValueError, "out of range"):
            validate_hierarchical_row(row)

    def test_cluster_support_size_is_checked(self):
        row = valid_observation()
        row["hierarchical_cluster_ids"][1].pop()
        with self.assertRaisesRegex(ValueError, "support size differs"):
            validate_hierarchical_row(row)

    def test_child_map_must_cover_each_child_once(self):
        row = valid_observation()
        row["hierarchical_child_maps"][0] = {}
        with self.assertRaisesRegex(ValueError, "not a partition"):
            validate_hierarchical_row(row)

    def test_child_map_duplicate_is_rejected(self):
        row = valid_observation()
        row["hierarchical_child_maps"][0][0] = [0, 0]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_hierarchical_row(row)

    def test_nonfinite_position_is_rejected(self):
        row = valid_observation()
        row["hierarchical_fps_positions"][0][0][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            validate_hierarchical_row(row)

    def test_entry_fps_binding_is_required_when_present(self):
        row = valid_observation()
        row["fps_superpoints"] = [0, 4]
        with self.assertRaisesRegex(ValueError, "entry FPS"):
            validate_hierarchical_row(row)

    def test_flat_observation_binding(self):
        positions = [
            [[0.0], [1.0]],
            [[0.0]],
            [[0.0], [1.0]],
            [[0.0]],
        ]
        ids = [
            [[0, 0], [0, 1]],
            [[0, 0], [0, 0]],
        ]
        maps = [
            [{0: [0]}, {0: [0]}],
        ]
        rows = partition_rows_from_observations(
            positions, ids, maps, [2, 2], 2)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(
            row["hierarchical_partition_sha256"] for row in rows))

    def test_flat_observation_count_is_checked(self):
        with self.assertRaisesRegex(ValueError, "call count"):
            partition_rows_from_observations(
                [[[0.0]]], [[[0]]], [], [1, 1], 1)


if __name__ == "__main__":
    unittest.main()
