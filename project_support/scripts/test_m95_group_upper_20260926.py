import unittest

from m95_group_upper_20260926 import select


class OpposingGroupTests(unittest.TestCase):
    def test_exclusion_and_directional_lexicon(self):
        manifest = {"rows": [
            {"scene_id": f"s{i}", "ann_id": i, "target_object_id": str(i)}
            for i in range(256)]}
        lower = {"rows": [{"scene": "old", "ann_id": 1, "target": "2"}]}
        source = [
            {"scene_id": "old", "ann_id": 1, "object_id": "2",
             "object_name": "pillow", "description": "top of the stack"},
            {"scene_id": "new", "ann_id": 3, "object_id": "4",
             "object_name": "pillow", "description": "the UPPER pillow in the row"},
            {"scene_id": "new", "ann_id": 4, "object_id": "5",
             "object_name": "pillow", "description": "on a shelf above a group"},
        ]
        rows = select(source, manifest, lower)
        self.assertEqual([(r["scene"], r["target"]) for r in rows], [("new", "4")])


if __name__ == "__main__":
    unittest.main()
