import unittest

from m95_partition_drift_spread_20260925 import summarize


def row(ids):
    return {"native_input_sha256": "same", "hierarchical_cluster_ids": [ids]}


def features(values, masks):
    return {"features": {"final": [[value] for value in values]},
            "query_masks": masks}


class DriftSpreadTest(unittest.TestCase):
    def setUp(self):
        self.old_rows = {83: row([0, 0]), 174: row([0, 0, 1, 1])}
        self.new_rows = {83: row([0, 0]), 174: row([0, 1, 1, 1])}
        self.old_features = {
            83: features([0, 0], {103: [0, 0]}),
            174: features([0, 0, 0, 0], {70: [0, 1, 0, 0], 87: [0, 1, 0, 0]}),
        }
        self.new_features = {
            83: features([0, 0], {103: [0, 0]}),
            174: features([0, 0.2, 0.01, 0], {70: [0, 0, 0, 0], 87: [0, 1, 0, 0]}),
        }

    def test_spread_and_mask_change(self):
        result = summarize(self.old_rows, self.new_rows,
                           self.old_features, self.new_features)
        observed = result["rows"][1]
        self.assertEqual(observed["changed_assignment_points"], [1])
        self.assertEqual(observed["changed_mask_points"], [1])
        self.assertEqual(observed["groups"]["changed_assignment"]["above_1e-3"], 1)
        self.assertEqual(observed["groups"]["same_old_cluster_unchanged"]["points"], 1)
        self.assertEqual(observed["groups"]["same_new_cluster_unchanged"]["above_1e-3"], 1)
        self.assertEqual(observed["above_1e-3_total"], 2)
        self.assertFalse(result["admission"])

    def test_input_mismatch_fails(self):
        self.new_rows[174]["native_input_sha256"] = "other"
        with self.assertRaisesRegex(ValueError, "Native input"):
            summarize(self.old_rows, self.new_rows,
                      self.old_features, self.new_features)

    def test_feature_axis_mismatch_fails(self):
        self.new_features[174]["features"]["final"].pop()
        with self.assertRaisesRegex(ValueError, "axes"):
            summarize(self.old_rows, self.new_rows,
                      self.old_features, self.new_features)


if __name__ == "__main__":
    unittest.main()
