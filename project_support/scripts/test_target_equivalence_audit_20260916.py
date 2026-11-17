import unittest
from target_equivalence_audit_20260916 import audit


def row(scene, ann, target, winner, iou):
    return dict(scene=scene, ann_id=ann, target_ids=[target], winner_id=winner,
                winner_overlap=.9, before=iou, utterance=f"description {ann}")


class AuditTests(unittest.TestCase):
    def test_does_not_join_cross_scene(self):
        result = audit([row("a", 1, 2, 2, .9), row("b", 2, 2, 2, .9)])
        self.assertEqual(result["summary"]["pairs"], 0)

    def test_does_not_join_different_targets(self):
        result = audit([row("a", 1, 2, 2, .9), row("a", 2, 3, 2, 0)])
        self.assertEqual(result["summary"]["pairs"], 0)

    def test_strict_threshold_and_identity_are_distinct(self):
        result = audit([row("a", 1, 2, 2, .5), row("a", 2, 2, 2, .7)])
        self.assertTrue(result["pairs"][0]["same_winner"])
        self.assertTrue(result["pairs"][0]["success_disagreement"])

    def test_unknown_identity_is_not_agreement(self):
        result = audit([row("a", 1, 2, None, 0), row("a", 2, 2, None, 0)])
        self.assertIsNone(result["pairs"][0]["same_winner"])
        self.assertEqual(result["summary"]["observable_pairs"], 0)

    def test_permutation(self):
        rows = [row("a", 1, 2, 2, .7), row("a", 2, 2, 3, 0)]
        self.assertEqual(audit(rows), audit(rows[::-1]))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            audit([row("a", 1, 2, 2, .7)] * 2)


if __name__ == "__main__":
    unittest.main()
