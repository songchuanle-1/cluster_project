"""Compare three discrepant M95 query masks in two frozen native captures."""
import hashlib
import json
import sys
from pathlib import Path

import torch


PAIRS = {83: (103,), 174: (70, 87)}
EXPECTED = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025",
    "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a",
)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_for(capture_path, expected_hash, indices):
    if sha256(capture_path) != expected_hash:
        raise ValueError("Capture hash differs")
    capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    entries = capture.get("feature_artifacts", [])
    selected = {}
    for entry in entries:
        path = Path(capture_path).parent / entry["path"]
        if sha256(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        artifacts = torch.load(path, map_location="cpu", weights_only=False)
        for artifact in artifacts:
            index = int(artifact["manifest_index"])
            if index in indices:
                if index in selected:
                    raise ValueError("Duplicate artifact index")
                selected[index] = artifact
    if set(selected) != set(indices):
        raise ValueError("Target artifact rows missing")
    return selected


def as_bool(value):
    return torch.as_tensor(value, dtype=torch.bool).flatten()


def compare(left, right):
    result = []
    for index, queries in PAIRS.items():
        a, b = left[index], right[index]
        target_a, target_b = as_bool(a["target_union"]), as_bool(b["target_union"])
        labels_a = torch.as_tensor(a["physical_instance_labels"]).flatten()
        labels_b = torch.as_tensor(b["physical_instance_labels"]).flatten()
        if target_a.shape != target_b.shape or labels_a.shape != labels_b.shape:
            raise ValueError("Physical point axis differs")
        row = {
            "manifest_index": index,
            "point_count": target_a.numel(),
            "target_support_changed": int((target_a != target_b).sum()),
            "physical_labels_changed": int((labels_a != labels_b).sum()),
            "queries": [],
        }
        for query in queries:
            mask_a = as_bool(a["query_masks"][query])
            mask_b = as_bool(b["query_masks"][query])
            if mask_a.shape != mask_b.shape or mask_a.shape != target_a.shape:
                raise ValueError("Query point axis differs")
            row["queries"].append({
                "query": query,
                "mask_support_changed": int((mask_a != mask_b).sum()),
                "reference_mask_points": int(mask_a.sum()),
                "candidate_mask_points": int(mask_b.sum()),
                "reference_intersection": int((mask_a & target_a).sum()),
                "candidate_intersection": int((mask_b & target_b).sum()),
                "reference_union": int((mask_a | target_a).sum()),
                "candidate_union": int((mask_b | target_b).sum()),
            })
        result.append(row)
    return result


def main():
    reference, candidate = sys.argv[1:3]
    result = compare(
        artifact_for(reference, EXPECTED[0], PAIRS),
        artifact_for(candidate, EXPECTED[1], PAIRS),
    )
    print(json.dumps({
        "contract": "m95_raw_support_comparison_v1",
        "reference_capture_sha256": EXPECTED[0],
        "candidate_capture_sha256": EXPECTED[1],
        "rows": result,
        "admission": False,
        "strict_reproducibility_status": "fail",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
