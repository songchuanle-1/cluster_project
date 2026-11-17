"""Execute the predeclared same-category witness permutation control."""
import hashlib
import json
import os
from pathlib import Path

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    path = PIPE / "relation_witness_audit_20261012.json"
    assert sha(path) == "5c28b69591846c08805fa7edfb318879eea939c01fd3fb48bfdeb691cc9dd50d"
    audit = json.loads(path.read_text())
    rows = []
    for record in audit["rows"]:
        for e in record["eligible"]:
            ids = e["reference_ids"]
            if not ids:
                continue
            values = [int(e["signed_vertical_offsets"][str(i)] > 0) for i in ids]
            reversed_values = list(reversed(values))
            rows.append({"scene": record["scene"], "ann_id": record["ann_id"],
                         "reference_ids": ids, "vertical_truth": values,
                         "same_category_reversed_truth": reversed_values,
                         "control_max_delta": max(abs(a - b) for a, b in zip(values, reversed_values)),
                         "alternative_reference_count": len(ids),
                         "identifiable_by_vertical_truth": len(set(values)) > 1})
    result = {"contract": "vertical_witness_permutation_control_v1",
              "audit_sha256": sha(path), "script_sha256": sha(Path(__file__)),
              "eligible_with_geometry": len(rows),
              "rows_with_multiple_reference_candidates": sum(r["alternative_reference_count"] > 1 for r in rows),
              "control_separated_rows": sum(r["control_max_delta"] > 0 for r in rows),
              "rows": rows, "cpu_only": True, "admission": False,
              "limits": "Exact null control for vertical-sign witness identity in this frozen cohort. Not rejection of full3D support/other relations, and not a native efficacy test."}
    out = PIPE / "relation_witness_control_20261012.json"
    assert not out.exists()
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
