import unittest

from hierarchical_partition_contract_20260916 import hierarchical_partition_sha256
from m95_hierarchy_geometry_drift_20260925 import compare


def row():
    positions = [[[0.0], [1.0]], [[0.0]]]
    ids = [[0, 1], [0, 0]]
    maps = [{"0": [0]}]
    return {
        "original_superpoint_ids": [0, 1],
        "native_input_sha256": "same",
        "hierarchical_fps_positions": positions,
        "hierarchical_cluster_ids": ids,
        "hierarchical_child_maps": maps,
        "hierarchical_partition_sha256": hierarchical_partition_sha256(
            positions, ids, maps),
    }


def rehash(entry):
    entry["hierarchical_partition_sha256"] = hierarchical_partition_sha256(
        entry["hierarchical_fps_positions"],
        entry["hierarchical_cluster_ids"],
        entry["hierarchical_child_maps"],
    )


class GeometryDriftTest(unittest.TestCase):
    def test_shift_and_assignment(self):
        before = {83: row(), 174: row()}
        after = {83: row(), 174: row()}
        after[174]["hierarchical_fps_positions"][0][1][0] = 1.25
        after[174]["hierarchical_cluster_ids"][0][1] = 0
        rehash(after[174])
        result = compare(before, after)
        level = result["rows"][1]["levels"][0]
        self.assertEqual(level["max_center_shift"], 0.25)
        self.assertEqual(level["changed_assignments"][0]["point"], 1)
        self.assertEqual(result["rows"][0]["levels"][0]["max_center_shift"], 0)
        self.assertFalse(result["admission"])

    def test_different_input_fails_closed(self):
        before = {83: row(), 174: row()}
        after = {83: row(), 174: row()}
        after[174]["native_input_sha256"] = "changed"
        with self.assertRaisesRegex(ValueError, "Native input"):
            compare(before, after)

    def test_tampered_partition_fails_closed(self):
        before = {83: row(), 174: row()}
        after = {83: row(), 174: row()}
        after[174]["hierarchical_cluster_ids"][0][1] = 0
        with self.assertRaisesRegex(ValueError, "hash differs"):
            compare(before, after)


if __name__ == "__main__":
    unittest.main()
