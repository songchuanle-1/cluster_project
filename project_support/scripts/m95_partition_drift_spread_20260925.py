"""Measure feature-drift spread around changed frozen hierarchy assignments."""
import argparse
import json
from pathlib import Path

import torch

from m95_partition_drift_20260925 import load_rows
from m95_raw_support_compare_20260925 import EXPECTED, PAIRS, artifact_for


def summarize(reference_rows, candidate_rows, reference_features, candidate_features):
    rows = []
    for index in PAIRS:
        old, new = reference_rows[index], candidate_rows[index]
        if old["native_input_sha256"] != new["native_input_sha256"]:
            raise ValueError("Native input differs")
        old_ids = old["hierarchical_cluster_ids"][0]
        new_ids = new["hierarchical_cluster_ids"][0]
        a = torch.as_tensor(reference_features[index]["features"]["final"])
        b = torch.as_tensor(candidate_features[index]["features"]["final"])
        if a.shape != b.shape or a.ndim != 2 or len(old_ids) != len(new_ids) or len(old_ids) != a.shape[0]:
            raise ValueError("Feature and partition axes differ")
        if not torch.isfinite(a).all() or not torch.isfinite(b).all():
            raise ValueError("Nonfinite features")
        delta = (a - b).abs().amax(dim=1)
        changed = [point for point, (x, y) in enumerate(zip(old_ids, new_ids)) if x != y]
        affected_old = {old_ids[point] for point in changed}
        affected_new = {new_ids[point] for point in changed}
        groups = {
            "changed_assignment": set(changed),
            "same_old_cluster_unchanged": {
                point for point, cluster in enumerate(old_ids)
                if point not in changed and cluster in affected_old
            },
            "same_new_cluster_unchanged": {
                point for point, cluster in enumerate(new_ids)
                if point not in changed and cluster in affected_new
            },
        }
        groups["other"] = set(range(len(old_ids))) - set.union(
            set(), *groups.values())
        threshold = 1e-3
        summary = {}
        for name, points in groups.items():
            indices = sorted(points)
            values = delta[indices]
            summary[name] = {
                "points": len(indices),
                "above_1e-3": int((values > threshold).sum()),
                "max_abs": float(values.max()) if indices else 0.0,
            }
        changed_masks = sorted({
            point for query in PAIRS[index]
            for point, (x, y) in enumerate(zip(
                reference_features[index]["query_masks"][query],
                candidate_features[index]["query_masks"][query],
            )) if bool(x) != bool(y)
        })
        rows.append({
            "manifest_index": index,
            "point_count": len(old_ids),
            "changed_assignment_points": changed,
            "changed_mask_points": changed_masks,
            "groups": summary,
            "above_1e-3_total": int((delta > threshold).sum()),
        })
    return {
        "contract": "m95_partition_drift_spread_v1",
        "reference_capture_sha256": EXPECTED[0],
        "candidate_capture_sha256": EXPECTED[1],
        "rows": rows,
        "scope": "Frozen paired captures only; group overlap is possible and association is not causal.",
        "strict_reproducibility_status": "fail_28_of_65",
        "native_execution_completed": False,
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
    result = summarize(
        load_rows(args.reference, EXPECTED[0]),
        load_rows(args.candidate, EXPECTED[1]),
        artifact_for(args.reference, EXPECTED[0], PAIRS),
        artifact_for(args.candidate, EXPECTED[1], PAIRS),
    )
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "rows": len(result["rows"])}))


if __name__ == "__main__":
    main()
