"""Bounded upstream parameter-group coupling audit for frozen M95.

This is a read-only diagnostic. It compares oracle-selection CE and
oracle-mask BCE+Dice parameter gradients in the top-level upstream parameter
groups of the frozen M95 checkpoint. It does not update a checkpoint or
admit a mechanism.
"""
import argparse
import gc
import hashlib
import importlib
import json
import logging
import os
import sys
import time
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

MANIFEST_SHA = "84a7d60f85ecd5bec44b77b304140ff00c8c1fa00177dc12ecf7ef5ebfabb468"
BUFFER_KEYS = {
    "text_encoder.embeddings.position_ids",
    "text_encoder.embeddings.token_type_ids",
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def key(record):
    return record["scene_id"], str(record["object_id"]), str(record["ann_id"])


def cosine(left, right, eps=1e-12):
    left = left.float()
    right = right.float()
    denominator = float(left.norm() * right.norm())
    if denominator <= eps:
        return 0.0
    return float((left * right).sum() / denominator)


def flat_grad(loss, parameters, retain_graph):
    torch = __import__("torch")
    grads = torch.autograd.grad(
        loss, parameters, retain_graph=retain_graph, allow_unused=True
    )
    pieces = []
    for parameter, grad in zip(parameters, grads):
        if grad is None:
            pieces.append(parameter.new_zeros(parameter.numel()))
        else:
            pieces.append(grad.reshape(-1))
    return torch.cat(pieces)


def mask_objective(logits, target, valid):
    torch = __import__("torch")
    F = __import__("torch.nn.functional", fromlist=["binary_cross_entropy_with_logits"])
    logits = logits[valid].float()
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


def top_level_group(name):
    if name.startswith("dec.decoder_layers."):
        return "decoder_layers"
    if name.startswith("dec."):
        return "dec_shared"
    return name.split(".", 1)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scene-limit", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-memory-gb", type=float, default=7.0)
    args = parser.parse_args()

    root = Path(args.code_root)
    output = Path(args.out)
    assert not output.exists(), "Immutable output directory already exists"
    assert sha(args.manifest) == MANIFEST_SHA
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    assert sha(audit["checkpoint"]) == audit["checkpoint_sha256"]
    assert sha(audit["config"]) == audit["config_sha256"]

    import subprocess

    assert subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip() == audit["code_head"]

    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import gorilla
    import torch
    import torch.nn.functional as F
    from framework.dataset import build_dataset

    torch.set_num_threads(1)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the bounded diagnostic")
    free, total = torch.cuda.mem_get_info()
    if free < 3 * 1024**3:
        raise RuntimeError(f"Insufficient preflight free memory: {free}")
    torch.cuda.set_per_process_memory_fraction(
        min(args.max_memory_gb * 1024**3 / total, 0.95)
    )
    gorilla.set_random_seed(1999)
    cfg = gorilla.Config.fromfile(audit["config"])
    assert cfg.test.seed == 1999
    assert not cfg.data.val.training and cfg.data.val.get("src_sample", -1) == -1

    data_root = Path(cfg.data.val.data_root)
    source = data_root / "scanrefer/ScanRefer_val_new.json"
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    assert sha(source) == manifest["source_sha256"]
    records = json.loads(source.read_text(encoding="utf-8"))
    by_key = {key(record): record for record in records}
    assert len(by_key) == len(records)
    samples = [
        sample for sample in manifest["samples"] if sample["subset"] == "diagnostic"
    ]
    scenes = sorted({sample["scene_id"] for sample in samples})
    if args.scene_limit:
        scenes = scenes[: args.scene_limit]
    chosen = [sample for sample in samples if sample["scene_id"] in scenes]
    if args.limit:
        chosen = chosen[: args.limit]
    assert chosen

    module = importlib.import_module(audit["explicit_module"])
    package = Path(module.__file__).parent
    assert {path.name: sha(path) for path in sorted(package.glob("*.py"))} == audit[
        "package_sha256"
    ]
    get_iou = importlib.import_module(audit["explicit_module"] + ".loss").get_iou
    model = module.Network(**cfg.model)
    assert model.task_type == "res"
    checkpoint = torch.load(
        audit["checkpoint"], map_location="cpu", weights_only=False
    )
    state = checkpoint["model"]
    expected = model.state_dict()
    assert set(state) - set(expected) == BUFFER_KEYS
    assert not set(expected) - set(state)
    for name in BUFFER_KEYS:
        runtime = getattr(
            model.text_encoder.embeddings, name.rsplit(".", 1)[1]
        )
        assert torch.equal(state[name], runtime)
    model.load_state_dict(
        {name: value for name, value in state.items() if name not in BUFFER_KEYS},
        strict=True,
    )
    del state, checkpoint, expected
    gc.collect()
    model.cuda().eval()

    logger = logging.getLogger("upstream_group_coupling")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    dataset = build_dataset(cfg.data.val, logger)
    dataset.scene_inputs = [[by_key[key(sample)]] for sample in chosen]

    captured = {}

    def capture_decoder(module, inputs, output):
        captured["out"] = output

    handle = model.dec.register_forward_hook(capture_decoder)
    layers = list(model.dec.decoder_layers)

    grouped = {}
    seen = set()
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad or id(parameter) in seen:
            continue
        seen.add(id(parameter))
        grouped.setdefault(top_level_group(name), []).append(parameter)
    group_names = sorted(grouped)
    all_params = [parameter for name in group_names for parameter in grouped[name]]
    offsets = {}
    cursor = 0
    for name in group_names:
        end = cursor + sum(parameter.numel() for parameter in grouped[name])
        offsets[name] = (cursor, end)
        cursor = end

    rows = []
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for index in range(len(dataset)):
        assert time.monotonic() - start < 1800, "Audit time budget exceeded"
        free, _ = torch.cuda.mem_get_info()
        assert free >= 2 * 1024**3, "Shared memory headroom dropped"
        sample = chosen[index]
        batch = dataset.collate_fn([dataset[index]])
        captured.clear()
        with torch.enable_grad():
            model(batch, mode="predict")
        out = captured.get("out")
        assert out is not None
        aux = out.get("aux_outputs", [])
        layer_masks = [item["masks"] for item in aux] + [out["masks"]]
        layer_indis = [item["indis"] for item in aux] + [out["indis"]]
        assert len(layer_masks) == len(layer_indis) == len(layers)

        batch_mask = out["batch_mask"].bool()
        valid = ~batch_mask[0]
        gt = batch["gt_spmasks"][0].bool().to(batch_mask.device)
        assert gt.numel() == valid.numel()

        selection_losses = []
        mask_losses = []
        layer_meta = []
        for layer_index, (masks, indis) in enumerate(
            zip(layer_masks, layer_indis)
        ):
            masks = masks[0].float()
            indis = indis[0].float()
            with torch.no_grad():
                target = gt.unsqueeze(0).expand_as(masks)
                candidate_ious = get_iou(masks, target).float()
                oracle = int(candidate_ious.argmax())
            selection_target = torch.zeros(
                indis.shape[0], dtype=torch.long, device=indis.device
            )
            selection_target[oracle] = 1
            selection_losses.append(
                F.cross_entropy(indis, selection_target)
            )
            mask_losses.append(mask_objective(masks[oracle], gt, valid))
            layer_meta.append(
                {
                    "layer": layer_index,
                    "oracle_index": oracle,
                    "oracle_iou": float(candidate_ious[oracle].detach()),
                }
            )

        selection_total = sum(selection_losses)
        mask_total = sum(mask_losses)
        selection_gradient = flat_grad(
            selection_total, all_params, retain_graph=True
        )
        mask_gradient = flat_grad(
            mask_total, all_params, retain_graph=False
        )
        group_meta = {}
        for name in group_names:
            start_offset, end_offset = offsets[name]
            group_meta[name] = {
                "cos_parameter_selection_mask": cosine(
                    selection_gradient[start_offset:end_offset],
                    mask_gradient[start_offset:end_offset],
                ),
                "selection_gradient_norm": float(
                    selection_gradient[start_offset:end_offset].norm()
                ),
                "mask_gradient_norm": float(
                    mask_gradient[start_offset:end_offset].norm()
                ),
                "parameter_count": int(
                    sum(parameter.numel() for parameter in grouped[name])
                ),
            }

        final_probs = F.softmax(layer_indis[-1][0].float(), dim=-1)[:, 1]
        final_selected = int(final_probs.argmax())
        final_oracle = int(layer_meta[-1]["oracle_index"])
        final_masks = layer_masks[-1][0].float().unsqueeze(0)
        final_ious = get_iou(final_masks, gt.unsqueeze(0))[0]
        final_selected_iou = float(final_ious[final_selected].detach())
        final_oracle_iou = float(final_ious[final_oracle].detach())
        rows.append(
            {
                "scene_id": sample["scene_id"],
                "object_id": str(sample["object_id"]),
                "ann_id": str(sample["ann_id"]),
                "candidate_count": int(final_probs.numel()),
                "valid_superpoints": int(valid.sum()),
                "final_selected_index": final_selected,
                "final_selected_iou": final_selected_iou,
                "final_oracle_index": final_oracle,
                "final_oracle_iou": final_oracle_iou,
                "recoverable": (
                    final_selected_iou <= 0.5 and final_oracle_iou > 0.5
                ),
                "success": (
                    final_selected_iou > 0.5 and final_oracle_iou > 0.5
                ),
                "groups": group_meta,
            }
        )
        del batch, out, aux, layer_masks, layer_indis, selection_losses
        del mask_losses, selection_total, mask_total
        del selection_gradient, mask_gradient
        if (index + 1) % 10 == 0:
            gc.collect()
            torch.cuda.empty_cache()
        if (index + 1) % 20 == 0:
            print(f"AUDITED {index + 1} of {len(chosen)}", flush=True)

    handle.remove()
    subsets = {
        "all": rows,
        "recoverable": [row for row in rows if row["recoverable"]],
        "success": [row for row in rows if row["success"]],
    }
    group_summary = {}
    for subset_name, subset in subsets.items():
        group_summary[subset_name] = {}
        for name in group_names:
            group_summary[subset_name][name] = {
                "cosine": summarize(
                    row["groups"][name]["cos_parameter_selection_mask"]
                    for row in subset
                ),
                "selection_gradient_norm": summarize(
                    row["groups"][name]["selection_gradient_norm"]
                    for row in subset
                ),
                "mask_gradient_norm": summarize(
                    row["groups"][name]["mask_gradient_norm"]
                    for row in subset
                ),
                "parameter_count": next(
                    row["groups"][name]["parameter_count"] for row in rows
                ),
            }

    summary = {
        "status": "complete",
        "protocol": (
            "Read-only upstream parameter-group gradient audit. The frozen "
            "M95 checkpoint is run with gradients enabled on the 284-bank "
            "diagnostic manifest. Oracle-selection CE and oracle-mask "
            "BCE+Dice gradients are compared in top-level parameter groups. "
            "No training or mechanism admission follows."
        ),
        "checkpoint_sha256": audit["checkpoint_sha256"],
        "module": audit["explicit_module"],
        "audit_sha256": sha(args.audit),
        "manifest_sha256": sha(args.manifest),
        "worker_sha256": sha(__file__),
        "selected_scenes": scenes,
        "descriptions": len(rows),
        "limits": {"scene_limit": args.scene_limit, "limit": args.limit},
        "subsets": {name: len(subset) for name, subset in subsets.items()},
        "group_names": group_names,
        "group_summary": group_summary,
        "elapsed_seconds": time.monotonic() - start,
        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024**2,
        "peak_reserved_mib": torch.cuda.max_memory_reserved() / 1024**2,
        "rows": rows,
        "limitation": (
            "The audit measures local parameter-gradient alignment on one "
            "frozen checkpoint and one validation-derived manifest. It does "
            "not establish full-model causality, training efficacy, or "
            "primary-source novelty."
        ),
    }
    output.mkdir(parents=True)
    (output / "result.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    lines = [
        "# M95 Upstream Parameter-Group Coupling Audit",
        "",
        f"Date: 2026-09-12. Read-only gradient audit on {len(rows)} frozen banks.",
        "",
        "## Question",
        "",
        "Do top-level upstream parameter groups contain a systematic direction",
        "that jointly improves oracle selection and oracle mask quality?",
        "",
        "## Parameter-Gradient Cosine By Group",
        "",
        "| Group | Recoverable mean | Recoverable median | Negative fraction | Success mean |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in group_names:
        recoverable = group_summary["recoverable"][name]["cosine"]
        success = group_summary["success"][name]["cosine"]
        lines.append(
            f"| {name} | {recoverable.get('mean', 0.0):.5f} | "
            f"{recoverable.get('median', 0.0):.5f} | "
            f"{recoverable.get('negative_fraction', 0.0):.4f} | "
            f"{success.get('mean', 0.0):.5f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Positive cosine means the two objectives push a group in",
            "  compatible directions on the frozen bank.",
            "- Gradient norms are reported in `result.json`; a cosine without",
            "  the corresponding norms is not interpreted as a mechanism.",
            "- This is a diagnostic of the current checkpoint, not a causal",
            "  training result or an admission of a new mechanism.",
            "",
            "## Limitation",
            "",
            "Groups share upstream paths, success banks are controls rather",
            "than independent samples, and the bank set is validation-derived",
            "and previously mined. The result cannot authorize training or",
            "label a parameter direction as a novel contribution.",
        ]
    )
    (output / "diagnostic_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {name: value for name, value in summary.items() if name != "rows"},
            indent=2,
        )
    )
    print("D1_UPSTREAM_GROUP_COUPLING_COMPLETE", output, flush=True)


if __name__ == "__main__":
    main()
