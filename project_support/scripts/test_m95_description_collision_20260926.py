import unittest

from m95_description_collision_20260926 import audit


class DescriptionCollisionTest(unittest.TestCase):
    def test_distinct_target_only(self):
        cohort = {"rows": [
            {"manifest_index": i, "scene": "s" + str(i), "ann_id": i,
             "target": "1", "stratum": "ambiguous" if i < 128 else "class_unique",
             "failed": i == 0} for i in range(256)]}
        source = [{"scene_id": "s" + str(i), "ann_id": i, "object_id": "1",
                   "description": "A chair."} for i in range(256)]
        source += [{"scene_id": "s0", "ann_id": 999, "object_id": "2",
                    "description": "a chair !"},
                   {"scene_id": "s1", "ann_id": 998, "object_id": "1",
                    "description": "a chair"}]
        result = audit(cohort, source)
        self.assertEqual(result["summary"]["all"]["collisions"], 1)
        self.assertEqual(result["summary"]["all"]["collision_failures"], 1)
        self.assertEqual(result["summary"]["all"]["raw_collisions"], 0)


if __name__ == "__main__":
    unittest.main()
