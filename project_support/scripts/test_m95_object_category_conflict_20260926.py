import unittest

from m95_object_category_conflict_20260926 import audit


class ObjectCategoryConflictTest(unittest.TestCase):
    def test_same_instance_names(self):
        cohort = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "target": "1", "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 0} for i in range(256)]}
        source = [{"scene_id": "s" + str(i), "ann_id": i, "object_id": "1",
                   "object_name": "chair", "description": "chair"} for i in range(256)]
        source.extend([
            {"scene_id": "s0", "ann_id": 999, "object_id": "1",
             "object_name": "stool", "description": "stool"},
            {"scene_id": "s1", "ann_id": 998, "object_id": "1",
             "object_name": "chairs", "description": "chairs"},
        ])
        result = audit(cohort, source)
        self.assertEqual(result["summary"]["all"]["exposed"], 1)
        self.assertEqual(result["summary"]["all"]["exposed_failures"], 1)
        self.assertEqual(result["summary"]["all"]["multi_same_name"], 1)


if __name__ == "__main__":
    unittest.main()
