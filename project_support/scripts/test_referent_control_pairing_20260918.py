import unittest

from referent_control_pairing_20260918 import summarize_pairs, validate_source


def row(scene, slot, ann_id, wrong_id, same_class=True, connected=False):
    return {
        "scene": scene,
        "step": 0,
        "expression_slot": slot,
        "ann_id": ann_id,
        "object_id": "1",
        "object_name": "chair",
        "wrong_object_id": wrong_id,
        "wrong_object_name": "chair" if same_class else "table",
        "wrong_is_same_class": same_class,
        "same_class_peer": True,
        "same_class_peer_ids": ["2", "3"],
        "same_target_repeated": True,
        "same_target_descriptions": 2,
        "target_has_relation_edge": True,
        "target_has_attribute": True,
        "target_has_relation_span": True,
        "connected_same_class_peer": connected,
    }


class ReferentControlPairingTest(unittest.TestCase):
    def test_scene_weights_balance_repeated_failures(self):
        summary = summarize_pairs([
            row("scene0001_00", 0, "10", "2"),
            row("scene0001_00", 1, "11", "3"),
            row("scene0002_00", 0, "12", "2"),
        ])
        self.assertEqual(summary["scenes"], 2)
        self.assertAlmostEqual(summary["pair_weight_total"], 2.0)
        self.assertAlmostEqual(summary["max_scene_weight"], 1.0)

    def test_cross_class_control_is_not_primary(self):
        summary = summarize_pairs([
            row("scene0001_00", 0, "10", "9", same_class=False),
        ])
        self.assertEqual(summary["same_class_primary_pairs"], 0)
        self.assertEqual(summary["cross_class_excluded_pairs"], 1)

    def test_connected_pair_is_counted_separately(self):
        summary = summarize_pairs([
            row("scene0001_00", 0, "10", "2", connected=True),
        ])
        self.assertEqual(summary["direct_connected_same_class_peer_pairs"], 1)
        self.assertEqual(summary["direct_connected_primary_pairs"], 1)

    def test_validation_rejects_same_class_control_outside_pool(self):
        bad = {
            "observed_failure_coverage": {
                "rows": [row("scene0001_00", 0, "10", "99")],
            },
        }
        with self.assertRaises(ValueError):
            validate_source(bad)


if __name__ == "__main__":
    unittest.main()
