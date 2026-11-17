import unittest

from m95_utterance_provenance_20260926 import audit


class UtteranceProvenanceTest(unittest.TestCase):
    def test_punctuation_and_word_change(self):
        cohort = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "target": "1", "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 1} for i in range(256)]}
        source = [{"scene_id": "s" + str(i), "ann_id": i, "object_id": "1",
                   "description": "red chair."} for i in range(256)]
        graphs = {"s" + str(i): {str(i): {
            "utterance": "red chair !" if i == 0 else
                         "blue chair" if i == 1 else "red chair."}}
            for i in range(256)}
        result = audit(cohort, source, graphs)
        self.assertEqual(result["summary"]["all"]["punctuation_only"], 1)
        self.assertEqual(result["summary"]["all"]["word_changed"], 1)
        self.assertEqual(result["summary"]["all"]["word_changed_failures"], 1)


if __name__ == "__main__":
    unittest.main()
