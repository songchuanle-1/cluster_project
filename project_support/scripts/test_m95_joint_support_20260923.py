import unittest

from m95_joint_support_20260923 import resolve_object, shared_margin, shared_support, summarize, STAGES


class JointSupportTests(unittest.TestCase):
    def setUp(self):
        self.target = [True, True, False, False]
        self.peer = [False, False, True, True]
        self.deployed = [False, False, True, False]
        self.acceptable = [True, False, False, False]
        self.matrix = [[1, 0], [1, 0], [0, 1], [0, 1]]

    def calc(self, matrix=None):
        return shared_margin(self.matrix if matrix is None else matrix, self.target,
                             self.peer, self.deployed, self.acceptable)

    def test_shared_disjoint_support(self):
        masks, counts, missing = shared_support(
            self.target, self.peer, self.deployed, self.acceptable)
        self.assertEqual(masks["target"], [False, True, False, False])
        self.assertEqual(masks["peer"], [False, False, False, True])
        self.assertEqual(counts["union_size"], 2)
        self.assertEqual(missing, [])
        self.assertEqual(self.calc()["contrast"], 2)

    def test_swapping_queries_preserves_support_and_negates_contrast(self):
        swapped = shared_margin(self.matrix, self.target, self.peer,
                                self.acceptable, self.deployed)
        self.assertEqual(swapped["contrast"], -self.calc()["contrast"])
        self.assertEqual(swapped["counts"]["target_remaining"], 1)

    def test_joint_exhaustion_even_when_each_individual_leaves_support(self):
        self.deployed = [False, True, False, False]
        result = self.calc()
        self.assertIsNone(result["contrast"])
        self.assertIn("target_exhausted_by_union", result["missing_reasons"])

    def test_absent_peer_not_zero(self):
        self.peer = [False] * 4
        self.assertIsNone(self.calc()["contrast"])
        self.assertIn("peer_absent", self.calc()["missing_reasons"])

    def test_zero_norm_prototype_missing(self):
        result = self.calc([[1, 0], [0, 0], [0, 1], [0, 1]])
        self.assertIsNone(result["contrast"])
        self.assertIn("target_zero_norm", result["missing_reasons"])

    def test_empty_query_missing(self):
        self.deployed = [False] * 4
        self.assertIn("deployed_empty", self.calc()["missing_reasons"])

    def test_target_peer_overlap_rejected(self):
        self.peer[0] = True
        with self.assertRaises(ValueError):
            self.calc()

    def test_support_shape_rejected(self):
        self.target.append(False)
        with self.assertRaises(ValueError):
            self.calc()

    def test_feature_shape_rejected(self):
        with self.assertRaises(ValueError):
            self.calc([[1, 0], [1], [0, 1], [0, 1]])

    def test_nonfinite_feature_rejected(self):
        with self.assertRaises(ValueError):
            self.calc([[float("nan"), 0]] + self.matrix[1:])

    def test_structural_missing_denominator_retained(self):
        rows = []
        for i, reasons in enumerate(([], ["peer_absent"])):
            rows.append({"manifest_index": i, "scene_id": "same_scene",
                         "structural_missing_reasons": reasons,
                         "stages": {s: {"contrast": None if reasons else 2,
                                        "missing_reasons": reasons} for s in STAGES}})
        result = summarize(rows, draws=20)
        self.assertEqual(result["expressions"], 2)
        self.assertEqual(result["scenes"], 1)
        self.assertEqual(result["support_feasible"], 1)
        self.assertEqual(result["stages"]["final"]["available"], 1)
        self.assertEqual(result["stages"]["final"]["missing_indices"], [1])

    def test_graph_node_id_never_used_as_object_id(self):
        annotations = [{"scene_id": "s", "ann_id": 55, "object_id": "18", "object_name": "chair"}]
        graphs = {"s": {"55": {"graph_node": [{"node_id": 8, "lemma_head": "chair"}]}}}
        result = resolve_object(annotations, graphs, "s", 8, 18, 55, [8, 18])
        self.assertEqual(result["status"], "unknown_no_object_aligned_graph")
        self.assertFalse(result["ontology_class_verified"])

    def test_wrong_target_alignment_rejected(self):
        annotations = [{"scene_id": "s", "ann_id": 55, "object_id": "17"}]
        with self.assertRaises(ValueError):
            resolve_object(annotations, {}, "s", 8, 18, 55, [8, 18])

    def test_absent_physical_id_rejected(self):
        annotations = [{"scene_id": "s", "ann_id": 55, "object_id": "18"}]
        with self.assertRaises(ValueError):
            resolve_object(annotations, {}, "s", 8, 18, 55, [18])

    def test_annotation_aligned_graph(self):
        annotations = [
            {"scene_id": "s", "ann_id": 55, "object_id": "18"},
            {"scene_id": "s", "ann_id": 70, "object_id": "8", "object_name": "desk"},
        ]
        graphs = {"s": {"70": {"graph_node": [{"node_id": 0, "lemma_head": "desk"}]}}}
        result = resolve_object(annotations, graphs, "s", 8, 18, 55, [8, 18])
        self.assertEqual(result["status"], "annotation_graph_aligned")
        self.assertEqual(result["aligned_graph_records"][0]["object_id"], "8")


if __name__ == "__main__":
    unittest.main()
