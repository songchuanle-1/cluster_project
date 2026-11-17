import unittest

from m95_mask_equivalence_20260923 import equivalence, sign, summarize_equivalence, transitions


class EquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.m = {"target_object_id": "1", "same_class_peer_object_ids": ["2"],
                  "manifest_index": 0, "scene_id": "s"}
        self.masks = [[True, False, False], [True, False, False], [False, True, False]]
        self.positive = [True, False, False]
        self.seeds = [0, 1, 1]

    def calc(self):
        return equivalence(self.masks, self.positive, self.seeds, [1, 2, 8],
                           [True, False, False], self.m)

    def test_exact_class_discordance_and_seed_binding(self):
        r = self.calc()
        self.assertEqual((r["query_count"], r["unique_mask_count"]), (3, 2))
        c = r["classes"][0]
        self.assertEqual(c["query_indices"], [0, 1])
        self.assertTrue(c["label_discordant"])
        self.assertTrue(c["seed_target_discordant"])
        self.assertEqual(c["distinct_seed_count"], 2)
        self.assertEqual(c["identity"], "target_dominant")

    def test_equal_iou_does_not_merge_different_masks(self):
        self.masks = [[False, False, True], [False, True, False], [True, False, False]]
        self.assertEqual(self.calc()["unique_mask_count"], 3)

    def test_same_label_duplicates_are_not_discordant(self):
        self.positive = [True, True, False]
        self.assertEqual(self.calc()["discordant_classes"], 0)

    def test_empty_masks_retained_without_identity(self):
        self.masks[:2] = [[False] * 3, [False] * 3]
        c = self.calc()["classes"][0]
        self.assertTrue(c["empty_mask"])
        self.assertEqual(c["identity"], "no_instance")

    def test_outside_peer_is_not_cross_class(self):
        self.masks[2] = [False, False, True]
        self.assertEqual(self.calc()["classes"][-1]["identity"], "outside_target_and_registered_peers")

    def test_query_axis_rejected(self):
        self.positive.pop()
        with self.assertRaises(ValueError):
            self.calc()

    def test_mask_axis_rejected(self):
        self.masks[0].pop()
        with self.assertRaises(ValueError):
            self.calc()

    def test_seed_bounds_rejected(self):
        self.seeds[0] = -1
        with self.assertRaises(ValueError):
            self.calc()

    def test_nonboolean_rejected(self):
        self.masks[0][0] = 1
        with self.assertRaises(ValueError):
            self.calc()

    def test_target_alignment_rejected(self):
        self.m["target_object_id"] = 2
        with self.assertRaises(ValueError):
            self.calc()

    def test_scene_denominator_and_no_cross_expression_dedup(self):
        a, b = self.calc(), self.calc()
        b["manifest_index"] = 1
        r = summarize_equivalence([a, b])
        self.assertEqual((r["expressions"], r["scenes"], r["unique_mask_count"]), (2, 1, 4))
        self.assertEqual(r["discordant_scenes"], 1)
        self.assertEqual(r["queries_in_discordant_classes"], 4)


class TransitionTests(unittest.TestCase):
    def row(self, i=0):
        return {"manifest_index": i, "scene_id": "s", "stages": {
            "raw_3d": {"deployed": -1., "acceptable": 0., "contrast": 1.},
            "fused": {"deployed": 1., "acceptable": 2., "contrast": 1.},
            "final": {"deployed": 0., "acceptable": 1., "contrast": 1.}}}

    def test_signs_and_paired_changes(self):
        r = transitions([self.row()], draws=20)
        p = r["paired_changes"]["deployed_raw_3d_to_fused"]
        self.assertEqual(p["pooled_mean"], 2)
        self.assertEqual(p["sign_transitions"], {"negative_to_positive": 1})
        self.assertEqual(r["sign_counts"]["deployed"]["final"], {"zero": 1})

    def test_missing_not_imputed(self):
        a = self.row(1)
        a["stages"]["fused"]["contrast"] = None
        r = transitions([self.row(), a], draws=20)
        self.assertEqual((r["available"], r["missing_indices"]), (1, [1]))

    def test_duplicate_index_rejected(self):
        with self.assertRaises(ValueError):
            transitions([self.row(), self.row()], draws=20)

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            sign(float("nan"))

    def test_paired_scene_unit(self):
        r = transitions([self.row(), self.row(1)], draws=20)
        p = r["paired_changes"]["acceptable_fused_to_final"]
        self.assertEqual((p["available"], p["scenes"]), (2, 1))
        self.assertEqual(p["scene_bootstrap_95ci"]["point_estimate"], -1)


if __name__ == "__main__":
    unittest.main()
