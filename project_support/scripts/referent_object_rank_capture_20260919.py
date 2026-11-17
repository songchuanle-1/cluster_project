"""Build the frozen referent target-rank capture from native M95 observations.

The builder is CPU-only and outcome-blind. It assigns each native instance query
to the physical object containing its sampled seed superpoint, then scores every
predeclared target/candidate object by the best query on each axis. Missing
native seed coverage or malformed evidence fails closed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


SCHEMA_VERSION = 1
SCORE_NAMES = ("referent", "objectness")
SCORE_SEMANTICS = "negative_confidence_lower_is_better"
QUERY_ASSIGNMENT_POLICY = "seed_superpoint_instance_membership"


def stable_sha256(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_hex(value, length):
    if not isinstance(value, str) or len(value) != length:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _require_hash(value, field, length=64):
    if not _is_hex(value, length):
        raise ValueError("Invalid hash field: " + field)
    return value.lower()


def _require_cost_vector(value, field, expected_length):
    if not isinstance(value, list) or len(value) != expected_length:
        raise ValueError("Cost vector differs from query axis: " + field)
    costs = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError("Numeric cost required: " + field)
        item = float(item)
        if not math.isfinite(item):
            raise ValueError("Nonfinite cost: " + field)
        costs.append(item)
    return costs


def _require_instance_labels(value, length):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError("Instance-label axis differs from native support")
    labels = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError("Integer instance labels required")
        labels.append(item)
    return labels


def _mask_sha256(mask):
    payload = {
        "dtype": "bool",
        "shape": [len(mask)],
        "data": [1 if value else 0 for value in mask],
    }
    return stable_sha256(payload)


def _require_seed_indices(value, support_size, query_count):
    if not isinstance(value, list) or len(value) != query_count:
        raise ValueError("Query seed indices differ from query axis")
    indices = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError("Integer query seed indices required")
        if item < 0 or item >= support_size:
            raise ValueError("Query seed index is outside native support")
        indices.append(item)
    return indices


def _validate_registry(registry):
    if registry.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported registry schema")
    rows = registry.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Registry rows are missing")
    if registry.get("registry_sha256") != stable_sha256(rows):
        raise ValueError("Registry content hash mismatch")

    keys = []
    for row in rows:
        key = row.get("registry_key")
        if not isinstance(key, str) or not key:
            raise ValueError("Registry key is missing")
        keys.append(key)
        candidates = row.get("same_class_candidate_ids")
        if not isinstance(candidates, list):
            raise ValueError("Candidate pool is missing")
        if candidates != sorted(set(candidates)):
            raise ValueError("Candidate pool must be sorted and unique")
        if row.get("target_object_id") in candidates:
            raise ValueError("Target cannot be its own candidate")
        if row.get("primary_rank_eligible") != bool(candidates):
            raise ValueError("Rank eligibility differs from candidate pool")
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate registry key")
    return rows


def _validate_binding(binding):
    if not isinstance(binding, dict):
        raise ValueError("Capture binding is missing")
    normalized = dict(binding)
    normalized["code_commit"] = _require_hash(
        binding.get("code_commit"), "code_commit", length=40
    )
    for field in ("config_sha256", "model_package_sha256", "checkpoint_sha256"):
        normalized[field] = _require_hash(binding.get(field), field)
    return normalized


def build_capture(registry, expression_inputs, binding):
    """Return a capture document accepted by the frozen rank evaluator."""
    registry_rows = _validate_registry(registry)
    normalized_binding = _validate_binding(binding)
    by_key = {row["registry_key"]: row for row in registry_rows}
    eligible = {
        row["registry_key"]: row
        for row in registry_rows
        if row["primary_rank_eligible"]
    }

    if not isinstance(expression_inputs, list):
        raise ValueError("Expression inputs must be a list")
    by_input = {}
    for item in expression_inputs:
        if not isinstance(item, dict):
            raise ValueError("Expression input must be an object")
        key = item.get("registry_key")
        if key not in eligible:
            raise ValueError("Unknown or ineligible expression input")
        if key in by_input:
            raise ValueError("Duplicate expression input")
        by_input[key] = item
    if set(by_input) != set(eligible):
        raise ValueError("Expression inputs differ from rank-eligible registry")

    output_rows = []
    for key in sorted(eligible):
        registry_row = eligible[key]
        item = by_input[key]
        if item.get("scene") != registry_row["scene"]:
            raise ValueError("Expression scene differs from registry")
        if item.get("target_object_id") != registry_row["target_object_id"]:
            raise ValueError("Expression target differs from registry")

        native_input_sha256 = _require_hash(
            item.get("native_input_sha256"), "native_input_sha256"
        )
        partition_sha256 = _require_hash(
            item.get("hierarchical_partition_sha256"),
            "hierarchical_partition_sha256",
        )
        labels = _require_instance_labels(
            item.get("instance_labels"), len(item.get("instance_labels", []))
        )
        support_size = len(labels)
        if support_size == 0:
            raise ValueError("Native support is empty")

        referent_costs = item.get("referent_costs")
        if not isinstance(referent_costs, list) or not referent_costs:
            raise ValueError("Native query scores are missing")
        query_count = len(referent_costs)
        query_seed_indices = _require_seed_indices(
            item.get("query_seed_indices"), support_size, query_count
        )
        costs = {}
        for score_name in SCORE_NAMES:
            costs[score_name] = _require_cost_vector(
                item.get(score_name + "_costs"),
                score_name + "_costs",
                query_count,
            )

        object_ids = [
            registry_row["target_object_id"],
            *registry_row["same_class_candidate_ids"],
        ]
        object_masks = {}
        for object_id in object_ids:
            try:
                numeric_id = int(object_id)
            except (TypeError, ValueError):
                raise ValueError("Registry object ID is not an integer string")
            mask = [label == numeric_id for label in labels]
            if not any(mask):
                raise ValueError("Candidate has empty native instance mask")
            object_masks[object_id] = mask

        query_assignment = {}
        native_query_costs = {}
        score_maps = {score_name: {} for score_name in SCORE_NAMES}
        for object_id in object_ids:
            numeric_id = int(object_id)
            query_indices = [
                query_index
                for query_index, seed_index in enumerate(query_seed_indices)
                if labels[seed_index] == numeric_id
            ]
            if not query_indices:
                raise ValueError("Candidate has no native query seed coverage")
            query_assignment[object_id] = {"query_indices": query_indices}
            native_query_costs[object_id] = {
                score_name: [
                    costs[score_name][query_index]
                    for query_index in query_indices
                ]
                for score_name in SCORE_NAMES
            }
            for score_name in SCORE_NAMES:
                selected_query = min(
                    query_indices, key=lambda index: costs[score_name][index]
                )
                score_maps[score_name][object_id] = costs[score_name][selected_query]
                query_assignment[object_id][score_name + "_selected_query"] = (
                    selected_query
                )

        output_rows.append({
            "registry_key": key,
            "scene": registry_row["scene"],
            "target_object_id": registry_row["target_object_id"],
            "native_input_sha256": native_input_sha256,
            "hierarchical_partition_sha256": partition_sha256,
            "scores": score_maps,
            "object_support_size": {
                object_id: sum(1 for value in object_masks[object_id] if value)
                for object_id in object_ids
            },
            "mask_sha256": {
                object_id: _mask_sha256(object_masks[object_id])
                for object_id in object_ids
            },
            "native_query_assignment": query_assignment,
            "native_query_costs": native_query_costs,
            "native_query_axes": {
                "instance_labels": labels,
                "seed_indices": query_seed_indices,
                "costs": {
                    score_name: costs[score_name]
                    for score_name in SCORE_NAMES
                },
            },
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "registry_sha256": registry["registry_sha256"],
        "binding": normalized_binding,
        "capture_contract": {
            "score_direction": "lower_is_better",
            "missing_data_policy": "reject_expression_no_imputation",
            "required_score_names": list(SCORE_NAMES),
            "tie_policy": "reject",
        },
        "score_semantics": SCORE_SEMANTICS,
        "query_assignment_policy": QUERY_ASSIGNMENT_POLICY,
        "rows": output_rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--expressions", required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    registry_path = Path(args.registry).resolve()
    expressions_path = Path(args.expressions).resolve()
    binding_path = Path(args.binding).resolve()
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    expressions = json.loads(expressions_path.read_text(encoding="utf-8"))
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    capture = build_capture(registry, expressions, binding)
    Path(args.output).write_text(
        json.dumps(capture, indent=2, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(json.dumps({
        "capture_sha256": file_sha256(args.output),
        "rows": len(capture["rows"]),
    }, indent=2))


if __name__ == "__main__":
    main()
