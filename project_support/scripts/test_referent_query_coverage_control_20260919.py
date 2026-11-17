import copy
import unittest

from referent_query_coverage_control_20260919 import (
    audit_capture,
    validate_query_assignment,
)
from test_referent_target_rank_evaluator_20260919 import (
    capture_fixture,
    registry_fixture,
)


def add_query_assignment(capture):
    for row_index, row in enumerate(capture["rows"]):
        object_ids = list(row["scores"]["referent"])
        assignment = {}
        query_costs = {}
        support_size = {}
        instance_labels = []
        seed_indices = []
        global_costs = {"referent": [], "objectness": []}
        cursor = 0
        for object_index, object_id in enumerate(object_ids):
            count = (object_index + row_index) % 2 + 1
            support_count = (object_index + row_index) % 2 + 2
            support_start = len(instance_labels)
            instance_labels.extend([int(object_id)] * support_count)
            seed_indices.extend(
                support_start + offset for offset in range(count)
            )
            indices = list(range(cursor, cursor + count))
            cursor += count
            selected_referent = indices[0]
            selected_objectness = indices[-1]
            assignment[object_id] = {
                "query_indices": indices,
                "referent_selected_query": selected_referent,
                "objectness_selected_query": selected_objectness,
            }
            query_costs[object_id] = {}
            for score_name, selected_query in (
                ("referent", selected_referent),
                ("objectness", selected_objectness),
            ):
                selected_cost = float(row["scores"][score_name][object_id])
                values = [
                    selected_cost
                    if query_index == selected_query
                    else selected_cost + (query_index + 1) * 0.01
                    for query_index in indices
                ]
                query_costs[object_id][score_name] = values
                global_costs[score_name].extend(values)
            support_size[object_id] = support_count
        row["native_query_assignment"] = assignment
        row["native_query_costs"] = query_costs
        row["object_support_size"] = support_size
        row["native_query_axes"] = {
            "instance_labels": instance_labels,
            "seed_indices": seed_indices,
            "costs": global_costs,
        }
    return capture


class ReferentQueryCoverageControlTest(unittest.TestCase):
    def test_complete_query_assignment_is_accepted(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        summary = audit_capture(registry, capture)
        self.assertEqual(summary["coverage_summary"]["complete_expressions"], 3)
        self.assertEqual(summary["coverage_summary"]["rejected_expressions"], 0)
        self.assertEqual(
            summary["selection_verification"]["verified_expressions"],
            3,
        )

    def test_assignment_object_set_mismatch_is_rejected(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        capture["rows"][0]["native_query_assignment"]["9"] = {
            "query_indices": [99],
            "referent_selected_query": 99,
            "objectness_selected_query": 99,
        }
        summary = audit_capture(registry, capture)
        self.assertEqual(summary["coverage_summary"]["complete_expressions"], 2)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query assignment differs from object set",
        )

    def test_selected_query_outside_object_pool_is_rejected(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        capture["rows"][0]["native_query_assignment"]["0"][
            "referent_selected_query"
        ] = 999
        summary = audit_capture(registry, capture)
        self.assertEqual(summary["coverage_summary"]["complete_expressions"], 2)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Selected query is outside its object pool",
        )

    def test_overlapping_query_pools_are_rejected(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        row = capture["rows"][1]["native_query_assignment"]
        row["2"]["query_indices"] = [0, 1]
        row["2"]["referent_selected_query"] = 0
        row["2"]["objectness_selected_query"] = 1
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query indices overlap across objects",
        )

    def test_exact_match_subset_keeps_only_equal_coverage_candidates(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        summary = audit_capture(registry, capture)
        rows = {row["registry_key"]: row for row in summary["rows"]}
        matched = rows["sceneA:1:2"]["coverage"]["matched_object_ids"]
        self.assertEqual(matched, ["2", "4"])

    def test_missing_assignment_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        del capture["rows"][0]["native_query_assignment"]
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query assignment differs from object set",
        )

    def test_dual_balance_subset_requires_coverage_and_support_match(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        summary = audit_capture(registry, capture)
        rows = {row["registry_key"]: row for row in summary["rows"]}
        matched = rows["sceneA:1:2"]["coverage"]["dual_matched_object_ids"]
        self.assertEqual(matched, ["2", "4"])
        self.assertEqual(
            summary["dual_balanced_summary"]["expressions"],
            1,
        )

    def test_missing_object_support_size_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        del capture["rows"][0]["object_support_size"]
        summary = audit_capture(registry, capture)
        self.assertEqual(summary["coverage_summary"]["complete_expressions"], 2)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native object support size differs from object set",
        )

    def test_invalid_object_support_size_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        capture["rows"][0]["object_support_size"]["0"] = 0
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native object support size is invalid",
        )

    def test_missing_native_query_costs_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        del capture["rows"][0]["native_query_costs"]
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query costs differ from object set",
        )

    def test_missing_native_query_axes_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        del capture["rows"][0]["native_query_axes"]
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query axes are missing",
        )

    def test_global_seed_assignment_mismatch_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        axes = capture["rows"][0]["native_query_axes"]
        axes["seed_indices"][0] = axes["seed_indices"][1]
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query pools differ from global seed-instance membership",
        )

    def test_global_cost_projection_mismatch_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        axes = capture["rows"][0]["native_query_axes"]
        axes["costs"]["referent"][0] += 0.01
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query cost vector differs from global query axes",
        )

    def test_global_seed_out_of_range_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        axes = capture["rows"][0]["native_query_axes"]
        axes["seed_indices"][0] = len(axes["instance_labels"])
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Native query seed index is invalid",
        )

    def test_selected_cost_mismatch_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        capture["rows"][0]["native_query_costs"]["0"]["referent"][0] += 0.01
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Selected query cost differs from native score",
        )

    def test_nonminimum_selected_query_rejects_expression(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        costs = capture["rows"][1]["native_query_costs"]["0"]["referent"]
        costs[1] = costs[0] - 0.01
        summary = audit_capture(registry, capture)
        self.assertEqual(
            summary["rejected"][0]["reason"],
            "Selected query is not the minimum native cost",
        )

    def test_query_assignment_validator_does_not_mutate_input(self):
        registry = registry_fixture()
        capture = add_query_assignment(capture_fixture(registry))
        original = copy.deepcopy(capture["rows"][0]["native_query_assignment"])
        validate_query_assignment(capture["rows"][0], registry["rows"][0])
        self.assertEqual(
            capture["rows"][0]["native_query_assignment"],
            original,
        )


if __name__ == "__main__":
    unittest.main()
