import unittest

from m95_wrong_seed_context_20260926 import audit


class SeedContextTest(unittest.TestCase):
    def test_context_excludes_target_and_matched(self):
        rows, graphs = [], {}
        for i in range(256):
            scene = "scene%03d" % i
            graphs[scene] = {str(i): {"utterance": "chair beside bed"}}
            rows.append({
                "manifest_index": i, "scene": scene, "ann_id": i,
                "stratum": "ambiguous" if i < 128 else "class_unique",
                "target_instances": [1], "sampled_seed_indices": [0, 1, 2],
                "fps_superpoints": [0, 1, 2],
                "physical_instance_labels": [1, 2, 3],
                "semantic_labels": [0, 0, 1],
                "native_positive": [True, False, True],
                "native_match_cause": {"native_positive": [True, False, True]},
                "selected_query": 1, "ious": [0.9, 0.0, 0.1],
            })
        result = audit(
            {"capture_mode": "full_train_scan", "native_match_cause_completed": True,
             "rows": rows}, graphs,
            {"chair": 2, "bed": 1, "others": 17}, {0: 2, 1: 1})
        self.assertEqual(result["summary"]["all"]["selected_exposed"], 256)
        self.assertEqual(result["summary"]["all"]["context_upper_bound_queries"], 256)
        self.assertEqual(result["summary"]["all"]["matched_positive_queries"], 512)


if __name__ == "__main__":
    unittest.main()
