import unittest

from m95_target_label_alignment_20260926 import audit, normalize


class TargetLabelAlignmentTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("Office_Chairs"), "office chair")

    def test_identity_and_mismatch(self):
        cohort = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "target": "1", "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 0}
            for i in range(256)]}
        source = [{"scene_id": "s" + str(i), "ann_id": i, "object_id": "1",
                   "object_name": "office chair", "description": "office chair"}
                  for i in range(256)]
        graphs = {"s" + str(i): {str(i): {"graph_node": [
            {"node_id": 0, "node_type": "Object",
             "lemma_head": "table" if i == 0 else "office chairs",
             "target_char_span": [[0, 5]]}],
             "utterance": "office chair"}}
            for i in range(256)}
        result = audit(cohort, source, graphs)
        self.assertEqual(result["summary"]["all"]["mismatches"], 1)
        self.assertEqual(result["summary"]["all"]["mismatch_failures"], 1)


if __name__ == "__main__":
    unittest.main()
