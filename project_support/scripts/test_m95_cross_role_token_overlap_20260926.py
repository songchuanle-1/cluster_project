import unittest

from m95_cross_role_token_overlap_20260926 import analyze


class CrossRoleOverlapTest(unittest.TestCase):
    def test_exact_token_intersection(self):
        rows = []
        for i in range(256):
            rows.append({"manifest_index": i, "scene": "s" + str(i),
                         "ann_id": i, "stratum": "ambiguous" if i < 128 else "class_unique",
                         "failed": i == 0, "spans": [
                             {"role": "target", "kind": "target_char_span", "mapped": True,
                              "token_positions": [1, 2]},
                             {"role": "other", "kind": "target_char_span", "mapped": True,
                              "token_positions": [2 if i == 0 else 3, 3]}]})
        receipt = {"rows": rows, "source_sha256": "a", "graph_sha256": "b",
                   "capture_sha256": "c"}
        result = analyze(receipt)
        self.assertEqual(result["summary"]["all"]["primary_overlap"], 1)
        self.assertEqual(result["summary"]["all"]["primary_overlap_failures"], 1)


if __name__ == "__main__":
    unittest.main()
