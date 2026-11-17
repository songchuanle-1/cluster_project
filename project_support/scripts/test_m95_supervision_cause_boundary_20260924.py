import copy
import unittest

from m95_supervision_cause_boundary_20260924 import analyze, EXCLUSION, WITHIN


def fixture():
    rows = []
    for i in range(256):
        group = EXCLUSION if i < 6 else WITHIN if i < 13 else "deployed_success"
        rows.append({
            "manifest_index": i, "scene_id": str(i), "partition": group,
            "acceptable_queries": 2,
            "acceptable_native_positive_queries": 0 if i < 6 else 1,
            "native_positive_queries": 1,
            "target_seed_query": None if i < 5 else i,
            "common_support": i >= 5,
        })
    return (
        {"contract": "m95_failure_partition_descriptive_v1", "admission": False, "rows": rows},
        {"admission": False, "rows": [{
            "manifest_index": 0, "query_count": 2,
            "positive_outside_seed_count": 1,
            "seeds": [
                {"positive": True, "inside_target": False},
                {"positive": False, "inside_target": False},
            ],
        }]},
    )


class CauseBoundaryTests(unittest.TestCase):
    def test_denominators_and_unknown_cause(self):
        result = analyze(*fixture())
        exclusion = result["groups"][EXCLUSION]
        self.assertEqual(exclusion["expressions"], 6)
        self.assertEqual(exclusion["target_seed_selector_available"], 1)
        self.assertEqual(exclusion["rows_with_saved_outside_seed_positive"], 1)
        self.assertEqual(result["groups"][WITHIN]["expressions"], 7)
        self.assertFalse(exclusion["rows"][0]["matcher_cause_observed"])
        self.assertFalse(result["admission"])

    def test_rejects_duplicate_manifest(self):
        partition, discordance = fixture()
        partition["rows"][1]["manifest_index"] = 0
        with self.assertRaisesRegex(ValueError, "manifest"):
            analyze(partition, discordance)

    def test_rejects_label_contradiction(self):
        partition, discordance = fixture()
        partition["rows"][0]["acceptable_native_positive_queries"] = 1
        with self.assertRaisesRegex(ValueError, "Exclusion"):
            analyze(partition, discordance)

    def test_rejects_discordance_count_drift(self):
        partition, discordance = fixture()
        discordance = copy.deepcopy(discordance)
        discordance["rows"][0]["positive_outside_seed_count"] = 0
        with self.assertRaisesRegex(ValueError, "Outside-seed"):
            analyze(partition, discordance)

    def test_rejects_excess_positive(self):
        partition, discordance = fixture()
        partition["rows"][0]["native_positive_queries"] = 0
        with self.assertRaisesRegex(ValueError, "exceed"):
            analyze(partition, discordance)


if __name__ == "__main__":
    unittest.main()
