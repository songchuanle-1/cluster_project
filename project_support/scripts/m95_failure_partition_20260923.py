"""Post-capture descriptive audit. No training, capture, or admission."""
import argparse
import json
import math
import os
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    EXPECTED_MANIFEST_SHA256, STAGES, as_list, bool_list, cosine,
    file_sha256, float_list, int_list, mask_iou, mean_feature,
    paired_summary, score_pick, validate_artifact_header, validate_manifest_hash,
)

ANALYSIS_SHA256 = "1980ac6fe2731dd5cd3b03194e1529905562e4eeceaac04b96823f6de5da131f"
CAPTURE_SHA256 = "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
HELPER_SHA256 = "bd9615e401d4862d55e20c7bbc9b165f59ca9998ea94d5917d3481f7b181c6f6"


def identity(label, manifest):
    if label is None:
        return "no_instance"
    if str(label) == str(manifest["target_object_id"]):
        return "target_dominant"
    if str(label) in {str(x) for x in manifest["same_class_peer_object_ids"]}:
        return "same_class_peer"
    return "outside_target_and_registered_peers"


def validate_row(row, manifest):
    n = row["query_count"]
    if n <= 0 or any(len(row[key]) != n for key in (
        "scores", "ious", "native_positive", "fps_seed_inside_target", "dominant_instance"
    )):
        raise ValueError("Query axes differ")
    float_list(row["scores"], "scores")
    ious = float_list(row["ious"], "ious")
    if any(not 0 <= x <= 1 for x in ious):
        raise ValueError("IoU outside unit interval")
    bool_list(row["native_positive"], "positives")
    bool_list(row["fps_seed_inside_target"], "seeds")
    if (row["scene_id"], row["ann_id"], row["manifest_index"]) != (
        manifest["scene_id"], manifest["ann_id"], manifest["manifest_index"]
    ):
        raise ValueError("Expression differs from manifest")
    for query_key, allowed in (
        ("deployed_query", [True] * n),
        ("target_positive_query", row["native_positive"]),
        ("target_objectness_query", row["fps_seed_inside_target"]),
    ):
        if row[query_key] != score_pick(row["scores"], allowed):
            raise ValueError("Recorded selector differs")
    if not math.isclose(row["deployed_iou"], ious[row["deployed_query"]], abs_tol=1e-7):
        raise ValueError("Deployed IoU differs")


def row_audit(row, manifest):
    validate_row(row, manifest)
    scores, ious = row["scores"], row["ious"]
    positive = row["native_positive"]
    deployed = row["deployed_query"]
    acceptable = [q for q, value in enumerate(ious) if value > 0.5]
    acceptable_positive = [q for q in acceptable if positive[q]]
    best = score_pick(scores, [value > 0.5 for value in ious])
    if ious[deployed] > 0.5:
        partition = "deployed_success"
    elif not acceptable:
        partition = "no_acceptable_query"
    elif not any(positive):
        partition = "recoverable_no_native_positive"
    elif not acceptable_positive:
        partition = "recoverable_positive_set_excludes_acceptable"
    elif ious[row["target_positive_query"]] > 0.5:
        partition = "recoverable_positive_selector_repairs"
    else:
        partition = "recoverable_within_positive_score_failure"
    rank = None if best is None else 1 + sum(
        (scores[q], -q) > (scores[best], -best) for q in range(len(scores))
    )
    pos, seed = row["target_positive_query"], row["target_objectness_query"]
    result = {
        "manifest_index": row["manifest_index"], "scene_id": row["scene_id"],
        "ann_id": row["ann_id"], "stratum": row["stratum"],
        "partition": partition, "deployed_query": deployed,
        "deployed_iou": ious[deployed], "best_acceptable_query": best,
        "best_acceptable_score_rank": rank,
        "acceptable_queries": len(acceptable),
        "acceptable_native_positive_queries": len(acceptable_positive),
        "native_positive_queries": sum(positive),
        "deployed_native_positive": positive[deployed],
        "deployed_identity": identity(row["dominant_instance"][deployed], manifest),
        "positive_query": pos, "target_seed_query": seed,
        "common_support": pos is not None and seed is not None,
        "same_selected_query": None if pos is None or seed is None else pos == seed,
        "positive_set_equals_target_seed_set": positive == row["fps_seed_inside_target"],
        "pair": None,
    }
    pair = row["score_matched_pair"]
    if pair is not None:
        p, n = pair["positive_index"], pair["negative_index"]
        if p == n or not positive[p] or identity(row["dominant_instance"][n], manifest) != "same_class_peer":
            raise ValueError("Registered pair membership invalid")
        result["pair"] = {
            "positive_index": p, "negative_index": n,
            "positive_dominant_identity": identity(row["dominant_instance"][p], manifest),
            "negative_also_native_positive": positive[n],
            "positive_seed_inside_target": row["fps_seed_inside_target"][p],
            "negative_seed_inside_target": row["fps_seed_inside_target"][n],
            "positive_equals_positive_selector": p == pos,
            "positive_equals_target_seed_selector": p == seed,
        }
    return result


def mask_support(mask, target, labels, peer_ids):
    size = sum(mask)
    counts = Counter(label for label, take in zip(labels, mask) if take and label >= 0)
    return {
        "selected_superpoints": size, "known_instance_count": len(counts),
        "mixed_known_instance_support": len(counts) > 1,
        "target_fraction": None if not size else sum(a and b for a, b in zip(mask, target)) / size,
        "peer_fraction": None if not size else sum(
            take and str(label) in peer_ids for take, label in zip(mask, labels)
        ) / size,
        "unlabelled_fraction": None if not size else sum(
            take and label < 0 for take, label in zip(mask, labels)
        ) / size,
        "exactly_target_union": mask == target,
        "target_prototype_remaining_without_query": sum(t and not q for t, q in zip(target, mask)),
    }


def feature_audit(artifact, row, manifest, detail):
    validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)
    if artifact["manifest_index"] != row["manifest_index"]:
        raise ValueError("Artifact index differs")
    labels = int_list(artifact["physical_instance_labels"], "labels")
    target = bool_list(artifact["target_union"], "target")
    masks = [bool_list(m, "mask") for m in as_list(artifact["query_masks"])]
    scores = float_list(artifact["query_scores"], "scores")
    if len(masks) != row["query_count"] or len(target) != len(labels):
        raise ValueError("Artifact axes differ")
    if scores != row["scores"] or bool_list(artifact["native_positive"], "positive") != row["native_positive"]:
        raise ValueError("Artifact queries differ from analysis")
    if bool_list(artifact["fps_seed_inside_target"], "seed") != row["fps_seed_inside_target"]:
        raise ValueError("Artifact seed support differs")
    for q, mask in enumerate(masks):
        if len(mask) != len(labels) or not math.isclose(mask_iou(mask, target), row["ious"][q], abs_tol=1e-7):
            raise ValueError("Artifact mask differs from analysis")
    peers = {str(x) for x in manifest["same_class_peer_object_ids"]}
    peer_mask = [str(x) in peers for x in labels]
    selected = {
        "deployed": masks[detail["deployed_query"]],
        "acceptable": masks[detail["best_acceptable_query"]],
    }
    support = {name: mask_support(mask, target, labels, peers) for name, mask in selected.items()}
    stages = {}
    for stage in STAGES:
        if stage not in artifact["features"]:
            stages[stage] = {"missing": "stage_not_captured"}
            continue
        matrix = [float_list(v, "feature") for v in as_list(artifact["features"][stage])]
        if len(matrix) != len(labels):
            raise ValueError("Feature support differs")
        values = {}
        for name, mask in selected.items():
            query_proto = mean_feature(matrix, mask)
            for control, tm, pm in (
                ("overlapping", target, peer_mask),
                ("query_excluded", [t and not q for t, q in zip(target, mask)],
                 [p and not q for p, q in zip(peer_mask, mask)]),
            ):
                left = cosine(query_proto, mean_feature(matrix, tm))
                right = cosine(query_proto, mean_feature(matrix, pm))
                values[name + "_" + control + "_margin"] = (
                    None if left is None or right is None else left - right
                )
        for control in ("overlapping", "query_excluded"):
            a, d = values["acceptable_" + control + "_margin"], values["deployed_" + control + "_margin"]
            values[control + "_acceptable_minus_deployed"] = None if a is None or d is None else a - d
        stages[stage] = values
    return {"support": support, "stages": stages}


def summarize(details):
    recoverable = [r for r in details if r["partition"].startswith("recoverable_")]
    common = [r for r in details if r["common_support"]]
    pairs = [r["pair"] for r in details if r["pair"] is not None]
    feature_rows = [r for r in recoverable if "features" in r]
    stages = {}
    for stage in STAGES:
        stages[stage] = {}
        for control in ("overlapping", "query_excluded"):
            key = control + "_acceptable_minus_deployed"
            rows = [
                {"scene_id": r["scene_id"], key: r["features"]["stages"][stage].get(key)}
                for r in feature_rows
            ]
            stages[stage][control] = paired_summary(rows, key)
            stages[stage][control]["missing_of_recoverable"] = len(recoverable) - stages[stage][control]["available"]
    return {
        "expressions": len(details), "scenes": len({r["scene_id"] for r in details}),
        "partitions": dict(Counter(r["partition"] for r in details)),
        "recoverable_identity": dict(Counter(r["deployed_identity"] for r in recoverable)),
        "no_acceptable_identity": dict(Counter(r["deployed_identity"] for r in details if r["partition"] == "no_acceptable_query")),
        "recoverable_best_acceptable_rank": dict(sorted(Counter(r["best_acceptable_score_rank"] for r in recoverable).items())),
        "common_support": {
            "rows": len(common), "same_selected_query": sum(r["same_selected_query"] for r in common),
            "different_selected_query": sum(not r["same_selected_query"] for r in common),
            "identical_eligibility_sets": sum(r["positive_set_equals_target_seed_set"] for r in common),
        },
        "registered_pairs": {
            "rows": len(pairs),
            "positive_dominant_identity": dict(Counter(p["positive_dominant_identity"] for p in pairs)),
            **{key: sum(p[key] for p in pairs) for key in (
                "negative_also_native_positive", "positive_seed_inside_target",
                "negative_seed_inside_target", "positive_equals_positive_selector",
                "positive_equals_target_seed_selector",
            )},
        },
        "features": {
            "rows": len(feature_rows),
            "deployed_mixed_known_instances": sum(r["features"]["support"]["deployed"]["mixed_known_instance_support"] for r in feature_rows),
            "acceptable_exactly_target_union": sum(r["features"]["support"]["acceptable"]["exactly_target_union"] for r in feature_rows),
            "stages": stages,
        },
    }


def checked_json(path, expected):
    if file_sha256(path) != expected:
        raise ValueError("Evidence hash mismatch: " + str(path))
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name == "nt" or os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("Native audit requires authorized server CPU with CUDA hidden")
    helper = Path(__file__).with_name("analyze_m95_manifest_identity_controls_20260922.py")
    if file_sha256(helper) != HELPER_SHA256:
        raise ValueError("Frozen helper changed")
    analysis = checked_json(args.analysis, ANALYSIS_SHA256)
    manifest_doc = checked_json(args.manifest, EXPECTED_MANIFEST_SHA256)
    manifest = validate_manifest_hash(manifest_doc, EXPECTED_MANIFEST_SHA256, EXPECTED_MANIFEST_SHA256)
    capture = checked_json(args.capture, CAPTURE_SHA256)
    if analysis["contract"] != "m95_manifest_identity_control_analysis_v1" or len(analysis["rows"]) != 256:
        raise ValueError("Unexpected analysis contract or row count")
    details = [row_audit(row, manifest[row["manifest_index"]]) for row in analysis["rows"]]
    by_index = {r["manifest_index"]: r for r in analysis["rows"]}
    if len(by_index) != 256 or set(by_index) != set(manifest):
        raise ValueError("Analysis coverage differs")
    needed = {r["manifest_index"]: r for r in details if r["partition"].startswith("recoverable_")}
    import torch
    torch.set_num_threads(1)
    seen = set()
    shard_evidence = []
    for item in capture["feature_artifacts"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Shard path escapes capture")
        path = Path(args.capture).parent / relative
        if file_sha256(path) != item["sha256"]:
            raise ValueError("Shard hash mismatch")
        entries = torch.load(path, map_location="cpu", weights_only=True)
        if len(entries) != item["rows"]:
            raise ValueError("Shard row count differs")
        for artifact in entries:
            index = artifact["manifest_index"]
            if index in seen or index not in manifest:
                raise ValueError("Duplicate or unexpected artifact index")
            seen.add(index)
            if index in needed:
                needed[index]["features"] = feature_audit(artifact, by_index[index], manifest[index], needed[index])
        shard_evidence.append({"path": str(path), "sha256": item["sha256"]})
    if seen != set(manifest) or any("features" not in r for r in needed.values()):
        raise ValueError("Incomplete feature coverage")
    result = {
        "contract": "m95_failure_partition_descriptive_v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(), "cpu_only": True, "admission": False,
        "source": [
            {"path": str(path), "sha256": digest} for path, digest in (
                (args.analysis, ANALYSIS_SHA256), (args.manifest, EXPECTED_MANIFEST_SHA256),
                (args.capture, CAPTURE_SHA256), (helper, HELPER_SHA256),
                (__file__, file_sha256(__file__)),
            )
        ],
        "feature_shards": shard_evidence, "summary": summarize(details), "rows": details,
        "limitations": [
            "Post-capture descriptive TRAIN subset; not a new registered endpoint or population estimate.",
            "Recoverable failures and acceptable queries are selected by observed target IoU.",
            "Highest-score acceptable query is an oracle, not deployable selection.",
            "Outside registered peers is an ID category, not verified cross-class semantics.",
            "Mixed support counts multiple nonnegative instance labels, independently of dominant identity.",
            "Margins use superpoint-unweighted means and target-informed prototypes.",
            "Query-excluded prototypes differ between query masks and can be empty; not a causal control.",
            "No class-unique peer prototype exists; missing values are not zero.",
            "Stage contrasts do not establish causal identity destruction, novelty or candidate efficacy.",
        ],
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
