"""Bounded one-layer upstream coupling audit for the frozen M95 checkpoint.

The existing 284-bank capture contains the input to the final decoder layer
and the final head tensors. This read-only CPU worker reconstructs that one
decoder layer, verifies its forward output against the capture, and compares
the parameter-gradient directions of:

    L_sel  = CE(indis_logits, oracle_candidate)
    L_mask = BCE+Dice(oracle_mask, ground_truth_mask)

The comparison is local to the final decoder layer. It does not propagate
through the encoder or claim a full training-time causal effect.
"""
import argparse
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path

import torch
import torch.nn.functional as F


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cosine(left, right, eps=1e-12):
    left = left.float()
    right = right.float()
    denom = float(left.norm() * right.norm())
    if denom <= eps:
        return 0.0
    return float(torch.dot(left, right) / denom)


def flat_grad(loss, parameters):
    grads = torch.autograd.grad(
        loss, parameters, retain_graph=True, allow_unused=True
    )
    pieces = []
    for parameter, grad in zip(parameters, grads):
        if grad is None:
            pieces.append(torch.zeros_like(parameter).reshape(-1))
        else:
            pieces.append(grad.reshape(-1))
    return torch.cat(pieces)


def mask_objective(logits, target, valid):
    logits = logits[valid]
    target = target[valid].float()
    bce = F.binary_cross_entropy_with_logits(logits, target)
    probs = logits.sigmoid()
    intersection = 2.0 * (probs * target).sum()
    denominator = probs.sum() + target.sum()
    dice = 1.0 - (intersection + 1e-6) / (denominator + 1e-6)
    return bce + dice


def summarize(values):
    values = sorted(float(value) for value in values)
    count = len(values)
    if not count:
        return {"count": 0}
    midpoint = count // 2
    median = (
        values[midpoint]
        if count % 2
        else 0.5 * (values[midpoint - 1] + values[midpoint])
    )
    return {
        "count": count,
        "mean": sum(values) / count,
        "median": median,
        "min": values[0],
        "max": values[-1],
        "positive_fraction": sum(value > 0 for value in values) / count,
        "negative_fraction": sum(value < 0 for value in values) / count,
    }


def parameter_groups(layer):
    return {
        "qia": list(layer.qia.parameters()),
        "qla": list(layer.qla.parameters()),
        "qqa": list(layer.qqa.parameters()),
        "qqa_ffn": list(layer.qqa_ffn.parameters()),
        "norm_qqa": list(layer.norm_qqa.parameters()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layer", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    root = Path(args.code_root)
    capture_dir = Path(args.capture)
    output = Path(args.output)
    assert not output.exists(), "Immutable output path already exists"
    assert (capture_dir / "summary.json").exists()

    sys.path[:0] = [str(root), str(root / "framework/lib")]
    dec = importlib.import_module(
        "framework.model.Quard_model."
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.dec"
    )
    layer = dec.Decoder_layer(
        d_model=256,
        nhead=8,
        hidden_dim=1024,
        dropout=0.0,
        activation_fn="gelu",
        contrastive_align_loss=True,
        num_proposal_fine=512,
        gamma=0.3,
    )
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    state = checkpoint["model"]
    prefix = f"dec.decoder_layers.{args.layer}."
    layer_state = {
        name[len(prefix):]: value
        for name, value in state.items()
        if name.startswith(prefix)
    }
    layer.load_state_dict(layer_state, strict=True)
    layer.eval()
    del checkpoint, state, layer_state
    for parameter in layer.parameters():
        parameter.requires_grad_(True)

    summary = json.loads(
        (capture_dir / "summary.json").read_text(encoding="utf-8")
    )
    assert summary["status"] == "complete"
    assert summary["checkpoint_sha256"] == sha(args.checkpoint)
    groups = parameter_groups(layer)
    all_parameters = [parameter for group in groups.values() for parameter in group]

    rows = []
    forward_errors = {
        "query": 0.0,
        "mask": 0.0,
        "indis": 0.0,
    }
    selected_rows = (
        summary["rows"][: args.limit] if args.limit else summary["rows"]
    )
    for index, row in enumerate(selected_rows):
        saved = torch.load(
            capture_dir / row["artifact"], map_location="cpu", weights_only=False
        )
        tensors = saved["tensors"]
        lang = tensors["lang_feats"].float().unsqueeze(0)
        lang_mask = tensors["lang_masks"].bool().unsqueeze(0)
        inst = tensors["inst_feats"].float().unsqueeze(0)
        batch_mask = tensors["batch_mask"].bool().unsqueeze(0)
        query_in = (
            tensors["query_in"].float().unsqueeze(0).requires_grad_(True)
        )
        gt = tensors["gt_spmask"].bool().unsqueeze(0)

        reconstructed = layer(
            lang,
            lang_mask,
            inst,
            batch_mask,
            query_in,
            None,
            None,
            None,
        )
        query, pred_scores, pred_masks, pred_indis, _, _ = reconstructed
        saved_query = tensors["query"].float()
        saved_masks = tensors["mask_logits"].float()
        saved_indis = tensors["indis_logits"].float()
        forward_errors["query"] = max(
            forward_errors["query"],
            float((query.detach() - saved_query).abs().max()),
        )
        forward_errors["mask"] = max(
            forward_errors["mask"],
            float((pred_masks.detach() - saved_masks).abs().max()),
        )
        forward_errors["indis"] = max(
            forward_errors["indis"],
            float((pred_indis.detach() - saved_indis).abs().max()),
        )

        oracle = int(row["oracle_index"])
        selected = int(torch.softmax(saved_indis, dim=-1)[:, 1].argmax())
        valid = ~batch_mask[0]
        assert valid.any()
        selection_target = torch.zeros(
            pred_indis.shape[1], dtype=torch.long
        )
        selection_target[oracle] = 1
        selection_loss = F.cross_entropy(pred_indis[0], selection_target)
        mask_loss = mask_objective(pred_masks[0, oracle], gt[0], valid)

        sel_groups = {}
        mask_groups = {}
        for name, parameters in groups.items():
            sel_groups[name] = flat_grad(selection_loss, parameters)
            mask_groups[name] = flat_grad(mask_loss, parameters)
        sel_all = torch.cat([sel_groups[name] for name in groups])
        mask_all = torch.cat([mask_groups[name] for name in groups])
        query_sel = torch.autograd.grad(
            selection_loss, query_in, retain_graph=True
        )[0].reshape(-1)
        query_mask = torch.autograd.grad(mask_loss, query_in)[0].reshape(-1)

        rows.append(
            {
                "scene_id": row["scene_id"],
                "object_id": row["object_id"],
                "ann_id": row["ann_id"],
                "artifact": row["artifact"],
                "candidate_count": int(pred_indis.shape[0]),
                "valid_superpoints": int(valid.sum()),
                "oracle_index": oracle,
                "selected_index": selected,
                "selected_iou": float(row["indis_iou"]),
                "oracle_iou": float(row["oracle_iou"]),
                "recoverable": (
                    float(row["indis_iou"]) <= 0.5
                    and float(row["oracle_iou"]) > 0.5
                ),
                "success": (
                    float(row["indis_iou"]) > 0.5
                    and float(row["oracle_iou"]) > 0.5
                ),
                "selection_loss": float(selection_loss.detach()),
                "oracle_mask_loss": float(mask_loss.detach()),
                "cos_parameter_selection_mask": cosine(sel_all, mask_all),
                "cos_query_selection_mask": cosine(query_sel, query_mask),
                "cos_group": {
                    name: cosine(sel_groups[name], mask_groups[name])
                    for name in groups
                },
            }
        )
        if (index + 1) % 25 == 0:
            print(f"AUDITED {index + 1} of {len(selected_rows)}", flush=True)

    def select(predicate):
        return [row for row in rows if predicate(row)]

    subsets = {
        "all": rows,
        "recoverable": select(lambda row: row["recoverable"]),
        "success": select(lambda row: row["success"]),
    }
    result = {
        "status": "complete",
        "protocol": (
            "One-layer upstream parameter-Jacobian audit. The final decoder "
            "layer is reconstructed from the frozen checkpoint and run on "
            "captured inputs. Parameter gradients of oracle-selection CE and "
            "oracle-mask BCE+Dice are compared. No encoder gradient and no "
            "training effect is claimed."
        ),
        "capture_summary_sha256": sha(capture_dir / "summary.json"),
        "checkpoint_sha256": summary["checkpoint_sha256"],
        "worker_sha256": sha(__file__),
        "layer": args.layer,
        "forward_max_abs_error": forward_errors,
        "subsets": {
            name: {
                "count": len(subset),
                "cos_parameter_selection_mask": summarize(
                    row["cos_parameter_selection_mask"] for row in subset
                ),
                "cos_query_selection_mask": summarize(
                    row["cos_query_selection_mask"] for row in subset
                ),
                "cos_group": {
                    group: summarize(
                        row["cos_group"][group] for row in subset
                    )
                    for group in groups
                },
            }
            for name, subset in subsets.items()
        },
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
    print("D1_UPSTREAM_LAYER_COUPLING_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
