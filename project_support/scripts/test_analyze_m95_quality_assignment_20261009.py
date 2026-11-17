import copy
import unittest

from analyze_m95_quality_assignment_20261009 import summarize


def fixture():
    records = []
    for repeat in range(2):
        for ann_id in range(31):
            records.append({
                "repeat": repeat, "frozen": True, "scene": str(ann_id % 2),
                "ann_id": ann_id, "queries": 128, "matched": 2,
                "supervised": 1, "censored": 1, "qids": [0, 1],
                "quality": [0.25, 0.75], "scores": [0.4, 0.8],
                "selected_query": 0, "selected_is_matched": True,
                "selected_iou": 0.25, "all_layer_assignments_identical": True,
                "score_gradient_nonzero_queries": 1, "score_gradient_finite": True,
                "input_sha256": str(ann_id),
            })
    return {
        "contract": "m95_quality_assignment_capture_v1",
        "records": records, "elapsed_seconds": 1, "peak_allocated_mib": 1,
        "batches": [{"repeat": repeat, "layer_count": 7,
                     "assignments": ["a"] * 7, "rotated_control_differs": True,
                     "layers": [{"matched": 62, "censored": 31}] * 7}
                    for repeat in range(2)],
    }


class AnalysisTests(unittest.TestCase):
    def test_counts_and_matching(self):
        result = summarize(fixture())
        self.assertEqual(result["frozen"]["censored_query_targets"], 31)
        self.assertEqual(result["frozen"]["selected_is_censored"], 31)
        self.assertTrue(result["native_layer_assignment_agreement"])
        self.assertEqual(result["repeat"]["status"], "PASS")

    def test_numeric_failure_is_not_relaxed(self):
        data = fixture()
        data["records"][31]["scores"][0] += 2e-6
        self.assertEqual(summarize(data)["repeat"]["status"], "FAIL")

    def test_discrete_difference_fails_repeat(self):
        data = fixture()
        data["records"][31]["input_sha256"] = "changed"
        self.assertEqual(summarize(data)["repeat"]["status"], "FAIL")

    def test_duplicate_expression_rejected(self):
        data = fixture()
        data["records"][1] = copy.deepcopy(data["records"][0])
        with self.assertRaises(ValueError):
            summarize(data)

    def test_missing_stage_rejected(self):
        data = fixture()
        data["batches"][0]["layer_count"] = 6
        with self.assertRaises(ValueError):
            summarize(data)


if __name__ == "__main__":
    unittest.main()
