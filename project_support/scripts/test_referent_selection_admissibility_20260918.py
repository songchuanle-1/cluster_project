import unittest

from referent_selection_admissibility_20260918 import (
    classify_pairing,
    compare_rate,
    fisher_exact_two_sided,
    wilson_interval,
)


def coverage_row(index):
    return {
        "scene": "scene%04d_00" % index,
        "expression_slot": 0,
        "ann_id": str(index),
    }


def coverage_fixture():
    rows = [coverage_row(index) for index in range(33)]
    return {
        "sample": {"expressions": 123},
        "observed_failure_coverage": {
            "summary": {
                "expressions": 33,
                "same_class_peer": {"count": 33, "rate": 1.0},
                "graph_same_class_peer": {"count": 4, "rate": 4 / 33},
                "target_has_relation_edge": {"count": 30, "rate": 30 / 33},
                "connected_same_class_peer": {"count": 2, "rate": 2 / 33},
                "target_has_attribute": {"count": 23, "rate": 23 / 33},
                "target_has_relation_span": {"count": 30, "rate": 30 / 33},
                "same_target_repeated": {"count": 32, "rate": 32 / 33},
            },
            "rows": rows,
        },
        "train_metadata_coverage": {
            "expressions": 100,
            "same_class_peer": {"count": 60, "rate": 0.6},
            "graph_same_class_peer": {"count": 10, "rate": 0.1},
            "target_has_relation_edge": {"count": 80, "rate": 0.8},
            "connected_same_class_peer": {"count": 8, "rate": 0.08},
            "target_has_attribute": {"count": 70, "rate": 0.7},
            "target_has_relation_span": {"count": 70, "rate": 0.7},
            "same_target_repeated": {"count": 99, "rate": 0.99},
        },
    }


def pairing_fixture():
    rows = []
    for index in range(33):
        primary = index < 31
        rows.append({
            "scene": "scene%04d_00" % index,
            "expression_slot": 0,
            "ann_id": str(index),
            "primary_same_class_pair_eligible": primary,
            "same_class_control_pool": ["2", "3"],
        })
    return {
        "summary": {"same_class_primary_pairs": 31},
        "pairs": rows,
    }


class SelectionAdmissibilityTest(unittest.TestCase):
    def test_wilson_interval_contains_rate(self):
        low, high = wilson_interval(33, 33)
        self.assertLessEqual(low, 1.0)
        self.assertEqual(high, 1.0)
        self.assertGreater(low, 0.8)

    def test_fisher_table_is_symmetric(self):
        self.assertAlmostEqual(
            fisher_exact_two_sided(3, 1, 2, 4),
            fisher_exact_two_sided(2, 4, 3, 1),
        )

    def test_risk_ratio_detects_enrichment(self):
        result = compare_rate(30, 33, 60, 100)
        self.assertGreater(result["risk_ratio"], 1.0)
        self.assertLess(result["fisher_two_sided_p"], 0.01)

    def test_failure_selected_registry_is_diagnostic_only(self):
        gate = classify_pairing(coverage_fixture(), pairing_fixture())
        self.assertEqual(gate["primary_pairs"], 31)
        self.assertEqual(gate["outcome_independent_expressions"], 0)
        self.assertTrue(gate["failure_local_diagnostic_admissible"])
        self.assertFalse(gate["population_effect_admissible"])

    def test_non_failure_pair_is_rejected(self):
        pairing = pairing_fixture()
        pairing["pairs"][0]["ann_id"] = "999"
        with self.assertRaises(ValueError):
            classify_pairing(coverage_fixture(), pairing)


if __name__ == "__main__":
    unittest.main()
