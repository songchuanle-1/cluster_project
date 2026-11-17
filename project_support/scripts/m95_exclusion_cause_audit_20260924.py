"""Attribute frozen exclusion rows only after an opt-in native matcher capture."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from m95_match_cause_contract_20260923 import check_row
from m95_repeated_gt_mask_contract_20260924 import audit as audit_mask_source, mask_binding
from m95_identity_query_controls_20260923 import PRODUCER_FILES

ROOT = Path(__file__).resolve().parent.parent
PARTITION = "pipeline/reports/m95_failure_partition_20260923-0318.json"
PARTITION_SHA256 = "491492118b2f55d78c02bc023f8e1e9408bd359eb5ef2af8824faee6bff6b5ee"
FROZEN_MANIFEST = "pipeline/diagnostic_runs/m95_identity_controls_20260922/manifest.json"
FROZEN_MANIFEST_SHA256 = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"
CHECKPOINT_SHA256 = "fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e"
FOCUS = "recoverable_positive_set_excludes_acceptable"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def producer_sha256():
    return hashlib.sha256(b"".join(
        (ROOT / "scripts" / name).read_bytes() for name in PRODUCER_FILES
    )).hexdigest()


def audit(partition, capture, manifest):
    mask_source = audit_mask_source()["source"]
    producer_hash = producer_sha256()
    if capture.get("producer_sha256") != producer_hash:
        raise ValueError("Native capture producer hash differs")
    frozen = partition["rows"]
    manifest_rows = manifest["rows"]
    if (partition.get("contract") != "m95_failure_partition_descriptive_v1"
            or partition.get("admission") is not False
            or len(frozen) != 256
            or {r["manifest_index"] for r in frozen} != set(range(256))
            or manifest.get("contract") != "m95_preregistered_identity_controls_v1"
            or len(manifest_rows) != 256
            or [r["manifest_index"] for r in manifest_rows] != list(range(256))):
        raise ValueError("Frozen partition identity differs")
    focus = {r["manifest_index"]: r for r in frozen if r["partition"] == FOCUS}
    if len(focus) != 6:
        raise ValueError("Exclusion denominator differs")
    rows = capture["rows"]
    if (capture.get("manifest", {}).get("sha256") != FROZEN_MANIFEST_SHA256
            or capture.get("checkpoint_sha256") != CHECKPOINT_SHA256
            or capture.get("native_match_cause_completed") is not True
            or capture.get("selected_expressions") != 256
            or len(rows) != 256
            or {r["manifest_index"] for r in rows} != set(range(256))):
        raise ValueError("Incomplete or mismatched native capture")
    result = []
    all_binding = []
    partition_binding = {}
    by_index = {r["manifest_index"]: r for r in rows}
    for index, old in sorted((r["manifest_index"], r) for r in frozen):
        row = by_index[index]
        if row["scene_id"] != old["scene_id"] or row["ann_id"] != old["ann_id"]:
            raise ValueError("Expression binding differs")
        registered = manifest_rows[index]
        if (registered["scene_id"] != old["scene_id"]
                or registered["ann_id"] != old["ann_id"]
                or str(row["target_object_id"]) != str(registered["target_object_id"])):
            raise ValueError("Frozen manifest target binding differs")
        cause = row["native_match_cause"]
        check_row(cause)
        gt_ids = [str(value) for value in cause["object_ids"]]
        positive = cause["native_positive"]
        ious = row["ious"]
        if any(type(value) not in (int, float) or not math.isfinite(value)
               or not 0 <= value <= 1 for value in ious):
            raise ValueError("Invalid native IoU axis")
        acceptable_positive = sum(
            p and value > 0.5 for p, value in zip(positive, ious)
        )
        if (len(ious) != len(positive)
                or sum(positive) != old["native_positive_queries"]
                or sum(value > 0.5 for value in ious) != old["acceptable_queries"]
                or acceptable_positive != old["acceptable_native_positive_queries"]):
            raise ValueError("Frozen query outcomes differ")
        target = str(row["target_object_id"])
        if target not in gt_ids:
            raise ValueError("Native target GT missing")
        expected_pairs = (
            [(q, gt) for gt, q in enumerate(cause["nearest_query_per_gt"])]
            + [(q, gt) for gt, group in enumerate(cause["member_queries_per_gt"])
               for q in group]
        )
        pairs = cause["matched_query_gt_pairs"]
        if pairs != [list(pair) for pair in expected_pairs]:
            raise ValueError("Native matched pair order differs from causes")
        binding = mask_binding([gt for _, gt in pairs], len(gt_ids))
        target_gt = gt_ids.index(target)
        target_nearest = cause["nearest_query_per_gt"][target_gt]
        target_nearest_shared_gt_count = (
            cause["nearest_query_per_gt"].count(target_nearest) - 1
        )
        target_pair_positions = [
            i for i, (_, gt) in enumerate(pairs) if gt == target_gt
        ]
        target_mismatched = [
            i for i in target_pair_positions
            if binding["addressed_mask_gt_ids"][i] != target_gt
        ]
        binding_row = {
            "manifest_index": index,
            "gt_count": len(gt_ids),
            "pair_count": len(pairs),
            "nearest_collision_extra_pairs": (
                len(cause["nearest_query_per_gt"])
                - len(set(cause["nearest_query_per_gt"]))
            ),
            "target_nearest_shared_gt_count": target_nearest_shared_gt_count,
            "mismatched_pair_count": len(binding["mismatched_pair_positions"]),
            "target_pair_count": len(target_pair_positions),
            "target_mismatched_pair_count": len(target_mismatched),
            "other_to_target_pair_count": sum(
                gt != target_gt and binding["addressed_mask_gt_ids"][i] == target_gt
                for i, (_, gt) in enumerate(pairs)
            ),
        }
        binding_row["target_collision_and_misbinding"] = (
            binding_row["target_nearest_shared_gt_count"] > 0
            and binding_row["target_mismatched_pair_count"] > 0
        )
        binding_row["any_collision_and_misbinding"] = (
            binding_row["nearest_collision_extra_pairs"] > 0
            and binding_row["mismatched_pair_count"] > 0
        )
        all_binding.append(binding_row)
        group = partition_binding.setdefault(old["partition"], {
            "rows": 0,
            "multi_gt_rows": 0,
            "nearest_collision_rows": 0,
            "nearest_collision_extra_pairs": 0,
            "target_nearest_collision_rows": 0,
            "target_nearest_shared_gt_count": 0,
            "mismatched_rows": 0,
            "mismatched_pairs": 0,
            "total_pairs": 0,
            "target_mismatched_rows": 0,
            "target_mismatched_pairs": 0,
            "target_pairs": 0,
            "other_to_target_pairs": 0,
            "target_collision_and_misbinding_rows": 0,
            "any_collision_and_misbinding_rows": 0,
        })
        group["rows"] += 1
        group["multi_gt_rows"] += len(gt_ids) > 1
        group["nearest_collision_rows"] += binding_row["nearest_collision_extra_pairs"] > 0
        group["nearest_collision_extra_pairs"] += binding_row["nearest_collision_extra_pairs"]
        group["target_nearest_collision_rows"] += target_nearest_shared_gt_count > 0
        group["target_nearest_shared_gt_count"] += target_nearest_shared_gt_count
        group["mismatched_rows"] += binding_row["mismatched_pair_count"] > 0
        group["mismatched_pairs"] += binding_row["mismatched_pair_count"]
        group["total_pairs"] += binding_row["pair_count"]
        group["target_mismatched_rows"] += binding_row["target_mismatched_pair_count"] > 0
        group["target_mismatched_pairs"] += binding_row["target_mismatched_pair_count"]
        group["target_pairs"] += binding_row["target_pair_count"]
        group["other_to_target_pairs"] += binding_row["other_to_target_pair_count"]
        group["target_collision_and_misbinding_rows"] += binding_row["target_collision_and_misbinding"]
        group["any_collision_and_misbinding_rows"] += binding_row["any_collision_and_misbinding"]
        if index not in focus:
            continue
        if acceptable_positive != 0:
            raise ValueError("Frozen query outcomes differ")
        binding["pairs"] = [
            {"query": query, "matched_object_id": gt_ids[gt],
             "addressed_mask_object_id": gt_ids[binding["addressed_mask_gt_ids"][i]]}
            for i, (query, gt) in enumerate(pairs)
        ]
        tags = [set() for _ in positive]
        for gt, query in enumerate(cause["nearest_query_per_gt"]):
            tags[query].add(("nearest_gt", gt_ids[gt]))
        for gt, group in enumerate(cause["member_queries_per_gt"]):
            for query in group:
                tags[query].add(("instance_member", gt_ids[gt]))
        positives = [{
            "query": query,
            "causes": [{"kind": kind, "object_id": object_id,
                        "target_gt": object_id == target}
                       for kind, object_id in sorted(tags[query])],
            "sampled_label_matches_target":
                str(cause["sampled_instance_labels"][query]) == target,
            "acceptable_mask": ious[query] > 0.5,
        } for query, value in enumerate(positive) if value]
        result.append({
            "manifest_index": index,
            "scene_id": old["scene_id"],
            "ann_id": old["ann_id"],
            "target_seed_selector_available": old["target_seed_query"] is not None,
            "native_positive_queries": positives,
            "target_cause_count": sum(
                any(c["target_gt"] for c in item["causes"]) for item in positives
            ),
            "other_gt_only_count": sum(
                not any(c["target_gt"] for c in item["causes"]) for item in positives
            ),
            "gt_mask_binding": binding,
        })
    return {
        "contract": "m95_exclusion_native_cause_v1",
        "scope": "Six outcome-selected TRAIN expressions; descriptive matcher attribution",
        "rows": result,
        "all_256_mask_binding": {
            "rows": all_binding,
            "multi_gt_rows": sum(r["gt_count"] > 1 for r in all_binding),
            "nearest_collision_rows": sum(
                r["nearest_collision_extra_pairs"] > 0 for r in all_binding
            ),
            "nearest_collision_extra_pairs": sum(
                r["nearest_collision_extra_pairs"] for r in all_binding
            ),
            "target_nearest_collision_rows": sum(
                r["target_nearest_shared_gt_count"] > 0 for r in all_binding
            ),
            "target_nearest_shared_gt_count": sum(
                r["target_nearest_shared_gt_count"] for r in all_binding
            ),
            "mismatched_rows": sum(r["mismatched_pair_count"] > 0 for r in all_binding),
            "mismatched_pairs": sum(r["mismatched_pair_count"] for r in all_binding),
            "total_pairs": sum(r["pair_count"] for r in all_binding),
            "target_mismatched_rows": sum(
                r["target_mismatched_pair_count"] > 0 for r in all_binding
            ),
            "target_mismatched_pairs": sum(
                r["target_mismatched_pair_count"] for r in all_binding
            ),
            "target_pairs": sum(r["target_pair_count"] for r in all_binding),
            "other_to_target_pairs": sum(
                r["other_to_target_pair_count"] for r in all_binding
            ),
            "target_collision_and_misbinding_rows": sum(
                r["target_collision_and_misbinding"] for r in all_binding
            ),
            "any_collision_and_misbinding_rows": sum(
                r["any_collision_and_misbinding"] for r in all_binding
            ),
        },
        "binding_by_frozen_partition": partition_binding,
        "mask_binding_mismatched_rows": sum(
            bool(row["gt_mask_binding"]["mismatched_pair_positions"]) for row in result
        ),
        "mask_binding_mismatched_pairs": sum(
            len(row["gt_mask_binding"]["mismatched_pair_positions"]) for row in result
        ),
        "mask_source": mask_source,
        "producer_sha256": producer_hash,
        "admission": False,
        "limitations": [
            "A nearest-GT assignment is not evidence of a label error.",
            "Target-GT cause does not imply an acceptable predicted mask.",
            "No matched training intervention, native backward, resource or efficacy result.",
            "GT-mask indexing is a conditional source contract, not a measured training effect.",
            "A query nearest to multiple GTs is separately counted; collision is not a mask-binding cause.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source = ROOT / PARTITION
    capture = Path(args.capture)
    if digest(source) != PARTITION_SHA256:
        raise ValueError("Frozen partition hash differs")
    manifest_path = ROOT / FROZEN_MANIFEST
    if digest(manifest_path) != FROZEN_MANIFEST_SHA256:
        raise ValueError("Frozen manifest hash differs")
    result = audit(json.loads(source.read_text(encoding="utf-8")),
                   json.loads(capture.read_text(encoding="utf-8")),
                   json.loads(manifest_path.read_text(encoding="utf-8")))
    result["evidence"] = [
        {"path": PARTITION, "sha256": PARTITION_SHA256},
        {"path": FROZEN_MANIFEST, "sha256": FROZEN_MANIFEST_SHA256},
        {"path": str(capture), "sha256": digest(capture)},
    ]
    with Path(args.output).open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
