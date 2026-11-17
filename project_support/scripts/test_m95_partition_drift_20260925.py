import unittest

from hierarchical_partition_contract_20260916 import (
    hierarchical_partition_sha256,
)
from m95_partition_drift_20260925 import compare


def row(changed=False):
    positions = [[[0.0], [1.0]], [[0.0]]]
    ids = [[0, 1], [0, 0]]
    maps = [{"0": [0]}]
    if changed:
        ids[0][1] = 0
    return {
        "original_superpoint_ids": [0, 1],
        "native_input_sha256": "same",
        "hierarchical_fps_positions": positions,
        "hierarchical_cluster_ids": ids,
        "hierarchical_child_maps": maps,
        "hierarchical_partition_sha256": hierarchical_partition_sha256(
            positions, ids, maps),
    }


class PartitionDriftTest(unittest.TestCase):
    def test_assignment_change(self):
        before = {83: row(), 174: row()}
        after = {83: row(), 174: row(True)}
        result = compare(before, after)
        self.assertEqual(result["rows"][1]["levels"][0]["changed_assignments"], 1)
        self.assertTrue(result["rows"][1]["positions_identical"])
        self.assertFalse(result["admission"])

    def test_changed_input_fails_closed(self):
        before = {83: row(), 174: row()}
        after = {83: row(), 174: row()}
        after[174]["native_input_sha256"] = "different"
        with self.assertRaisesRegex(ValueError, "Native input"):
            compare(before, after)


if __name__ == "__main__":
    unittest.main()
