"""Build a scene-balanced design registry from the audited failure controls.

This is a CPU-only metadata transformation. It does not load a model, use a
GPU, modify candidate state, or claim a causal effect.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize_pairs(rows):
    scene_counts = Counter(row["scene"] for row in rows)
    pairs = []
    for row in rows:
        control_pool = sorted({str(value) for value in row["same_class_peer_ids"]})
        observed_control = str(row["wrong_object_id"])
        primary_eligible = bool(row["wrong_is_same_class"]) and (
            observed_control in control_pool
        )
        pairs.append({
            "pair_id": "%s:%s:%s" % (
                row["scene"],
                row["expression_slot"],
                row["ann_id"],
            ),
            "scene": row["scene"],
            "step": row["step"],
            "expression_slot": row["expression_slot"],
            "ann_id": str(row["ann_id"]),
            "target_object_id": str(row["object_id"]),
            "target_object_name": row["object_name"],
            "observed_control_object_id": observed_control,
            "observed_control_object_name": row["wrong_object_name"],
            "same_target_repeated": bool(row["same_target_repeated"]),
            "same_target_descriptions": int(row["same_target_descriptions"]),
            "same_class_control_pool": control_pool,
            "same_class_control_pool_size": len(control_pool),
            "observed_control_in_same_class_pool": observed_control in control_pool,
            "primary_same_class_pair_eligible": primary_eligible,
            "target_has_relation_edge": bool(row["target_has_relation_edge"]),
            "target_has_attribute": bool(row["target_has_attribute"]),
            "target_has_relation_span": bool(row["target_has_relation_span"]),
            "direct_connected_same_class_peer": bool(
                row["connected_same_class_peer"]
            ),
            "scene_weight": 1.0 / scene_counts[row["scene"]],
        })

    primary = [row for row in pairs if row["primary_same_class_pair_eligible"]]
    repeated = [row for row in pairs if row["same_target_repeated"]]
    connected = [
        row for row in pairs if row["direct_connected_same_class_peer"]
    ]
    pool_sizes = [row["same_class_control_pool_size"] for row in pairs]
    scene_weights = Counter(row["scene"] for row in pairs)
    weighted_scenes = {
        scene: 1.0 / count for scene, count in sorted(scene_weights.items())
    }
    return {
        "expressions": len(pairs),
        "scenes": len(scene_weights),
        "same_class_primary_pairs": len(primary),
        "cross_class_excluded_pairs": len(pairs) - len(primary),
        "same_target_repeated_pairs": len(repeated),
        "same_target_repeated_among_primary": sum(
            row["same_target_repeated"] for row in primary
        ),
        "relation_edge_targets": sum(
            row["target_has_relation_edge"] for row in pairs
        ),
        "relation_edge_targets_among_primary": sum(
            row["target_has_relation_edge"] for row in primary
        ),
        "direct_connected_same_class_peer_pairs": len(connected),
        "direct_connected_primary_pairs": sum(
            row["primary_same_class_pair_eligible"] for row in connected
        ),
        "same_class_pool_size": {
            "min": min(pool_sizes),
            "median": median(pool_sizes),
            "max": max(pool_sizes),
        },
        "pair_weight_total": sum(row["scene_weight"] for row in pairs),
        "max_scene_weight": max(weighted_scenes.values()),
        "weighted_scenes": weighted_scenes,
    }


def validate_source(report):
    rows = report["observed_failure_coverage"]["rows"]
    if len(rows) != 33:
        raise ValueError("Expected 33 observed failure rows")
    keys = {
        (str(row["scene"]), int(row["expression_slot"]), str(row["ann_id"]))
        for row in rows
    }
    if len(keys) != len(rows):
        raise ValueError("Duplicate failure keys")
    for row in rows:
        if not row.get("same_class_peer"):
            raise ValueError("Every audited failure must have a same-class peer")
        pool = {str(value) for value in row.get("same_class_peer_ids", [])}
        if row.get("wrong_is_same_class") and str(row["wrong_object_id"]) not in pool:
            raise ValueError("Observed same-class control is absent from target pool")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    coverage_path = Path(args.coverage).resolve()
    source = json.loads(coverage_path.read_text(encoding="utf-8"))
    rows = validate_source(source)
    pair_rows = []
    scene_counts = Counter(row["scene"] for row in rows)
    for row in rows:
        pair_rows.append({
            **row,
            "scene_weight": 1.0 / scene_counts[row["scene"]],
        })
    summary = summarize_pairs(rows)
    report = {
        "scope": (
            "CPU-only scene-balanced pairing contract derived from the audited "
            "ScanRefer failure controls; no model forward, GPU execution, "
            "admission, or causal-effect claim"
        ),
        "producer_sha256": file_sha256(__file__),
        "source": {
            "path": "pipeline/reports/referent_control_coverage_20260918-1618.json",
            "sha256": file_sha256(coverage_path),
            "scope": source["scope"],
        },
        "summary": summary,
        "evaluation_contract": {
            "primary_contrast": (
                "For each eligible failure, compare the native target query "
                "selection against its observed wrong instance while preserving "
                "scene, ann_id, expression_slot, transformed-input hash, and "
                "hierarchical-partition hash."
            ),
            "scene_balance": (
                "Aggregate pair effects with the recorded 1/failures_per_scene "
                "weights, then report a scene-level uncertainty interval."
            ),
            "repeated_description_sensitivity": (
                "Report the repeated same-target-description subset as a "
                "predefined sensitivity analysis, not as a replacement primary."
            ),
            "relation_connected_subgroup": (
                "Report the direct-connected same-class subgroup only as "
                "exploratory; the current sample has insufficient support for a "
                "primary relation-context claim."
            ),
            "missing_data": (
                "A pair without native candidate coverage, mask support, or an "
                "exact partition hash is missing and must not be imputed."
            ),
        },
        "pairs": [
            {
                "pair_id": "%s:%s:%s" % (
                    row["scene"],
                    row["expression_slot"],
                    row["ann_id"],
                ),
                "scene": row["scene"],
                "step": row["step"],
                "expression_slot": row["expression_slot"],
                "ann_id": str(row["ann_id"]),
                "target_object_id": str(row["object_id"]),
                "target_object_name": row["object_name"],
                "observed_control_object_id": str(row["wrong_object_id"]),
                "observed_control_object_name": row["wrong_object_name"],
                "primary_same_class_pair_eligible": (
                    bool(row["wrong_is_same_class"])
                    and str(row["wrong_object_id"]) in {
                        str(value) for value in row["same_class_peer_ids"]
                    }
                ),
                "same_class_control_pool": sorted({
                    str(value) for value in row["same_class_peer_ids"]
                }),
                "same_target_repeated": bool(row["same_target_repeated"]),
                "target_has_relation_edge": bool(row["target_has_relation_edge"]),
                "direct_connected_same_class_peer": bool(
                    row["connected_same_class_peer"]
                ),
                "scene_weight": row["scene_weight"],
            }
            for row in pair_rows
        ],
        "limitations": [
            "Metadata class equality does not prove native candidate-query "
            "coverage or geometric confusability.",
            "The observed wrong instance is an outcome-selected control and "
            "cannot by itself identify a broad same-class population effect.",
            "The direct-connected same-class subgroup has only two expressions.",
            "The registry prepares a future paired capture; it does not provide "
            "the missing native evidence or an efficacy result.",
        ],
    }
    Path(args.output).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="ascii",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
