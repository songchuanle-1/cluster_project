import copy
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_m95_manifest_identity_controls_20260922 import (
    CAPTURE_ARTIFACT_CONTRACT,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_MANIFEST_SHA256,
    analyze_artifacts,
    compact_row,
    dominant_overlap,
    score_match_pair,
    score_pick,
    validate_artifact_header,
)


def synthetic_artifact():
    labels = [1, 1, 1, 1, 2, 2]
    target = [True, True, True, True, False, False]
    masks = [
        [True, True, True, True, False, False],
        [False, False, False, False, True, True],
        [False, False, False, True, True, False],
    ]
    features = [
        [1.0, 0.0],
        [1.0, 0.0],
        [1.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [0.0, 1.0],
    ]
    return {
        "manifest_index": 0,
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "artifact_contract": CAPTURE_ARTIFACT_CONTRACT,
        "query_scores": [0.8, 0.75, 0.1],
        "query_masks": masks,
        "native_positive": [True, False, False],
        "fps_seed_inside_target": [True, False, False],
        "physical_instance_labels": labels,
        "target_union": target,
        "features": {stage: features for stage in (
            "raw_3d",
            "raw_2d",
            "projected_3d",
            "projected_2d",
            "fused",
            "final",
        )},
    }


def synthetic_manifest_row(index=0, stratum="ambiguous", peers=None):
    return {
        "manifest_index": index,
        "stratum": stratum,
        "scene_id": "scene%04d_00" % index,
        "ann_id": index,
        "target_object_id": "1",
        "target_class": "chair",
        "same_class_peer_object_ids": ["2"] if peers is None else peers,
    }


def synthetic_report_row(artifact):
    masks = artifact["query_masks"]
    target = artifact["target_union"]
    ious = []
    for mask in masks:
        overlap = sum(a and b for a, b in zip(mask, target))
        union = sum(a or b for a, b in zip(mask, target))
        ious.append(overlap / max(union, 1))
    return {
        "manifest_index": artifact["manifest_index"],
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "scene": "scene%04d_00" % artifact["manifest_index"],
        "ann_id": artifact["manifest_index"],
        "scores": list(artifact["query_scores"]),
        "ious": ious,
        "native_positive": list(artifact["native_positive"]),
        "seed_inside": list(artifact["fps_seed_inside_target"]),
    }


class ManifestIdentityAnalysisTest(unittest.TestCase):
    def test_score_pick_uses_lowest_index_on_tie(self):
        self.assertEqual(score_pick([0.5, 0.5], [True, True]), 0)
        self.assertIsNone(score_pick([0.5, 0.5], [False, False]))

    def test_dominant_overlap_uses_lowest_instance_on_tie(self):
        self.assertEqual(
            dominant_overlap(
                [True, True, True, False],
                [9, 3, 3, 9],
            ),
            3,
        )
        self.assertIsNone(
            dominant_overlap([True, False], [-1, -1])
        )

    def test_score_match_pair_is_thresholded_and_deterministic(self):
        pair = score_match_pair([0.8, 0.72, 0.69], [0, 2], [1])
        self.assertEqual(pair["negative_index"], 1)
        self.assertEqual(pair["positive_index"], 2)
        self.assertAlmostEqual(pair["score_difference"], 0.03)
        self.assertIsNone(score_match_pair([0.8], [0], []))

    def test_compact_row_derives_registered_controls(self):
        artifact = synthetic_artifact()
        row = compact_row(
            artifact,
            synthetic_report_row(artifact),
            synthetic_manifest_row(),
        )
        self.assertEqual(row["deployed_query"], 0)
        self.assertEqual(row["target_positive_query"], 0)
        self.assertEqual(row["target_objectness_query"], 0)
        self.assertEqual(row["class_matched_selector_query"], 0)
        self.assertEqual(row["class_matched_non_target_query"], 1)
        self.assertEqual(row["score_matched_pair"]["negative_index"], 1)
        self.assertAlmostEqual(row["primary_pair_iou_uplift"], 1.0)
        self.assertAlmostEqual(
            row["stage_identity"]["final"]["margin"], 1.0
        )

    def test_artifact_header_rejects_manifest_drift(self):
        artifact = synthetic_artifact()
        validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)
        artifact["manifest_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "manifest hash"):
            validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)

    def test_full_synthetic_analysis_supports_only_when_gates_pass(self):
        manifest = {}
        report_rows = []
        artifacts = {}
        for index in range(256):
            artifact = copy.deepcopy(synthetic_artifact())
            artifact["manifest_index"] = index
            report = synthetic_report_row(artifact)
            report["scene"] = "scene%04d_00" % index
            report["ann_id"] = index
            manifest[index] = synthetic_manifest_row(index)
            report_rows.append(report)
            artifacts[index] = artifact
        report = {
            "artifact_contract": CAPTURE_ARTIFACT_CONTRACT,
            "native_capture_completed": True,
            "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
            "manifest": {
                "sha256": EXPECTED_MANIFEST_SHA256,
                "rows": 256,
            },
            "rows": report_rows,
        }
        result = analyze_artifacts(
            report,
            manifest,
            artifacts,
            draws=200,
        )
        primary = result["summary"]["primary_estimand"]
        self.assertTrue(primary["supported"])
        self.assertEqual(primary["available"], 256)
        self.assertEqual(primary["scenes"], 256)
        self.assertGreater(primary["scene_bootstrap_95ci"]["lo"], 0.0)
        self.assertEqual(
            result["summary"]["selectors"]["target_positive"]["available"],
            256,
        )

    def test_missing_peer_pool_rejects_primary_pair(self):
        artifact = synthetic_artifact()
        manifest_row = synthetic_manifest_row(peers=[])
        row = compact_row(
            artifact,
            synthetic_report_row(artifact),
            manifest_row,
        )
        self.assertIsNone(row["class_matched_non_target_query"])
        self.assertIsNone(row["primary_pair_iou_uplift"])


if __name__ == "__main__":
    unittest.main()
