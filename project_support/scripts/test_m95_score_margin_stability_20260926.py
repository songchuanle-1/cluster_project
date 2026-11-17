import unittest

from m95_score_margin_stability_20260926 import audit


class RankMarginAuditTest(unittest.TestCase):
    def rows(self, margin=0.5, drift=0.0):
        a, b = [], []
        for i in range(256):
            base = {"manifest_index": i, "scene_id": "scene_%d" % (i // 2),
                    "deployed_query": 0}
            a.append({**base, "scores": [1.0, 1.0 - margin]})
            b.append({**base, "scores": [1.0 - drift, 1.0 - margin + drift]})
        return {"rows": a}, {"rows": b}

    def test_stable_margin(self):
        result = audit(*self.rows())
        self.assertEqual(result["pairwise_bound_exposed"], 0)
        self.assertEqual(result["scenes"], 128)

    def test_exposed_margin(self):
        a, b = self.rows(margin=0.1)
        for row in b["rows"]:
            row["scores"][0] -= 0.051
        result = audit(a, b)
        self.assertEqual(result["pairwise_bound_exposed"], 256)
        self.assertEqual(result["selected_changes"], 0)

    def test_selector_guard(self):
        a, b = self.rows()
        b["rows"][0]["deployed_query"] = 1
        with self.assertRaises(ValueError):
            audit(a, b)

    def test_nonfinite_guard(self):
        a, b = self.rows()
        a["rows"][0]["scores"][0] = float("nan")
        with self.assertRaises(ValueError):
            audit(a, b)


if __name__ == "__main__":
    unittest.main()
