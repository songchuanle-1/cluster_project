"""Read-only hierarchy divergence census for two frozen M95 full scans."""
import argparse
import hashlib
import json
from pathlib import Path

REFERENCE_SHA256 = "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025"
CANDIDATE_SHA256 = "9271ea8e5202590e99e3d1e2da1a729ee87262bba8fecf96bd394c7f0abda1cd"


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path, expected):
    if sha256(path) != expected:
        raise ValueError("Capture hash differs")
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("selected_expressions") != 256 or len(document.get("rows", [])) != 256:
        raise ValueError("Not a 256-row full scan")
    rows = {int(row["manifest_index"]): row for row in document["rows"]}
    if set(rows) != set(range(256)):
        raise ValueError("Manifest coverage differs")
    return rows


def compare(reference, candidate):
    summary = {
        "native_input_differ": [],
        "entry_fps_differ": [],
        "hierarchical_positions_differ": [],
        "hierarchical_child_maps_differ": [],
        "partition_hash_differ": [],
        "assignment_differ": [[], [], []],
        "selected_query_differ": [],
        "selected_iou_differ": [],
    }
    changed = []
    for index in range(256):
        old, new = reference[index], candidate[index]
        checks = {
            "native_input_differ": old["native_input_sha256"] != new["native_input_sha256"],
            "entry_fps_differ": old["fps_superpoints"] != new["fps_superpoints"],
            "hierarchical_positions_differ": old["hierarchical_fps_positions"] != new["hierarchical_fps_positions"],
            "hierarchical_child_maps_differ": old["hierarchical_child_maps"] != new["hierarchical_child_maps"],
            "partition_hash_differ": old["hierarchical_partition_sha256"] != new["hierarchical_partition_sha256"],
            "selected_query_differ": old["selected_query"] != new["selected_query"],
            "selected_iou_differ": old["ious"][old["selected_query"]] != new["ious"][new["selected_query"]],
        }
        if len(old["hierarchical_cluster_ids"]) != 3 or len(new["hierarchical_cluster_ids"]) != 3:
            raise ValueError("Hierarchy level count differs")
        counts = []
        for level, (a, b) in enumerate(zip(
            old["hierarchical_cluster_ids"], new["hierarchical_cluster_ids"]
        )):
            if len(a) != len(b):
                raise ValueError("Hierarchy support differs")
            count = sum(x != y for x, y in zip(a, b))
            counts.append(count)
            if count:
                summary["assignment_differ"][level].append(index)
        for key, differs in checks.items():
            if differs:
                summary[key].append(index)
        if any(checks.values()) or any(counts):
            changed.append({
                "manifest_index": index,
                "checks": [key for key, differs in checks.items() if differs],
                "changed_assignments": counts,
            })
    return {
        "contract": "m95_fullscan_hierarchy_census_v1",
        "reference_capture_sha256": REFERENCE_SHA256,
        "candidate_capture_sha256": CANDIDATE_SHA256,
        "rows": 256,
        "counts": {key: [len(x) for x in value] if key == "assignment_differ"
                   else len(value) for key, value in summary.items()},
        "indices": summary,
        "changed_rows": changed,
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
        load_rows(args.reference, REFERENCE_SHA256),
        load_rows(args.candidate, CANDIDATE_SHA256),
    )
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result["counts"]))


if __name__ == "__main__":
    main()
