"""Compare hierarchical assignments for the two discrepant M95 rows."""
import argparse
import hashlib
import json
from pathlib import Path

from hierarchical_partition_contract_20260916 import validate_hierarchical_row
from m95_raw_support_compare_20260925 import EXPECTED, PAIRS


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
    result = []
    for index in PAIRS:
        a, b = reference[index], candidate[index]
        validate_hierarchical_row(a)
        validate_hierarchical_row(b)
        if a["native_input_sha256"] != b["native_input_sha256"]:
            raise ValueError("Native input differs")
        levels = []
        for level, (old, new) in enumerate(zip(
                a["hierarchical_cluster_ids"],
                b["hierarchical_cluster_ids"],
        )):
            if len(old) != len(new):
                raise ValueError("Cluster assignment axes differ")
            changed = [point for point, pair in enumerate(zip(old, new))
                       if pair[0] != pair[1]]
            levels.append({
                "level": level,
                "support": len(old),
                "changed_assignments": len(changed),
                "first_changed_indices": changed[:20],
            })
        result.append({
            "manifest_index": index,
            "native_input_sha256": a["native_input_sha256"],
            "reference_partition_sha256": a["hierarchical_partition_sha256"],
            "candidate_partition_sha256": b["hierarchical_partition_sha256"],
            "positions_identical": (
                a["hierarchical_fps_positions"] ==
                b["hierarchical_fps_positions"]
            ),
            "child_maps_identical": (
                a["hierarchical_child_maps"] ==
                b["hierarchical_child_maps"]
            ),
            "levels": levels,
        })
    return {
        "contract": "m95_partition_drift_v1",
        "reference_capture_sha256": EXPECTED[0],
        "candidate_capture_sha256": EXPECTED[1],
        "rows": result,
        "strict_reproducibility_status": "fail",
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare(load_rows(args.reference, EXPECTED[0]),
                     load_rows(args.candidate, EXPECTED[1]))
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "rows": len(result["rows"])}))


if __name__ == "__main__":
    main()
