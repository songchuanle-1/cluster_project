"""Exact-mask label audit and saved joint-support transitions, CPU only."""
import argparse
import hashlib
import json
import math
import os
import socket
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    as_list, bool_list, dominant_overlap, file_sha256, float_list, int_list,
    mask_iou, paired_summary, validate_artifact_header, validate_manifest_hash,
)
from m95_failure_partition_20260923 import (
    ANALYSIS_SHA256, CAPTURE_SHA256, EXPECTED_MANIFEST_SHA256, HELPER_SHA256,
    checked_json, identity, validate_row,
)
from m95_failure_followup_20260923 import PARTITION_SHA256, keyed

JOINT_SHA256 = "8e3a543a9064f9bdf394bef4e71ff7fe70d2b637e132381ca26f0b0999f14614"


def equivalence(masks, positive, seeds, labels, target, manifest):
    masks = [bool_list(m, "mask") for m in as_list(masks)]
    positive = bool_list(positive, "positive")
    seeds = int_list(seeds, "seed")
    labels = int_list(labels, "physical labels")
    target = bool_list(target, "target")
    if not masks or not labels or len(target) != len(labels):
        raise ValueError("Empty or incompatible physical axes")
    if len(masks) != len(positive) or len(seeds) != len(masks):
        raise ValueError("Query axes differ")
    if any(len(m) != len(labels) for m in masks):
        raise ValueError("Mask axes differ")
    if any(s < 0 or s >= len(labels) for s in seeds):
        raise ValueError("Seed outside physical axis")
    if target != [str(v) == str(manifest["target_object_id"]) for v in labels]:
        raise ValueError("Target and physical IDs differ")
    groups = defaultdict(list)
    for q, mask in enumerate(masks):
        groups[tuple(mask)].append(q)
    classes = []
    for mask, queries in groups.items():
        positives = sum(positive[q] for q in queries)
        dominant = dominant_overlap(mask, labels)
        classes.append({
            "query_indices": queries, "query_count": len(queries),
            "mask_sha256": hashlib.sha256(bytes(mask)).hexdigest(),
            "mask_size": sum(mask), "empty_mask": not any(mask),
            "native_positive_queries": positives,
            "label_discordant": 0 < positives < len(queries),
            "seed_indices": [seeds[q] for q in queries],
            "distinct_seed_count": len({seeds[q] for q in queries}),
            "seed_inside_target_count": sum(target[seeds[q]] for q in queries),
            "seed_target_discordant": len({target[seeds[q]] for q in queries}) > 1,
            "dominant_physical_id": dominant, "identity": identity(dominant, manifest),
            "target_iou": mask_iou(mask, target),
            "acceptable": mask_iou(mask, target) > 0.5,
        })
    return {
        "manifest_index": manifest["manifest_index"], "scene_id": manifest["scene_id"],
        "query_count": len(masks), "unique_mask_count": len(classes),
        "duplicate_classes": sum(c["query_count"] > 1 for c in classes),
        "discordant_classes": sum(c["label_discordant"] for c in classes),
        "classes": classes,
    }


def summarize_equivalence(rows):
    classes = [(r["scene_id"], c) for r in rows for c in r["classes"]]
    result = {
        "expressions": len(rows), "scenes": len({r["scene_id"] for r in rows}),
        "query_count": sum(r["query_count"] for r in rows),
        "unique_mask_count": len(classes),
        "duplicate_class_count": sum(c["query_count"] > 1 for _, c in classes),
        "queries_in_duplicate_classes": sum(c["query_count"] for _, c in classes if c["query_count"] > 1),
        "discordant_class_count": sum(c["label_discordant"] for _, c in classes),
        "queries_in_discordant_classes": sum(c["query_count"] for _, c in classes if c["label_discordant"]),
        "discordant_scenes": len({s for s, c in classes if c["label_discordant"]}),
        "empty_mask_classes": sum(c["empty_mask"] for _, c in classes),
        "duplicate_classes_distinct_seeds": sum(c["distinct_seed_count"] > 1 for _, c in classes),
        "by_identity": {},
    }
    for name in sorted({c["identity"] for _, c in classes}):
        subset = [(s, c) for s, c in classes if c["identity"] == name]
        result["by_identity"][name] = {
            "classes": len(subset), "queries": sum(c["query_count"] for _, c in subset),
            "scenes": len({s for s, _ in subset}),
            "duplicate_classes": sum(c["query_count"] > 1 for _, c in subset),
            "discordant_classes": sum(c["label_discordant"] for _, c in subset),
            "discordant_scenes": len({s for s, c in subset if c["label_discordant"]}),
            "acceptable_classes": sum(c["acceptable"] for _, c in subset),
            "acceptable_discordant_classes": sum(c["acceptable"] and c["label_discordant"] for _, c in subset),
        }
    return result


def sign(value):
    if not isinstance(value, (float, int)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("Invalid margin")
    return "positive" if value > 0 else "negative" if value < 0 else "zero"


def transitions(rows, draws=10000):
    keyed(rows)
    complete, missing = [], []
    stages = ("raw_3d", "fused", "final")
    for row in rows:
        if any(row["stages"][s].get("contrast") is None for s in stages):
            missing.append(row["manifest_index"])
            continue
        record = {"manifest_index": row["manifest_index"], "scene_id": row["scene_id"],
                  "margins": {}, "signs": {}, "changes": {}}
        for query in ("deployed", "acceptable"):
            margins = {s: row["stages"][s][query] for s in stages}
            record["margins"][query] = margins
            record["signs"][query] = {s: sign(margins[s]) for s in stages}
            for left, right in (("raw_3d", "fused"), ("fused", "final"), ("raw_3d", "final")):
                record["changes"][query + "_" + left + "_to_" + right] = margins[right] - margins[left]
        complete.append(record)
    summaries, counts = {}, {}
    for query in ("deployed", "acceptable"):
        counts[query] = {
            s: dict(Counter(r["signs"][query][s] for r in complete)) for s in stages
        }
        for left, right in (("raw_3d", "fused"), ("fused", "final"), ("raw_3d", "final")):
            key = query + "_" + left + "_to_" + right
            summaries[key] = {
                **paired_summary([{"scene_id": r["scene_id"], "change": r["changes"][key]}
                                  for r in complete], "change", draws=draws),
                "sign_transitions": dict(Counter(
                    r["signs"][query][left] + "_to_" + r["signs"][query][right] for r in complete)),
            }
    return {
        "expressions": len(rows), "available": len(complete),
        "scenes": len({r["scene_id"] for r in complete}), "missing_indices": missing,
        "sign_counts": counts, "paired_changes": summaries, "rows": complete,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("analysis", "partition", "capture", "manifest", "joint", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if os.name == "nt" or socket.gethostname() != "das" or os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("Native analysis restricted to verified server-6 CPU")
    helper = Path(__file__).with_name("analyze_m95_manifest_identity_controls_20260922.py")
    if file_sha256(helper) != HELPER_SHA256:
        raise ValueError("Frozen helper changed")
    analysis_doc = checked_json(args.analysis, ANALYSIS_SHA256)
    partition = checked_json(args.partition, PARTITION_SHA256)
    capture = checked_json(args.capture, CAPTURE_SHA256)
    manifest_doc = checked_json(args.manifest, EXPECTED_MANIFEST_SHA256)
    joint = checked_json(args.joint, JOINT_SHA256)
    manifest = validate_manifest_hash(manifest_doc, EXPECTED_MANIFEST_SHA256, EXPECTED_MANIFEST_SHA256)
    analysis, details = keyed(analysis_doc["rows"]), keyed(partition["rows"])
    capture_rows = keyed(capture["rows"])
    if set(analysis) != set(manifest) or set(details) != set(manifest) or set(capture_rows) != set(manifest):
        raise ValueError("Frozen coverage differs")
    needed = {i for i, r in details.items() if r["partition"].startswith("recoverable_")}
    if len(needed) != 40 or set(keyed(joint["rows"])) != needed:
        raise ValueError("Frozen failure cohort differs")
    import torch
    torch.set_num_threads(1)
    seen, rows, shard_refs = set(), [], []
    for item in capture["feature_artifacts"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Shard escapes capture")
        path = Path(args.capture).parent / relative
        if file_sha256(path) != item["sha256"]:
            raise ValueError("Shard hash differs")
        entries = torch.load(path, map_location="cpu", weights_only=True)
        if len(entries) != item["rows"]:
            raise ValueError("Shard row count differs")
        shard_refs.append({"path": str(path), "sha256": item["sha256"]})
        for artifact in entries:
            validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)
            i = artifact["manifest_index"]
            if i in seen or i not in manifest:
                raise ValueError("Duplicate or unexpected artifact")
            seen.add(i)
            if i not in needed:
                continue
            a, m, c = analysis[i], manifest[i], capture_rows[i]
            validate_row(a, m)
            labels = int_list(artifact["physical_instance_labels"], "labels")
            target = bool_list(artifact["target_union"], "target")
            masks = [bool_list(x, "mask") for x in as_list(artifact["query_masks"])]
            positive = bool_list(artifact["native_positive"], "positives")
            fps = int_list(c["fps_superpoints"], "FPS")
            sampled = int_list(c["sampled_seed_indices"], "sample indices")
            if any(s < 0 or s >= len(fps) for s in sampled):
                raise ValueError("Sample index out of bounds")
            seeds = [fps[s] for s in sampled]
            record = equivalence(masks, positive, seeds, labels, target, m)
            scores = float_list(artifact["query_scores"], "scores")
            if scores != a["scores"] or positive != a["native_positive"]:
                raise ValueError("Query values differ")
            inside = bool_list(artifact["fps_seed_inside_target"], "seed support")
            if inside != a["fps_seed_inside_target"] or inside != [target[s] for s in seeds]:
                raise ValueError("Seed physical binding differs")
            original = int_list(artifact["axis"]["original_superpoint_ids"], "physical axis")
            if len(original) != len(labels) or len(set(original)) != len(original):
                raise ValueError("Physical axis invalid")
            for q, mask in enumerate(masks):
                if not math.isclose(mask_iou(mask, target), a["ious"][q], abs_tol=1e-7):
                    raise ValueError("Frozen IoU differs")
                if dominant_overlap(mask, labels) != a["dominant_instance"][q]:
                    raise ValueError("Frozen identity differs")
            for group in record["classes"]:
                group["seed_original_superpoint_ids"] = [original[s] for s in group["seed_indices"]]
            record["partition"] = details[i]["partition"]
            rows.append(record)
    if seen != set(manifest) or {r["manifest_index"] for r in rows} != needed:
        raise ValueError("Incomplete capture coverage")
    stage_report = transitions(joint["rows"])
    if stage_report["available"] != 16 or stage_report["scenes"] != 16:
        raise ValueError("Joint support denominator changed")
    result = {
        "contract": "m95_exact_mask_equivalence_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(), "cpu_only": True, "admission": False,
        "native_backward_executed": False, "model_forward_executed": False,
        "rows": sorted(rows, key=lambda r: r["manifest_index"]),
        "summary": summarize_equivalence(rows), "stage_transitions": stage_report,
        "feature_shards": shard_refs,
        "evidence": [{"path": str(p), "sha256": file_sha256(p)}
                     for p in (args.analysis, args.partition, args.capture, args.manifest,
                               args.joint, helper, __file__)],
        "limitations": [
            "Forty TRAIN outcome-selected failures, not population or held-out evidence.",
            "Exact boolean masks only; identical thresholded masks need not share logits or query states.",
            "Mask classes are expression-local; physical axes are not pooled across scenes.",
            "Positive-label discordance is descriptive, not an erroneous-label or causal-gradient claim.",
            "Outside registered peers does not imply verified cross-class; object8 remains unknown.",
            "Stage cosine margins inhabit different feature spaces; paired changes are not causal damage.",
            "Joint-support complete cases exclude 24 failures and need not be representative.",
            "No deduplication, selector, weighting, ranking, modality-loss variant or admission.",
        ],
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"summary": result["summary"],
                      "stage_signs": stage_report["sign_counts"],
                      "paired_changes": stage_report["paired_changes"]}, indent=2))


if __name__ == "__main__":
    main()
