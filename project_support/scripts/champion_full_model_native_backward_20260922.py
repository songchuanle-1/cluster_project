"""Exercise the bound champion through one synthetic full-model native backward.

The batch mirrors the tensors produced by ``scannetv2_sample_graph_edge.collate_fn``
for one scene with one expression. The probe calls the production
``Network.forward(..., mode="loss")`` path, so the text encoder, decoder, cluster
attention, sampler, matching code and criterion all execute before backward.

This is a runtime-contract diagnostic only. It does not load a checkpoint, build
the dataset, run an optimizer, or provide efficacy or admission evidence.
"""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np


CONTRACT = "champion-full-model-native-backward-v1"
CHAMPION_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CHAMPION_CONFIG = (
    "configs/Quard/ctf_hcg_csort/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml")
EXPECTED_MODEL_SOURCE_SHA256 = (
    "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0")
EXPECTED_CONFIG_SHA256 = (
    "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a")
MIN_FREE_MIB = 8192
N_POINTS = 8192
N_SUPERPOINTS = 512
POINTS_PER_SUPERPOINT = N_POINTS // N_SUPERPOINTS
GRID = 64
LANG_LEN = 4
SEED = 1999
INACTIVE_ROUTING_PREFIXES = (
    "dec.cluster_att.query_linear.",
    "dec.cluster_att.k_linear.",
    "dec.cluster_att.v_linear.",
)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_package_sha256(code_root, model_class):
    package = Path(code_root) / "framework/model/Quard_model" / model_class
    if not package.is_dir():
        raise ValueError("Bound model package is missing")
    sources = sorted(package.rglob("*.py"))
    if not sources:
        raise ValueError("Bound model package has no Python sources")
    digest = hashlib.sha256()
    for path in sources:
        relative = path.relative_to(package).as_posix().encode("ascii")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _write_new(path, value):
    output = Path(path)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("Fresh output path required")
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")
    descriptor = os.open(
        output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return output, hashlib.sha256(encoded).hexdigest()


def _build_dense_map(torch):
    positive_map = torch.zeros(1, 256)
    positive_map[:, [0, 1, 2]] = 1.0
    modify_positive_map = torch.zeros(1, 256)
    modify_positive_map[:, [0, 1]] = 1.0
    pron_positive_map = torch.zeros(1, 256)
    pron_positive_map[:, [2]] = 1.0
    return {
        "positive_map": positive_map,
        "modify_positive_map": modify_positive_map,
        "pron_positive_map": pron_positive_map,
        "other_entity_map": torch.zeros(1, 256),
        "rel_positive_map": torch.zeros(1, 256),
    }


def _set_target_support(torch, batch, labels):
    object_id = 1
    labels = labels.long()
    target_superpoints = (labels == object_id)
    batch["sp_ins_labels"] = [labels]
    batch["gt_spmasks"] = [target_superpoints.float()]
    batch["sp_ref_masks"] = [
        torch.where(
            target_superpoints,
            torch.ones_like(labels, dtype=torch.float32),
            torch.full_like(labels, 0.5, dtype=torch.float32))
    ]
    batch["gt_pmasks"] = [
        target_superpoints[batch["superpoints"].long()].float()
    ]


def _calibrate_support_mask(torch, prediction_masks, allowed_queries):
    layer_logits = []
    layer_masks = []
    for masks in prediction_masks:
        if masks.ndim == 3:
            masks = masks[0]
        if masks.ndim != 2:
            raise ValueError(
                "Unexpected predicted-mask shape: %s" % list(masks.shape))
        layer_logits.append(masks)
        layer_masks.append(masks.sigmoid() >= 0.5)

    if not allowed_queries:
        raise ValueError("Criterion reported no matched query")
    candidates = []
    for layer_index, masks in enumerate(layer_logits):
        for query_id in sorted(allowed_queries):
            selected_scores = masks[query_id]
            target = selected_scores.sigmoid() >= 0.5
            missing_support = 64 - int(target.sum().item())
            if missing_support > 0:
                candidates_for_padding = torch.nonzero(
                    ~target, as_tuple=False).squeeze(-1)
                add_count = min(
                    missing_support, int(candidates_for_padding.numel()))
                add_indices = candidates_for_padding[
                    torch.topk(
                        selected_scores[candidates_for_padding],
                        add_count, largest=True).indices]
                target[add_indices] = True
            ious = []
            for other_masks in layer_masks:
                intersection = (other_masks & target).sum(dim=-1)
                union = (
                    other_masks.sum(dim=-1)
                    + target.sum()
                    - intersection)
                ious.append(float(
                    (intersection / union.clamp_min(1)).max().item()))
            candidates.append({
                "target": target,
                "source_layer": layer_index,
                "source_query": int(query_id),
                "min_layer_iou": min(ious),
                "layer_iou": ious,
            })
    if not candidates:
        raise ValueError("Prediction contained no positive mask candidate")
    best = max(candidates, key=lambda item: item["min_layer_iou"])
    return best


def _make_batch(torch, pointgroup_ops, data_root):
    generator = torch.Generator(device="cpu").manual_seed(SEED)

    xyz = torch.randint(
        0, GRID, (N_POINTS, 3), generator=generator, dtype=torch.long)
    batch_idx = torch.zeros(N_POINTS, 1, dtype=torch.long)
    coords = torch.cat((batch_idx, xyz), dim=1).long().contiguous()

    voxel_coords, p2v_map, v2p_map = pointgroup_ops.voxelization_idx(
        coords, 1, 4)
    spatial_shape_np = np.clip(
        (coords.max(0)[0][1:] + 1).numpy(), 128, None)
    spatial_shape = torch.tensor(
        [int(value) for value in spatial_shape_np], dtype=torch.long)

    coords_float = torch.rand(
        N_POINTS, 3, generator=generator, dtype=torch.float32)
    rgb = torch.rand(
        N_POINTS, 3, generator=generator, dtype=torch.float32)
    feats = torch.cat((rgb, coords_float), dim=1).contiguous()

    superpoints = torch.arange(
        N_SUPERPOINTS, dtype=torch.long).repeat_interleave(
            POINTS_PER_SUPERPOINT)
    sp_ins_labels = torch.zeros(N_SUPERPOINTS, dtype=torch.long)
    sp_ins_labels[N_SUPERPOINTS // 2:] = 1
    object_id = 1
    gt_spmask = (sp_ins_labels == object_id).float()
    sp_ref_mask = torch.where(
        sp_ins_labels == object_id,
        torch.ones_like(sp_ins_labels, dtype=torch.float32),
        torch.full_like(
            sp_ins_labels, 0.5, dtype=torch.float32))
    gt_pmask = (superpoints == object_id).float()

    # Valid RoBERTa ids for a short synthetic sentence. The dense maps use token
    # positions that are present after the criterion slices them to this length.
    lang_tokenss = torch.tensor(
        [[0, 100, 200, 2]], dtype=torch.long)
    lang_masks = torch.ones_like(lang_tokenss)
    feats_2d = torch.randn(
        N_SUPERPOINTS, 1024, generator=generator)

    batch = {
        "ann_ids": ["synthetic-ann"],
        "scan_ids": ["synthetic-scene"],
        "voxel_coords": voxel_coords,
        "p2v_map": p2v_map,
        "v2p_map": v2p_map,
        "spatial_shape": spatial_shape,
        "feats": feats,
        "superpoints": superpoints,
        "batch_offsets": torch.tensor([0, N_SUPERPOINTS], dtype=torch.int),
        "object_idss": [[object_id]],
        "gt_pmasks": [gt_pmask],
        "gt_spmasks": [gt_spmask],
        "sp_ref_masks": [sp_ref_mask],
        "lang_tokenss": lang_tokenss,
        "lang_masks": lang_masks,
        "coords_float": coords_float,
        "sp_ins_labels": [sp_ins_labels],
        "scenes_len": torch.tensor([1], dtype=torch.int),
        "meta_datas": [None],
        "view_dependents": [None],
        "dense_maps": [_build_dense_map(torch)],
        "feats_2d": feats_2d,
    }
    _set_target_support(torch, batch, sp_ins_labels)
    return batch, {
        "points": N_POINTS,
        "voxels": int(voxel_coords.shape[0]),
        "superpoints": N_SUPERPOINTS,
        "spatial_shape": spatial_shape.tolist(),
        "language_tokens": LANG_LEN,
        "target_superpoints": int(gt_spmask.sum().item()),
        "data_root": str(data_root),
    }


def _gradient_summary(torch, model):
    groups = {}
    trainable_total = 0
    trainable_with_grad = 0
    trainable_nonzero = 0
    nonfinite = []
    trainable_missing = []

    for name, parameter in model.named_parameters():
        top = name.split(".", 1)[0]
        entry = groups.setdefault(
            top, {
                "tensors": 0,
                "params": 0,
                "trainable_tensors": 0,
                "with_grad_tensors": 0,
                "nonzero_grad_tensors": 0,
                "grad_abs_sum": 0.0,
            })
        entry["tensors"] += 1
        entry["params"] += parameter.numel()

        if parameter.requires_grad:
            trainable_total += 1
            entry["trainable_tensors"] += 1
        if parameter.grad is None:
            if parameter.requires_grad:
                trainable_missing.append(name)
            continue

        grad = parameter.grad
        finite = bool(torch.isfinite(grad).all().item())
        if not finite:
            nonfinite.append(name)
        if parameter.requires_grad:
            trainable_with_grad += 1
            entry["with_grad_tensors"] += 1
        grad_abs_sum = float(grad.abs().sum().item())
        entry["grad_abs_sum"] += grad_abs_sum
        if grad_abs_sum > 0.0:
            if parameter.requires_grad:
                trainable_nonzero += 1
            entry["nonzero_grad_tensors"] += 1

    return {
        "trainable_tensors": trainable_total,
        "trainable_with_grad": trainable_with_grad,
        "trainable_nonzero_grad": trainable_nonzero,
        "trainable_missing_grad": trainable_missing,
        "nonfinite_grad": nonfinite,
        "groups": dict(sorted(groups.items())),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise ValueError("Native probe must run on POSIX")

    os.environ.update(
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false")

    code_root = Path(args.code_root).resolve(strict=True)
    data_root = args.data_root
    for entry in (
            str(code_root), str(code_root / "framework" / "lib"),
            str(code_root / "scripts")):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices != "7":
        raise ValueError("CUDA_VISIBLE_DEVICES must be 7")

    started = time.time()
    model_source_sha256 = _model_package_sha256(
        code_root, CHAMPION_CLASS)
    if model_source_sha256 != EXPECTED_MODEL_SOURCE_SHA256:
        raise ValueError("Bound model package source digest changed")
    config_path = code_root / CHAMPION_CONFIG
    config_sha256 = _sha256(config_path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError("Bound config digest changed")

    import gorilla
    import pointgroup_ops
    import torch
    from framework import resolve_network

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.20)
    torch.cuda.init()
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    free_mib = free_bytes / 1024 / 1024
    if free_mib < MIN_FREE_MIB:
        raise ValueError("Insufficient free GPU memory: %.1f MiB" % free_mib)

    cfg = gorilla.Config.fromfile(str(config_path))
    model_kwargs = dict(cfg.model)
    model_kwargs["data_root"] = data_root

    Network = resolve_network(str(config_path))
    expected_module = (
        "framework.model.Quard_model.%s.network" % CHAMPION_CLASS)
    if Network.__module__ != expected_module:
        raise ValueError("Network resolution fell back: %s" % Network.__module__)

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    model = Network(**model_kwargs).cuda()
    model.train()
    model.text_encoder.eval()

    batch, input_summary = _make_batch(torch, pointgroup_ops, data_root)
    batch["feats"] = batch["feats"].cuda().requires_grad_(True)

    # The production score loss only runs for queries whose predicted mask has
    # IoU > 0.5. A randomly initialized model normally has none, leaving the
    # score heads without a backward path. Calibrate one synthetic support mask
    # from a train-mode prediction so the score head is exercised as well; this
    # target is diagnostic only and is never treated as supervision evidence.
    held_prediction = {}
    held_matching = {}

    def capture_prediction(_module, inputs):
        held_prediction["pred"] = inputs[0]

    native_loss_masks = model.criterion.loss_masks

    def capture_matching(pred_masks, pred_scores, targets, indices, num_boxes):
        held_matching["indices"] = [
            (pair[0].detach(), pair[1].detach()) for pair in indices]
        return native_loss_masks(
            pred_masks, pred_scores, targets, indices, num_boxes)

    capture_hook = model.criterion.register_forward_pre_hook(capture_prediction)
    model.criterion.loss_masks = capture_matching
    try:
        with torch.no_grad():
            model(batch, mode="loss")
    finally:
        capture_hook.remove()
        model.criterion.loss_masks = native_loss_masks
    prediction = held_prediction.get("pred")
    if prediction is None:
        raise ValueError("Warm-up did not expose a criterion prediction")
    matched_indices = held_matching.get("indices")
    if not matched_indices:
        raise ValueError("Warm-up did not expose criterion matching")
    allowed_queries = {
        int(query_id)
        for pair in matched_indices
        for query_id in pair[0].detach().cpu().tolist()
    }
    selected = _calibrate_support_mask(
        torch, prediction["masks"], allowed_queries)
    support = selected["target"]
    calibrated_labels = torch.zeros(
        N_SUPERPOINTS, dtype=torch.long, device=support.device)
    calibrated_labels[support] = 1
    _set_target_support(
        torch, batch, calibrated_labels.detach().cpu())
    input_summary["target_selection"] = {
        "source": "train_mode_model_prediction",
        "source_layer": selected["source_layer"],
        "query_index": selected["source_query"],
        "matched_queries": sorted(allowed_queries),
        "min_layer_iou": selected["min_layer_iou"],
        "layer_iou": selected["layer_iou"],
        "support_superpoints": int(calibrated_labels.sum().item()),
        "diagnostic_only": True,
    }
    model.zero_grad(set_to_none=True)

    calls = {
        "text_encoder": 0,
        "decoder": 0,
        "cluster_attention": 0,
        "sampling_module": 0,
        "criterion": 0,
    }
    shapes = {}

    def text_hook(_module, _inputs, output):
        calls["text_encoder"] += 1
        shapes["text_encoder_output"] = list(output[0].shape)

    def decoder_hook(_module, _inputs, output):
        calls["decoder"] += 1
        shapes["decoder_masks"] = list(output["masks"][0].shape)
        shapes["decoder_scores"] = list(output["scores"][0].shape)

    def cluster_hook(_module, _inputs, _output):
        calls["cluster_attention"] += 1

    def sampling_hook(_module, _inputs, _output):
        calls["sampling_module"] += 1

    def criterion_hook(_module, _inputs, output):
        calls["criterion"] += 1
        shapes["criterion_loss_terms"] = len(output[1])

    hooks = [
        model.text_encoder.register_forward_hook(text_hook),
        model.dec.register_forward_hook(decoder_hook),
        model.dec.cluster_att.register_forward_hook(cluster_hook),
        model.dec.sampling_module.register_forward_hook(sampling_hook),
        model.criterion.register_forward_hook(criterion_hook),
    ]

    torch.cuda.reset_peak_memory_stats(0)
    try:
        forward_started = time.time()
        loss, loss_dict = model(batch, mode="loss")
        torch.cuda.synchronize()
        forward_seconds = time.time() - forward_started

        if not bool(torch.isfinite(loss).all().item()):
            raise ValueError("Non-finite total loss")
        loss_terms = {}
        for key, value in loss_dict.items():
            if torch.is_tensor(value) and value.numel() == 1:
                scalar = float(value.detach().cpu())
                if not np.isfinite(scalar):
                    raise ValueError("Non-finite loss term: %s" % key)
                loss_terms[key] = scalar

        backward_started = time.time()
        loss.backward()
        torch.cuda.synchronize()
        backward_seconds = time.time() - backward_started
    finally:
        for hook in hooks:
            hook.remove()

    peak_allocated = torch.cuda.max_memory_allocated(0)
    peak_reserved = torch.cuda.max_memory_reserved(0)
    input_grad = batch["feats"].grad
    input_grad_present = input_grad is not None
    input_grad_finite = bool(
        input_grad_present and torch.isfinite(input_grad).all().item())
    input_grad_abs_sum = float(
        input_grad.abs().sum().item()) if input_grad_present else 0.0

    grad_summary = _gradient_summary(torch, model)
    required_calls = {
        "text_encoder": 1,
        "decoder": 1,
        "cluster_attention": 1,
        "sampling_module": 1,
        "criterion": 1,
    }
    for name, expected in required_calls.items():
        if calls[name] != expected:
            raise ValueError(
                "Expected %d %s call(s), observed %d" % (
                    expected, name, calls[name]))
    if grad_summary["nonfinite_grad"]:
        raise ValueError("Non-finite parameter gradients")
    inactive_missing = [
        name for name in grad_summary["trainable_missing_grad"]
        if name.startswith(INACTIVE_ROUTING_PREFIXES)
    ]
    conditional_score_missing = [
        name for name in grad_summary["trainable_missing_grad"]
        if name.startswith("dec.decoder_layers.")
        and ".out_score." in name
    ]
    allowed_missing = inactive_missing + conditional_score_missing
    unexpected_missing = [
        name for name in grad_summary["trainable_missing_grad"]
        if name not in allowed_missing
    ]
    if unexpected_missing:
        raise ValueError(
            "Some trainable parameters received no gradient: %s" %
            unexpected_missing[:20])
    active_trainable = (
        grad_summary["trainable_tensors"] - len(allowed_missing))
    active_with_grad = (
        grad_summary["trainable_with_grad"])
    active_nonzero = grad_summary["trainable_nonzero_grad"]
    if active_with_grad != active_trainable:
        raise ValueError("An active trainable parameter received no gradient")
    if active_nonzero != active_trainable:
        raise ValueError(
            "Some active trainable parameters received only zero gradients")
    score_tensors_total = 0
    score_tensors_with_nonzero_grad = 0
    for name, parameter in model.named_parameters():
        if ".out_score." not in name:
            continue
        score_tensors_total += 1
        if parameter.grad is not None and \
                float(parameter.grad.abs().sum().item()) > 0.0:
            score_tensors_with_nonzero_grad += 1
    if score_tensors_with_nonzero_grad == 0:
        raise ValueError("No score-head gradient was observed")
    for module in ("input_conv", "unet", "output_layer", "dec"):
        group = grad_summary["groups"].get(module)
        if not group or group["nonzero_grad_tensors"] == 0:
            raise ValueError("No nonzero gradient for module %s" % module)
    param_tensors = 0
    trainable_params = 0
    for name, parameter in model.named_parameters():
        param_tensors += 1
        if parameter.requires_grad:
            trainable_params += parameter.numel()
    if trainable_params != 32838458:
        raise ValueError("Trainable parameter count changed")
    if param_tensors != 847:
        raise ValueError("Parameter tensor count changed")

    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "elapsed_seconds": time.time() - started,
        "scope": "synthetic_full_model_loss_graph",
        "runtime": {
            "python": sys.executable,
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "visible_devices": [visible_devices],
        },
        "bound_identity": {
            "model_class": CHAMPION_CLASS,
            "model_source_sha256": model_source_sha256,
            "config_sha256": config_sha256,
            "resolved_module": Network.__module__,
            "seed": SEED,
        },
        "synthetic_input": input_summary,
        "execution": {
            "calls": calls,
            "shapes": shapes,
            "forward_seconds": forward_seconds,
            "backward_seconds": backward_seconds,
            "loss": float(loss.detach().cpu()),
            "loss_terms": loss_terms,
        },
        "accounting": {
            "parameter_tensors": param_tensors,
            "trainable_params": trainable_params,
            "inactive_registered_routing_tensors": inactive_missing,
            "conditional_score_tensors_not_selected": (
                conditional_score_missing),
            "score_tensors_total": score_tensors_total,
            "score_tensors_with_nonzero_grad": (
                score_tensors_with_nonzero_grad),
            "active_trainable_tensors": active_trainable,
            **grad_summary,
        },
        "gradients": {
            "input_grad_present": input_grad_present,
            "input_grad_finite": input_grad_finite,
            "input_grad_abs_sum": input_grad_abs_sum,
        },
        "gpu_memory": {
            "free_mib_before": free_mib,
            "total_mib": total_bytes / 1024 / 1024,
            "peak_allocated_mib": peak_allocated / 1024 / 1024,
            "peak_reserved_mib": peak_reserved / 1024 / 1024,
        },
        "boundary": {
            "dataset_built": False,
            "checkpoint_loaded": False,
            "text_encoder_executed": True,
            "decoder_executed": True,
            "criterion_executed": True,
            "optimizer_created": False,
            "optimizer_step": False,
            "training_started": False,
            "full_model_backward_verified": True,
            "train_mode": True,
            "text_encoder_eval": True,
            "resources_verified": False,
            "admission": False,
        },
        "limitations": [
            "Synthetic random input, not a real ScanRefer batch.",
            "The synthetic support mask is model-derived to exercise score heads "
            "and is not valid supervision or efficacy evidence.",
            "The ctf_hcg_csort forward intentionally bypasses the registered "
            "legacy cluster-routing Q/K/V projections; their missing gradients "
            "are recorded as inactive parameters.",
            "The score loss is conditional on matching and per-layer IoU > 0.5. "
            "The synthetic random model did not activate every decoder score "
            "head; the unselected score tensors are recorded explicitly.",
            "No checkpoint, dataset, optimizer step or training was used.",
            "The resource gate still needs the project's calibrated FLOPs, "
            "latency and peak-memory protocol with its baseline comparison.",
            "This is runtime-contract evidence, not efficacy or admission evidence.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))

    del model, loss, loss_dict
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
