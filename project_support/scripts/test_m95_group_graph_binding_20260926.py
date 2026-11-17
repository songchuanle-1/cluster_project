import unittest

from m95_group_graph_binding_20260926 import audit


class BindingTests(unittest.TestCase):
    def test_target_and_reference_modifiers_are_separate(self):
        lower = {"rows": [{"scene": "scene", "ann_id": 1, "target": "2",
                           "object_name": "pillow"}]}
        upper = {"rows": []}
        graph = {"scene": {"1": {
            "graph_node": [{"node_id": 0, "target": "pillow",
                            "mod_text": ["bottom"], "node_type": "main"},
                           {"node_id": 1, "target": "shelf",
                            "mod_text": ["lower"], "node_type": "other"}],
            "graph_edge": []}}}
        row = audit(lower, upper, graph)["rows"][0]
        self.assertTrue(row["target_modifier_cue"])
        self.assertTrue(row["other_modifier_cue"])
        with self.assertRaisesRegex(ValueError, "Missing parsed graph"):
            audit(lower, upper, {})


if __name__ == "__main__":
    unittest.main()
