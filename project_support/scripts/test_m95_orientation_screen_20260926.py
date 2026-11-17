import unittest

from m95_orientation_screen_20260926 import analyze


class OrientationScreenTests(unittest.TestCase):
    def test_exact_binding_and_pair(self):
        manifest = {"rows": [
            {"manifest_index": i, "scene_id": "scene" if i < 2 else f"scene{i}",
             "ann_id": i, "target_object_id": i, "stratum": "ambiguous"}
            for i in range(256)]}
        outcomes = {"rows": [
            {"manifest_index": i, "scene": row["scene_id"], "failed": i == 0}
            for i, row in enumerate(manifest["rows"])]}
        source = [
            {"scene_id": row["scene_id"], "ann_id": i, "object_id": i,
             "description": "the TILTED chair" if i == 0 else "a chair"}
            for i, row in enumerate(manifest["rows"])]
        result = analyze(manifest, outcomes, source)
        self.assertEqual(result["summary"]["all"]["exposed_failures"], 1)
        self.assertEqual(result["summary"]["same_scene_discordant_pairs"], 1)
        self.assertEqual(result["summary"]["same_scene_no_orientation_failures"], 0)
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            analyze(manifest, outcomes, source + [source[0]])

    def test_duplicate_or_missing_input_fails(self):
        source = [{"scene_id": "scene", "ann_id": 1, "object_id": 2,
                   "description": "tilted"}]
        manifest = {"rows": [{"manifest_index": i + 1, "scene_id": "scene", "ann_id": 1,
                              "target_object_id": 2, "stratum": "ambiguous"}
                             for i in range(256)]}
        outcomes = {"rows": [{"manifest_index": i + 1, "scene": "scene", "failed": False}
                             for i in range(256)]}
        with self.assertRaisesRegex(ValueError, "index mismatch"):
            analyze(manifest, outcomes, source)


if __name__ == "__main__":
    unittest.main()
