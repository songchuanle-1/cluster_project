import copy
import unittest

from instance_collision_audit_20260916 import audit


def row(ann, target, winner, overlap=0.8, scene="s"):
    return dict(scene=scene, ann_id=ann, target_ids=[target], winner_id=winner,
                winner_overlap=overlap, before=0.8 if target == winner else 0.0,
                winner_same_name=True, utterance="a chair")


class AuditTests(unittest.TestCase):
    def test_wrong_and_success_control(self):
        result = audit({"rows": [row(1, 1, 2), row(2, 2, 2)]})
        self.assertEqual(result["summary"]["collision_groups"], 1)
        self.assertEqual(result["summary"]["wrong_with_successful_winner_control"], 1)

    def test_repeated_target_is_not_collision(self):
        self.assertEqual(audit({"rows": [row(1, 2, 2), row(2, 2, 2)]})
                         ["summary"]["collision_groups"], 0)

    def test_scene_identity_isolation(self):
        self.assertEqual(audit({"rows": [row(1, 1, 2), row(2, 2, 2, scene="t")]})
                         ["summary"]["collision_groups"], 0)

    def test_overlap_boundary_excluded(self):
        result = audit({"rows": [row(1, 1, 2, overlap=0.5), row(2, 2, 2)]})
        self.assertEqual(result["summary"]["confident_wrong"], 0)
        self.assertEqual(result["summary"]["collision_groups"], 0)

    def test_duplicate_rejected(self):
        r = row(1, 1, 2)
        with self.assertRaises(ValueError):
            audit({"rows": [r, copy.deepcopy(r)]})

    def test_two_wrong_targets_without_control(self):
        result = audit({"rows": [row(1, 1, 3), row(2, 2, 3)]})
        self.assertEqual(result["summary"]["wrong_in_captured_collision"], 2)
        self.assertEqual(result["summary"]["wrong_with_successful_winner_control"], 0)

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            audit({"rows": []})

    def test_missing_identity_not_confident(self):
        result = audit({"rows": [row(1, 1, None)]})
        self.assertEqual(result["summary"]["confident_wrong"], 0)


if __name__ == "__main__":
    unittest.main()
