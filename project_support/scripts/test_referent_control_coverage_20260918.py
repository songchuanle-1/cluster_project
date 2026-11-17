import unittest

from referent_control_coverage_20260918 import (
    control_features,
    summarize,
    wrong_instance_features,
)


class ReferentControlCoverageTest(unittest.TestCase):
    def setUp(self):
        self.target = {
            "scene_id": "scene0001_00",
            "ann_id": "0",
            "object_id": "1",
            "object_name": "table",
        }
        self.scene_objects = [
            self.target,
            {
                "scene_id": "scene0001_00",
                "ann_id": "1",
                "object_id": "2",
                "object_name": "table",
            },
            {
                "scene_id": "scene0001_00",
                "ann_id": "2",
                "object_id": "3",
                "object_name": "chair",
            },
        ]
        self.graph = {
            "graph_node": [
                {"node_id": 0, "node_type": "Object", "target": "table",
                 "lemma_head": "table", "mod_text": ["wooden"],
                 "rel_char_span": [[10, 14]]},
                {"node_id": 1, "node_type": "Object", "target": "table",
                 "lemma_head": "table", "mod_text": [],
                 "rel_char_span": []},
                {"node_id": 2, "node_type": "Object", "target": "chair",
                 "lemma_head": "chair", "mod_text": [],
                 "rel_char_span": []},
            ],
            "graph_edge": [
                {
                    "sub_idx": 0,
                    "obj_idx": 1,
                    "subject": "table",
                    "object": "table",
                    "relation": "next to",
                },
                {
                    "sub_idx": 0,
                    "obj_idx": 2,
                    "subject": "table",
                    "object": "chair",
                    "relation": "in front of",
                },
            ],
        }

    def test_connected_same_class_peer_is_exact(self):
        result = control_features(self.target, self.graph, self.scene_objects)
        self.assertTrue(result["same_class_peer"])
        self.assertTrue(result["graph_same_class_peer"])
        self.assertTrue(result["target_has_relation_edge"])
        self.assertTrue(result["connected_same_class_peer"])
        self.assertEqual(result["connected_same_class_target"], ["table"])
        self.assertTrue(result["target_has_attribute"])
        self.assertTrue(result["target_has_relation_span"])

    def test_target_label_mismatch_uses_graph_root(self):
        target = dict(self.target, object_name="tables")
        result = control_features(target, self.graph, self.scene_objects)
        self.assertTrue(result["connected_same_class_peer"])

    def test_wrong_instance_class_and_connectivity(self):
        result = wrong_instance_features(
            self.target,
            "2",
            self.graph,
            self.scene_objects,
        )
        self.assertTrue(result["wrong_is_same_class"])
        self.assertTrue(result["wrong_graph_connected"])

    def test_summary_counts_boolean_rates(self):
        result = summarize([
            {"connected_same_class_peer": True},
            {"connected_same_class_peer": False},
        ])
        self.assertEqual(result["connected_same_class_peer"]["count"], 1)
        self.assertEqual(result["connected_same_class_peer"]["rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
