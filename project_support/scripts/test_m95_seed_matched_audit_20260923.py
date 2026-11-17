import copy
import unittest

from m95_seed_matched_audit_20260923 import audit


class SeedMatchedAuditTests(unittest.TestCase):
    def fixture(self):
        rows = []
        for i in range(32):
            rows.append({
                "manifest_index": i, "mask_sha256": str(i), "scene_id": str(i % 24),
                "acceptable": i < 23, "identity": "target_dominant",
                "dominant_physical_id": 1, "query_count": 2, "positive_count": 1,
                "seeds": [
                    {"query": 0, "positive": True, "seed_physical_id": 1,
                     "physical_seed_index": 7, "score": 0.8, "inside_target": True},
                    {"query": 1, "positive": False, "seed_physical_id": 2,
                     "physical_seed_index": 8, "score": 0.1, "inside_target": False},
                ],
            })
        return rows

    def test_matched_instance_but_not_same_seed(self):
        rows = self.fixture()
        rows[0]["seeds"][1]["seed_physical_id"] = 1
        result = audit(rows)
        self.assertEqual(result["matched_classes"], 1)
        self.assertEqual(result["positive_higher_groups"], 1)
        self.assertEqual(result["exact_seed_index_pairs"], 0)
        self.assertAlmostEqual(result["rows"][0]["positive_minus_negative_mean_score"], 0.7)

    def test_same_exact_seed_index_is_counted(self):
        rows = self.fixture()
        rows[0]["seeds"][1]["seed_physical_id"] = 1
        rows[0]["seeds"][1]["physical_seed_index"] = 7
        self.assertEqual(audit(rows)["exact_seed_index_pairs"], 1)

    def test_binding_and_cohort_guards(self):
        rows = self.fixture()
        rows[0]["positive_count"] = 0
        with self.assertRaises(ValueError):
            audit(rows)
        rows = self.fixture()
        rows[1] = copy.deepcopy(rows[0])
        with self.assertRaises(ValueError):
            audit(rows)


if __name__ == "__main__":
    unittest.main()
