import unittest

from m95_region_language_screen_20260926 import analyze


class RegionScreenTest(unittest.TestCase):
    def test_sparse_phrases_and_same_scene_pair(self):
        entries = []
        outcomes = []
        source = []
        for i in range(256):
            scene = "scene%03d" % (i // 2)
            entries.append({"manifest_index": i, "scene_id": scene,
                            "ann_id": i, "target_object_id": str(i),
                            "stratum": "ambiguous" if i < 128 else "class_unique",
                            "target_class": "chair"})
            outcomes.append({"manifest_index": i, "scene": scene,
                             "failed": i == 0})
            source.append({"scene_id": scene, "ann_id": i, "object_id": str(i),
                           "description": "chair in the corner" if i == 0
                           else "chair near wall"})
        result = analyze({"rows": entries}, {"rows": outcomes}, source)
        self.assertEqual(result["summary"]["all"]["exposed_failures"], 1)
        self.assertEqual(result["summary"]["same_scene_discordant_pairs"], 1)
        self.assertEqual(result["summary"]["same_scene_unexposed_failures"], 0)

    def test_duplicate_description_fails(self):
        entries = [{"manifest_index": i, "scene_id": str(i), "ann_id": i,
                    "target_object_id": str(i), "stratum": "ambiguous",
                    "target_class": "chair"} for i in range(256)]
        outcomes = [{"manifest_index": i, "scene": str(i), "failed": False}
                    for i in range(256)]
        source = [{"scene_id": str(i), "ann_id": i, "object_id": str(i),
                   "description": "chair"} for i in range(256)]
        source.append(dict(source[0]))
        with self.assertRaisesRegex(ValueError, "identity"):
            analyze({"rows": entries}, {"rows": outcomes}, source)


if __name__ == "__main__":
    unittest.main()
