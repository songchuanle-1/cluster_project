import copy
import unittest

from m95_supervision_partition_controls_20260923 import audit


def fixture():
    rows = []
    for i in range(256):
        partition = "deployed_success"
        acceptable, positive = 2, 1
        if i < 6:
            partition, acceptable, positive = (
                "recoverable_positive_set_excludes_acceptable", 2, 0
            )
        elif i < 13:
            partition, acceptable, positive = (
                "recoverable_within_positive_score_failure", 2, 1
            )
        rows.append({
            "manifest_index": i, "scene_id": str(i), "partition": partition,
            "stratum": "ambiguous" if i < 128 else "class_unique",
            "acceptable_queries": acceptable,
            "acceptable_native_positive_queries": positive,
            "positive_set_equals_target_seed_set": i >= 6,
            "common_support": True,
        })
    return {
        "contract": "m95_failure_partition_descriptive_v1",
        "admission": False, "rows": rows,
    }


class PartitionControlsTests(unittest.TestCase):
    def test_control_denominators_and_limitations(self):
        result = audit(fixture())
        self.assertEqual(result["focus_expressions"], 13)
        self.assertEqual(result["focus_scenes"], 13)
        self.assertEqual(
            result["groups"]["recoverable_positive_set_excludes_acceptable"]
            ["acceptable_native_positives"], 0
        )
        self.assertFalse(result["admission"])
        self.assertFalse(result["native_backward_executed"])

    def test_rejects_duplicate_manifest(self):
        document = fixture()
        document["rows"][1]["manifest_index"] = 0
        with self.assertRaisesRegex(ValueError, "manifest"):
            audit(document)

    def test_rejects_invalid_query_count(self):
        document = fixture()
        document["rows"][0]["acceptable_native_positive_queries"] = 3
        with self.assertRaisesRegex(ValueError, "counts"):
            audit(document)

    def test_rejects_focus_drift(self):
        document = fixture()
        document["rows"][0]["acceptable_native_positive_queries"] = 1
        with self.assertRaisesRegex(ValueError, "drift"):
            audit(document)

    def test_rejects_missing_control(self):
        document = copy.deepcopy(fixture())
        document["rows"][0].pop("common_support")
        with self.assertRaises(KeyError):
            audit(document)


if __name__ == "__main__":
    unittest.main()
