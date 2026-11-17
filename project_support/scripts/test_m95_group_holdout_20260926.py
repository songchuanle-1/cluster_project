import unittest

from m95_group_holdout_20260926 import selection


class HoldoutTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {"rows": [
            {"scene_id": f"s{i}", "ann_id": i, "target_object_id": str(i)}
            for i in range(256)]}

    def test_exact_lexicon_and_exclusion(self):
        source = [
            {"scene_id": "s0", "ann_id": 0, "object_id": "0",
             "object_name": "pillow", "description": "lower in the stack"},
            {"scene_id": "new", "ann_id": 10, "object_id": "2",
             "object_name": "pillow", "description": "The bottom of a stacked pair."},
            {"scene_id": "new", "ann_id": 11, "object_id": "3",
             "object_name": "pillow", "description": "low near another pillow"},
        ]
        rows = selection(source, self.manifest)
        self.assertEqual([(r["scene"], r["target"]) for r in rows], [("new", "2")])

    def test_duplicate_selected_description_fails(self):
        item = {"scene_id": "new", "ann_id": 10, "object_id": "2",
                "object_name": "pillow", "description": "bottom of stack"}
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            selection([item, item], self.manifest)


if __name__ == "__main__":
    unittest.main()
