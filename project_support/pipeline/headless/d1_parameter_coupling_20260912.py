"""Read-only query-state Jacobian audit for the frozen M95 selection/mask heads.

The 2026-09-12 semantic-projection capture contains final decoder queries,
selection logits, mask logits, instance features, and ground-truth masks for
284 fixed diagnostic banks. This script reconstructs the final decoder head
from the frozen checkpoint, verifies the captured forward tensors, and measures
whether the local selection objective and oracle-mask objective align on the
shared query state.

No model, config, checkpoint, dataset, queue, or training artifact is changed.
"""
import argparse
import json
import math
from pathlib import Path

import torch
import torch.nn.functional as F


def sha(path):
    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cosine(left, right, eps=1e-12):
    denom = float(left.norm() * right.norm())
    if denom <= eps:
        return 0.0
    return float(torch.dot(left, right) / denom)


def dice_loss(logits, target, eps=1e-6):
    probs = logits.sigmoid()
    numerator = 2 * (probs * target).sum()
    denominator = probs.sum() + target.sum()
    return 1 - (numerator + eps) / (denominator + eps)


def load_head(state, layer):
    prefix = f"dec.decoder_layers.{layer}."
    names = [
        "out_norm.weight",
        "out_norm.bias",
        "indi_embedding.0.weight",
        "indi_embedding.0.bias",
        "indi_embedding.2.weight",
        "indi_embedding.2.bias",
        "indi_embedding.3.weight",
        "indi_embedding.3.bias",
    ]
    return {name: state[prefix + name].float() for name in names}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layer", type=int, default=5)
    args = parser.parse_args()

    capture_dir = Path(args.capture)
    output = Path(args.output)
    assert not output.exists(), "Immutable output path already exists"
    summary_path = capture_dir / "summary.json"
    assert summary_path.exists(), summary_path
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["checkpoint_sha256"] == sha(args.checkpoint)

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    head = load_head(checkpoint["model"], args.layer)
    del checkpoint

    rows = []
    max_mask_error = 0.0
    max_indis_error = 0.0
    sum_mask_squared_error = 0.0
    mask_value_count = 0
    for row in summary["rows"]:
        artifact_path = capture_dir / row["artifact"]
        saved = torch.load(artifact_path, map_location="cpu", weights_only=False)
        tensors = saved["tensors"]
        identity = saved["identity"]
        assert (
            identity["scene_id"],
            str(identity["object_id"]),
            str(identity["ann_id"]),
        ) == (row["scene_id"], str(row["object_id"]), str(row["ann_id"]))

        query = tensors["query"].float()
        inst_feats = tensors["inst_feats"].float()
        batch_mask = tensors["batch_mask"].bool()
        gt_mask = tensors["gt_spmask"].bool()
        saved_indis = tensors["indis_logits"].float()
        saved_masks = tensors["mask_logits"].float()
        assert query.ndim == 2 and query.shape[1] == 256
        assert inst_feats.shape == (query.shape[0], 256) or inst_feats.shape[0] == gt_mask.numel()
        assert saved_indis.shape == (query.shape[0], 2)
        assert saved_masks.shape[0] == query.shape[0]
        assert gt_mask.numel() == saved_masks.shape[1]

        q = query.detach().requires_grad_(True)
        q_norm = F.layer_norm(
            q,
            (q.shape[-1],),
            head["out_norm.weight"],
            head["out_norm.bias"],
        )
        masks = q_norm @ inst_feats.T
        z = F.linear(
            F.relu(F.linear(q, head["indi_embedding.0.weight"], head["indi_embedding.0.bias"])),
            head["indi_embedding.2.weight"],
            head["indi_embedding.2.bias"],
        )
        z = F.linear(z, head["indi_embedding.3.weight"], head["indi_embedding.3.bias"])

        mask_error = (masks.detach() - saved_masks).abs()
        mask_max_error = float(mask_error.max())
        mask_rmse = float(torch.sqrt((mask_error**2).mean()))
        indis_error = float((z.detach() - saved_indis).abs().max())
        max_mask_error = max(max_mask_error, mask_max_error)
        max_indis_error = max(max_indis_error, indis_error)
        sum_mask_squared_error += float((mask_error**2).sum())
        mask_value_count += mask_error.numel()
        assert mask_rmse < 0.01, (row["artifact"], mask_rmse)
        assert mask_max_error < 0.1, (row["artifact"], mask_max_error)
        assert indis_error < 0.03, (row["artifact"], indis_error)

        p = z.softmax(-1)[:, 1]
        selected = int(p.argmax())
        oracle = int(row["oracle_index"])
        selected_prob = float(p[selected])
        oracle_prob = float(p[oracle])
        selection_target = torch.zeros(query.shape[0], dtype=torch.long)
        selection_target[oracle] = 1
        selection_loss = F.cross_entropy(z, selection_target)
        g_select = torch.autograd.grad(selection_loss, q, retain_graph=True)[0]
        margin = z[:, 1] - z[:, 0]
        g_margin_selected = torch.autograd.grad(
            margin[selected], q, retain_graph=True
        )[0][selected]
        g_margin_oracle = torch.autograd.grad(
            margin[oracle], q, retain_graph=True
        )[0][oracle]

        gt = gt_mask.float()
        oracle_mask_loss = F.binary_cross_entropy_with_logits(
            masks[oracle], gt
        ) + dice_loss(masks[oracle], gt)
        g_mask_oracle = torch.autograd.grad(
            oracle_mask_loss, q, retain_graph=True
        )[0][oracle]

        selected_mask_loss = F.binary_cross_entropy_with_logits(
            masks[selected], gt
        ) + dice_loss(masks[selected], gt)
        g_mask_selected = torch.autograd.grad(
            selected_mask_loss, q, retain_graph=True
        )[0][selected]

        selected_iou = float(row["indis_iou"])
        oracle_iou = float(row["oracle_iou"])
        recoverable = selected_iou <= 0.5 < oracle_iou
        rows.append(
            {
                "scene_id": row["scene_id"],
                "object_id": row["object_id"],
                "ann_id": row["ann_id"],
                "candidate_count": int(query.shape[0]),
                "superpoint_count": int(gt_mask.numel()),
                "oracle_index": oracle,
                "selected_index": selected,
                "selected_iou": selected_iou,
                "oracle_iou": oracle_iou,
                "selected_probability": selected_prob,
                "oracle_probability": oracle_prob,
                "selected_margin": float((z[selected, 1] - z[selected, 0]).detach()),
                "oracle_margin": float((z[oracle, 1] - z[oracle, 0]).detach()),
                "recoverable": bool(recoverable),
                "mask_forward_max_error": mask_max_error,
                "mask_forward_rmse": mask_rmse,
                "indis_forward_max_error": indis_error,
                "selection_to_oracle": float(selection_loss),
                "oracle_mask_loss": float(oracle_mask_loss),
                "selected_mask_loss": float(selected_mask_loss),
                "cos_select_oracle_to_oracle_mask_improve": cosine(
                    g_select[oracle], -g_mask_oracle
                ),
                "cos_select_selected_to_oracle_mask_improve": cosine(
                    g_select[selected], -g_mask_oracle
                ),
                "cos_select_selected_to_selected_mask_improve": cosine(
                    g_select[selected], -g_mask_selected
                ),
                "selection_grad_oracle_norm": float(g_select[oracle].norm()),
                "selection_grad_selected_norm": float(g_select[selected].norm()),
                "margin_grad_oracle_norm": float(g_margin_oracle.norm()),
                "margin_grad_selected_norm": float(g_margin_selected.norm()),
                "mask_grad_oracle_norm": float(g_mask_oracle.norm()),
                "mask_grad_selected_norm": float(g_mask_selected.norm()),
                "cos_margin_selected_to_oracle_mask_improve": cosine(
                    g_margin_selected, -g_mask_oracle
                ),
            }
        )

    def aggregate(values):
        values = sorted(float(value) for value in values)
        count = len(values)
        if not count:
            return {"count": 0}
        return {
            "count": count,
            "mean": sum(values) / count,
            "median": values[count // 2] if count % 2 else 0.5 * (values[count // 2 - 1] + values[count // 2]),
            "min": values[0],
            "max": values[-1],
            "positive_fraction": sum(value > 0 for value in values) / count,
            "below_minus_0_1_fraction": sum(value < -0.1 for value in values) / count,
        }

    recoverable_rows = [row for row in rows if row["recoverable"]]
    success_rows = [row for row in rows if row["selected_iou"] > 0.5 < row["oracle_iou"]]
    result = {
        "status": "complete",
        "capture_summary_sha256": sha(summary_path),
        "checkpoint_sha256": summary["checkpoint_sha256"],
        "layer": args.layer,
        "banks": len(rows),
        "recoverable_banks": len(recoverable_rows),
        "success_banks": len(success_rows),
        "reconstruction": {
            "mask_max_abs_error": max_mask_error,
            "mask_rmse": math.sqrt(sum_mask_squared_error / mask_value_count),
            "indis_max_abs_error": max_indis_error,
            "note": "Captured tensors are float16; reconstructed forward uses float32.",
        },
        "shared_head_parameter_intersection": [],
        "score_head_parameters": "dec.decoder_layers.5.indi_embedding.*",
        "mask_head_parameters": "dec.decoder_layers.5.out_norm.* and decoder query/instance features",
        "interpretation_limit": (
            "This is an exact local Jacobian of the final-head objective with "
            "respect to the frozen shared query state. It does not propagate "
            "through the upstream decoder and is not a full parameter-level "
            "training causal estimate."
        ),
        "aggregate": {
            "all": {
                "cos_select_oracle_to_oracle_mask_improve": aggregate(
                    row["cos_select_oracle_to_oracle_mask_improve"] for row in rows
                ),
                "cos_select_selected_to_oracle_mask_improve": aggregate(
                    row["cos_select_selected_to_oracle_mask_improve"] for row in rows
                ),
                "cos_select_selected_to_selected_mask_improve": aggregate(
                    row["cos_select_selected_to_selected_mask_improve"] for row in rows
                ),
                "selection_grad_oracle_zero_fraction": sum(
                    row["selection_grad_oracle_norm"] <= 1e-10 for row in rows
                )
                / len(rows),
                "selection_grad_selected_zero_fraction": sum(
                    row["selection_grad_selected_norm"] <= 1e-10 for row in rows
                )
                / len(rows),
                "margin_grad_oracle_zero_fraction": sum(
                    row["margin_grad_oracle_norm"] <= 1e-10 for row in rows
                )
                / len(rows),
                "margin_grad_selected_zero_fraction": sum(
                    row["margin_grad_selected_norm"] <= 1e-10 for row in rows
                )
                / len(rows),
                "cos_margin_selected_to_oracle_mask_improve": aggregate(
                    row["cos_margin_selected_to_oracle_mask_improve"]
                    for row in rows
                ),
                "selected_probability_gt_0_999_fraction": sum(
                    row["selected_probability"] > 0.999 for row in rows
                )
                / len(rows),
                "selected_probability": aggregate(
                    row["selected_probability"] for row in rows
                ),
                "oracle_probability": aggregate(
                    row["oracle_probability"] for row in rows
                ),
                "selected_margin": aggregate(row["selected_margin"] for row in rows),
                "oracle_margin": aggregate(row["oracle_margin"] for row in rows),
            },
            "recoverable": {
                "cos_select_oracle_to_oracle_mask_improve": aggregate(
                    row["cos_select_oracle_to_oracle_mask_improve"]
                    for row in recoverable_rows
                ),
                "cos_select_selected_to_oracle_mask_improve": aggregate(
                    row["cos_select_selected_to_oracle_mask_improve"]
                    for row in recoverable_rows
                ),
                "cos_select_selected_to_selected_mask_improve": aggregate(
                    row["cos_select_selected_to_selected_mask_improve"]
                    for row in recoverable_rows
                ),
                "selection_grad_oracle_zero_fraction": sum(
                    row["selection_grad_oracle_norm"] <= 1e-10
                    for row in recoverable_rows
                )
                / len(recoverable_rows),
                "selection_grad_selected_zero_fraction": sum(
                    row["selection_grad_selected_norm"] <= 1e-10
                    for row in recoverable_rows
                )
                / len(recoverable_rows),
                "margin_grad_oracle_zero_fraction": sum(
                    row["margin_grad_oracle_norm"] <= 1e-10
                    for row in recoverable_rows
                )
                / len(recoverable_rows),
                "margin_grad_selected_zero_fraction": sum(
                    row["margin_grad_selected_norm"] <= 1e-10
                    for row in recoverable_rows
                )
                / len(recoverable_rows),
                "cos_margin_selected_to_oracle_mask_improve": aggregate(
                    row["cos_margin_selected_to_oracle_mask_improve"]
                    for row in recoverable_rows
                ),
                "selected_probability_gt_0_999_fraction": sum(
                    row["selected_probability"] > 0.999
                    for row in recoverable_rows
                )
                / len(recoverable_rows),
                "selected_probability": aggregate(
                    row["selected_probability"] for row in recoverable_rows
                ),
                "oracle_probability": aggregate(
                    row["oracle_probability"] for row in recoverable_rows
                ),
                "selected_margin": aggregate(
                    row["selected_margin"] for row in recoverable_rows
                ),
                "oracle_margin": aggregate(
                    row["oracle_margin"] for row in recoverable_rows
                ),
            },
            "success": {
                "cos_select_oracle_to_oracle_mask_improve": aggregate(
                    row["cos_select_oracle_to_oracle_mask_improve"]
                    for row in success_rows
                ),
                "cos_select_selected_to_oracle_mask_improve": aggregate(
                    row["cos_select_selected_to_oracle_mask_improve"]
                    for row in success_rows
                ),
                "cos_select_selected_to_selected_mask_improve": aggregate(
                    row["cos_select_selected_to_selected_mask_improve"]
                    for row in success_rows
                ),
                "selection_grad_oracle_zero_fraction": sum(
                    row["selection_grad_oracle_norm"] <= 1e-10 for row in success_rows
                )
                / len(success_rows),
                "selection_grad_selected_zero_fraction": sum(
                    row["selection_grad_selected_norm"] <= 1e-10 for row in success_rows
                )
                / len(success_rows),
                "margin_grad_oracle_zero_fraction": sum(
                    row["margin_grad_oracle_norm"] <= 1e-10 for row in success_rows
                )
                / len(success_rows),
                "margin_grad_selected_zero_fraction": sum(
                    row["margin_grad_selected_norm"] <= 1e-10 for row in success_rows
                )
                / len(success_rows),
                "cos_margin_selected_to_oracle_mask_improve": aggregate(
                    row["cos_margin_selected_to_oracle_mask_improve"]
                    for row in success_rows
                ),
                "selected_probability_gt_0_999_fraction": sum(
                    row["selected_probability"] > 0.999 for row in success_rows
                )
                / len(success_rows),
                "selected_probability": aggregate(
                    row["selected_probability"] for row in success_rows
                ),
                "oracle_probability": aggregate(
                    row["oracle_probability"] for row in success_rows
                ),
                "selected_margin": aggregate(
                    row["selected_margin"] for row in success_rows
                ),
                "oracle_margin": aggregate(
                    row["oracle_margin"] for row in success_rows
                ),
            },
        },
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    print("D1_PARAMETER_COUPLING_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
