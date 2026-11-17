import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


from native_manifest_capture_20260922 import (
    MANIFEST_CONTRACT,
    ManifestSubset,
    ManifestRows,
    load_manifest,
    manifest_artifact_entry,
    manifest_dataset_indices,
    matcher_cause_record,
    selected_axes,
)


def manifest_row(index):
    return {
        "manifest_index": index,
        "stratum": "ambiguous" if index < 128 else "class_unique",
        "scene_id": "scene%04d_00" % index,
        "ann_id": index,
        "target_object_id": str(index),
        "target_class": "chair",
        "same_class_peer_object_ids": ["900"] if index < 128 else [],
        "description_sha256": "%064x" % index,
    }


def manifest_document():
    return {
        "schema_version": 1,
        "contract": MANIFEST_CONTRACT,
        "rows": [manifest_row(index) for index in range(256)],
    }


class ManifestCaptureTest(unittest.TestCase):
    def test_matcher_pair_order_is_native_and_checked(self):
        args = (
            [[0, 0, 0], [2, 0, 0], [4, 0, 0]],
            [[0, 0, 0], [4, 0, 0]],
            [2, 2, 1],
            [2, 1],
        )
        result = ([0, 2], [[1], []], ([0, 2, 1], [0, 1, 0]), [2, 1])
        row, _ = matcher_cause_record(*args, result, [True, True, True])
        self.assertEqual(row["matched_query_gt_pairs"], [[0, 0], [2, 1], [1, 0]])
        reordered = ([0, 2], [[1], []], ([0, 1, 2], [0, 0, 1]), [2, 1])
        with self.assertRaisesRegex(ValueError, "pair order"):
            matcher_cause_record(*args, reordered, [True, True, True])

    def test_load_requires_exact_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            payload = json.dumps(manifest_document(), sort_keys=True).encode(
                "ascii"
            )
            path.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest()
            loaded = load_manifest(path, expected)
            self.assertEqual(loaded.sha256, expected)
            with self.assertRaisesRegex(ValueError, "hash differs"):
                load_manifest(path, "0" * 64)

    def test_reject_outcome_fields_and_duplicate_rows(self):
        document = manifest_document()
        document["rows"][0]["scores"] = [1.0]
        with self.assertRaisesRegex(ValueError, "outcome"):
            ManifestRows(document, "a" * 64)

        document = manifest_document()
        document["rows"][1] = dict(document["rows"][0])
        document["rows"][1]["manifest_index"] = 1
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            ManifestRows(document, "a" * 64)

    def test_selects_only_manifest_axes(self):
        manifest = ManifestRows(manifest_document(), "a" * 64)
        axes = [
            {"scene": "scene0000_00", "ann_id": 0},
            {"scene": "not-selected", "ann_id": 999},
            {"scene": "scene0200_00", "ann_id": 200},
        ]
        selected = selected_axes(axes, manifest)
        self.assertEqual([index for index, _ in selected], [0, 2])
        self.assertEqual(
            [row["manifest_index"] for _, row in selected], [0, 200]
        )

    def test_require_complete_rejects_missing_and_unexpected(self):
        manifest = ManifestRows(manifest_document(), "a" * 64)
        found = {
            (row["scene_id"], row["ann_id"])
            for row in manifest_document()["rows"][:-1]
        }
        with self.assertRaisesRegex(ValueError, "missing 1"):
            manifest.require_complete(found)
        found.add(("scene0255_00", 255))
        found.add(("scene0999_00", 999))
        with self.assertRaisesRegex(ValueError, "unexpected"):
            manifest.require_complete(found)

    def test_native_axis_key_types_are_normalized(self):
        manifest = ManifestRows(manifest_document(), "a" * 64)
        self.assertIsNotNone(manifest.get("scene0001_00", "1"))
        self.assertIsNone(manifest.get("scene0001_00", 2))

    def test_manifest_subset_maps_exact_native_indices(self):
        manifest = SimpleNamespace(
            rows={
                ("scene0000_00", 0): manifest_row(0),
                ("scene0001_00", 1): manifest_row(1),
            }
        )

        class Dataset:
            scene_inputs = [
                [{"scene_id": "scene0001_00", "ann_id": "1"}],
                [{"scene_id": "other", "ann_id": "0"}],
                [{"scene_id": "scene0000_00", "ann_id": "0"}],
            ]

        indices = manifest_dataset_indices(Dataset(), manifest)
        self.assertEqual(indices, [0, 2])

    def test_manifest_subset_rejects_missing_expression(self):
        manifest = SimpleNamespace(
            rows={
                ("scene0000_00", 0): manifest_row(0),
                ("scene0001_00", 1): manifest_row(1),
            }
        )

        class Dataset:
            scene_inputs = [[{"scene_id": "scene0000_00", "ann_id": "0"}]]

        with self.assertRaisesRegex(ValueError, "absent"):
            manifest_dataset_indices(Dataset(), manifest)

    def test_manifest_subset_delegates_native_access(self):
        class Dataset:
            def __len__(self):
                return 3

            def __getitem__(self, index):
                return index

            def collate_fn(self, items):
                return items

        subset = ManifestSubset(Dataset(), [2, 0])
        self.assertEqual(len(subset), 2)
        self.assertEqual(subset[1], 0)
        self.assertEqual(subset.collate_fn([1, 2]), [1, 2])

    def test_artifact_binds_query_evidence_to_support(self):
        axis = {
            "original_superpoint_ids": [1, 2],
            "sample_inverse": [0, 1],
            "semantic_labels": [3, 4],
        }
        entry = manifest_artifact_entry(
            axis,
            {"manifest_index": 7},
            {"final": "features"},
            [[0.1, 0.2]],
            [[True, False]],
            [0.8],
            [True],
            [False],
            [10, 11],
            [True, False],
            "a" * 64,
        )
        self.assertEqual(entry["manifest_index"], 7)
        self.assertEqual(entry["physical_instance_labels"], [10, 11])
        self.assertEqual(entry["query_scores"], [0.8])
        self.assertEqual(
            entry["artifact_contract"], "m95_manifest_native_query_artifact_v1"
        )


if __name__ == "__main__":
    unittest.main()
