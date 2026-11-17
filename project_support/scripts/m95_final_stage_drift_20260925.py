"""Localize pointwise final-stage drift in two hash-verified M95 captures."""
import argparse
import json
from pathlib import Path

import torch

from m95_raw_support_compare_20260925 import EXPECTED, PAIRS, artifact_for


def summarize(reference, candidate):
    rows = []
    for index, queries in PAIRS.items():
        old, new = reference[index], candidate[index]
        fused_old = torch.as_tensor(old["features"]["fused"])
        fused_new = torch.as_tensor(new["features"]["fused"])
        final_old = torch.as_tensor(old["features"]["final"])
        final_new = torch.as_tensor(new["features"]["final"])
        if fused_old.shape != fused_new.shape or final_old.shape != final_new.shape:
            raise ValueError("Feature axes differ")
        if fused_old.shape != final_old.shape or final_old.ndim != 2:
            raise ValueError("Fused/final physical point axes differ")
        if not all(torch.isfinite(x).all() for x in
                   (fused_old, fused_new, final_old, final_new)):
            raise ValueError("Nonfinite features")
        point_max = (final_old - final_new).abs().amax(dim=1)
        point_energy = (final_old - final_new).square().sum(dim=1)
        fused_point_max = (fused_old - fused_new).abs().amax(dim=1)
        target = torch.as_tensor(old["target_union"], dtype=torch.bool)
        if target.numel() != point_max.numel():
            raise ValueError("Target point axis differs")
        largest = torch.argsort(point_max, descending=True)[:10]
        changed_mask_points = sorted({
            int(point)
            for query in queries
            for point in torch.nonzero(
                torch.as_tensor(old["query_masks"][query], dtype=torch.bool)
                != torch.as_tensor(new["query_masks"][query], dtype=torch.bool)
            ).flatten().tolist()
        })
        rows.append({
            "manifest_index": index,
            "point_count": int(point_max.numel()),
            "changed_mask_points": changed_mask_points,
            "final_points_above_1e-3": int((point_max > 1e-3).sum()),
            "final_points_above_1e-2": int((point_max > 1e-2).sum()),
            "final_energy_top1_fraction": (
                float(point_energy.max() / point_energy.sum())
                if float(point_energy.sum()) else 0.0
            ),
            "largest_final_point_deltas": [{
                "point": int(point),
                "final_max_abs": float(point_max[point]),
                "fused_max_abs": float(fused_point_max[point]),
                "target": bool(target[point]),
                "changed_mask": int(point) in changed_mask_points,
            } for point in largest.tolist()],
            "changed_mask_point_deltas": [{
                "point": point,
                "final_max_abs": float(point_max[point]),
                "fused_max_abs": float(fused_point_max[point]),
            } for point in changed_mask_points],
        })
    return {
        "contract": "m95_final_stage_drift_v1",
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
    result = summarize(
        artifact_for(args.reference, EXPECTED[0], PAIRS),
        artifact_for(args.candidate, EXPECTED[1], PAIRS),
    )
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"output": str(output), "rows": len(result["rows"])}))


if __name__ == "__main__":
    main()
