import unittest

from m95_seed_context_score_control_20260926 import analyze


class ScoreControlTest(unittest.TestCase):
    def test_within_expression_pair(self):
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
                "native_positive": [True, False, False],
                "scores": [0.9, 0.8, 0.2], "selected_query": 0,
                "ious": [0.9, 0.1, 0.1],
            })
        # Bed and chair are both context; change third to a non-context class.
        result = analyze({"rows": rows}, graphs,
                         {"chair": 2, "others": 17}, {0: 2, 1: 1})
        self.assertEqual(result["summary"]["all"]["paired_rows"], 256)
        self.assertAlmostEqual(result["summary"]["all"]["mean_delta"], 0.6)


if __name__ == "__main__":
    unittest.main()
