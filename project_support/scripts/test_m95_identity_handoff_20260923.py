import unittest

from m95_identity_handoff_20260923 import audit


def row(**updates):
    item = {
        "scene_id": "scene0",
        "target_positive_iou": 0.8,
        "target_objectness_iou": 0.8,
        "primary_pair_iou_uplift": 0.7,
        "stratum": "ambiguous",
        "class_matched_non_target_query": 1,
        "deployed_iou": 0.2,
        "ious": [0.2, 0.8],
    }
    item.update(updates)
    return item


class HandoffTests(unittest.TestCase):
    def test_common_support_has_no_fallback(self):
        result = audit([row(), row(target_objectness_iou=None)])
        self.assertEqual(result["common_support_expressions"], 1)
        self.assertEqual(result["excluded_from_common_support"], 1)
        summary = result["common_support_positive_minus_target_objectness"]
        self.assertEqual(summary["scene_bootstrap_95ci"]["point_estimate"], 0)

    def test_missing_pairs_disjoint(self):
        result = audit([
            row(primary_pair_iou_uplift=None, stratum="class_unique"),
            row(primary_pair_iou_uplift=None, class_matched_non_target_query=None),
            row(primary_pair_iou_uplift=None),
        ])
        self.assertEqual(sum(result["primary_missingness"].values()), 3)
        self.assertTrue(all(v == 1 for v in result["primary_missingness"].values()))

    def test_half_iou_is_failure(self):
        result = audit([row(deployed_iou=0.5, ious=[0.5])])
        self.assertEqual(result["failure_counts"]["total"], 1)
        self.assertEqual(result["failure_counts"]["no_acceptable_candidate"], 1)


if __name__ == "__main__":
    unittest.main()
