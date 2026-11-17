"""Audit exact-capture mask threshold crossings without running the model."""
import argparse
import json
from pathlib import Path

import torch

from m95_raw_support_compare_20260925 import EXPECTED, PAIRS, artifact_for


def audit(reference, candidate):
    rows = []
    for index, queries in PAIRS.items():
        old, new = reference[index], candidate[index]
        feature_deltas = {}
        if set(old["features"]) != set(new["features"]):
            raise ValueError("Feature stage keys differ")
        for stage in old["features"]:
            left = torch.as_tensor(old["features"][stage])
            right = torch.as_tensor(new["features"][stage])
            if left.shape != right.shape or not bool(torch.isfinite(left).all() and torch.isfinite(right).all()):
                raise ValueError("Feature stage shape or finiteness differs")
            feature_deltas[stage] = {
                "max_abs": float((left - right).abs().max()),
                "mean_abs": float((left - right).abs().mean()),
            }
        old_states = old.get("identity_query", {}).get("query_states")
        new_states = new.get("identity_query", {}).get("query_states")
        query_state_deltas = None
        if old_states is not None and new_states is not None:
            left = torch.as_tensor(old_states)
            right = torch.as_tensor(new_states)
            if left.shape != right.shape or not bool(torch.isfinite(left).all() and torch.isfinite(right).all()):
                raise ValueError("Query state shape or finiteness differs")
            query_state_deltas = {
                "max_abs": float((left - right).abs().max()),
                "mean_abs": float((left - right).abs().mean()),
            }
        query_rows = []
        for query in queries:
            a = torch.as_tensor(old["query_mask_logits"][query]).flatten()
            b = torch.as_tensor(new["query_mask_logits"][query]).flatten()
            mask_a = torch.as_tensor(old["query_masks"][query], dtype=torch.bool).flatten()
            mask_b = torch.as_tensor(new["query_masks"][query], dtype=torch.bool).flatten()
            if a.shape != b.shape or a.shape != mask_a.shape or b.shape != mask_b.shape:
                raise ValueError("Query logit/mask axes differ")
            if not bool(torch.isfinite(a).all() and torch.isfinite(b).all()):
                raise ValueError("Nonfinite mask logit")
            if not torch.equal(a > 0, mask_a) or not torch.equal(b > 0, mask_b):
                raise ValueError("Stored mask does not match zero logit threshold")
            changed = torch.nonzero(mask_a != mask_b).flatten().tolist()
            query_rows.append({
                "query": query,
                "changed_point_count": len(changed),
                "changed_points": [{
                    "point_index": int(point),
                    "reference_logit": float(a[point]),
                    "candidate_logit": float(b[point]),
                    "reference_mask": bool(mask_a[point]),
                    "candidate_mask": bool(mask_b[point]),
                    "target": bool(torch.as_tensor(old["target_union"])[point]),
                } for point in changed],
                "max_abs_logit_delta": float((a - b).abs().max()),
                "mean_abs_logit_delta": float((a - b).abs().mean()),
            })
        rows.append({"manifest_index": index, "feature_deltas": feature_deltas,
                     "query_state_deltas": query_state_deltas, "queries": query_rows})
    return {
        "contract": "m95_boundary_logit_audit_v1",
        "reference_capture_sha256": EXPECTED[0],
        "candidate_capture_sha256": EXPECTED[1],
        "rows": rows,
        "strict_reproducibility_status": "fail",
        "native_backward_measured": False,
        "resources_measured": False,
        "admission": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("candidate")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(
        artifact_for(args.reference, EXPECTED[0], PAIRS),
        artifact_for(args.candidate, EXPECTED[1], PAIRS),
    )
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output, "rows": len(result["rows"]),
                      "changed_points": sum(q["changed_point_count"]
                                            for row in result["rows"] for q in row["queries"])}))


if __name__ == "__main__":
    main()
