import copy
import unittest

from paired_capture_evaluation_20260916 import control_manifest, paired_summary


def row(scene="a", ann=1, success=True):
    return dict(scene=scene, ann_id=ann, scene_occurrence=0, dataset_index=0,
                expression_slot=ann, original_superpoint_ids=[4, 8],
                sample_inverse=[0, 1], instance_labels=[2, 3],
                target_instances=[2], capture_id="test", producer_sha256="a" * 64,
                scores=[.8, .2], ious=[.8 if success else .1, .9],
                selected_query=0)


class PairedTests(unittest.TestCase):
    def test_identity_and_different_producer(self):
        left = [row(), row("b")]
        right = copy.deepcopy(left)
        right[0]["producer_sha256"] = "b" * 64
        result = paired_summary(left, right)
        self.assertEqual(result["scene_balanced_delta"], 0)
        self.assertEqual(result["scene_bootstrap_percentile_95"], [0, 0])

    def test_scene_weighting_not_expression_weighting(self):
        left = [row("a", 1, False), row("a", 2, False), row("b", 3)]
        right = [row("a", 1), row("a", 2), row("b", 3, False)]
        result = paired_summary(left, right)
        self.assertEqual(result["scene_balanced_delta"], 0)
        self.assertEqual((result["fixed"], result["broken"]), (2, 1))

    def test_reordered_rows(self):
        rows = [row(), row("b")]
        self.assertEqual(paired_summary(rows, rows[::-1])["expressions"], 2)

    def test_missing_and_duplicate(self):
        for rhs in ([], [row(), row()]):
            with self.assertRaises(ValueError):
                paired_summary([row()], rhs)

    def test_physical_mismatch(self):
        for field, value in (("sample_inverse", [1, 0]),
                             ("target_instances", [3]),
                             ("instance_labels", [3, 2]),
                             ("original_superpoint_ids", [8, 4])):
            rhs = row()
            rhs[field] = value
            with self.assertRaises(ValueError):
                paired_summary([row()], [rhs])

    def test_invalid_query(self):
        for field, value in (("selected_query", 1), ("scores", [float("nan"), .2]),
                             ("ious", [1.1, .2])):
            rhs = row()
            rhs[field] = value
            with self.assertRaises(ValueError):
                paired_summary([row()], [rhs])

    def test_one_scene_no_interval(self):
        self.assertIsNone(paired_summary([row()], [row()])[
            "scene_bootstrap_percentile_95"])

    def test_control_nodes_preserved(self):
        controls = [dict(scene="a", ann_id=2, node_id=i) for i in (1, 3)]
        self.assertEqual(control_manifest(controls),
                         [dict(scene="a", ann_id=2, node_ids=[1, 3])])
        with self.assertRaises(ValueError):
            control_manifest(controls * 2)


if __name__ == "__main__":
    unittest.main()
