import unittest

from m95_discordance_provenance_20260923 import audit_class, summarize


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.group = {
            "query_indices": [0, 1], "native_positive_queries": 1,
            "seed_indices": [0, 1], "seed_original_superpoint_ids": [10, 11],
            "seed_inside_target_count": 1, "identity": "target_dominant",
            "dominant_physical_id": 1, "acceptable": True,
            "target_iou": 1., "mask_sha256": "example",
        }
        self.artifact = {
            "manifest_index": 1, "query_mask_logits": [[1., -1.], [2., -2.]],
            "query_masks": [[True, False], [True, False]],
            "query_scores": [0.8, 0.4], "native_positive": [True, False],
            "target_union": [True, False], "physical_instance_labels": [1, 2],
            "axis": {"original_superpoint_ids": [10, 11]},
        }
        self.capture = {"fps_superpoints": [0, 1], "sampled_seed_indices": [0, 1]}

    def test_distinct_logits_and_physical_seeds(self):
        r = audit_class(self.group, self.artifact, self.capture)
        self.assertEqual(r["max_abs_logit_difference"], 1.)
        self.assertEqual(r["mean_positive_minus_negative_score"], .4)
        self.assertTrue(r["seed_membership_equals_label"])
        self.assertEqual([x["original_superpoint_id"] for x in r["seeds"]], [10, 11])

    def test_equal_logits_are_not_assumed_distinct(self):
        self.artifact["query_mask_logits"][1] = [1., -1.]
        self.assertTrue(audit_class(self.group, self.artifact, self.capture)["all_cross_label_logits_equal"])

    def test_nearest_match_possible_outside_seed(self):
        self.artifact["native_positive"] = [False, True]
        r = audit_class(self.group, self.artifact, self.capture)
        self.assertEqual(r["positive_outside_seed_count"], 1)
        self.assertEqual(r["negative_inside_seed_count"], 1)
        self.assertFalse(r["seed_membership_equals_label"])

    def test_threshold_mismatch_rejected(self):
        self.artifact["query_mask_logits"][1][0] = -2.
        with self.assertRaises(ValueError):
            audit_class(self.group, self.artifact, self.capture)

    def test_frozen_seed_binding_rejected(self):
        self.group["seed_original_superpoint_ids"] = [10, 12]
        with self.assertRaises(ValueError):
            audit_class(self.group, self.artifact, self.capture)

    def test_nonfinite_rejected(self):
        self.artifact["query_mask_logits"][0][0] = float("nan")
        with self.assertRaises(ValueError):
            audit_class(self.group, self.artifact, self.capture)

    def test_scene_unit_and_acceptable_denominator(self):
        a = audit_class(self.group, self.artifact, self.capture)
        a["scene_id"] = "one"
        b = dict(a, scene_id="two", acceptable=False)
        self.assertEqual(summarize([a, b], "all")["classes"], 2)
        self.assertEqual(summarize([a, b], "acceptable")["scenes"], 1)


if __name__ == "__main__":
    unittest.main()
