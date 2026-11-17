import unittest

from m95_sample_context_role_control_20260926 import analyze


class RoleControlTest(unittest.TestCase):
    def test_other_span_vs_target(self):
        screen = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 0, "target_key": "chair",
             "matched_class_keys": ["chair", "table"]} for i in range(256)]}
        graphs = {"s" + str(i): {str(i): {
            "utterance": "chair near table",
            "graph_node": [
                {"node_id": 0, "target_char_span": [[0, 5]]},
                {"node_id": 1, "node_type": "Object", "target_char_span": [[11, 16]]}]}}
            for i in range(256)}
        result = analyze(screen, graphs)
        self.assertEqual(result["summary"]["other_only"]["rows"], 128)
        self.assertEqual(result["rows"][0]["other_only_keys"], ["table"])
        self.assertEqual(result["rows"][0]["target_span_keys"], ["chair"])


if __name__ == "__main__":
    unittest.main()
