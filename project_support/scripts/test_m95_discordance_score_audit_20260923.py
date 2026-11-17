import copy
import unittest

from m95_discordance_score_audit_20260923 import audit


class ScoreAuditTests(unittest.TestCase):
    def fixture(self):
        rows = []
        for i in range(32):
            rows.append({
                "manifest_index": i, "mask_sha256": str(i),
                "scene_id": str(i % 24), "acceptable": i < 23,
                "seed_membership_equals_label": i < 26,
                "positive_outside_seed_count": int(i >= 26),
                "identity": "target_dominant",
                "mean_positive_minus_negative_score": -0.1 if i in (2, 26, 31) else 0.2,
            })
        return rows

    def test_strata_and_direction(self):
        result = audit(self.fixture())
        self.assertEqual(result["all"]["positive_lower"], 3)
        self.assertEqual(result["acceptable"]["positive_lower"], 1)
        self.assertEqual(result["seed_label_aligned"]["classes"], 26)
        self.assertEqual(result["positive_outside_seed"]["classes"], 6)

    def test_duplicate_or_changed_cohort_rejected(self):
        rows = self.fixture()
        rows[1] = copy.deepcopy(rows[0])
        with self.assertRaises(ValueError):
            audit(rows)
        rows = self.fixture()
        rows[8]["scene_id"] = rows[1]["scene_id"]
        with self.assertRaises(ValueError):
            audit(rows)

    def test_nonpartitioned_seed_strata_rejected(self):
        rows = self.fixture()
        rows[0]["positive_outside_seed_count"] = 1
        with self.assertRaises(ValueError):
            audit(rows)


if __name__ == "__main__":
    unittest.main()
