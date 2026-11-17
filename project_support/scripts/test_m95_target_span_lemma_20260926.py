import unittest

from m95_target_span_lemma_20260926 import audit


class SpanLemmaTest(unittest.TestCase):
    def test_exact_and_missing_head(self):
        cohort = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 0} for i in range(256)]}
        graphs = {"s" + str(i): {str(i): {
            "utterance": "red chair", "graph_node": [{
                "node_id": 0, "node_type": "Object",
                "lemma_head": "table" if i == 0 else "chair",
                "target_char_span": [[4, 9]]}]}} for i in range(256)}
        result = audit(cohort, graphs)
        self.assertEqual(result["summary"]["all"]["exposed"], 1)
        self.assertEqual(result["summary"]["all"]["exposed_failures"], 1)
        self.assertEqual(result["summary"]["all"]["exact"], 255)


if __name__ == "__main__":
    unittest.main()
