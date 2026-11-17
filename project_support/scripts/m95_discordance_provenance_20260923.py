"""Saved-capture logit and native-label provenance audit; CPU only."""
import argparse
import hashlib
import json
import math
import os
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    as_list, bool_list, file_sha256, float_list, int_list, paired_summary,
    validate_artifact_header,
)
from m95_failure_partition_20260923 import EXPECTED_MANIFEST_SHA256

EQUIVALENCE_SHA256 = "6a219bd48f5cc28bd56e437280fc6336e9834253c8d9fa6848502e8ab66b6790"
CAPTURE_SHA256 = "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
CRITERION_SHA256 = "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"


def audit_class(group, artifact, capture_row):
    indices = int_list(group["query_indices"], "query indices")
    logits = [float_list(x, "mask logits") for x in as_list(artifact["query_mask_logits"])]
    masks = [bool_list(x, "binary mask") for x in as_list(artifact["query_masks"])]
    scores = float_list(artifact["query_scores"], "indicator scores")
    positive = bool_list(artifact["native_positive"], "native positives")
    target = bool_list(artifact["target_union"], "target union")
    fps = int_list(capture_row["fps_superpoints"], "FPS")
    samples = int_list(capture_row["sampled_seed_indices"], "sampled seeds")
    original = int_list(artifact["axis"]["original_superpoint_ids"], "original IDs")
    labels = int_list(artifact["physical_instance_labels"], "physical labels")
    if len(logits) != len(masks) or len(logits) != len(scores) or len(logits) != len(positive):
        raise ValueError("Query axes differ")
    if len(samples) != len(logits) or len(target) != len(labels) or len(original) != len(labels):
        raise ValueError("Physical axes differ")
    if len(set(indices)) != len(indices) or len(indices) < 2 or any(q < 0 or q >= len(logits) for q in indices):
        raise ValueError("Invalid discordant class indices")
    if any(len(logits[q]) != len(target) or len(masks[q]) != len(target) for q in indices):
        raise ValueError("Logit physical axis differs")
    if any(not math.isfinite(v) for q in indices for v in logits[q]):
        raise ValueError("Nonfinite logits")
    if any([v > 0 for v in logits[q]] != masks[q] for q in indices):
        raise ValueError("Captured logit threshold differs")
    if len({tuple(masks[q]) for q in indices}) != 1:
        raise ValueError("Class masks differ")
    if sum(positive[q] for q in indices) != group["native_positive_queries"]:
        raise ValueError("Class label count differs")
    seeds = []
    for q in indices:
        if samples[q] < 0 or samples[q] >= len(fps) or fps[samples[q]] < 0 or fps[samples[q]] >= len(target):
            raise ValueError("Seed index invalid")
        s = fps[samples[q]]
        seeds.append(s)
    if seeds != group["seed_indices"] or [original[s] for s in seeds] != group["seed_original_superpoint_ids"]:
        raise ValueError("Seed binding differs")
    inside = [target[s] for s in seeds]
    if sum(inside) != group["seed_inside_target_count"]:
        raise ValueError("Seed membership differs")
    pairs = [(p, n) for p in indices if positive[p] for n in indices if not positive[n]]
    if not pairs:
        raise ValueError("Not a discordant class")
    differences = [
        [abs(a - b) for a, b in zip(logits[p], logits[n])]
        for p, n in pairs
    ]
    score_differences = [scores[p] - scores[n] for p, n in pairs]
    return {
        "manifest_index": artifact["manifest_index"],
        "mask_sha256": group["mask_sha256"],
        "query_indices": indices,
        "identity": group["identity"],
        "dominant_physical_id": group["dominant_physical_id"],
        "acceptable": group["acceptable"],
        "target_iou": group["target_iou"],
        "query_count": len(indices),
        "positive_count": sum(positive[q] for q in indices),
        "cross_label_pair_count": len(pairs),
        "max_abs_logit_difference": max(max(d) for d in differences),
        "mean_abs_logit_difference": sum(sum(d) / len(d) for d in differences) / len(differences),
        "all_cross_label_logits_equal": all(all(x == 0 for x in d) for d in differences),
        "mean_positive_minus_negative_score": sum(score_differences) / len(score_differences),
        "max_abs_score_difference": max(abs(v) for v in score_differences),
        "positive_seed_inside_count": sum(target[fps[samples[q]]] for q in indices if positive[q]),
        "negative_seed_inside_count": sum(target[fps[samples[q]]] for q in indices if not positive[q]),
        "positive_outside_seed_count": sum(not target[fps[samples[q]]] for q in indices if positive[q]),
        "negative_inside_seed_count": sum(target[fps[samples[q]]] for q in indices if not positive[q]),
        "seed_membership_equals_label": all(inside[j] == positive[q] for j, q in enumerate(indices)),
        "seeds": [
            {"query": q, "positive": positive[q], "score": scores[q],
             "physical_seed_index": s, "original_superpoint_id": original[s],
             "seed_physical_id": labels[s], "inside_target": target[s]}
            for q, s in zip(indices, seeds)
        ],
    }


def summarize(rows, cohort):
    subset = [r for r in rows if cohort == "all" or r["acceptable"]]
    if not subset:
        raise ValueError("Empty cohort")
    metrics = {}
    for name, fn in (
        ("logits_differ", lambda r: int(not r["all_cross_label_logits_equal"])),
        ("seed_membership_equals_label", lambda r: int(r["seed_membership_equals_label"])),
        ("positive_outside_seed", lambda r: int(r["positive_outside_seed_count"] > 0)),
        ("negative_inside_seed", lambda r: int(r["negative_inside_seed_count"] > 0)),
    ):
        values = [{"scene_id": r["scene_id"], "value": fn(r)} for r in subset]
        metrics[name] = {
            "classes": sum(x["value"] for x in values),
            "scene_bootstrap": paired_summary(values, "value", draws=10000),
        }
    return {
        "classes": len(subset), "scenes": len({r["scene_id"] for r in subset}),
        "queries": sum(r["query_count"] for r in subset),
        "by_identity": dict(Counter(r["identity"] for r in subset)),
        "max_abs_logit_difference": max(r["max_abs_logit_difference"] for r in subset),
        "metrics": metrics,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("equivalence", "capture", "criterion", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if os.name == "nt" or socket.gethostname() != "das" or os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("Restricted to server-6 CPU")
    if file_sha256(args.equivalence) != EQUIVALENCE_SHA256 or file_sha256(args.capture) != CAPTURE_SHA256:
        raise ValueError("Frozen source changed")
    equivalence = json.loads(Path(args.equivalence).read_text(encoding="utf-8"))
    capture = json.loads(Path(args.capture).read_text(encoding="utf-8"))
    if equivalence["summary"]["discordant_class_count"] != 32 or equivalence["summary"]["expressions"] != 40:
        raise ValueError("Frozen cohort changed")
    capture_rows = {r["manifest_index"]: r for r in capture["rows"]}
    needed = {
        r["manifest_index"]: r for r in equivalence["rows"]
        if r["discordant_classes"]
    }
    import torch
    torch.set_num_threads(1)
    seen, rows = set(), []
    for shard in equivalence["feature_shards"]:
        path = Path(shard["path"])
        if not path.is_relative_to(Path(args.capture).parent) or file_sha256(path) != shard["sha256"]:
            raise ValueError("Shard path/hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=True):
            validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)
            i = artifact["manifest_index"]
            if i not in needed:
                continue
            if i in seen:
                raise ValueError("Duplicate expression")
            seen.add(i)
            source = needed[i]
            for group in source["classes"]:
                if group["label_discordant"]:
                    row = audit_class(group, artifact, capture_rows[i])
                    row["scene_id"] = source["scene_id"]
                    rows.append(row)
    if seen != set(needed) or len(rows) != 32 or sum(r["acceptable"] for r in rows) != 23:
        raise ValueError("Discordant class coverage differs")
    if file_sha256(args.criterion) != CRITERION_SHA256:
        raise ValueError("Frozen criterion differs")
    source = Path(args.criterion).read_text(encoding="utf-8")
    required = ("def match_sampled_ins(", "torch.cdist(sampled_pos, obj_pos",
                "sampled_ins_lbl==obj_id", "def loss_indi(", "target_mask[src_idx] = pos_mask")
    if any(fragment not in source for fragment in required):
        raise ValueError("Native criterion positive rule changed")
    result = {
        "contract": "m95_saved_discordance_provenance_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(), "cpu_only": True, "admission": False,
        "native_backward_executed": False, "model_forward_executed": False,
        "criterion_rule": (
            "Matched queries comprise nearest sampled query per GT and additional "
            "queries whose sampled instance ID equals a GT object ID; loss_indi "
            "marks matched indices positive. A positive outside target seed can "
            "arise from nearest assignment; this capture lacks per-query cause tags."
        ),
        "summary": {"all": summarize(rows, "all"), "acceptable": summarize(rows, "acceptable")},
        "rows": sorted(rows, key=lambda r: (r["manifest_index"], r["mask_sha256"])),
        "evidence": [
            {"path": p, "sha256": file_sha256(p)}
            for p in (args.equivalence, args.capture, args.criterion, __file__)
        ],
        "limitations": [
            "40 outcome-selected TRAIN failures; 32 classes, not a population effect.",
            "Equal thresholded masks do not entail equal logits or decoder query states.",
            "Saved positives identify matching membership, not nearest-vs-instance cause.",
            "Outside registered peers is not a validated cross-class annotation.",
            "No native backward, resource gate, mechanism admission or training.",
        ],
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
