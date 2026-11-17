"""Locate native boundary drift between two hash-bound M95 full scans."""
import argparse
import json
from pathlib import Path

import torch

from m95_raw_support_compare_20260925 import artifact_for, sha256


REFERENCE_SHA256 = "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
CANDIDATE_SHA256 = "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd"
QUERIES = {83: (103,), 174: (70, 87)}


def capture_rows(path, expected):
    if sha256(path) != expected:
        raise ValueError("Capture hash differs")
    rows = json.loads(Path(path).read_text(encoding="utf-8"))["rows"]
    selected = {int(row["manifest_index"]): row for row in rows
                if int(row["manifest_index"]) in QUERIES}
    if set(selected) != set(QUERIES):
        raise ValueError("Selected manifest rows missing")
    return selected


def tensor_delta(left, right):
    a, b = torch.as_tensor(left), torch.as_tensor(right)
    if a.shape != b.shape or not torch.isfinite(a).all() or not torch.isfinite(b).all():
        raise ValueError("Feature axis or finiteness differs")
    return {
        "max_abs": float((a - b).abs().max()),
        "mean_abs": float((a - b).abs().mean()),
    }


def compare(reference_rows, candidate_rows, reference_artifacts, candidate_artifacts):
    result = []
    for index, queries in QUERIES.items():
        old, new = reference_rows[index], candidate_rows[index]
        a, b = reference_artifacts[index], candidate_artifacts[index]
        if old["manifest_index"] != new["manifest_index"]:
            raise ValueError("Manifest index differs")
        levels = []
        for level, (left, right) in enumerate(zip(
            old["hierarchical_cluster_ids"], new["hierarchical_cluster_ids"]
        )):
            if len(left) != len(right):
                raise ValueError("Hierarchy axis differs")
            changed = [point for point, (x, y) in enumerate(zip(left, right)) if x != y]
            levels.append({
                "level": level,
                "changed_assignments": len(changed),
                "first_changed_points": changed[:8],
            })
        stages = {
            stage: tensor_delta(a["features"][stage], b["features"][stage])
            for stage in a["features"]
        }
        query_rows = []
        target_a = torch.as_tensor(a["target_union"], dtype=torch.bool).flatten()
        target_b = torch.as_tensor(b["target_union"], dtype=torch.bool).flatten()
        labels_a = torch.as_tensor(a["physical_instance_labels"]).flatten()
        labels_b = torch.as_tensor(b["physical_instance_labels"]).flatten()
        if not torch.equal(target_a, target_b) or not torch.equal(labels_a, labels_b):
            raise ValueError("Target or physical labels differ")
        for query in queries:
            logits_a = torch.as_tensor(a["query_mask_logits"][query]).flatten()
            logits_b = torch.as_tensor(b["query_mask_logits"][query]).flatten()
            mask_a = torch.as_tensor(a["query_masks"][query], dtype=torch.bool).flatten()
            mask_b = torch.as_tensor(b["query_masks"][query], dtype=torch.bool).flatten()
            if not torch.equal(logits_a > 0, mask_a) or not torch.equal(logits_b > 0, mask_b):
                raise ValueError("Saved mask and logit threshold disagree")
            changed = torch.nonzero(mask_a != mask_b).flatten().tolist()
            query_rows.append({
                "query": query,
                "logit_delta": tensor_delta(logits_a, logits_b),
                "changed_points": [{
                    "point": point,
                    "reference_logit": float(logits_a[point]),
                    "candidate_logit": float(logits_b[point]),
                    "target": bool(target_a[point]),
                } for point in changed],
            })
        result.append({
            "manifest_index": index,
            "native_input_sha256_equal": old.get("native_input_sha256") == new.get("native_input_sha256"),
            "entry_fps_indices_equal": old["fps_superpoints"] == new["fps_superpoints"],
            "partition_sha256_equal": old.get("hierarchical_partition_sha256") == new.get("hierarchical_partition_sha256"),
            "hierarchical_fps_positions_equal": old.get("hierarchical_fps_positions") == new.get("hierarchical_fps_positions"),
            "hierarchical_child_maps_equal": old.get("hierarchical_child_maps") == new.get("hierarchical_child_maps"),
            "levels": levels,
            "feature_stages": stages,
            "queries": query_rows,
        })
    return {
        "contract": "m95_fullscan_boundary_compare_v1",
        "reference_capture_sha256": REFERENCE_SHA256,
        "candidate_capture_sha256": CANDIDATE_SHA256,
        "rows": result,
        "scope": "Frozen full scans, read-only diagnostic; no causal or model-efficacy claim",
        "strict_reproducibility_status": "fail",
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    result = compare(
        capture_rows(args.reference, REFERENCE_SHA256),
        capture_rows(args.candidate, CANDIDATE_SHA256),
        artifact_for(args.reference, REFERENCE_SHA256, QUERIES),
        artifact_for(args.candidate, CANDIDATE_SHA256, QUERIES),
    )
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "rows": len(result["rows"])}))


if __name__ == "__main__":
    main()
