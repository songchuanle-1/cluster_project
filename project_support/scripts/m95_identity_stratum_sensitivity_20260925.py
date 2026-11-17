"""Audit class and peer-cardinality sensitivity of the M95 identity control.

This CPU-only checker extends the fixed-floor support-exclusion analysis. It
tests whether the final-stage identity-minus-score advantage survives removal
of any one target class or same-class peer-cardinality bucket. The result is
oracle diagnostic evidence, not a mechanism or admission receipt.
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_MANIFEST_SHA256,
    STAGES,
    as_list,
    bool_list,
    dominant_overlap,
    file_sha256,
    float_list,
    int_list,
    load_artifacts,
    load_json,
    mask_iou,
    validate_capture,
    validate_manifest_hash,
)
from m95_identity_self_support_control_20260925 import (
    identity_from_stats,
    prototype_stats,
    support_stats,
)
from m95_identity_support_sensitivity_20260925 import (
    identity_at_floor,
    make_floor_pair_rows,
    remaining_support_counts,
    validate_pair_rows,
)
from m95_instance_identity_discriminability_20260925 import (
    EXPECTED_CAPTURE_SHA256,
    EXPECTED_ROWS,
    mean_selected,
    summarize_pairs,
)


CONTRACT = "m95_identity_stratum_sensitivity_v1"
FINAL_STAGE = "final"
FIXED_SUPPORT_FLOOR = 3
MIN_DESCRIPTIVE_PAIRS = 10
MIN_DESCRIPTIVE_SCENES = 3


def peer_count_bucket(peer_count):
    peer_count = int(peer_count)
    if peer_count == 1:
        return "1"
    if peer_count in (2, 3):
        return "2-3"
    if peer_count >= 4:
        return "4+"
    raise ValueError("Identity strata require at least one same-class peer")


def attach_pair_metadata(pair_rows, metadata_by_index):
    attached = []
    for pair in pair_rows:
        manifest_index = int(pair["manifest_index"])
        metadata = metadata_by_index[manifest_index]
        attached.append(
            {
                **pair,
                "target_class": metadata["target_class"],
                "peer_count": metadata["peer_count"],
                "peer_count_bucket": peer_count_bucket(metadata["peer_count"]),
            }
        )
    return attached


def group_summaries(rows, field):
    grouped = defaultdict(list)
    for row in rows:
        grouped[str(row[field])].append(row)
    return {
        key: summarize_pairs(grouped[key])
        for key in sorted(grouped)
    }


def summarize_subset(rows):
    summary = summarize_pairs(rows)
    summary["scenes"] = len({str(row["scene_id"]) for row in rows})
    return summary


def leave_one_group_out(rows, field):
    groups = sorted({str(row[field]) for row in rows})
    return {
        group: summarize_subset(
            [row for row in rows if str(row[field]) != group]
        )
        for group in groups
    }


def descriptive_stability(rows):
    class_rows = defaultdict(list)
    for row in rows:
        class_rows[str(row["target_class"])].append(row)

    eligible = []
    for target_class, grouped in sorted(class_rows.items()):
        summary = summarize_subset(grouped)
        if (
            summary["pairs"] >= MIN_DESCRIPTIVE_PAIRS
            and summary["scenes"] >= MIN_DESCRIPTIVE_SCENES
        ):
            eligible.append(
                {
                    "target_class": target_class,
                    "pairs": summary["pairs"],
                    "scenes": summary["scenes"],
                    "identity_minus_score": summary["identity_minus_score"],
                }
            )
    return {
        "minimum_pairs": MIN_DESCRIPTIVE_PAIRS,
        "minimum_scenes": MIN_DESCRIPTIVE_SCENES,
        "eligible_classes": eligible,
        "positive_classes": sum(
            row["identity_minus_score"] > 0.0 for row in eligible
        ),
        "nonpositive_classes": [
            row["target_class"]
            for row in eligible
            if row["identity_minus_score"] <= 0.0
        ],
    }


def sensitivity_summary(pair_rows, metadata_by_index, expected_rows=EXPECTED_ROWS):
    if not pair_rows:
        raise ValueError("No final-stage floor-3 score-matched pairs")
    pair_rows = attach_pair_metadata(pair_rows, metadata_by_index)
    validate_pair_rows(pair_rows)

    class_leave_one_out = leave_one_group_out(pair_rows, "target_class")
    peer_leave_one_out = leave_one_group_out(pair_rows, "peer_count_bucket")
    class_points = [
        summary["identity_minus_score"]
        for summary in class_leave_one_out.values()
        if summary["identity_minus_score"] is not None
    ]
    peer_points = [
        summary["identity_minus_score"]
        for summary in peer_leave_one_out.values()
        if summary["identity_minus_score"] is not None
    ]
    classes = sorted({str(row["target_class"]) for row in pair_rows})
    peer_buckets = sorted({str(row["peer_count_bucket"]) for row in pair_rows})

    return {
        "fixed_support_floor": FIXED_SUPPORT_FLOOR,
        "overall": summarize_subset(pair_rows),
        "class_strata": group_summaries(pair_rows, "target_class"),
        "peer_count_strata": group_summaries(
            pair_rows, "peer_count_bucket"
        ),
        "leave_one_class_out": class_leave_one_out,
        "leave_one_peer_count_bucket_out": peer_leave_one_out,
        "stability": {
            "all_leave_one_class_out_positive": all(
                value > 0.0 for value in class_points
            ),
            "all_leave_one_peer_bucket_out_positive": all(
                value > 0.0 for value in peer_points
            ),
            "minimum_leave_one_class_out": (
                min(class_points) if class_points else None
            ),
            "maximum_leave_one_class_out": (
                max(class_points) if class_points else None
            ),
            "minimum_leave_one_peer_bucket_out": (
                min(peer_points) if peer_points else None
            ),
            "maximum_leave_one_peer_bucket_out": (
                max(peer_points) if peer_points else None
            ),
            "represented_classes": classes,
            "represented_peer_count_buckets": peer_buckets,
            "descriptive_class_stability": descriptive_stability(pair_rows),
        },
    }


def extract_final_floor3_pairs(report, manifest, artifacts):
    validate_capture(report, manifest, EXPECTED_CHECKPOINT_SHA256)
    if set(artifacts) != set(manifest):
        raise ValueError("Artifact coverage differs from the frozen manifest")

    query_rows = []
    metadata_by_index = {}
    ineligible_expressions = 0

    for index in range(EXPECTED_ROWS):
        manifest_row = manifest[index]
        artifact = artifacts[index]
        labels = int_list(
            artifact["physical_instance_labels"], "instance labels"
        )
        target = bool_list(artifact["target_union"], "target union")
        masks = [
            bool_list(mask, "query mask")
            for mask in as_list(artifact["query_masks"])
        ]
        scores = float_list(artifact["query_scores"], "query scores")
        positive = bool_list(
            artifact["native_positive"], "native positives"
        )
        if len(labels) != len(target):
            raise ValueError("Target and label axes differ")
        if any(len(mask) != len(labels) for mask in masks):
            raise ValueError("Query mask support differs from labels")
        if not (len(masks) == len(scores) == len(positive)):
            raise ValueError("Query axes differ")

        target_ids = sorted(
            {
                int(label)
                for take, label in zip(target, labels)
                if take and label >= 0
            }
        )
        peer_ids = sorted(
            {
                int(value)
                for value in manifest_row["same_class_peer_object_ids"]
            }
        )
        if not target_ids or not peer_ids:
            ineligible_expressions += 1
            continue

        dominant = [dominant_overlap(mask, labels) for mask in masks]
        peer_set = set(peer_ids)
        target_set = set(target_ids)
        candidate_queries = [
            query
            for query, dominant_id in enumerate(dominant)
            if dominant_id in target_set | peer_set
        ]
        features = [
            float_list(vector, FINAL_STAGE + " feature")
            for vector in as_list(artifact["features"][FINAL_STAGE])
        ]
        if len(features) != len(labels):
            raise ValueError("Feature support differs from labels")

        target_stats = prototype_stats(features, labels, target_ids)
        peer_stats = prototype_stats(features, labels, peer_ids)
        for query in candidate_queries:
            mask = masks[query]
            query_prototype = mean_selected(features, mask)
            if query_prototype is None:
                continue
            baseline = identity_from_stats(
                query_prototype, target_stats, peer_stats
            )
            if baseline is None:
                continue
            excluded = support_stats(
                features,
                labels,
                target_ids + peer_ids,
                mask,
            )
            identity = identity_at_floor(
                query_prototype,
                target_stats,
                peer_stats,
                excluded,
                FIXED_SUPPORT_FLOOR,
            )
            if identity is None:
                continue
            dominant_id = dominant[query]
            query_rows.append(
                {
                    "manifest_index": index,
                    "scene_id": str(manifest_row["scene_id"]),
                    "query": query,
                    "score": scores[query],
                    "iou": mask_iou(mask, target),
                    "native_positive": positive[query],
                    "truth": (
                        "target" if dominant_id in target_set else "peer"
                    ),
                    "identity": identity,
                }
            )

        metadata_by_index[index] = {
            "target_class": str(manifest_row["target_class"]),
            "peer_count": len(peer_ids),
        }

    pair_rows = make_floor_pair_rows(query_rows)
    return pair_rows, metadata_by_index, {
        "query_rows": len(query_rows),
        "ineligible_expressions": ineligible_expressions,
    }


def write_json(path, document):
    path = Path(path)
    if path.exists():
        raise ValueError("Output already exists: %s" % path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=True, sort_keys=True)
        + "\n",
        encoding="ascii",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    capture_path = Path(args.capture).resolve()
    manifest_path = Path(args.manifest).resolve()
    capture_sha256 = file_sha256(capture_path)
    if capture_sha256 != EXPECTED_CAPTURE_SHA256:
        raise ValueError("Capture hash differs from the frozen identity capture")
    manifest_sha256 = file_sha256(manifest_path)
    manifest = validate_manifest_hash(
        load_json(manifest_path),
        manifest_sha256,
        EXPECTED_MANIFEST_SHA256,
    )
    report = load_json(capture_path)
    if report.get("checkpoint_sha256") != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Capture checkpoint differs from M95")
    artifacts = load_artifacts(
        capture_path, report, EXPECTED_MANIFEST_SHA256
    )
    pair_rows, metadata_by_index, counts = extract_final_floor3_pairs(
        report, manifest, artifacts
    )
    result = sensitivity_summary(pair_rows, metadata_by_index)
    result.update(
        {
            "schema_version": 1,
            "contract": CONTRACT,
            "generated_at": datetime.now().astimezone().isoformat(),
            "scope": (
                "CPU-only class and peer-cardinality sensitivity audit of "
                "the frozen 256-expression M95 final-stage identity control."
            ),
            "source_capture": {
                "path": str(capture_path),
                "sha256": capture_sha256,
                "checkpoint_sha256": EXPECTED_CHECKPOINT_SHA256,
                "producer_sha256": report.get("producer_sha256"),
            },
            "manifest": {
                "path": str(manifest_path),
                "sha256": manifest_sha256,
                "rows": len(manifest),
            },
            "counts": counts,
            "admission": False,
            "native_backward_measured": False,
            "resources_measured": False,
            "not_evidence_of": [
                "admission",
                "native backward",
                "resource gate",
                "deployable efficacy",
                "population effect",
                "novelty",
                "whole-mechanism benefit",
            ],
        }
    )
    write_json(args.output, result)
    print(json.dumps(result["stability"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
