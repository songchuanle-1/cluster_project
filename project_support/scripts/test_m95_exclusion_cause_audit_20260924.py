import copy
import unittest

from m95_exclusion_cause_audit_20260924 import (
    audit as native_audit, FOCUS, FROZEN_MANIFEST_SHA256, producer_sha256,
)


def audit(old, capture, target_overrides=None):
    targets = target_overrides or {}
    manifest = {
        "contract": "m95_preregistered_identity_controls_v1",
        "rows": [
            {"manifest_index": row["manifest_index"],
             "scene_id": row["scene_id"], "ann_id": row["ann_id"],
             "target_object_id": targets.get(row["manifest_index"], "1")}
            for row in old["rows"]
        ],
    }
    return native_audit(old, capture, manifest)


def fixture():
    frozen = [{
        "manifest_index": i, "scene_id": str(i), "ann_id": i,
        "partition": FOCUS if i < 6 else "deployed_success",
        "native_positive_queries": 2, "acceptable_queries": 1,
        "acceptable_native_positive_queries": 0,
        "target_seed_query": None if i < 5 else 1,
    } for i in range(256)]
    cause = {
        "sampled_pos": [[0, 0, 0], [2, 0, 0], [4, 0, 0]],
        "obj_pos": [[0, 0, 0], [4, 0, 0]],
        "sampled_instance_labels": [2, 0, 1],
        "object_ids": [2, 1],
        "nearest_query_per_gt": [0, 2],
        "member_queries_per_gt": [[], []],
        "native_positive": [True, False, True],
        "matched_query_gt_pairs": [[0, 0], [2, 1]],
    }
    rows = [{
        "manifest_index": i, "scene_id": str(i), "ann_id": i,
        "target_object_id": "1", "ious": [0, 0.8, 0],
        "native_match_cause": copy.deepcopy(cause),
    } for i in range(256)]
    capture = {
        "manifest": {"sha256": FROZEN_MANIFEST_SHA256},
        "checkpoint_sha256": "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e",
        "producer_sha256": producer_sha256(),
        "native_match_cause_completed": True,
        "selected_expressions": 256, "rows": rows,
    }
    return {"contract": "m95_failure_partition_descriptive_v1",
            "admission": False, "rows": frozen}, capture


class ExclusionCauseTests(unittest.TestCase):
    def test_other_gt_nearest_requires_native_target_axis(self):
        old, capture = fixture()
        result = audit(old, capture)
        self.assertEqual(len(result["rows"]), 6)
        self.assertEqual(result["rows"][0]["other_gt_only_count"], 1)
        self.assertEqual(result["rows"][0]["target_cause_count"], 1)
        self.assertEqual(result["mask_binding_mismatched_rows"], 0)
        self.assertEqual(result["mask_binding_mismatched_pairs"], 0)
        self.assertEqual(result["all_256_mask_binding"]["total_pairs"], 512)
        self.assertEqual(result["all_256_mask_binding"]["multi_gt_rows"], 256)
        self.assertEqual(result["all_256_mask_binding"]["nearest_collision_rows"], 0)
        self.assertEqual(result["all_256_mask_binding"]["target_pairs"], 256)
        self.assertEqual(result["all_256_mask_binding"]["target_mismatched_pairs"], 0)
        groups = result["binding_by_frozen_partition"]
        self.assertEqual(groups[FOCUS]["rows"], 6)
        self.assertEqual(groups["deployed_success"]["rows"], 250)
        self.assertEqual(groups[FOCUS]["target_pairs"], 6)
        self.assertFalse(result["admission"])

    def test_repeated_first_gt_misbinds_other_gt_mask(self):
        old, capture = fixture()
        for row in capture["rows"][:6]:
            cause = row["native_match_cause"]
            cause["sampled_instance_labels"][1] = 2
            cause["sampled_pos"].append([3, 0, 0])
            cause["sampled_instance_labels"].append(-1)
            cause["member_queries_per_gt"][0] = [1]
            cause["matched_query_gt_pairs"].append([1, 0])
            cause["native_positive"][1] = True
            cause["native_positive"].append(False)
            row["ious"] = [0, 0, 0, 0.8]
        for row in old["rows"][:6]:
            row["native_positive_queries"] = 3
        result = audit(old, capture)
        self.assertEqual(result["mask_binding_mismatched_rows"], 6)
        self.assertEqual(result["mask_binding_mismatched_pairs"], 6)
        self.assertEqual(result["all_256_mask_binding"]["mismatched_rows"], 6)
        self.assertEqual(result["all_256_mask_binding"]["mismatched_pairs"], 6)
        self.assertEqual(result["all_256_mask_binding"]["total_pairs"], 518)
        self.assertEqual(result["all_256_mask_binding"]["target_mismatched_rows"], 6)
        self.assertEqual(result["all_256_mask_binding"]["target_mismatched_pairs"], 6)
        self.assertEqual(result["all_256_mask_binding"]["other_to_target_pairs"], 0)
        binding = result["rows"][0]["gt_mask_binding"]
        self.assertEqual(binding["matched_gt_ids"], [0, 1, 0])
        self.assertEqual(binding["mismatched_pair_positions"], [1])
        self.assertEqual(binding["pairs"][1]["matched_object_id"], "1")
        self.assertEqual(binding["pairs"][1]["addressed_mask_object_id"], "2")

    def test_shared_nearest_query_is_separate_from_mask_misbinding(self):
        old, capture = fixture()
        cause = capture["rows"][6]["native_match_cause"]
        cause["obj_pos"][1] = [0, 0, 0]
        cause["nearest_query_per_gt"][1] = 0
        cause["matched_query_gt_pairs"][1] = [0, 1]
        cause["native_positive"][2] = False
        cause["sampled_instance_labels"][2] = -1
        old["rows"][6]["native_positive_queries"] = 1
        result = audit(old, capture)
        total = result["all_256_mask_binding"]
        self.assertEqual(total["nearest_collision_rows"], 1)
        self.assertEqual(total["nearest_collision_extra_pairs"], 1)
        self.assertEqual(total["target_nearest_collision_rows"], 1)
        self.assertEqual(total["target_nearest_shared_gt_count"], 1)
        self.assertEqual(total["mismatched_rows"], 0)
        self.assertEqual(total["rows"][6]["pair_count"], 2)
        self.assertEqual(
            result["binding_by_frozen_partition"]["deployed_success"]["nearest_collision_rows"],
            1,
        )

    def test_other_gt_nearest_collision_is_not_target_collision(self):
        old, capture = fixture()
        cause = capture["rows"][6]["native_match_cause"]
        cause["obj_pos"].append([0, 0, 0])
        cause["object_ids"].append(3)
        cause["nearest_query_per_gt"].append(0)
        cause["member_queries_per_gt"].append([])
        cause["matched_query_gt_pairs"].append([0, 2])
        result = audit(old, capture)
        total = result["all_256_mask_binding"]
        self.assertEqual(total["nearest_collision_rows"], 1)
        self.assertEqual(total["target_nearest_collision_rows"], 0)
        self.assertEqual(total["target_nearest_shared_gt_count"], 0)
        self.assertEqual(total["mismatched_rows"], 0)
        group = result["binding_by_frozen_partition"]["deployed_success"]
        self.assertEqual(group["nearest_collision_rows"], 1)
        self.assertEqual(group["target_nearest_collision_rows"], 0)

    def test_nonfocus_misbinding_is_counted_separately(self):
        old, capture = fixture()
        cause = capture["rows"][6]["native_match_cause"]
        cause["sampled_instance_labels"][1] = 2
        cause["member_queries_per_gt"][0] = [1]
        cause["matched_query_gt_pairs"].append([1, 0])
        cause["native_positive"][1] = True
        old["rows"][6]["native_positive_queries"] = 3
        old["rows"][6]["acceptable_native_positive_queries"] = 1
        result = audit(old, capture)
        self.assertEqual(result["mask_binding_mismatched_rows"], 0)
        self.assertEqual(result["all_256_mask_binding"]["mismatched_rows"], 1)
        self.assertEqual(result["all_256_mask_binding"]["rows"][6]["mismatched_pair_count"], 1)
        self.assertEqual(result["all_256_mask_binding"]["target_mismatched_rows"], 1)
        groups = result["binding_by_frozen_partition"]
        self.assertEqual(groups[FOCUS]["mismatched_rows"], 0)
        self.assertEqual(groups["deployed_success"]["mismatched_rows"], 1)
        self.assertEqual(groups["deployed_success"]["target_mismatched_pairs"], 1)
        self.assertEqual(
            sum(group["mismatched_pairs"] for group in groups.values()),
            result["all_256_mask_binding"]["mismatched_pairs"],
        )

    def test_other_gt_pair_can_address_target_without_target_pair_mismatch(self):
        old, capture = fixture()
        cause = capture["rows"][6]["native_match_cause"]
        cause["sampled_instance_labels"][1] = 2
        cause["member_queries_per_gt"][0] = [1]
        cause["matched_query_gt_pairs"].append([1, 0])
        cause["native_positive"][1] = True
        old["rows"][6]["native_positive_queries"] = 3
        old["rows"][6]["acceptable_native_positive_queries"] = 1
        capture["rows"][6]["target_object_id"] = "2"
        result = audit(old, capture, {6: "2"})["all_256_mask_binding"]
        self.assertEqual(result["mismatched_rows"], 1)
        self.assertEqual(result["target_mismatched_rows"], 0)
        self.assertEqual(result["other_to_target_pairs"], 1)
        groups = audit(old, capture, {6: "2"})["binding_by_frozen_partition"]
        self.assertEqual(groups["deployed_success"]["target_mismatched_pairs"], 0)
        self.assertEqual(groups["deployed_success"]["other_to_target_pairs"], 1)

    def test_collision_binding_intersection_distinguishes_target_from_other_gt(self):
        old, capture = fixture()
        for index in (6, 7):
            cause = capture["rows"][index]["native_match_cause"]
            cause["sampled_instance_labels"][1] = 2
            cause["member_queries_per_gt"][0] = [1]
            cause["matched_query_gt_pairs"].append([1, 0])
            cause["native_positive"][1] = True
            old["rows"][index]["native_positive_queries"] = 3
            old["rows"][index]["acceptable_native_positive_queries"] = 1
        target_cause = capture["rows"][6]["native_match_cause"]
        target_cause["obj_pos"][1] = [0, 0, 0]
        target_cause["nearest_query_per_gt"][1] = 0
        target_cause["matched_query_gt_pairs"][1] = [0, 1]
        target_cause["native_positive"][2] = False
        target_cause["sampled_instance_labels"][2] = -1
        old["rows"][6]["native_positive_queries"] = 2
        old["rows"][6]["acceptable_native_positive_queries"] = 1

        other_cause = capture["rows"][7]["native_match_cause"]
        other_cause["obj_pos"].append([0, 0, 0])
        other_cause["object_ids"].append(3)
        other_cause["nearest_query_per_gt"].append(0)
        other_cause["member_queries_per_gt"].append([])
        other_cause["matched_query_gt_pairs"].insert(2, [0, 2])
        result = audit(old, capture)
        total = result["all_256_mask_binding"]
        self.assertEqual(total["any_collision_and_misbinding_rows"], 2)
        self.assertEqual(total["target_collision_and_misbinding_rows"], 1)
        self.assertTrue(total["rows"][6]["target_collision_and_misbinding"])
        self.assertFalse(total["rows"][7]["target_collision_and_misbinding"])
        group = result["binding_by_frozen_partition"]["deployed_success"]
        self.assertEqual(group["any_collision_and_misbinding_rows"], 2)
        self.assertEqual(group["target_collision_and_misbinding_rows"], 1)

    def test_missing_target_axis_rejected(self):
        old, capture = fixture()
        for row in capture["rows"][:6]:
            row["target_object_id"] = "3"
        with self.assertRaisesRegex(ValueError, "target GT"):
            audit(old, capture, {i: "3" for i in range(6)})

    def test_valid_but_substituted_target_gt_rejected(self):
        old, capture = fixture()
        capture["rows"][6]["target_object_id"] = "2"
        with self.assertRaisesRegex(ValueError, "Frozen manifest target binding"):
            audit(old, capture)

    def test_manifest_expression_drift_rejected(self):
        old, capture = fixture()
        manifest = {
            "contract": "m95_preregistered_identity_controls_v1",
            "rows": [{"manifest_index": i, "scene_id": str(i),
                      "ann_id": i, "target_object_id": "1"} for i in range(256)],
        }
        manifest["rows"][6]["ann_id"] = 999
        with self.assertRaisesRegex(ValueError, "Frozen manifest target binding"):
            native_audit(old, capture, manifest)

    def test_native_pair_order_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][6]["native_match_cause"]["matched_query_gt_pairs"].reverse()
        with self.assertRaisesRegex(ValueError, "pair order"):
            audit(old, capture)

    def test_incomplete_capture_rejected(self):
        old, capture = fixture()
        capture["rows"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            audit(old, capture)

    def test_stale_producer_rejected(self):
        old, capture = fixture()
        capture["producer_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "producer hash"):
            audit(old, capture)

    def test_analysis_hash_cannot_replace_capture_manifest_hash(self):
        old, capture = fixture()
        capture["manifest"]["sha256"] = (
            "1980ac6fe2731dd5cd3b03194e1529905562e4eeceaac04b96823f6de5da131f"
        )
        with self.assertRaisesRegex(ValueError, "Incomplete or mismatched native capture"):
            audit(old, capture)

    def test_outcome_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][0]["ious"][0] = 0.8
        with self.assertRaisesRegex(ValueError, "outcomes"):
            audit(old, capture)

    def test_matcher_cause_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][0]["native_match_cause"]["nearest_query_per_gt"] = [1, 2]
        with self.assertRaisesRegex(ValueError, "nearest"):
            audit(old, capture)

    def test_nonfocus_matcher_cause_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][6]["native_match_cause"]["nearest_query_per_gt"] = [1, 2]
        with self.assertRaisesRegex(ValueError, "nearest"):
            audit(old, capture)

    def test_nonfocus_positive_count_drift_rejected(self):
        old, capture = fixture()
        old["rows"][6]["native_positive_queries"] = 1
        with self.assertRaisesRegex(ValueError, "outcomes"):
            audit(old, capture)

    def test_nonfocus_acceptable_count_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][6]["ious"][1] = 0.4
        with self.assertRaisesRegex(ValueError, "outcomes"):
            audit(old, capture)

    def test_nonfocus_positive_acceptable_overlap_drift_rejected(self):
        old, capture = fixture()
        cause = capture["rows"][6]["native_match_cause"]
        cause["obj_pos"][1] = [2, 0, 0]
        cause["nearest_query_per_gt"][1] = 1
        cause["matched_query_gt_pairs"][1] = [1, 1]
        cause["native_positive"] = [True, True, False]
        cause["sampled_instance_labels"][2] = -1
        with self.assertRaisesRegex(ValueError, "outcomes"):
            audit(old, capture)

    def test_nonfocus_query_axis_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][6]["ious"].pop()
        with self.assertRaisesRegex(ValueError, "outcomes"):
            audit(old, capture)

    def test_nonfinite_iou_rejected_even_when_frozen_counts_match(self):
        old, capture = fixture()
        capture["rows"][6]["ious"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "Invalid native IoU"):
            audit(old, capture)

    def test_out_of_range_iou_rejected_even_when_frozen_counts_match(self):
        old, capture = fixture()
        capture["rows"][6]["ious"][0] = -0.1
        with self.assertRaisesRegex(ValueError, "Invalid native IoU"):
            audit(old, capture)

    def test_nonfocus_target_axis_drift_rejected(self):
        old, capture = fixture()
        capture["rows"][6]["target_object_id"] = "3"
        with self.assertRaisesRegex(ValueError, "Frozen manifest target binding"):
            audit(old, capture)


if __name__ == "__main__":
    unittest.main()
