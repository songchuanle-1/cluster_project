"""Run one synthetic native forward/backward through the champion backbone.

This exercises the exact production call sequence of ``Network.loss`` up to the
superpoint-pooled feature: ``pointgroup_ops.voxelization_idx`` ->
``pointgroup_ops.voxelization`` -> ``spconv.SparseConvTensor`` ->
``Network.extract_feat`` (submanifold conv + UNet + output layer + scatter_mean).

It is deliberately a *subgraph* check: no dataset, no checkpoint, no criterion,
no decoder, no optimizer step, no training. It does not establish full-model
gradients or efficacy.
"""
import argparse
import hashlib
import gc
import json
import os
from pathlib import Path
import resource
import sys
import time

import numpy as np


CONTRACT = "champion-backbone-native-backward-v1"
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
GRID = 64
SEED = 1999


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise ValueError("Native probe must run on POSIX")

    code_root = Path(args.code_root).resolve(strict=True)
    data_root = args.data_root
    lib_dir = code_root / "framework" / "lib"
    for entry in (str(code_root), str(lib_dir), str(code_root / "scripts")):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices != "7":
        raise ValueError("CUDA_VISIBLE_DEVICES must be 7")

    started = time.time()

    model_source_sha256 = _model_package_sha256(code_root, CHAMPION_CLASS)
    if model_source_sha256 != EXPECTED_MODEL_SOURCE_SHA256:
        raise ValueError("Bound model package source digest changed")
    config_path = code_root / CHAMPION_CONFIG
    config_sha256 = _sha256(config_path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError("Bound config digest changed")

    import gorilla
    import torch
    import pointgroup_ops
    import spconv.pytorch as spconv
    from framework import resolve_network

    torch.cuda.init()
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    free_mib = free_bytes / 1024 / 1024
    if free_mib < MIN_FREE_MIB:
        raise ValueError("Insufficient free GPU memory: %.1f MiB" % free_mib)

    cfg = gorilla.Config.fromfile(str(config_path))
    model_kwargs = dict(cfg.model)
    model_kwargs["data_root"] = data_root

    Network = resolve_network(str(config_path))
    expected_module = "framework.model.Quard_model.%s.network" % CHAMPION_CLASS
    if Network.__module__ != expected_module:
        raise ValueError("Network resolution fell back: %s" % Network.__module__)

    torch.manual_seed(SEED)
    np.random.seed(SEED)

    model = Network(**model_kwargs).cuda()
    model.train()

    # Synthetic voxelized batch, built exactly like the ScanNet dataset does.
    generator = torch.Generator(device="cpu").manual_seed(SEED)
    xyz = torch.randint(
        0, GRID, (N_POINTS, 3), generator=generator, dtype=torch.long)
    batch_idx = torch.zeros(N_POINTS, 1, dtype=torch.long)
    coords = torch.cat((batch_idx, xyz), dim=1).long().contiguous()

    out_coords, p2v_map, v2p_map = pointgroup_ops.voxelization_idx(coords, 1, 4)
    # Same construction as framework/dataset/scannetv2.py line 510.
    spatial_shape = np.clip(
        (coords.max(0)[0][1:] + 1).numpy(), 128, None)
    spatial_shape = [int(v) for v in spatial_shape]

    # In production Network.loss is wrapped in @cuda_cast, which moves these
    # tensors to the device. spconv's implicit-gemm path asserts that the
    # SparseConvTensor indices are CUDA, so replicate that placement here.
    out_coords = out_coords.int().cuda()
    p2v_map = p2v_map.long().cuda()
    v2p_map = v2p_map.int().cuda().contiguous()

    feats = torch.randn(N_POINTS, 6, generator=generator).cuda()
    feats.requires_grad_(True)
    superpoints = torch.randint(
        0, N_SUPERPOINTS, (N_POINTS,), generator=generator).cuda().long()

    n_points = int(coords.shape[0])
    n_voxels = int(out_coords.shape[0])
    map_rule_cols = int(v2p_map.shape[1])

    torch.cuda.reset_peak_memory_stats(0)
    forward_started = time.time()
    voxel_feats = pointgroup_ops.voxelization(feats, v2p_map)
    sparse_input = spconv.SparseConvTensor(
        voxel_feats, out_coords, spatial_shape, 1)
    sp_feats = model.extract_feat(sparse_input, superpoints, p2v_map)
    torch.cuda.synchronize()
    forward_seconds = time.time() - forward_started

    loss = sp_feats.square().mean()
    backward_started = time.time()
    loss.backward()
    torch.cuda.synchronize()
    backward_seconds = time.time() - backward_started
    peak_allocated = torch.cuda.max_memory_allocated(0)
    peak_reserved = torch.cuda.max_memory_reserved(0)

    feats_grad = feats.grad
    if feats_grad is None:
        raise ValueError("No gradient reached the input features")
    input_grad_finite = bool(torch.isfinite(feats_grad).all().item())
    input_grad_abs_sum = float(feats_grad.abs().sum().item())

    param_total = 0
    param_with_grad = 0
    param_finite = 0
    param_nonzero = 0
    for name, param in model.named_parameters():
        if name.startswith("text_encoder."):
            continue
        param_total += 1
        if param.grad is None:
            continue
        param_with_grad += 1
        if bool(torch.isfinite(param.grad).all().item()):
            param_finite += 1
        if float(param.grad.abs().sum().item()) > 0.0:
            param_nonzero += 1

    if not input_grad_finite or input_grad_abs_sum == 0.0:
        raise ValueError("Input gradient missing, nonfinite or identically zero")
    if param_with_grad == 0 or param_finite != param_with_grad:
        raise ValueError("Backbone parameters did not receive finite gradients")

    torch.cuda.synchronize()
    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "elapsed_seconds": time.time() - started,
        "scope": "backbone_subgraph",
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
        "synthetic_input": {
            "points": n_points,
            "voxels": n_voxels,
            "map_rule_columns": map_rule_cols,
            "spatial_shape": spatial_shape,
            "grid": GRID,
            "superpoints": N_SUPERPOINTS,
            "lang_num": 0,
        },
        "execution": {
            "voxelization_idx": True,
            "pointgroup_voxelization": True,
            "sparse_conv_tensor": True,
            "extract_feat": True,
            "forward_seconds": forward_seconds,
            "backward_seconds": backward_seconds,
            "sp_feats_shape": list(sp_feats.shape),
            "loss": float(loss.detach().cpu()),
        },
        "gradients": {
            "input_grad_finite": input_grad_finite,
            "input_grad_abs_sum": input_grad_abs_sum,
            "backbone_param_tensors": param_total,
            "param_tensors_with_grad": param_with_grad,
            "param_tensors_finite": param_finite,
            "param_tensors_nonzero_grad": param_nonzero,
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
            "text_encoder_executed": False,
            "decoder_executed": False,
            "criterion_executed": False,
            "optimizer_created": False,
            "optimizer_step": False,
            "training_started": False,
            "full_model_backward_verified": False,
        },
        "limitations": [
            "Synthetic random input, not a real ScanRefer batch.",
            "Scope is the backbone subgraph up to superpoint pooling.",
            "The text encoder, decoder, matcher and criterion were not executed.",
            "This is not full-model native backward, efficacy evidence or admission.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))

    del model, sp_feats, sparse_input, voxel_feats, loss
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
