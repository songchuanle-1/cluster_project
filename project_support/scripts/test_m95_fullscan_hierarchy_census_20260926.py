import unittest

from m95_fullscan_hierarchy_census_20260926 import compare


def row(index):
    return {
        "manifest_index": index,
        "native_input_sha256": "a" * 64,
        "fps_superpoints": [0, 1],
        "hierarchical_fps_positions": [[0.0]],
        "hierarchical_child_maps": [[0]],
        "hierarchical_partition_sha256": "b" * 64,
        "hierarchical_cluster_ids": [[0, 1], [0], [0]],
        "selected_query": 1,
        "ious": [0.0, 0.5],
    }


class CensusTest(unittest.TestCase):
    def test_counts_entry_and_assignment_changes(self):
        reference = {i: row(i) for i in range(256)}
        candidate = {i: row(i) for i in range(256)}
        candidate[7]["fps_superpoints"] = [1, 0]
        candidate[7]["hierarchical_cluster_ids"] = [[1, 1], [0], [0]]
        candidate[83]["hierarchical_fps_positions"] = [[1e-6]]
        candidate[83]["hierarchical_partition_sha256"] = "c" * 64
        result = compare(reference, candidate)
        self.assertEqual(result["counts"]["entry_fps_differ"], 1)
        self.assertEqual(result["indices"]["assignment_differ"][0], [7])
        self.assertEqual(result["indices"]["hierarchical_positions_differ"], [83])
        self.assertEqual(result["counts"]["selected_iou_differ"], 0)

    def test_rejects_hierarchy_axis_change(self):
        reference = {i: row(i) for i in range(256)}
        candidate = {i: row(i) for i in range(256)}
        candidate[17]["hierarchical_cluster_ids"] = [[0], [0], [0]]
        with self.assertRaisesRegex(ValueError, "support"):
            compare(reference, candidate)


if __name__ == "__main__":
    unittest.main()
