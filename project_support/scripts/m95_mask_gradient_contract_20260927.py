"""Check native BCE direction on frozen positive query error superpoints."""
import argparse
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, MANIFEST_SHA, sha,
)


def evaluate(row, artifact):
    import torch
    query = int(row["selected_query"])
    if (artifact["manifest_index"] != row["manifest_index"]
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]
            or not row["native_positive"][query]):
        raise ValueError("Native positive query identity differs")
    logits = artifact["query_mask_logits"][query].detach().float()
    target = artifact["target_union"].bool()
    mask = artifact["query_masks"][query].bool()
    if logits.shape != target.shape or mask.shape != target.shape:
        raise ValueError("Mask/logit support differs")
    recomputed = (mask & target).sum().item() / max(1, (mask | target).sum().item())
    if abs(recomputed - row["ious"][query]) > 1e-6:
        raise ValueError("Native IoU differs")
    grad = torch.sigmoid(logits) - target.float()
    fn = target & ~mask
    fp = ~target & mask
    if not (torch.isfinite(grad).all() and torch.isfinite(logits).all()):
        raise ValueError("Nonfinite native logits")
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "selected_iou": recomputed,
        "fn": int(fn.sum()), "fp": int(fp.sum()),
        "fn_nonzero_correct_direction": int((grad[fn] < 0).sum()),
        "fp_nonzero_correct_direction": int((grad[fp] > 0).sum()),
        "fn_mean_abs_bce_derivative": float(grad[fn].abs().mean()) if fn.any() else None,
        "fp_mean_abs_bce_derivative": float(grad[fp].abs().mean()) if fp.any() else None,
        "all_mean_abs_bce_derivative": float(grad.abs().mean()),
    }


def analyze(capture_path, support_path, artifact_root):
    import torch

    if sha(capture_path) != CAPTURE_SHA:
        raise ValueError("Frozen capture differs")
    support = json.loads(support_path.read_text(encoding="utf-8"))
    if (support["contract"] != "m95_target_support_contract_v1"
            or support["capture_sha256"] != CAPTURE_SHA):
        raise ValueError("Control selection contract differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    if len(rows) != 256:
        raise ValueError("Capture population differs")
    failures = {r["manifest_index"] for r in support["failure_rows"]}
    controls = {r["manifest_index"] for r in support["control_rows"]}
    if len(failures) != 4 or len(controls) != 4 or failures & controls:
        raise ValueError("Frozen cohort differs")
    pending = failures | controls
    result = {}
    for entry in capture["feature_artifacts"]:
        if not pending:
            break
        path = artifact_root / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("Artifact hash differs")
        for artifact in torch.load(path, map_location="cpu", weights_only=False):
            index = int(artifact["manifest_index"])
            if index in pending:
                if artifact["artifact_contract"] != capture["artifact_contract"]:
                    raise ValueError("Artifact contract differs")
                result[index] = evaluate(rows[index], artifact)
                pending.remove(index)
    if pending:
        raise ValueError("Missing cohort artifact")
    failure_rows = [result[i] for i in sorted(failures)]
    control_rows = [result[i] for i in sorted(controls)]
    return {
        "contract": "m95_mask_gradient_contract_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "support_sha256": sha(support_path),
        "failure_rows": failure_rows, "control_rows": control_rows,
        "failure_correct_direction": all(
            r["fn"] == r["fn_nonzero_correct_direction"]
            and r["fp"] == r["fp_nonzero_correct_direction"]
            for r in failure_rows),
        "limits": "Analytical native BCE derivative, not a native new-model backward or efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.support, args.artifact_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"failure_correct_direction": result["failure_correct_direction"],
                      "failure_count": len(result["failure_rows"]),
                      "control_count": len(result["control_rows"])}))


if __name__ == "__main__":
    main()
