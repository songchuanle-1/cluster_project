import unittest

from physical_mask_endpoints_20260916 import mask_endpoints, recoverable_same_class_stratum


class Tests(unittest.TestCase):
    def setUp(self):
        self.axis = dict(original_superpoint_ids=[2, 5, 8, 11, 19],
                         sample_inverse=[0, 1, 2, 3, 4, 4])
        self.labels = [1, 1, 2, 2, -100]
        self.mask = [False, False, True, True, False]

    def endpoint(self, **kwargs):
        return mask_endpoints(self.axis, self.mask, self.labels, [1], **kwargs)

    def test_wrong_instance(self):
        result = self.endpoint(semantic_labels=[4, 4, 4, 4, -100])
        self.assertEqual(result["best_overlap_instances"], [2])
        self.assertTrue(recoverable_same_class_stratum([.1, .8], 0, result))

    def test_unknown_semantics_fail_closed(self):
        result = self.endpoint()
        self.assertIsNone(result["same_class"])
        self.assertFalse(recoverable_same_class_stratum([.1, .8], 0, result))

    def test_different_class(self):
        self.assertFalse(self.endpoint(semantic_labels=[4, 4, 5, 5, -100])["same_class"])

    def test_mixed_class_not_majority_vote(self):
        self.assertIsNone(self.endpoint(semantic_labels=[4, 4, 4, 5, -100])["same_class"])

    def test_ties_preserved(self):
        self.mask = [True, False, True, False, False]
        result = self.endpoint(semantic_labels=[4, 4, 4, 4, -100])
        self.assertEqual(result["best_overlap_instances"], [1, 2])
        self.assertFalse(result["unique_wrong_instance"])
        self.assertIsNone(result["same_class"])

    def test_background_in_union(self):
        self.mask[-1] = True
        result = self.endpoint()
        self.assertEqual(result["selected_background"], 1)
        self.assertAlmostEqual(result["overlaps"][1]["iou"], 2 / 3)

    def test_empty_mask_no_endpoint(self):
        self.mask = [False] * 5
        self.assertEqual(self.endpoint()["best_overlap_instances"], [])

    def test_support_mismatch_rejected(self):
        self.mask.pop()
        with self.assertRaises(ValueError):
            self.endpoint()

    def test_non_boolean_mask_rejected(self):
        self.mask = [0, 0, 1, 1, 0]
        with self.assertRaises(ValueError):
            self.endpoint()

    def test_absent_target_rejected(self):
        with self.assertRaises(ValueError):
            mask_endpoints(self.axis, self.mask, self.labels, [3])

    def test_strict_threshold(self):
        result = self.endpoint(semantic_labels=[4, 4, 4, 4, -100])
        self.assertFalse(recoverable_same_class_stratum([.1, .5], 0, result))
        self.assertFalse(recoverable_same_class_stratum([.8, .9], 0, result))

    def test_invalid_query_iou_rejected(self):
        with self.assertRaises(ValueError):
            recoverable_same_class_stratum([float("nan")], 0, self.endpoint())


if __name__ == "__main__":
    unittest.main()
