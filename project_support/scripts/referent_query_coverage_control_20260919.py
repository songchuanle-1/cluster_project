"""Audit query-count confounding in the frozen referent rank capture.

The primary rank score selects the best query assigned to each object. Objects
with more assigned seed queries can gain from this best-of-k operation, so the
capture must expose and audit per-object query coverage. This module is CPU-only
and does not run a model, impute missing rows, or make an efficacy claim.
"""
import argparse
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

from referent_target_rank_evaluator_20260919 import (
    SCORE_NAMES,
    rank_capture_row,
    validate_capture_document,
    validate_registry_document,
)


SCHEMA_VERSION = 1
MIN_EXACT_MATCH_RATE = 0.75
MAX_MEAN_ABS_COVERAGE_DELTA = 1.0
MIN_MATCHED_SCENES = 2


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile(values, probability):
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot compute percentile of an empty sample")
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _scene_balanced(rows, getter):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(float(getter(row)))
    means = [sum(values) / len(values) for values in by_scene.values()]
    return sum(means) / len(means)


def _scene_bootstrap(rows, getter, seed_material, draws=2000):
    by_scene = defaultdict(list)
    for row in rows:
        by_scene[row["scene"]].append(float(getter(row)))
    scenes = list(by_scene.values())
    seed = int(
        hashlib.sha256(seed_material.encode("ascii")).hexdigest()[:16],
        16,
    )
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        sampled = [scenes[rng.randrange(len(scenes))] for _ in scenes]
        means = [sum(values) / len(values) for values in sampled]
        samples.append(sum(means) / len(means))
    return {
        "low": _percentile(samples, 0.025),
        "high": _percentile(samples, 0.975),
        "draws": draws,
    }


def _average_ranks(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        average = (start + 1 + end) / 2.0
        for position in range(start, end):
            ranks[order[position]] = average
        start = end
    return ranks


def _spearman(left, right):
    if len(left) < 3 or len(left) != len(right):
        return None
    left_ranks = _average_ranks(left)
    right_ranks = _average_ranks(right)
    left_mean = sum(left_ranks) / len(left_ranks)
    right_mean = sum(right_ranks) / len(right_ranks)
    numerator = sum(
        (a - left_mean) * (b - right_mean)
        for a, b in zip(left_ranks, right_ranks)
    )
    left_scale = sum((value - left_mean) ** 2 for value in left_ranks)
    right_scale = sum((value - right_mean) ** 2 for value in right_ranks)
    if left_scale == 0.0 or right_scale == 0.0:
        return None
    return numerator / math.sqrt(left_scale * right_scale)


def validate_query_assignment(capture_row, registry_row):
    object_ids = [
        registry_row["target_object_id"],
        *registry_row["same_class_candidate_ids"],
    ]
    assignment = capture_row.get("native_query_assignment")
    if not isinstance(assignment, dict) or set(assignment) != set(object_ids):
        raise ValueError("Native query assignment differs from object set")

    seen_queries = set()
    coverage = {}
    for object_id in object_ids:
        item = assignment.get(object_id)
        if not isinstance(item, dict):
            raise ValueError("Native query assignment row is missing")
        indices = item.get("query_indices")
        if not isinstance(indices, list) or not indices:
            raise ValueError("Native query pool is missing")
        if any(
            isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            for index in indices
        ):
            raise ValueError("Native query index is invalid")
        if indices != sorted(set(indices)):
            raise ValueError("Native query indices must be sorted and unique")
        if seen_queries.intersection(indices):
            raise ValueError("Native query indices overlap across objects")
        seen_queries.update(indices)
        coverage[object_id] = len(indices)
        for score_name in SCORE_NAMES:
            field = score_name + "_selected_query"
            selected = item.get(field)
            if (
                isinstance(selected, bool)
                or not isinstance(selected, int)
                or selected not in indices
            ):
                raise ValueError("Selected query is outside its object pool")
    return assignment, coverage


def validate_object_support_balance(capture_row, registry_row):
    object_ids = [
        registry_row["target_object_id"],
        *registry_row["same_class_candidate_ids"],
    ]
    support_size = capture_row.get("object_support_size")
    if not isinstance(support_size, dict) or set(support_size) != set(object_ids):
        raise ValueError("Native object support size differs from object set")

    normalized = {}
    for object_id in object_ids:
        value = support_size.get(object_id)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Native object support size is invalid")
        normalized[object_id] = value
    return normalized


def validate_native_query_costs(
    capture_row,
    registry_row,
    assignment,
    coverage,
    score_maps,
):
    object_ids = [
        registry_row["target_object_id"],
        *registry_row["same_class_candidate_ids"],
    ]
    query_costs = capture_row.get("native_query_costs")
    if not isinstance(query_costs, dict) or set(query_costs) != set(object_ids):
        raise ValueError("Native query costs differ from object set")

    axes = capture_row.get("native_query_axes")
    if not isinstance(axes, dict):
        raise ValueError("Native query axes are missing")
    required_axes = {"instance_labels", "seed_indices", "costs"}
    if not required_axes.issubset(axes):
        raise ValueError("Native query axes are incomplete")

    raw_labels = axes.get("instance_labels")
    if not isinstance(raw_labels, list) or not raw_labels:
        raise ValueError("Native query instance labels are missing")
    labels = []
    for label in raw_labels:
        if isinstance(label, bool) or not isinstance(label, int):
            raise ValueError("Native query instance labels are invalid")
        labels.append(label)

    raw_seed_indices = axes.get("seed_indices")
    if not isinstance(raw_seed_indices, list) or not raw_seed_indices:
        raise ValueError("Native query seed indices are missing")
    seed_indices = []
    for seed_index in raw_seed_indices:
        if (
            isinstance(seed_index, bool)
            or not isinstance(seed_index, int)
            or seed_index < 0
            or seed_index >= len(labels)
        ):
            raise ValueError("Native query seed index is invalid")
        seed_indices.append(seed_index)

    raw_global_costs = axes.get("costs")
    if (
        not isinstance(raw_global_costs, dict)
        or set(raw_global_costs) != set(SCORE_NAMES)
    ):
        raise ValueError("Native global query cost axes are missing")
    global_costs = {}
    for score_name in SCORE_NAMES:
        values = raw_global_costs.get(score_name)
        if not isinstance(values, list) or len(values) != len(seed_indices):
            raise ValueError("Native global query cost vector differs from query axis")
        normalized = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Native global query cost is not numeric")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("Native global query cost is nonfinite")
            normalized.append(value)
        global_costs[score_name] = normalized

    object_support_size = capture_row.get("object_support_size")
    if (
        not isinstance(object_support_size, dict)
        or set(object_support_size) != set(object_ids)
    ):
        raise ValueError("Native object support size differs from object set")

    margins = {score_name: {} for score_name in SCORE_NAMES}
    verified_object_axes = 0
    for object_id in object_ids:
        try:
            numeric_id = int(object_id)
        except (TypeError, ValueError):
            raise ValueError("Registry object ID is not an integer string")
        item = query_costs.get(object_id)
        if not isinstance(item, dict) or set(item) != set(SCORE_NAMES):
            raise ValueError("Native query cost axes are missing")
        query_indices = assignment[object_id]["query_indices"]
        expected_query_indices = [
            query_index
            for query_index, seed_index in enumerate(seed_indices)
            if labels[seed_index] == numeric_id
        ]
        if query_indices != expected_query_indices:
            raise ValueError(
                "Native query pools differ from global seed-instance membership"
            )
        expected_support = sum(label == numeric_id for label in labels)
        if object_support_size[object_id] != expected_support:
            raise ValueError(
                "Native object support size differs from global instance labels"
            )
        for score_name in SCORE_NAMES:
            values = item.get(score_name)
            if not isinstance(values, list) or len(values) != len(query_indices):
                raise ValueError("Native query cost vector differs from query pool")
            normalized = []
            for value in values:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("Native query cost is not numeric")
                value = float(value)
                if not math.isfinite(value):
                    raise ValueError("Native query cost is nonfinite")
                normalized.append(value)

            selected_query = assignment[object_id][
                score_name + "_selected_query"
            ]
            selected_position = query_indices.index(selected_query)
            selected_cost = normalized[selected_position]
            if selected_cost != score_maps[score_name][object_id]:
                raise ValueError("Selected query cost differs from native score")
            minimum = min(normalized)
            if selected_cost != minimum:
                raise ValueError("Selected query is not the minimum native cost")
            first_minimum_query = query_indices[normalized.index(minimum)]
            if selected_query != first_minimum_query:
                raise ValueError("Selected query does not match deterministic minimum")
            expected_projection = [
                global_costs[score_name][query_index]
                for query_index in query_indices
            ]
            if normalized != expected_projection:
                raise ValueError(
                    "Native query cost vector differs from global query axes"
                )

            ordered = sorted(normalized)
            margins[score_name][object_id] = (
                None if len(ordered) == 1 else ordered[1] - ordered[0]
            )
            verified_object_axes += 1
    return {
        "verified_objects": len(object_ids),
        "verified_object_axes": verified_object_axes,
        "global_axes_verified": True,
        "global_query_count": len(seed_indices),
        "margins": margins,
    }


def _coverage_metrics(
    registry_row,
    coverage,
    support_size,
    score_maps,
    selection_margins,
):
    target_id = registry_row["target_object_id"]
    object_ids = [
        target_id,
        *registry_row["same_class_candidate_ids"],
    ]
    ordered = sorted(object_ids, key=lambda object_id: (-coverage[object_id], object_id))
    target_rank = ordered.index(target_id) + 1
    candidate_ids = [
        object_id
        for object_id in object_ids
        if object_id != target_id
    ]
    deltas = [
        coverage[target_id] - coverage[object_id]
        for object_id in candidate_ids
    ]
    matched_ids = [
        target_id,
        *[
            object_id
            for object_id in candidate_ids
            if coverage[object_id] == coverage[target_id]
        ],
    ]
    support_deltas = [
        support_size[target_id] - support_size[object_id]
        for object_id in candidate_ids
    ]
    support_matched_ids = [
        target_id,
        *[
            object_id
            for object_id in candidate_ids
            if support_size[object_id] == support_size[target_id]
        ],
    ]
    coverage_matched_set = set(matched_ids)
    dual_matched_ids = [
        object_id
        for object_id in support_matched_ids
        if object_id in coverage_matched_set
    ]
    correlations = []
    for score_name in SCORE_NAMES:
        correlation = _spearman(
            [coverage[object_id] for object_id in object_ids],
            [score_maps[score_name][object_id] for object_id in object_ids],
        )
        if correlation is not None:
            correlations.append(correlation)
    observed_margins = [
        margin
        for score_name in SCORE_NAMES
        for object_id, margin in selection_margins[score_name].items()
        if object_id in object_ids and margin is not None
    ]
    singleton_axes = sum(
        margin is None
        for score_name in SCORE_NAMES
        for object_id, margin in selection_margins[score_name].items()
        if object_id in object_ids
    )
    return {
        "target_coverage": coverage[target_id],
        "candidate_coverage_min": min(coverage[object_id] for object_id in candidate_ids),
        "candidate_coverage_max": max(coverage[object_id] for object_id in candidate_ids),
        "target_coverage_rank_desc": target_rank,
        "pool_size": len(object_ids),
        "mean_candidate_coverage_delta": sum(deltas) / len(deltas),
        "abs_candidate_coverage_delta": [abs(delta) for delta in deltas],
        "exact_match_candidate_count": len(matched_ids) - 1,
        "matched_object_ids": matched_ids,
        "target_support_size": support_size[target_id],
        "candidate_support_size_min": min(
            support_size[object_id] for object_id in candidate_ids
        ),
        "candidate_support_size_max": max(
            support_size[object_id] for object_id in candidate_ids
        ),
        "mean_candidate_support_delta": sum(support_deltas) / len(support_deltas),
        "abs_candidate_support_delta": [
            abs(delta) for delta in support_deltas
        ],
        "support_exact_match_candidate_count": len(support_matched_ids) - 1,
        "support_matched_object_ids": support_matched_ids,
        "dual_exact_match_candidate_count": len(dual_matched_ids) - 1,
        "dual_matched_object_ids": dual_matched_ids,
        "score_coverage_spearman": correlations,
        "min_selected_query_cost_margin": (
            min(observed_margins) if observed_margins else None
        ),
        "mean_selected_query_cost_margin": (
            sum(observed_margins) / len(observed_margins)
            if observed_margins
            else None
        ),
        "singleton_query_pool_axes": singleton_axes,
    }


def _matched_rank(score_map, matched_ids, target_id):
    ordered = sorted(matched_ids, key=lambda object_id: score_map[object_id])
    rank = ordered.index(target_id) + 1
    return {
        "rank": rank,
        "pool_size": len(ordered),
        "top1": rank == 1,
        "normalized_excess": (
            0.0 if len(ordered) == 1 else (rank - 1) / (len(ordered) - 1)
        ),
    }


def _score_summary(rows, score_name, score_field="matched_scores"):
    score_rows = [
        {
            "scene": row["scene"],
            "value": row[score_field][score_name],
        }
        for row in rows
        if score_name in row[score_field]
    ]
    if not score_rows:
        return {
            "expressions": 0,
            "scenes": 0,
            "status": "no_exact_coverage_matched_candidates",
        }

    def value(row):
        return row["value"]

    top1 = _scene_balanced(score_rows, lambda row: value(row)["top1"])
    excess = _scene_balanced(
        score_rows,
        lambda row: value(row)["normalized_excess"],
    )
    uniform_top1 = _scene_balanced(
        score_rows,
        lambda row: 1.0 / value(row)["pool_size"],
    )
    return {
        "expressions": len(score_rows),
        "scenes": len({row["scene"] for row in score_rows}),
        "scene_balanced_top1_success": top1,
        "scene_balanced_top1_ci95": _scene_bootstrap(
            score_rows,
            lambda row: value(row)["top1"],
            "query-coverage:" + score_name + ":top1",
        ),
        "uniform_scene_balanced_top1_success": uniform_top1,
        "top1_lift_over_uniform": top1 - uniform_top1,
        "scene_balanced_normalized_rank_excess": excess,
        "normalized_rank_excess_ci95": _scene_bootstrap(
            score_rows,
            lambda row: value(row)["normalized_excess"],
            "query-coverage:" + score_name + ":excess",
        ),
        "expression_top1_success": sum(
            bool(value(row)["top1"]) for row in score_rows
        ) / len(score_rows),
        "expression_mean_rank": sum(
            value(row)["rank"] for row in score_rows
        ) / len(score_rows),
    }


def _paired_contrast(rows, field, score_field="matched_scores"):
    paired = []
    for row in rows:
        if all(name in row[score_field] for name in SCORE_NAMES):
            paired.append({
                "scene": row["scene"],
                "value": (
                    row[score_field]["referent"][field]
                    - row[score_field]["objectness"][field]
                ),
            })
    if not paired:
        return {
            "expressions": 0,
            "scenes": 0,
            "status": "no_exact_coverage_matched_pairs",
        }
    return {
        "expressions": len(paired),
        "scenes": len({row["scene"] for row in paired}),
        "scene_balanced_referent_minus_objectness": _scene_balanced(
            paired,
            lambda row: row["value"],
        ),
        "scene_bootstrap_ci95": _scene_bootstrap(
            paired,
            lambda row: row["value"],
            "query-coverage:paired:" + field,
        ),
        "referent_fixed_objectness_failed": sum(
            row[score_field]["referent"]["top1"]
            and not row[score_field]["objectness"]["top1"]
            for row in rows
            if all(name in row[score_field] for name in SCORE_NAMES)
        ) if field == "top1" else None,
        "referent_broken_objectness_fixed": sum(
            not row[score_field]["referent"]["top1"]
            and row[score_field]["objectness"]["top1"]
            for row in rows
            if all(name in row[score_field] for name in SCORE_NAMES)
        ) if field == "top1" else None,
    }


def audit_capture(registry, capture):
    registry_rows = validate_registry_document(registry)
    capture_rows = validate_capture_document(capture, registry)
    valid = []
    rejected = []
    for registry_row in registry_rows:
        if not registry_row["primary_rank_eligible"]:
            continue
        key = registry_row["registry_key"]
        capture_row = capture_rows.get(key)
        if capture_row is None:
            rejected.append({"registry_key": key, "reason": "missing_expression"})
            continue
        try:
            rank_scores = rank_capture_row(capture_row, registry_row)
            assignment, coverage = validate_query_assignment(
                capture_row,
                registry_row,
            )
            support_size = validate_object_support_balance(
                capture_row,
                registry_row,
            )
            score_maps = capture_row["scores"]
            selection_audit = validate_native_query_costs(
                capture_row,
                registry_row,
                assignment,
                coverage,
                score_maps,
            )
        except ValueError as exc:
            rejected.append({"registry_key": key, "reason": str(exc)})
            continue

        coverage_metrics = _coverage_metrics(
            registry_row,
            coverage,
            support_size,
            score_maps,
            selection_audit["margins"],
        )
        matched_scores = {}
        matched_ids = coverage_metrics["matched_object_ids"]
        if len(matched_ids) > 1:
            for score_name in SCORE_NAMES:
                matched_scores[score_name] = _matched_rank(
                    score_maps[score_name],
                    matched_ids,
                    registry_row["target_object_id"],
                )
        dual_matched_scores = {}
        dual_matched_ids = coverage_metrics["dual_matched_object_ids"]
        if len(dual_matched_ids) > 1:
            for score_name in SCORE_NAMES:
                dual_matched_scores[score_name] = _matched_rank(
                    score_maps[score_name],
                    dual_matched_ids,
                    registry_row["target_object_id"],
                )
        valid.append({
            "registry_key": key,
            "scene": registry_row["scene"],
            "target_object_id": registry_row["target_object_id"],
            "primary_scores": rank_scores,
            "coverage": coverage_metrics,
            "matched_scores": matched_scores,
            "dual_matched_scores": dual_matched_scores,
            "object_support_size": support_size,
            "selection_audit": selection_audit,
            "selected_query_indices": {
                object_id: {
                    score_name: assignment[object_id][
                        score_name + "_selected_query"
                    ]
                    for score_name in SCORE_NAMES
                }
                for object_id in assignment
            },
        })

    if not valid:
        raise ValueError("No expression has complete query-coverage evidence")

    exact_matches = sum(
        row["coverage"]["exact_match_candidate_count"] > 0
        for row in valid
    )
    support_exact_matches = sum(
        row["coverage"]["support_exact_match_candidate_count"] > 0
        for row in valid
    )
    dual_exact_matches = sum(
        row["coverage"]["dual_exact_match_candidate_count"] > 0
        for row in valid
    )
    all_abs_deltas = [
        delta
        for row in valid
        for delta in row["coverage"]["abs_candidate_coverage_delta"]
    ]
    all_abs_support_deltas = [
        delta
        for row in valid
        for delta in row["coverage"]["abs_candidate_support_delta"]
    ]
    correlations = [
        value
        for row in valid
        for value in row["coverage"]["score_coverage_spearman"]
    ]
    coverage_summary = {
        "complete_expressions": len(valid),
        "complete_scenes": len({row["scene"] for row in valid}),
        "rejected_expressions": len(rejected),
        "exact_coverage_match_expressions": exact_matches,
        "exact_coverage_match_rate": exact_matches / len(valid),
        "mean_abs_candidate_coverage_delta": (
            sum(all_abs_deltas) / len(all_abs_deltas)
        ),
        "max_abs_candidate_coverage_delta": max(all_abs_deltas),
        "support_exact_match_expressions": support_exact_matches,
        "support_exact_match_rate": support_exact_matches / len(valid),
        "dual_exact_match_expressions": dual_exact_matches,
        "dual_exact_match_rate": dual_exact_matches / len(valid),
        "mean_abs_candidate_support_delta": (
            sum(all_abs_support_deltas) / len(all_abs_support_deltas)
        ),
        "max_abs_candidate_support_delta": max(all_abs_support_deltas),
        "mean_score_coverage_spearman": (
            sum(correlations) / len(correlations)
            if correlations
            else None
        ),
        "score_coverage_spearman_observations": len(correlations),
        "min_selected_query_cost_margin": (
            min(
                row["coverage"]["min_selected_query_cost_margin"]
                for row in valid
                if row["coverage"]["min_selected_query_cost_margin"] is not None
            )
            if any(
                row["coverage"]["min_selected_query_cost_margin"] is not None
                for row in valid
            )
            else None
        ),
        "singleton_query_pool_axes": sum(
            row["coverage"]["singleton_query_pool_axes"] for row in valid
        ),
    }
    matched_rows = [row for row in valid if row["matched_scores"]]
    dual_matched_rows = [row for row in valid if row["dual_matched_scores"]]
    gate_passed = (
        coverage_summary["exact_coverage_match_rate"] >= MIN_EXACT_MATCH_RATE
        and coverage_summary["mean_abs_candidate_coverage_delta"]
        <= MAX_MEAN_ABS_COVERAGE_DELTA
        and coverage_summary["complete_scenes"] >= MIN_MATCHED_SCENES
        and bool(matched_rows)
    )
    return {
        "coverage_summary": coverage_summary,
        "matched_summary": {
            "expressions": len(matched_rows),
            "scenes": len({row["scene"] for row in matched_rows}),
            "scores": {
                score_name: _score_summary(matched_rows, score_name)
                for score_name in SCORE_NAMES
            },
            "paired_top1": _paired_contrast(matched_rows, "top1"),
            "paired_normalized_excess": _paired_contrast(
                matched_rows,
                "normalized_excess",
            ),
        },
        "dual_balanced_summary": {
            "expressions": len(dual_matched_rows),
            "scenes": len({row["scene"] for row in dual_matched_rows}),
            "scores": {
                score_name: _score_summary(
                    dual_matched_rows,
                    score_name,
                    score_field="dual_matched_scores",
                )
                for score_name in SCORE_NAMES
            },
            "paired_top1": _paired_contrast(
                dual_matched_rows,
                "top1",
                score_field="dual_matched_scores",
            ),
            "paired_normalized_excess": _paired_contrast(
                dual_matched_rows,
                "normalized_excess",
                score_field="dual_matched_scores",
            ),
        },
        "selection_verification": {
            "verified_expressions": len(valid),
            "verified_object_axes": sum(
                row["selection_audit"]["verified_object_axes"] for row in valid
            ),
            "global_query_axes_verified": all(
                row["selection_audit"]["global_axes_verified"] for row in valid
            ),
            "selected_cost_equals_native_score": True,
            "selected_query_is_minimum": True,
            "deterministic_tie_break_verified": True,
            "failures": 0,
        },
        "coverage_admission_gate": {
            "status": "passed" if gate_passed else "not_met",
            "min_exact_match_rate": MIN_EXACT_MATCH_RATE,
            "max_mean_abs_coverage_delta": MAX_MEAN_ABS_COVERAGE_DELTA,
            "min_matched_scenes": MIN_MATCHED_SCENES,
            "consequence_if_not_met": (
                "Do not promote the all-candidate rank contrast; retain the "
                "exact-coverage matched contrast as diagnostic evidence."
            ),
        },
        "rejected": rejected,
        "rows": valid,
    }


def build_report(registry, capture, registry_path, capture_path):
    audit = audit_capture(registry, capture)
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": (
            "CPU-only query-coverage confounding audit for the frozen "
            "referent target-rank capture; no model forward, native score, "
            "imputation, queue mutation, or efficacy claim"
        ),
        "inputs": {
            "registry": {
                "path": str(registry_path),
                "sha256": file_sha256(registry_path),
            },
            "capture": {
                "path": str(capture_path),
                "sha256": file_sha256(capture_path),
            },
        },
        "binding": capture["binding"],
        "contract": {
            "primary_rank": "best query assigned to each object",
            "coverage_confounder": (
                "number of native queries whose sampled seed belongs to the "
                "object; best-of-k can improve with larger k"
            ),
            "matched_control": (
                "rank the target only against candidates with the same query "
                "count as the target"
            ),
            "secondary_support_balance": (
                "descriptively rank the target only against candidates with "
                "the same query count and the same native instance support size"
            ),
            "selection_provenance": (
                "persist global native query axes and per-object query costs; "
                "reconstruct each object pool from seed-instance membership "
                "and verify every score equals the deterministic best-of-k"
            ),
            "paired_contrast": (
                "referent minus objectness on identical exact-coverage rows; "
                "positive top1 is favorable and negative normalized excess is "
                "favorable"
            ),
            "missing_data": "reject expression; no query-count imputation",
        },
        "audit": audit,
        "limitations": [
            "Global query axes and per-object projections are now persisted, so "
            "seed-instance membership, support size, score equality, and "
            "deterministic minimum selection are checked in the derived audit.",
            "Exact query-count matching does not prove identical geometric "
            "difficulty or independent query behavior.",
            "Support-size matching is an extent-balance sensitivity control, "
            "not proof of identical geometry or visibility.",
            "The gate is a diagnostic admission rule, not evidence of target "
            "mIoU or a deployable mechanism.",
            "No native result exists in this contract-validation artifact.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    registry_path = Path(args.registry).resolve()
    capture_path = Path(args.capture).resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    report = build_report(
        registry,
        capture,
        registry_path=registry_path,
        capture_path=capture_path,
    )
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps(report["audit"]["coverage_summary"], indent=2))


if __name__ == "__main__":
    main()
