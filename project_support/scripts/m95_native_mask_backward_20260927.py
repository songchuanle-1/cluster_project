"""Replay champion's native matched-mask loss on frozen final logits."""
import argparse
import importlib.util
import json
from pathlib import Path

from m95_target_seed_full_population_20260927 import (
    CAPTURE_SHA, CHECKPOINT_SHA, MANIFEST_SHA, PRODUCER_SHA, sha,
)

SUPPORT_SHA = "0cc44842f05d713e2cc221de7f9a34ff4a59a3210d7b7d18c9ad9879de257cb2"
LOSS_SHA = "c172cfb26706c0dd335e0cab4e2ac0823e0b057a00352863151e24d5547ccbf5"


def evaluate(row, artifact, criterion):
    import torch
    query = int(row["selected_query"])
    positives = [i for i, flag in enumerate(row["native_positive"]) if flag]
    if (query not in positives or artifact["manifest_index"] != row["manifest_index"]
            or artifact["manifest_sha256"] != MANIFEST_SHA
            or artifact["axis"]["scene"] != row["scene"]
            or int(artifact["axis"]["ann_id"]) != row["ann_id"]
            or len(positives) == 0):
        raise ValueError("Native match/capture binding differs")
    mask = artifact["query_masks"][query].bool()
    target = artifact["target_union"].bool()
    iou = (mask & target).sum().item() / max(1, (mask | target).sum().item())
    if abs(iou - row["ious"][query]) > 1e-6:
        raise ValueError("Native selected IoU differs")
    logits = artifact["query_mask_logits"].detach().float().requires_grad_(True)
    scores = artifact["query_scores"].detach().float().view(-1, 1)
    idx = torch.tensor(positives, dtype=torch.long)
    target_masks = target.float().unsqueeze(0).repeat(len(positives), 1)
    bce, dice, score = criterion.loss_masks(
        [logits], [scores], [{"masks": target_masks}],
        [(idx, torch.arange(len(positives)))], torch.tensor([len(positives)], dtype=torch.float))
    (bce + dice).backward()
    grad = logits.grad[query]
    fn, fp = target & ~mask, ~target & mask
    return {
        "manifest_index": row["manifest_index"], "scene": row["scene"],
        "ann_id": row["ann_id"], "selected_iou": iou,
        "matched_queries": len(positives),
        "fn": int(fn.sum()), "fp": int(fp.sum()),
        "fn_correct": int((grad[fn] < 0).sum()),
        "fp_correct": int((grad[fp] > 0).sum()),
        "fn_min_abs_grad": float(grad[fn].abs().min()) if fn.any() else None,
        "fp_min_abs_grad": float(grad[fp].abs().min()) if fp.any() else None,
        "score_loss": float(score.item()),
        "all_finite": bool(torch.isfinite(grad).all()),
    }


def analyze(capture_path, support_path, artifact_root, loss_path):
    import torch
    if (sha(capture_path) != CAPTURE_SHA or sha(support_path) != SUPPORT_SHA
            or sha(loss_path) != LOSS_SHA):
        raise ValueError("Frozen capture/support/loss differs")
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    support = json.loads(support_path.read_text(encoding="utf-8"))
    if (capture["producer_sha256"] != PRODUCER_SHA
            or capture["checkpoint_sha256"] != CHECKPOINT_SHA
            or capture["manifest"]["sha256"] != MANIFEST_SHA
            or capture["capture_mode"] != "full_train_scan"
            or len(capture["rows"]) != 256):
        raise ValueError("Capture contract differs")
    spec = importlib.util.spec_from_file_location("m95_native_loss", loss_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    criterion = module.Criterion.__new__(module.Criterion)
    failures = {r["manifest_index"] for r in support["failure_rows"]}
    controls = {r["manifest_index"] for r in support["control_rows"]}
    if len(failures) != 4 or len(controls) != 4 or failures & controls:
        raise ValueError("Frozen cohort differs")
    rows = {r["manifest_index"]: r for r in capture["rows"]}
    pending, result = failures | controls, {}
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
                result[index] = evaluate(rows[index], artifact, criterion)
                pending.remove(index)
    if pending:
        raise ValueError("Missing cohort artifact")
    a, b = [result[i] for i in sorted(failures)], [result[i] for i in sorted(controls)]
    return {
        "contract": "m95_native_mask_backward_v1", "admission": False,
        "capture_sha256": CAPTURE_SHA, "support_sha256": SUPPORT_SHA,
        "loss_sha256": LOSS_SHA, "failure_rows": a, "control_rows": b,
        "failure_corrective": all(r["all_finite"] and r["fn"] == r["fn_correct"]
                                  and r["fp"] == r["fp_correct"] for r in a),
        "limits": "Champion final-loss subgraph only; no candidate backward or trained efficacy.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--support", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--loss", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    result = analyze(args.capture, args.support, args.artifact_root, args.loss)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"failure_corrective": result["failure_corrective"],
                      "failure_count": len(result["failure_rows"]),
                      "control_count": len(result["control_rows"])}))


if __name__ == "__main__":
    main()
