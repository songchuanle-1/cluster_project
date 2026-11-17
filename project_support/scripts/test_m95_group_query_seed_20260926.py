import unittest

from m95_group_query_seed_20260926 import inspect


class QuerySeedTest(unittest.TestCase):
    def test_nearest_other_instance_and_mixed_votes(self):
        row = {"manifest_index": 38, "scene": "scene", "ann_id": 1,
               "target_object_id": 2, "selected_query": 0,
               "native_match_cause": {
                   "sampled_pos": [[0, 0, 0], [1, 0, 2],
                                   [10, 0, 3], [11, 0, 1]] * 32,
                   "sampled_instance_labels": [2, 3, 2, 4] * 32}}
        capture = {"rows": [dict(row, manifest_index=i)
                            for i in range(256)]}
        screen = {"exposed_descriptions": [{
            "manifest_index": 38, "scene": "scene",
            "description": "bottom pillow of stack"}]}
        result = inspect(capture, screen)
        self.assertEqual(result["summary"]["target_covered"], 1)
        self.assertEqual(result["rows"][0]["target_seeds"], 64)
        self.assertEqual(result["rows"][0]["lower_votes"], 32)
        self.assertEqual(result["summary"]["lower_mixed"], 1)

    def test_identity_mismatch_fails_closed(self):
        row = {"manifest_index": 0, "scene": "a", "ann_id": 0}
        capture = {"rows": [dict(row, manifest_index=i) for i in range(256)]}
        with self.assertRaises(ValueError):
            inspect(capture, {"exposed_descriptions": [
                {"manifest_index": 0, "scene": "b"}]})


if __name__ == "__main__":
    unittest.main()
