import hashlib
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from m95_preregistered_identity_controls_20260922 import (
    EXPECTED_SOURCE_SHA256,
    build_manifest,
    normalize_class,
    select_stratum,
    stable_key,
    validate_manifest,
)


def record(scene, ann_id, object_id, class_name, peers):
    return {
        "scene_id": scene,
        "ann_id": ann_id,
        "target_object_id": object_id,
        "target_class": class_name,
        "same_class_peer_object_ids": peers,
        "same_class_peer_count": len(peers),
        "scene_object_count": 3 + len(peers),
        "description_sha256": hashlib.sha256(
            ("%s|%s" % (scene, ann_id)).encode("ascii")
        ).hexdigest(),
        "description_tokens": 5,
        "stratum": "ambiguous" if peers else "class_unique",
    }


class ManifestContractTest(unittest.TestCase):
    def test_normalize_class(self):
        self.assertEqual(normalize_class(" Office_Chair "), "officechair")
        self.assertEqual(normalize_class("trash-can"), "trashcan")

    def test_selection_is_stable_and_scene_class_capped(self):
        rows = [
            record("scene0002_00", 1, "1", "chair", ["2"]),
            record("scene0001_00", 1, "1", "chair", ["2"]),
            record("scene0001_00", 2, "2", "chair", ["1"]),
            record("scene0003_00", 1, "3", "table", ["4"]),
        ]
        first = select_stratum(rows, 3)
        second = select_stratum(list(reversed(rows)), 3)
        self.assertEqual(
            [(row["scene_id"], row["ann_id"]) for row in first],
            [(row["scene_id"], row["ann_id"]) for row in second],
        )
        self.assertEqual(len({row["scene_id"] for row in first}), 3)
        self.assertLessEqual(sum(row["target_class"] == "chair" for row in first), 2)

    def test_manifest_excludes_model_outcomes(self):
        rows = []
        for index in range(4):
            rows.append(
                record(
                    "scene%04d_00" % index,
                    index,
                    str(index),
                    "chair",
                    [str(index + 100)],
                )
            )
            rows.append(
                record(
                    "scene%04d_00" % (index + 10),
                    index,
                    str(index + 10),
                    "table",
                    [],
                )
            )
        document = build_manifest(
            rows,
            EXPECTED_SOURCE_SHA256,
            "2026-09-22T13:20:00+08:00",
            per_stratum=2,
        )
        original_limit = 2
        document["contract"] = document["contract"]
        # The production validator enforces 128 rows, so validate the local
        # shape and outcome-free property without changing the global contract.
        for row in document["rows"]:
            self.assertFalse(
                {"score", "scores", "iou", "ious", "selected_query", "success"}
                & set(row)
            )
        self.assertEqual(len(document["rows"]), 2 * original_limit)

    def test_stable_key_order(self):
        first = stable_key("scene0001_00", 2)
        second = stable_key("scene0001_00", 2)
        self.assertEqual(first, second)
        self.assertNotEqual(first, stable_key("scene0001_00", 3))

    def test_validator_rejects_outcome_leak(self):
        rows = []
        for index in range(256):
            stratum = "ambiguous" if index < 128 else "class_unique"
            rows.append(
                {
                    "manifest_index": index,
                    "stratum": stratum,
                    "scene_id": "scene%04d_00" % index,
                    "ann_id": index,
                }
            )
        document = {"contract": "m95_preregistered_identity_controls_v1", "rows": rows}
        self.assertTrue(validate_manifest(document))
        document["rows"][0]["scores"] = [1.0]
        with self.assertRaises(ValueError):
            validate_manifest(document)


if __name__ == "__main__":
    unittest.main()
