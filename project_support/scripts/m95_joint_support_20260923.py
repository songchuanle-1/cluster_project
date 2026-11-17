"""Shared disjoint prototype feasibility on frozen TRAIN failures, CPU only."""
import argparse
import json
import os
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    STAGES, as_list, bool_list, cosine, file_sha256, float_list, int_list,
    mean_feature, paired_summary, validate_artifact_header, validate_manifest_hash,
)
from m95_failure_partition_20260923 import (
    ANALYSIS_SHA256, CAPTURE_SHA256, EXPECTED_MANIFEST_SHA256, HELPER_SHA256,
    checked_json, feature_audit,
)
from m95_failure_followup_20260923 import PARTITION_SHA256, keyed


def shared_support(target, peer, deployed, acceptable):
    masks = [bool_list(x, "support mask") for x in (target, peer, deployed, acceptable)]
    if not masks[0] or len({len(x) for x in masks}) != 1:
        raise ValueError("Support axes differ or are empty")
    target, peer, deployed, acceptable = masks
    if any(t and p for t, p in zip(target, peer)):
        raise ValueError("Target and peer supports overlap")
    union = [a or d for a, d in zip(acceptable, deployed)]
    remainder = {
        "target": [t and not u for t, u in zip(target, union)],
        "peer": [p and not u for p, u in zip(peer, union)],
    }
    counts = {}
    reasons = []
    for name, original in (("target", target), ("peer", peer)):
        counts[name + "_total"] = sum(original)
        counts[name + "_remaining"] = sum(remainder[name])
        counts[name + "_removed"] = sum(original) - sum(remainder[name])
        if not any(original):
            reasons.append(name + "_absent")
        elif not any(remainder[name]):
            reasons.append(name + "_exhausted_by_union")
    for name, mask in (("deployed", deployed), ("acceptable", acceptable)):
        counts[name + "_size"] = sum(mask)
        if not any(mask):
            reasons.append(name + "_empty")
    counts["union_size"] = sum(union)
    return remainder, counts, reasons


def shared_margin(matrix, target, peer, deployed, acceptable):
    remainder, counts, reasons = shared_support(target, peer, deployed, acceptable)
    matrix = [float_list(v, "feature") for v in as_list(matrix)]
    if len(matrix) != len(target) or not matrix[0] or len({len(v) for v in matrix}) != 1:
        raise ValueError("Feature axes differ")
    if reasons:
        return {"counts": counts, "missing_reasons": reasons, "contrast": None}
    prototypes = {
        "target": mean_feature(matrix, remainder["target"]),
        "peer": mean_feature(matrix, remainder["peer"]),
        "deployed": mean_feature(matrix, deployed),
        "acceptable": mean_feature(matrix, acceptable),
    }
    zero_norm = [name + "_zero_norm" for name, vector in prototypes.items()
                 if not any(value != 0 for value in vector)]
    if zero_norm:
        return {"counts": counts, "missing_reasons": zero_norm, "contrast": None}
    margins = {
        name: cosine(prototypes[name], prototypes["target"])
        - cosine(prototypes[name], prototypes["peer"])
        for name in ("deployed", "acceptable")
    }
    return {
        "counts": counts, "missing_reasons": [], **margins,
        "contrast": margins["acceptable"] - margins["deployed"],
    }


def resolve_object(annotations, graphs, scene, wrong_id, target_id, ann_id, labels):
    wrong_id, target_id = str(wrong_id), str(target_id)
    own = [r for r in annotations if r["scene_id"] == scene and int(r["ann_id"]) == ann_id]
    if len(own) != 1 or str(own[0]["object_id"]) != target_id:
        raise ValueError("Target annotation ID does not align")
    if int(wrong_id) not in labels or int(target_id) not in labels:
        raise ValueError("Object ID missing from physical shard labels")
    wrong_annotations = [r for r in annotations if r["scene_id"] == scene
                         and str(r["object_id"]) == wrong_id]
    aligned = []
    for row in wrong_annotations:
        nodes = graphs.get(scene, {}).get(str(row["ann_id"]), {}).get("graph_node", [])
        if nodes:
            aligned.append({"ann_id": row["ann_id"], "object_id": wrong_id,
                            "object_name": row["object_name"],
                            "lemma_head": nodes[0].get("lemma_head")})
    return {
        "scene_id": scene, "wrong_object_id": wrong_id, "target_object_id": target_id,
        "target_ann_id": ann_id, "physical_id_alignment_verified": True,
        "wrong_physical_superpoints": labels.count(int(wrong_id)),
        "target_physical_superpoints": labels.count(int(target_id)),
        "wrong_annotation_count": len(wrong_annotations), "aligned_graph_records": aligned,
        "status": "annotation_graph_aligned" if aligned else "unknown_no_object_aligned_graph",
        "node_id_is_not_physical_object_id": True,
        "ontology_class_verified": False,
    }


def summarize(rows, draws=10000):
    result = {
        "expressions": len(rows), "scenes": len({r["scene_id"] for r in rows}),
        "support_feasible": sum(not r["structural_missing_reasons"] for r in rows),
        "structural_missing_counts": dict(Counter(
            reason for r in rows for reason in r["structural_missing_reasons"])),
        "structural_missing_combinations": dict(Counter(
            "|".join(r["structural_missing_reasons"]) or "complete" for r in rows)),
        "stages": {},
    }
    result["support_feasible_scenes"] = len({
        r["scene_id"] for r in rows if not r["structural_missing_reasons"]})
    for stage in STAGES:
        values = [{"scene_id": r["scene_id"], "contrast": r["stages"][stage]["contrast"]}
                  for r in rows]
        result["stages"][stage] = {
            **paired_summary(values, "contrast", draws=draws),
            "missing_indices": [r["manifest_index"] for r in rows
                                if r["stages"][stage]["contrast"] is None],
            "missing_reasons": dict(Counter(
                reason for r in rows for reason in r["stages"][stage]["missing_reasons"])),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    for name in ("analysis", "partition", "capture", "manifest", "output"):
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
    manifest = validate_manifest_hash(manifest_doc, EXPECTED_MANIFEST_SHA256, EXPECTED_MANIFEST_SHA256)
    analysis, details = keyed(analysis_doc["rows"]), keyed(partition["rows"])
    if set(analysis) != set(manifest) or set(details) != set(manifest):
        raise ValueError("Frozen coverage differs")
    needed = {i for i, r in details.items() if r["partition"].startswith("recoverable_")}
    if len(needed) != 40:
        raise ValueError("Expected 40 frozen recoverable failures")
    import torch
    torch.set_num_threads(1)
    seen, rows, shard_refs, semantic_labels = set(), [], [], None
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
            a, d, m = analysis[i], details[i], manifest[i]
            # Reuse the frozen axis and IoU validator before the new estimand.
            existing = feature_audit(artifact, a, m, d)
            if existing != d["features"]:
                raise ValueError("Frozen feature calculation differs")
            labels = int_list(artifact["physical_instance_labels"], "labels")
            target = bool_list(artifact["target_union"], "target")
            if target != [str(label) == str(m["target_object_id"]) for label in labels]:
                raise ValueError("Physical target ID and union differ")
            peer_ids = {str(x) for x in m["same_class_peer_object_ids"]}
            peer = [str(label) in peer_ids for label in labels]
            masks = as_list(artifact["query_masks"])
            deployed = bool_list(masks[d["deployed_query"]], "deployed")
            acceptable = bool_list(masks[d["best_acceptable_query"]], "acceptable")
            _, counts, reasons = shared_support(target, peer, deployed, acceptable)
            stages = {}
            for stage in STAGES:
                if stage not in artifact["features"]:
                    stages[stage] = {"contrast": None, "missing_reasons": ["stage_not_captured"]}
                else:
                    stages[stage] = shared_margin(
                        artifact["features"][stage], target, peer, deployed, acceptable)
            rows.append({
                "manifest_index": i, "scene_id": m["scene_id"], "partition": d["partition"],
                "deployed_query": d["deployed_query"], "acceptable_query": d["best_acceptable_query"],
                "counts": counts, "structural_missing_reasons": reasons, "stages": stages,
            })
            if i == 19:
                if m["scene_id"] != "scene0245_00" or a["dominant_instance"][d["deployed_query"]] != 8:
                    raise ValueError("Unresolved semantic query changed")
                semantic_labels = labels
    if seen != set(manifest) or {r["manifest_index"] for r in rows} != needed:
        raise ValueError("Incomplete capture coverage")
    sources = manifest_doc["native_sources"]
    annotations = checked_json(sources["ScanRefer_train_new.json"]["path"],
                               sources["ScanRefer_train_new.json"]["sha256"])
    graphs = checked_json(sources["scene_graphs_new_train.json"]["path"],
                          sources["scene_graphs_new_train.json"]["sha256"])
    semantics = resolve_object(annotations, graphs, "scene0245_00", "8", "18", 55, semantic_labels)
    result = {
        "contract": "m95_joint_support_v1", "generated_at": datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(), "cpu_only": True, "admission": False,
        "model_forward_executed": False, "native_backward_executed": False,
        "contract_definition": {
            "union": "U = deployed_mask OR highest-score acceptable_mask",
            "shared_target": "T_shared = target_union AND NOT U",
            "shared_peer": "P_shared = registered_peer_union AND NOT U",
            "margin": "cos(mean(query),mean(T_shared))-cos(mean(query),mean(P_shared))",
            "contrast": "acceptable margin - deployed margin, using IDENTICAL prototypes",
            "rejection": "Empty support, missing stage, or zero-norm prototype => missing, never zero",
        },
        "rows": sorted(rows, key=lambda r: r["manifest_index"]), "summary": summarize(rows),
        "semantic_resolution": semantics, "native_sources": sources,
        "feature_shards": shard_refs,
        "evidence": [{"path": str(p), "sha256": file_sha256(p)}
                     for p in (args.analysis, args.partition, args.capture, args.manifest,
                               helper, __file__)],
        "limitations": [
            "TRAIN failure-selected and target-informed; not population or held-out efficacy.",
            "Joint disjoint support is a descriptive feasibility control, not causal mediation.",
            "Union exclusion induces structural missingness; complete cases need not be representative.",
            "Peer prototype pools registered peers and is not instance-pair-specific.",
            "Graph node_id denotes a language-graph node, not a physical object ID.",
            "No new mechanism, native candidate backward, resources or admission is established.",
        ],
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"summary": result["summary"], "semantic_resolution": semantics}, indent=2))


if __name__ == "__main__":
    main()
