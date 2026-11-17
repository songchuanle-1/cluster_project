"""Freeze an outcome-independent referent target-rank registry.

The registry is built from the archived deterministic TRAIN sample before any
native score or model outcome is read. It enumerates every metadata same-class
object for each sampled expression and leaves rank fields unobserved.
"""
import argparse
import hashlib
import json
import logging
import os
from collections import Counter
from pathlib import Path
import sys

from referent_control_coverage_20260918 import (
    annotation_indices,
    control_features,
    normalized_name,
)


FORBIDDEN_OUTCOME_KEYS = {
    "baseline_rank",
    "correct",
    "error",
    "is_correct",
    "native_rank",
    "predicted_object_id",
    "predicted_rank",
    "score",
    "target_rank",
    "wrong_object_id",
}


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha256(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def stable_sha256(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def build_registry_rows(
    sample_rows,
    by_ann,
    by_scene,
    graphs,
    expected_expressions=123,
):
    """Return outcome-blind rows with complete metadata candidate pools."""
    if not sample_rows:
        raise ValueError("Empty sample")
    key_counts = Counter(
        (str(row["scene"]), int(row["expression_slot"]), str(row["ann_id"]))
        for row in sample_rows
    )
    if any(count != 1 for count in key_counts.values()):
        raise ValueError("Duplicate sampled expression key")

    scene_expression_counts = Counter(
        str(row["scene"]) for row in sample_rows
    )
    rows = []
    for sampled in sample_rows:
        scene = str(sampled["scene"])
        ann_id = str(sampled["ann_id"])
        record = by_ann[(scene, ann_id)]
        object_id = str(record["object_id"])
        object_name = str(record["object_name"])
        scene_objects = by_scene[scene]
        graph = graphs.get(scene, {}).get(object_id)
        features = control_features(record, graph, scene_objects)
        same_target_descriptions = sum(
            str(other["object_id"]) == object_id for other in scene_objects
        )
        candidate_ids = sorted(
            {
                str(value)
                for value in features["same_class_peer_ids"]
                if str(value) != object_id
            }
        )
        candidate_names = {}
        for candidate_id in candidate_ids:
            candidate_records = [
                row
                for row in scene_objects
                if str(row["object_id"]) == candidate_id
            ]
            if not candidate_records:
                raise ValueError("Candidate absent from scene annotations")
            candidate_name = normalized_name(
                candidate_records[0]["object_name"]
            )
            if candidate_name != normalized_name(object_name):
                raise ValueError("Candidate is not the target's same class")
            candidate_names[candidate_id] = str(
                candidate_records[0]["object_name"]
            )

        text = record.get("description", record.get("token", ""))
        rows.append({
            "registry_key": "%s:%s:%s" % (
                scene,
                int(sampled["expression_slot"]),
                ann_id,
            ),
            "dataset_order": {
                "step": int(sampled["step"]),
                "expression_slot": int(sampled["expression_slot"]),
            },
            "scene": scene,
            "ann_id": ann_id,
            "description_sha256": text_sha256(text),
            "target_object_id": object_id,
            "target_object_name": object_name,
            "same_class_candidate_ids": candidate_ids,
            "same_class_candidate_names": candidate_names,
            "same_class_candidate_count": len(candidate_ids),
            "primary_rank_eligible": bool(candidate_ids),
            "same_target_repeated": same_target_descriptions > 1,
            "target_has_relation_edge": bool(
                features["target_has_relation_edge"]
            ),
            "connected_same_class_peer": bool(
                features["connected_same_class_peer"]
            ),
            "scene_expression_count": scene_expression_counts[scene],
            "scene_weight": 1.0 / scene_expression_counts[scene],
        })
    validate_registry_rows(rows, expected_expressions=expected_expressions)
    return rows


def validate_registry_rows(rows, expected_expressions=123):
    if len(rows) != expected_expressions:
        raise ValueError(
            "Expected %d archived TRAIN expressions" % expected_expressions
        )
    keys = [row["registry_key"] for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate registry key")
    for row in rows:
        forbidden = FORBIDDEN_OUTCOME_KEYS.intersection(row)
        if forbidden:
            raise ValueError(
                "Outcome field leaked into frozen registry: %r"
                % sorted(forbidden)
            )
        candidates = row["same_class_candidate_ids"]
        if candidates != sorted(set(candidates)):
            raise ValueError("Candidate pool must be sorted and unique")
        if row["target_object_id"] in candidates:
            raise ValueError("Target cannot be its own candidate")
        if int(row["same_class_candidate_count"]) != len(candidates):
            raise ValueError("Candidate count differs from candidate pool")
        if not candidates and row["primary_rank_eligible"]:
            raise ValueError("Empty pool cannot be primary rank eligible")
        if candidates and not row["primary_rank_eligible"]:
            raise ValueError("Nonempty pool must be primary rank eligible")
        if abs(
            row["scene_weight"] * row["scene_expression_count"] - 1.0
        ) > 1e-12:
            raise ValueError("Scene weight is not normalized")


def summarize_registry(rows):
    eligible = [row for row in rows if row["primary_rank_eligible"]]
    pool_sizes = sorted(
        row["same_class_candidate_count"] for row in eligible
    )
    scene_weights = Counter(row["scene"] for row in rows)
    return {
        "expressions": len(rows),
        "scenes": len(scene_weights),
        "outcome_independent_expressions": len(rows),
        "primary_rank_eligible_expressions": len(eligible),
        "no_same_class_candidate_expressions": len(rows) - len(eligible),
        "same_class_candidate_count": sum(
            row["same_class_candidate_count"] for row in eligible
        ),
        "pool_size": {
            "min": pool_sizes[0],
            "median": pool_sizes[(len(pool_sizes) - 1) // 2],
            "max": pool_sizes[-1],
        },
        "scene_expression_distribution": dict(
            sorted(Counter(scene_weights.values()).items())
        ),
        "scene_weight_total": sum(row["scene_weight"] for row in rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--train-annotations", required=True)
    parser.add_argument("--train-graphs", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batches", type=int, default=16)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = Path(args.config).resolve()
    train_annotations = Path(args.train_annotations).resolve()
    train_graphs_path = Path(args.train_graphs).resolve()
    os.environ.update(
        CUDA_VISIBLE_DEVICES="",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false",
    )
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    from framework.dataset import build_dataset, build_dataloader

    train_records = json.loads(train_annotations.read_text())
    train_graphs = json.loads(train_graphs_path.read_text())
    by_ann, _, by_scene = annotation_indices(train_records)

    cfg = gorilla.Config.fromfile(str(config))
    cfg.model.data_root = cfg.data.train.data_root = (
        "/data3/songcl/data/data_cluster/"
    )
    gorilla.set_random_seed(1999)
    dataset = build_dataset(cfg.data.train, logging.getLogger("registry"))
    loader = build_dataloader(
        dataset,
        batch_size=2,
        num_workers=0,
        persistent_workers=False,
    )

    sample_rows = []
    for step, batch in enumerate(loader):
        scenes = [
            scene
            for scene, count in zip(batch["scan_ids"], batch["scenes_len"])
            for _ in range(int(count))
        ]
        slots = [
            slot
            for count in batch["scenes_len"]
            for slot in range(int(count))
        ]
        ann_ids = [str(value) for value in batch["ann_ids"]]
        if not (len(scenes) == len(slots) == len(ann_ids)):
            raise ValueError("Dataset expression axes differ")
        sample_rows.extend({
            "step": step,
            "scene": str(scene),
            "expression_slot": int(slot),
            "ann_id": ann_id,
        } for scene, slot, ann_id in zip(scenes, slots, ann_ids))
        if step + 1 >= args.batches:
            break

    rows = build_registry_rows(sample_rows, by_ann, by_scene, train_graphs)
    summary = summarize_registry(rows)
    report = {
        "schema_version": 1,
        "scope": (
            "CPU-only frozen outcome-independent registry for referent target "
            "rank; no model forward, native score, GPU execution, admission, or "
            "efficacy claim"
        ),
        "producer_sha256": file_sha256(__file__),
        "sources": {
            "config": {
                "path": str(config),
                "sha256": file_sha256(config),
            },
            "train_annotations": {
                "path": str(train_annotations),
                "sha256": file_sha256(train_annotations),
            },
            "train_graphs": {
                "path": str(train_graphs_path),
                "sha256": file_sha256(train_graphs_path),
            },
        },
        "cohort_contract": {
            "sample": "first 16 deterministic TRAIN batches",
            "seed": 1999,
            "selection_uses_model_outcome": False,
            "selection_uses_native_score_or_rank": False,
            "post_hoc_expression_exclusion": False,
            "registry_frozen_before_native_capture": True,
            "same_class_pool_definition": (
                "all non-target scene object instances whose normalized object "
                "name equals the target object name"
            ),
        },
        "primary_evaluation_contract": {
            "eligible_rows": "primary_rank_eligible=true",
            "rank": (
                "ascending native target score rank among the target plus every "
                "predeclared same-class candidate; rank 1 is best"
            ),
            "scene_balance": (
                "apply scene_weight, then aggregate expressions within scene and "
                "report a scene-level uncertainty interval"
            ),
            "missing_data": (
                "native candidate coverage, masks, transformed-input hashes, and "
                "hierarchical-partition hashes are required; never impute"
            ),
            "controls": [
                "objectness-only candidate score",
                "within-scene candidate permutation",
                "observed-failure pairs remain failure-local only",
            ],
        },
        "summary": summary,
        "registry_sha256": stable_sha256(rows),
        "rows": rows,
        "limitations": [
            "Metadata class equality does not establish native candidate-query "
            "coverage or geometric confusability.",
            "The fixed TRAIN sample is diagnostic and not a held-out population "
            "sample.",
            "This registry makes no novelty, causal-effect, or model-quality "
            "claim.",
        ],
    }
    Path(args.output).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="ascii",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
