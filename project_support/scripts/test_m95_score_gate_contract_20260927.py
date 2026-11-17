import unittest

from m95_score_gate_contract_20260927 import partition


class ScoreGateTest(unittest.TestCase):
    def setUp(self):
        self.row = {
            "manifest_index": 3, "scene": "scene", "ann_id": 7,
            "selected_query": 0, "ious": [.5, .6] + [0.] * 126,
            "native_positive": [True, True] + [False] * 126,
        }

    def test_gate_is_strict(self):
        result = partition(self.row)
        self.assertFalse(result["selected_score_supervised"])
        self.assertEqual(result["score_supervised_queries"], 1)

    def test_positive_above_half(self):
        self.row["ious"][0] = .5001
        self.assertTrue(partition(self.row)["selected_score_supervised"])

    def test_negative_query_not_supervised(self):
        self.row["native_positive"][0] = False
        self.assertFalse(partition(self.row)["selected_score_supervised"])

    def test_bad_axis(self):
        self.row["ious"].pop()
        with self.assertRaises(ValueError):
            partition(self.row)


if __name__ == "__main__":
    unittest.main()
