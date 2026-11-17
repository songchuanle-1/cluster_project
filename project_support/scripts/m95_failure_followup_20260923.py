"""Bounded CPU follow-up on the frozen capture; no model execution or admission."""
import argparse
import json
import os
import socket
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from analyze_m95_manifest_identity_controls_20260922 import (
    STAGES, as_list, bool_list, dominant_overlap, file_sha256, int_list,
    paired_summary, validate_artifact_header, validate_manifest_hash,
)
from m95_failure_partition_20260923 import (
    ANALYSIS_SHA256, CAPTURE_SHA256, EXPECTED_MANIFEST_SHA256, HELPER_SHA256,
    checked_json, identity, mask_support, row_audit,
)

PARTITION_SHA256 = "491492118b2f55d78c02bc023f8e1e9408bd359eb5ef2af8824faee6bff6b5ee"


def keyed(rows):
    result = {r["manifest_index"]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate manifest index")
    return result


def matched_features(details, draws=10000):
    stages = {}
    for stage in STAGES:
        rows = []
        missing = []
        for row in details:
            values = row["features"]["stages"][stage]
            overlap = values.get("overlapping_acceptable_minus_deployed")
            excluded = values.get("query_excluded_acceptable_minus_deployed")
            if overlap is None or excluded is None:
                missing.append(row["manifest_index"])
                continue
            rows.append({
                "manifest_index": row["manifest_index"], "scene_id": row["scene_id"],
                "overlap": overlap, "excluded": excluded,
                "excluded_minus_overlap": excluded - overlap,
            })
        stages[stage] = {
            "rows": rows, "missing_indices": missing,
            **{key: paired_summary(rows, key, draws=draws)
               for key in ("overlap", "excluded", "excluded_minus_overlap")},
        }
    return stages


def decompose_pairs(analysis, details, draws=10000):
    rows = []
    for detail in details:
        pair = detail["pair"]
        if pair is None:
            continue
        row = analysis[detail["manifest_index"]]
        p, n = pair["positive_index"], pair["negative_index"]
        rows.append({
            "manifest_index": detail["manifest_index"], "scene_id": detail["scene_id"],
            **pair, "positive_iou": row["ious"][p], "negative_iou": row["ious"][n],
            "contrast": row["ious"][p] - row["ious"][n],
        })
    groups = {
        "original_unchanged": rows,
        "target_dominant_positive": [r for r in rows if r["positive_dominant_identity"] == "target_dominant"],
        "peer_dominant_positive": [r for r in rows if r["positive_dominant_identity"] == "same_class_peer"],
        "negative_also_positive": [r for r in rows if r["negative_also_native_positive"]],
        "negative_not_positive": [r for r in rows if not r["negative_also_native_positive"]],
    }
    return {
        "rows": rows,
        "groups": {name: paired_summary(group, "contrast", draws=draws)
                   for name, group in groups.items()},
        "subgroup_status": "Post-outcome descriptive decompositions, not replacement primary tests.",
    }


def query_record(row, query, manifest):
    if query is None:
        return None
    return {
        "query": query, "score": row["scores"][query], "iou": row["ious"][query],
        "native_positive": row["native_positive"][query],
        "target_seed": row["fps_seed_inside_target"][query],
        "identity": identity(row["dominant_instance"][query], manifest),
        "dominant_instance": row["dominant_instance"][query],
    }


def supervision_row(row, detail, manifest):
    seeds, positive = row["fps_seed_inside_target"], row["native_positive"]
    if any(s and not p for s, p in zip(seeds, positive)):
        raise ValueError("Target-seed set is not contained in native positives")
    return {
        "manifest_index": row["manifest_index"], "scene_id": row["scene_id"],
        "partition": detail["partition"],
        "positive_minus_seed_indices": [q for q, (p, s) in enumerate(zip(positive, seeds)) if p and not s],
        "positive": query_record(row, detail["positive_query"], manifest),
        "seed": query_record(row, detail["target_seed_query"], manifest),
        "deployed": query_record(row, detail["deployed_query"], manifest),
        "acceptable": [query_record(row, q, manifest) for q, v in enumerate(row["ious"]) if v > 0.5],
    }


def support_details(artifact, row, detail, manifest):
    validate_artifact_header(artifact, EXPECTED_MANIFEST_SHA256)
    if artifact["manifest_index"] != row["manifest_index"]:
        raise ValueError("Artifact index mismatch")
    labels = int_list(artifact["physical_instance_labels"], "labels")
    target = bool_list(artifact["target_union"], "target")
    masks = [bool_list(v, "mask") for v in as_list(artifact["query_masks"])]
    if len(target) != len(labels) or len(masks) != row["query_count"]:
        raise ValueError("Artifact axes differ")
    peers = {str(x) for x in manifest["same_class_peer_object_ids"]}
    peer_mask = [str(label) in peers for label in labels]
    result = {}
    for name, q in (("deployed", detail["deployed_query"]),
                    ("acceptable", detail["best_acceptable_query"])):
        mask = masks[q]
        if len(mask) != len(labels) or dominant_overlap(mask, labels) != row["dominant_instance"][q]:
            raise ValueError("Physical support differs from frozen analysis")
        support = mask_support(mask, target, labels, peers)
        if support != detail["features"]["support"][name]:
            raise ValueError("Saved support differs from shard")
        support["peer_prototype_remaining_without_query"] = sum(p and not m for p, m in zip(peer_mask, mask))
        support["target_prototype_size"] = sum(target)
        support["peer_prototype_size"] = sum(peer_mask)
        support["target_overlap"] = sum(t and m for t, m in zip(target, mask))
        support["peer_overlap"] = sum(p and m for p, m in zip(peer_mask, mask))
        result[name] = support
    reasons = []
    for name, support in result.items():
        for kind in ("target", "peer"):
            if support[kind + "_prototype_size"] == 0:
                reasons.append(name + "_" + kind + "_prototype_absent")
            elif support[kind + "_prototype_remaining_without_query"] == 0:
                reasons.append(name + "_exhausts_" + kind + "_prototype")
    excluded = detail["features"]["stages"]["final"]["query_excluded_acceptable_minus_deployed"]
    if excluded is None and not reasons:
        reasons.append("zero_norm_or_nonstructural_feature_missingness")
    if excluded is not None and reasons:
        raise ValueError("Finite margin with empty prototype")
    return {"support": result, "missing_reasons": reasons}


def normalize_class(value):
    return "".join(c for c in str(value).strip().lower() if c.isalnum())


def semantic_rows(annotations, analysis, details, manifest):
    objects = defaultdict(set)
    for entry in annotations:
        objects[(str(entry["scene_id"]), str(entry["object_id"]))].add(normalize_class(entry["object_name"]))
    result = []
    for detail in details:
        if detail["deployed_identity"] != "outside_target_and_registered_peers":
            continue
        index, scene = detail["manifest_index"], detail["scene_id"]
        m, row = manifest[index], analysis[index]
        wrong = str(row["dominant_instance"][detail["deployed_query"]])
        names = sorted(objects.get((scene, wrong), set()))
        target_names = sorted(objects.get((scene, str(m["target_object_id"])), set()))
        if m["target_class"] not in target_names:
            raise ValueError("Target annotation class does not match manifest")
        if len(names) != 1:
            classification = "unresolved_missing_or_conflicting_annotation"
        elif names[0] == m["target_class"]:
            classification = "same_annotation_class_outside_registered_peers"
        else:
            classification = "different_annotation_class"
        result.append({
            "manifest_index": index, "scene_id": scene, "target_class": m["target_class"],
            "target_object_id": m["target_object_id"], "dominant_object_id": wrong,
            "dominant_annotation_classes": names, "classification": classification,
        })
    return result


def main():
    parser = argparse.ArgumentParser()
    for name in ("analysis", "partition", "capture", "manifest", "output", "loss"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    if os.name == "nt" or socket.gethostname() != "das" or os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("Only verified server-6 CPU with CUDA hidden is authorized")
    helper = Path(__file__).with_name("analyze_m95_manifest_identity_controls_20260922.py")
    if file_sha256(helper) != HELPER_SHA256:
        raise ValueError("Frozen analysis helper changed")
    analysis_doc = checked_json(args.analysis, ANALYSIS_SHA256)
    partition = checked_json(args.partition, PARTITION_SHA256)
    capture = checked_json(args.capture, CAPTURE_SHA256)
    manifest_doc = checked_json(args.manifest, EXPECTED_MANIFEST_SHA256)
    manifest = validate_manifest_hash(manifest_doc, EXPECTED_MANIFEST_SHA256, EXPECTED_MANIFEST_SHA256)
    analysis, details = keyed(analysis_doc["rows"]), keyed(partition["rows"])
    if set(analysis) != set(manifest) or set(details) != set(manifest):
        raise ValueError("Coverage differs")
    for index, row in analysis.items():
        computed = row_audit(row, manifest[index])
        if any(details[index][k] != v for k, v in computed.items()):
            raise ValueError("Partition differs from original analysis")
    recoverable = [r for r in details.values() if r["partition"].startswith("recoverable_")]
    focus = [supervision_row(analysis[i], d, manifest[i]) for i, d in details.items()
             if d["partition"] in ("recoverable_positive_set_excludes_acceptable",
                                   "recoverable_within_positive_score_failure")]
    # Read saved masks, never run a model or move tensors onto a GPU.
    import torch
    torch.set_num_threads(1)
    support, seen, shards = {}, set(), []
    needed = {r["manifest_index"] for r in recoverable}
    for item in capture["feature_artifacts"]:
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Shard escapes capture")
        path = Path(args.capture).parent / relative
        if file_sha256(path) != item["sha256"]:
            raise ValueError("Shard hash mismatch")
        entries = torch.load(path, map_location="cpu", weights_only=True)
        if len(entries) != item["rows"]:
            raise ValueError("Shard row count differs")
        for artifact in entries:
            index = artifact["manifest_index"]
            if index in seen or index not in manifest:
                raise ValueError("Duplicate or unexpected shard row")
            seen.add(index)
            if index in needed:
                support[index] = support_details(artifact, analysis[index], details[index], manifest[index])
        shards.append({"path": str(path), "sha256": item["sha256"]})
    if seen != set(manifest) or set(support) != needed:
        raise ValueError("Incomplete native shard coverage")
    ann_source = manifest_doc["native_sources"]["ScanRefer_train_new.json"]
    annotations = checked_json(ann_source["path"], ann_source["sha256"])
    semantics = semantic_rows(annotations, analysis, recoverable, manifest)
    stages = matched_features(recoverable)
    pairs = decompose_pairs(analysis, list(details.values()))
    discordant = [supervision_row(analysis[i], d, manifest[i]) for i, d in details.items()
                  if d["common_support"] and not d["same_selected_query"]]
    missing_seed = [supervision_row(analysis[i], d, manifest[i]) for i, d in details.items()
                    if d["target_seed_query"] is None]
    cross = Counter((r["partition"], r["deployed_identity"],
                     support[r["manifest_index"]]["support"]["deployed"]["mixed_known_instance_support"])
                    for r in recoverable)
    result = {
        "contract": "m95_failure_followup_v1", "generated_at": datetime.now().astimezone().isoformat(),
        "host": socket.gethostname(), "cpu_only": True, "admission": False,
        "source": [{"path": str(p), "sha256": file_sha256(p)} for p in (
            args.analysis, args.partition, args.capture, args.manifest, args.loss, helper, __file__)],
        "annotation_source": ann_source, "feature_shards": shards,
        "supervision_contract": {
            "matcher": "Nearest-centroid sampled query union target-seeded queries; not mask-IoU assignment.",
            "indicator": "loss_indi uses matched positives; deployed scores are positive-class softmax of indis.",
            "mask": "Matched query masks receive target BCE/Dice; separate score regression is not deployed indis.",
            "scope": "Static source interpretation plus observed labels; no counterfactual gradient or efficacy claim.",
        },
        "supervision_focus": focus, "registered_pairs": pairs, "discordant_selectors": discordant,
        "missing_seed_controls": missing_seed, "matched_features": stages,
        "recoverable_support": [{"manifest_index": i, "scene_id": details[i]["scene_id"], **s}
                                for i, s in support.items()],
        "outside_peer_semantics": semantics,
        "summary": {
            "expressions": len(details), "recoverable": len(recoverable), "focus_rows": len(focus),
            "registered_pairs": pairs["groups"], "discordant_selectors": len(discordant),
            "missing_seed_controls": len(missing_seed),
            "matched_final": {k: v for k, v in stages["final"].items() if k not in ("rows", "missing_indices")},
            "missing_reason_counts_nonexclusive": dict(Counter(reason for s in support.values() for reason in s["missing_reasons"])),
            "missing_reason_combinations": dict(Counter("|".join(s["missing_reasons"]) or "complete" for s in support.values())),
            "outside_peer_semantics": dict(Counter(r["classification"] for r in semantics)),
            "identity_partition_mixed_cross": [{"partition": p, "identity": i, "mixed": m, "rows": n}
                                             for (p, i, m), n in sorted(cross.items())],
        },
        "limitations": [
            "TRAIN failure-selected and target-informed; no population or held-out efficacy estimate.",
            "Registered 65-pair endpoint is unchanged. Subgroups and all follow-ups are descriptive.",
            "Prototype exclusion changes support and may empty it; same rows do not imply causal control.",
            "Normalized annotation class names are not a full semantic ontology.",
            "No new mechanism, native backward, resource gate, or training admission is established.",
        ],
    }
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
