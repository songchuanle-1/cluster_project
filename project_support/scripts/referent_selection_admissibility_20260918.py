"""Audit whether the failure-control registry can support a primary effect claim.

This is a CPU-only metadata audit. It makes no model or efficacy claim.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


FEATURE_KEYS = (
    "same_class_peer",
    "graph_same_class_peer",
    "target_has_relation_edge",
    "connected_same_class_peer",
    "target_has_attribute",
    "target_has_relation_span",
    "same_target_repeated",
)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wilson_interval(successes, total, z=1.959963984540054):
    if total < 1 or not 0 <= successes <= total:
        raise ValueError("Invalid binomial counts")
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    radius = (
        z
        * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
        / denominator
    )
    return [max(0.0, center - radius), min(1.0, center + radius)]


def log_choose(n, k):
    if not 0 <= k <= n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact_two_sided(a, b, c, d):
    if min(a, b, c, d) < 0:
        raise ValueError("Negative contingency count")
    row_one = a + b
    column_one = a + c
    total = a + b + c + d
    if total < 1:
        raise ValueError("Empty contingency table")
    lower = max(0, column_one - (total - row_one))
    upper = min(row_one, column_one)

    def log_probability(value):
        return (
            log_choose(column_one, value)
            + log_choose(total - column_one, row_one - value)
            - log_choose(total, row_one)
        )

    observed = log_probability(a)
    logs = [log_probability(value) for value in range(lower, upper + 1)]
    cutoff = observed + 1e-12
    return min(1.0, sum(math.exp(value) for value in logs if value <= cutoff))


def compare_rate(failure_count, failure_total, reference_count, reference_total):
    if min(failure_count, failure_total, reference_count, reference_total) < 0:
        raise ValueError("Negative rate count")
    if failure_count > failure_total or reference_count > reference_total:
        raise ValueError("Rate count exceeds denominator")
    failure_rate = failure_count / failure_total
    reference_rate = reference_count / reference_total
    risk_ratio = (
        failure_rate / reference_rate if reference_rate > 0 else None
    )
    return {
        "failure_count": failure_count,
        "failure_total": failure_total,
        "failure_rate": failure_rate,
        "failure_wilson_95": wilson_interval(failure_count, failure_total),
        "reference_count": reference_count,
        "reference_total": reference_total,
        "reference_rate": reference_rate,
        "reference_wilson_95": wilson_interval(
            reference_count, reference_total
        ),
        "risk_ratio": risk_ratio,
        "risk_difference": failure_rate - reference_rate,
        "fisher_two_sided_p": fisher_exact_two_sided(
            failure_count,
            failure_total - failure_count,
            reference_count,
            reference_total - reference_count,
        ),
    }


def feature_comparisons(coverage):
    failure = coverage["observed_failure_coverage"]["summary"]
    reference = coverage["train_metadata_coverage"]
    return {
        key: compare_rate(
            int(failure[key]["count"]),
            int(failure["expressions"]),
            int(reference[key]["count"]),
            int(reference["expressions"]),
        )
        for key in FEATURE_KEYS
    }


def validate_source_pair(coverage, pairing):
    if int(coverage["sample"]["expressions"]) != 123:
        raise ValueError("Expected the frozen 123-expression diagnostic sample")
    coverage_rows = coverage["observed_failure_coverage"]["rows"]
    pair_rows = pairing["pairs"]
    coverage_keys = {
        (str(row["scene"]), int(row["expression_slot"]), str(row["ann_id"]))
        for row in coverage_rows
    }
    pair_keys = {
        (str(row["scene"]), int(row["expression_slot"]), str(row["ann_id"]))
        for row in pair_rows
    }
    if len(coverage_keys) != 33:
        raise ValueError("Expected 33 observed failure keys")
    if not pair_keys.issubset(coverage_keys):
        raise ValueError("Pairing registry contains non-failure expressions")
    if int(pairing["summary"]["same_class_primary_pairs"]) != 31:
        raise ValueError("Expected 31 primary same-class pairs")
    return coverage_keys, pair_rows


def classify_pairing(coverage, pairing):
    coverage_keys, pair_rows = validate_source_pair(coverage, pairing)
    primary = [
        row for row in pair_rows if row["primary_same_class_pair_eligible"]
    ]
    scene_counts = Counter(str(row["scene"]) for row in primary)
    pool_sizes = [len(row["same_class_control_pool"]) for row in primary]
    pool_sizes.sort()
    median_pool = pool_sizes[(len(pool_sizes) - 1) // 2]
    failed_keys = {
        (
            str(row["scene"]),
            int(row["expression_slot"]),
            str(row["ann_id"]),
        )
        for row in primary
    }
    return {
        "sample_expressions": int(coverage["sample"]["expressions"]),
        "observed_failure_expressions": len(coverage_keys),
        "pair_rows": len(pair_rows),
        "primary_pairs": len(primary),
        "primary_pairs_matched_to_observed_failures": len(failed_keys),
        "outcome_independent_expressions": 0,
        "outcome_selected_wrong_controls": len(primary),
        "cohort_provenance": "observed model failures",
        "control_provenance": "observed wrong instance on the same failures",
        "failure_local_diagnostic_admissible": True,
        "population_effect_admissible": False,
        "reason": (
            "Every primary pair is selected from observed failures and its "
            "control is the instance chosen during failure. The contrast is "
            "conditional on the outcome and cannot identify a population "
            "referent-discrimination effect."
        ),
        "scenes": len(scene_counts),
        "scene_pair_distribution": dict(
            sorted(Counter(scene_counts.values()).items())
        ),
        "singleton_scene_count": sum(
            count == 1 for count in scene_counts.values()
        ),
        "same_class_pool_size": {
            "min": min(pool_sizes),
            "median": median_pool,
            "max": max(pool_sizes),
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--pairing", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    coverage_path = Path(args.coverage).resolve()
    pairing_path = Path(args.pairing).resolve()
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    pairing = json.loads(pairing_path.read_text(encoding="utf-8"))
    selection = classify_pairing(coverage, pairing)
    comparisons = feature_comparisons(coverage)
    report = {
        "scope": (
            "CPU-only outcome-selection audit of the frozen failure-control "
            "registry; no model forward, GPU execution, admission, or efficacy "
            "claim"
        ),
        "producer_sha256": file_sha256(__file__),
        "sources": {
            "coverage": {
                "path": coverage_path.relative_to(Path.cwd()).as_posix(),
                "sha256": file_sha256(coverage_path),
            },
            "pairing": {
                "path": pairing_path.relative_to(Path.cwd()).as_posix(),
                "sha256": file_sha256(pairing_path),
            },
        },
        "selection_gate": selection,
        "failure_vs_train_metadata": comparisons,
        "decision": {
            "reject_as_primary": (
                "Do not use target-versus-observed-wrong success as the primary "
                "population or causal effect estimator."
            ),
            "retain_as_diagnostic": (
                "Use the 31 observed pairs only for failure-local mechanism "
                "tracing after exact native coverage is captured."
            ),
            "required_primary_registry": (
                "Predeclare an outcome-independent expression cohort before "
                "native forward, enumerate every same-class candidate for each "
                "expression, bind exact config/model/checkpoint identities, and "
                "score target rank among the full candidate pool."
            ),
            "admission_condition": (
                "Primary native capture is admissible only when cohort "
                "provenance, complete same-class candidate coverage, and exact "
                "input/partition hashes validate without imputation."
            ),
        },
        "limitations": [
            "The comparison uses aggregate ScanRefer metadata, not native "
            "candidate coverage or model scores.",
            "Failure selection can coexist with a real identity failure; this "
            "audit rejects only the population-effect interpretation.",
            "No training candidate, queue state, or experimental mechanism is "
            "created by this audit.",
        ],
    }
    Path(args.output).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "selection_gate": selection,
        "same_class_peer_comparison": comparisons["same_class_peer"],
    }, indent=2))


if __name__ == "__main__":
    main()
