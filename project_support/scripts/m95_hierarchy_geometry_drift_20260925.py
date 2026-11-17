"""Compare geometry and child maps in two hash-bound frozen M95 captures."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from hierarchical_partition_contract_20260916 import validate_hierarchical_row

EXPECTED = (
    "f90286842d9d82d835652a29048100a10b6286ee5630e0d7c296363e95880025",
    "68c19cacf5c42d7dd99400e7c792003ccb094101f5fcb4093812eca78b1a403a",
)
PAIRS = {83: (103,), 174: (70, 87)}


def load_rows(path, expected):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("Capture hash differs")
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    selected = {int(row["manifest_index"]): row for row in rows
                if int(row["manifest_index"]) in PAIRS}
    if set(selected) != set(PAIRS):
        raise ValueError("Discrepant rows missing")
    return selected


def compare(reference, candidate):
    rows = []
    for index in PAIRS:
        old, new = reference[index], candidate[index]
        validate_hierarchical_row(old)
        validate_hierarchical_row(new)
        if old["native_input_sha256"] != new["native_input_sha256"]:
            raise ValueError("Native input differs")
        levels = []
        for level, (old_centers, new_centers, old_ids, new_ids) in enumerate(zip(
            old["hierarchical_fps_positions"],
            new["hierarchical_fps_positions"],
            old["hierarchical_cluster_ids"],
            new["hierarchical_cluster_ids"],
        )):
            if len(old_centers) != len(new_centers) or len(old_ids) != len(new_ids):
                raise ValueError("Hierarchy axes differ")
            distances = []
            for a, b in zip(old_centers, new_centers):
                if len(a) != len(b):
                    raise ValueError("Center dimension differs")
                distances.append(math.dist(a, b))
            changed = [
                {"point": point, "reference_id": a, "candidate_id": b}
                for point, (a, b) in enumerate(zip(old_ids, new_ids)) if a != b
            ]
            levels.append({
                "level": level,
                "centers": len(distances),
                "max_center_shift": max(distances),
                "shifted_centers_above_1e-6": sum(x > 1e-6 for x in distances),
                "changed_assignments": changed,
            })
        child_maps = []
        for level, (a, b) in enumerate(zip(
            old["hierarchical_child_maps"], new["hierarchical_child_maps"]
        )):
            keys = set(a) | set(b)
            changed = [key for key in keys if a.get(key) != b.get(key)]
            child_maps.append({
                "level": level,
                "changed_parent_count": len(changed),
                "changed_parent_ids": sorted(changed, key=int)[:20],
            })
        rows.append({
            "manifest_index": index,
            "native_input_sha256": old["native_input_sha256"],
            "levels": levels,
            "child_maps": child_maps,
        })
    return {
        "contract": "m95_hierarchy_geometry_drift_v1",
        "reference_capture_sha256": EXPECTED[0],
        "candidate_capture_sha256": EXPECTED[1],
        "rows": rows,
        "strict_reproducibility_status": "fail",
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare(
        load_rows(args.reference, EXPECTED[0]),
        load_rows(args.candidate, EXPECTED[1]),
    )
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "rows": len(result["rows"])}))


if __name__ == "__main__":
    main()
