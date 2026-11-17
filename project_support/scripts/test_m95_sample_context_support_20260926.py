import unittest

from m95_sample_context_support_20260926 import audit, class_keys


class SampleContextSupportTest(unittest.TestCase):
    def test_literal_class_keys(self):
        self.assertEqual(class_keys("self.type2class = {'chair': 1, 'others': 2}"),
                         {"chair"})

    def test_absent_target_word(self):
        cohort = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "target": "1", "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 0} for i in range(256)]}
        source = [{"scene_id": "s" + str(i), "ann_id": i, "object_id": "1",
                   "object_name": "chair"} for i in range(256)]
        graphs = {"s" + str(i): {str(i): {
            "utterance": "the seat" if i == 0 else "the chair"}} for i in range(256)}
        result = audit(cohort, source, graphs, {"chair", "table"}, "hash")
        self.assertEqual(result["summary"]["all"]["missing_target_key"], 1)
        self.assertEqual(result["summary"]["all"]["missing_target_key_failures"], 1)


if __name__ == "__main__":
    unittest.main()
