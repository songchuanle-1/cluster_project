import unittest

from referent_outcome_independent_registry_20260918 import (
    build_registry_rows,
    stable_sha256,
    summarize_registry,
    validate_registry_rows,
)


def fixture_rows():
    sample = [
        {"step": 0, "scene": "scene0001_00", "expression_slot": 0, "ann_id": "1"},
        {"step": 0, "scene": "scene0001_00", "expression_slot": 1, "ann_id": "2"},
        {"step": 1, "scene": "scene0002_00", "expression_slot": 0, "ann_id": "3"},
    ]
    by_ann = {
        ("scene0001_00", "1"): {
            "scene_id": "scene0001_00",
            "ann_id": "1",
            "object_id": "0",
            "object_name": "chair",
            "description": "left chair",
        },
        ("scene0001_00", "2"): {
            "scene_id": "scene0001_00",
            "ann_id": "2",
            "object_id": "2",
            "object_name": "chair",
            "description": "right chair",
        },
        ("scene0002_00", "3"): {
            "scene_id": "scene0002_00",
            "ann_id": "3",
            "object_id": "0",
            "object_name": "table",
            "description": "table",
        },
    }
    by_scene = {
        "scene0001_00": [
            by_ann[("scene0001_00", "1")],
            by_ann[("scene0001_00", "2")],
            {"object_id": "1", "object_name": "chair"},
        ],
        "scene0002_00": [by_ann[("scene0002_00", "3")]],
    }
    return sample, by_ann, by_scene, {}


class OutcomeIndependentRegistryTest(unittest.TestCase):
    def test_rows_are_outcome_blind_and_complete(self):
        sample, by_ann, by_scene, graphs = fixture_rows()
        rows = build_registry_rows(
            sample,
            by_ann,
            by_scene,
            graphs,
            expected_expressions=3,
        )
        self.assertEqual(rows[0]["same_class_candidate_ids"], ["1", "2"])
        self.assertEqual(rows[2]["same_class_candidate_ids"], [])
        self.assertTrue(rows[0]["primary_rank_eligible"])
        self.assertFalse(rows[2]["primary_rank_eligible"])
        self.assertNotIn("target_rank", rows[0])

    def test_scene_weights_are_normalized(self):
        sample, by_ann, by_scene, graphs = fixture_rows()
        rows = build_registry_rows(
            sample,
            by_ann,
            by_scene,
            graphs,
            expected_expressions=3,
        )
        self.assertAlmostEqual(
            sum(row["scene_weight"] for row in rows),
            2.0,
        )
        self.assertEqual(rows[0]["scene_weight"], 0.5)

    def test_duplicate_key_is_rejected(self):
        sample, by_ann, by_scene, graphs = fixture_rows()
        rows = build_registry_rows(
            sample,
            by_ann,
            by_scene,
            graphs,
            expected_expressions=3,
        )
        rows.append(dict(rows[0]))
        with self.assertRaises(ValueError):
            validate_registry_rows(rows, expected_expressions=4)

    def test_outcome_field_is_rejected(self):
        sample, by_ann, by_scene, graphs = fixture_rows()
        rows = build_registry_rows(
            sample,
            by_ann,
            by_scene,
            graphs,
            expected_expressions=3,
        )
        rows[0]["native_rank"] = 1
        with self.assertRaises(ValueError):
            validate_registry_rows(rows, expected_expressions=3)

    def test_stable_hash_ignores_mapping_order(self):
        self.assertEqual(
            stable_sha256({"a": 1, "b": 2}),
            stable_sha256({"b": 2, "a": 1}),
        )

    def test_summary_keeps_ineligible_rows_in_cohort(self):
        sample, by_ann, by_scene, graphs = fixture_rows()
        rows = build_registry_rows(
            sample,
            by_ann,
            by_scene,
            graphs,
            expected_expressions=3,
        )
        summary = summarize_registry(rows)
        self.assertEqual(summary["expressions"], 3)
        self.assertEqual(summary["outcome_independent_expressions"], 3)
        self.assertEqual(summary["primary_rank_eligible_expressions"], 2)
        self.assertEqual(summary["no_same_class_candidate_expressions"], 1)


if __name__ == "__main__":
    unittest.main()
