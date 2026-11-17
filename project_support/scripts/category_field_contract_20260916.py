"""Check information retained by category-union spatial fields, without ML."""
import hashlib
import json
import math
from pathlib import Path


def distance_field(queries, points):
    return [min((math.dist(q, p) for p in points), default=None) for q in queries]


def joint_instance_witness(groups, predicate_a, predicate_b):
    return any(any(predicate_a(p) for p in group)
               and any(predicate_b(p) for p in group) for group in groups)


def run():
    target = (0., 0., 0.)
    points = [(-1., 0., 1.), (1., 0., -1.)]
    queries = [(x, 0., z) for x in (-2., 0., 2.) for z in (-2., 0., 2.)]
    above = lambda p: p[2] > target[2]
    right = lambda p: p[0] > target[0]
    one_instance, two_instances = [points], [[p] for p in points]
    union_a = [p for group in one_instance for p in group]
    union_b = [p for group in two_instances for p in group]
    assert union_a == union_b
    assert distance_field(queries, union_a) == distance_field(queries, union_b)
    field_conjunction = any(map(above, points)) and any(map(right, points))
    truth_a = joint_instance_witness(one_instance, above, right)
    truth_b = joint_instance_witness(two_instances, above, right)
    assert field_conjunction and truth_a and not truth_b

    # A target mask identifies its own support, not partitions of other objects.
    remaining_a = [p for p in union_a if p != target]
    remaining_b = [p for p in union_b if p != target]
    assert remaining_a == remaining_b
    assert distance_field(queries, remaining_a) == distance_field(queries, remaining_b)

    # Nearest distances are min-plus fields: confidence shifts effective distance.
    def soft_distance(q, positions, probabilities):
        return min(math.dist(q, p) - math.log(s)
                   for p, s in zip(positions, probabilities) if s > 0)

    near, far = (1., 0., 0.), (2., 0., 0.)
    assert soft_distance(target, [near], [.1]) > soft_distance(target, [far], [1.])
    assert distance_field([target], [near, near]) == distance_field([target], [near])
    assert distance_field([target], []) == [None]
    return {
        "scope": "Synthetic information-contract tests; no native failure-rate claim.",
        "checks": {
            "same_category_support": True,
            "same_distance_field_at_nine_queries": True,
            "different_instance_conjunction_truth": True,
            "target_exclusion_does_not_restore_other_instance_partition": True,
            "min_distance_duplicate_invariant": True,
            "empty_category_explicit": True,
            "soft_distance_confidence_distance_tradeoff": True,
        },
        "counterexample": {
            "support": points, "queries": queries,
            "field": distance_field(queries, points),
            "category_union_conjunction": field_conjunction,
            "one_instance_truth": truth_a, "two_instance_truth": truth_b,
            "semantics": "One object has support above and right of the target. "
                         "This explicit support-based predicate is not claimed to "
                         "be a universal natural-language spatial relation.",
        },
        "disposition": "Do not admit a category-union distance-field-only mechanism "
                       "as a solution to instance binding. This does not reject "
                       "fields as features or mechanisms retaining instance evidence.",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    result = run()
    output = Path(__file__).resolve().parents[1] / (
        "pipeline/reports/category_field_contract_20260916.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
