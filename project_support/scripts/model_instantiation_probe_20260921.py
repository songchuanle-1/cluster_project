"""Instantiate the bound champion Network under an explicit memory budget.

Read-only diagnostic. Constructs the bound champion ``Network`` with the frozen
config, records parameter counts and CUDA peak allocation on the allocated GPU,
and stops. It does not load checkpoint weights, build a dataset, run a forward or
backward pass, or start training.
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


CONTRACT = "champion-network-instantiation-probe-v1"
CHAMPION_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CHAMPION_CONFIG = (
    "configs/Quard/ctf_hcg_csort/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml")
EXPECTED_MODEL_SOURCE_SHA256 = (
    "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0")
EXPECTED_CONFIG_SHA256 = (
    "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a")
# Refuse to start GPU work below this much free memory on the target device.
MIN_FREE_MIB = 8192


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_package_sha256(code_root, model_class):
    """Reproduce frozen_capture_contract_20260916.model_package_sha256 exactly."""
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


def _rss_mib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


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
    if not lib_dir.is_dir():
        raise ValueError("Missing framework/lib extension directory")
    for entry in (str(code_root), str(lib_dir), str(code_root / "scripts")):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices != "7":
        raise ValueError("CUDA_VISIBLE_DEVICES must be 7")
    if not Path(data_root, "roberta-base", "config.json").is_file():
        raise ValueError("roberta-base asset missing under data root")

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
    from framework import resolve_network

    # Memory guard before any allocation on the shared device.
    torch.cuda.init()
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    free_mib = free_bytes / 1024 / 1024
    total_mib = total_bytes / 1024 / 1024
    if free_mib < MIN_FREE_MIB:
        raise ValueError(
            "Insufficient free GPU memory: %.1f MiB < %d MiB"
            % (free_mib, MIN_FREE_MIB))

    cfg = gorilla.Config.fromfile(str(config_path))
    model_kwargs = dict(cfg.model)
    # The frozen config carries the server-4 data root; remap exactly as the
    # closure path mapping does for this server.
    configured_data_root = model_kwargs.get("data_root")
    model_kwargs["data_root"] = data_root

    Network = resolve_network(str(config_path))
    expected_module = "framework.model.Quard_model.%s.network" % CHAMPION_CLASS
    if Network.__module__ != expected_module:
        raise ValueError("Network resolution fell back: %s" % Network.__module__)

    rss_before = _rss_mib()
    cpu_started = time.time()
    model = Network(**model_kwargs)
    cpu_seconds = time.time() - cpu_started
    rss_after = _rss_mib()

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(
        p.numel() for p in model.parameters() if p.requires_grad)
    frozen_module_params = {}
    for name in ("text_encoder",):
        module = getattr(model, name, None)
        if module is not None:
            frozen_module_params[name] = sum(
                p.numel() for p in module.parameters())

    param_bytes = total_params * 4

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(0)
    base_allocated = torch.cuda.memory_allocated(0)
    gpu_started = time.time()
    model = model.cuda()
    torch.cuda.synchronize()
    gpu_seconds = time.time() - gpu_started
    peak_allocated = torch.cuda.max_memory_allocated(0)
    peak_reserved = torch.cuda.max_memory_reserved(0)

    num_buffers = sum(b.numel() for b in model.buffers())
    param_devices = sorted({str(p.device) for p in model.parameters()})

    # Release immediately; no training, no forward, no checkpoint.
    del model
    gc.collect()
    torch.cuda.empty_cache()
    free_after_bytes, _ = torch.cuda.mem_get_info(0)

    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "elapsed_seconds": time.time() - started,
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
            "configured_data_root": configured_data_root,
            "effective_data_root": data_root,
        },
        "memory_guard": {
            "min_free_mib_required": MIN_FREE_MIB,
            "free_mib_before": free_mib,
            "total_mib": total_mib,
            "guard_passed": True,
        },
        "cpu_construction": {
            "seconds": cpu_seconds,
            "max_rss_mib_before": rss_before,
            "max_rss_mib_after": rss_after,
        },
        "parameters": {
            "total": total_params,
            "trainable": trainable_params,
            "frozen_module_params": frozen_module_params,
            "buffers": num_buffers,
            "fp32_bytes_estimate": param_bytes,
            "fp32_gib_estimate": param_bytes / 1024 ** 3,
        },
        "gpu_transfer": {
            "seconds": gpu_seconds,
            "allocated_before_mib": base_allocated / 1024 / 1024,
            "peak_allocated_mib": peak_allocated / 1024 / 1024,
            "peak_reserved_mib": peak_reserved / 1024 / 1024,
            "parameter_devices": param_devices,
            "free_mib_after_release": free_after_bytes / 1024 / 1024,
        },
        "boundary": {
            "network_instantiated": True,
            "checkpoint_loaded": False,
            "dataset_built": False,
            "forward_executed": False,
            "backward_executed": False,
            "training_started": False,
            "optimizer_created": False,
        },
        "limitations": [
            "Instantiation proves constructor/asset viability, not forward correctness.",
            "No forward, backward, loss or optimizer step was executed.",
            "Peak allocation covers parameter transfer only, not activations or gradients.",
            "This is not efficacy evidence and grants no admission.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
