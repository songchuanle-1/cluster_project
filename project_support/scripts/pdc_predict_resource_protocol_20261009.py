"""Measure baseline and champion with the project's calibrated resource protocol.

Each target runs in its own process because variant packages register the same
gorilla criterion name. The two outputs are then paired by real validation sample
identity and protocol fields before the comparison is written.
"""
import argparse
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import statistics
import sys
import time


CONTRACT = "baseline-champion-real-validation-resources-v1"
SEED = 1999
MIN_FREE_MIB = 8192
ABSOLUTE_FLOP_LIMIT_G = 10.0
WARMUP = 20
REPEAT = 100
BASELINE = {
    "name": "model_base1_quard2_c2f_enc_lite",
    "config": "configs/Quard/model_base1_quard2_c2f_enc_lite.yaml",
    "config_sha256": (
        "492dae84bf33cf795293625262a8b1a3f2a4b5ec7fdc9da009363e5f0726893c"),
    "model_source_sha256": (
        "be91ac86fc7d0844b078ce37f986453669223e502175be81310498a1ca06b04e"),
}
CHAMPION = {
    "name": "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort",
    "config": (
        "configs/Quard/ctf_hcg_csort/"
        "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml"),
    "config_sha256": (
        "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"),
    "model_source_sha256": (
        "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0"),
}
TARGETS = {"baseline": BASELINE, "champion": CHAMPION}


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_package_sha256(code_root, model_class):
    package = Path(code_root) / "framework/model/Quard_model" / model_class
    if not package.is_dir():
        raise ValueError("Model package is missing: %s" % package)
    sources = sorted(package.rglob("*.py"))
    if not sources:
        raise ValueError("Model package has no Python sources")
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


def _sample_identity(batch):
    def values(key):
        value = batch.get(key)
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        return [str(value)]

    language_shape = None
    if hasattr(batch.get("lang_tokenss"), "shape"):
        language_shape = list(batch["lang_tokenss"].shape)
    feature_shape = None
    if hasattr(batch.get("feats"), "shape"):
        feature_shape = list(batch["feats"].shape)
    return {
        "scan_ids": values("scan_ids"),
        "ann_ids": values("ann_ids"),
        "language_tokens_shape": language_shape,
        "feature_shape": feature_shape,
    }


def _measure_target(target_name, code_root, data_root, output):
    if os.name != "posix":
        raise ValueError("Native resource measurement must run on POSIX")
    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices != "7":
        raise ValueError("CUDA_VISIBLE_DEVICES must be 7")

    os.environ.update(
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
        TOKENIZERS_PARALLELISM="false")
    code_root = Path(code_root).resolve(strict=True)
    data_root = Path(data_root).resolve(strict=True)
    for entry in (
            str(code_root), str(code_root / "framework" / "lib"),
            str(code_root / "scripts")):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    target = TARGETS[target_name]
    model_source_sha256 = _model_package_sha256(
        code_root, target["name"])
    if model_source_sha256 != target["model_source_sha256"]:
        raise ValueError("Bound model package source digest changed")
    config_path = code_root / target["config"]
    config_sha256 = _sha256(config_path)
    if config_sha256 != target["config_sha256"]:
        raise ValueError("Bound config digest changed")

    import gorilla
    import numpy as np
    import torch
    from fvcore.nn import FlopCountAnalysis
    from framework.dataset import build_dataset, build_dataloader

    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.20)
    torch.cuda.init()
    free_bytes, total_bytes = torch.cuda.mem_get_info(0)
    free_mib = free_bytes / 1024 / 1024
    if free_mib < MIN_FREE_MIB:
        raise ValueError("Insufficient free GPU memory: %.1f MiB" % free_mib)

    cfg = gorilla.Config.fromfile(str(config_path))
    cfg.model.data_root = str(data_root)
    cfg.data.val.data_root = str(data_root)
    cfg.data.val.lang_num_max = 1
    gorilla.set_random_seed(SEED)
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    dataset = build_dataset(
        copy.deepcopy(cfg.data.val), logging.getLogger("resource-gate"))
    loader = build_dataloader(
        dataset, training=False, batch_size=1, num_workers=0,
        persistent_workers=False)
    batch = next(iter(loader))
    sample_identity = _sample_identity(batch)

    Network = importlib.import_module(
        "framework.model.Quard_model.%s" % target["name"]).Network
    model = Network(**dict(cfg.model))
    checkpoint = data_root / "sp_unet_backbone.pth"
    if not checkpoint.is_file():
        raise ValueError("Missing backbone checkpoint: %s" % checkpoint)
    gorilla.load_checkpoint(
        model, str(checkpoint), strict=False, map_location="cpu")
    model = model.cuda().eval()
    checkpoint_sha256 = _sha256(checkpoint)

    def forward_once():
        with torch.no_grad():
            output = model(copy.deepcopy(batch), mode="predict")
        if output is None:
            raise ValueError("Model returned None")
        return output

    class PredictPath(torch.nn.Module):
        def __init__(self, wrapped_model):
            super().__init__()
            self.wrapped_model = wrapped_model

        def forward(self, inputs):
            return self.wrapped_model(inputs, mode="predict")

    profiled_model = PredictPath(model).eval()
    torch.cuda.synchronize(0)
    torch.cuda.reset_peak_memory_stats(0)
    flop_started = time.perf_counter()
    profile = FlopCountAnalysis(profiled_model, (copy.deepcopy(batch),))
    profile.unsupported_ops_warnings(False)
    profile.uncalled_modules_warnings(False)
    total_flops = float(profile.total())
    torch.cuda.synchronize(0)
    flop_seconds = time.perf_counter() - flop_started

    for _ in range(WARMUP):
        forward_once()
    torch.cuda.synchronize(0)
    timings_ms = []
    for _ in range(REPEAT):
        torch.cuda.synchronize(0)
        started = time.perf_counter()
        forward_once()
        torch.cuda.synchronize(0)
        timings_ms.append((time.perf_counter() - started) * 1000.0)
    median_ms = float(statistics.median(timings_ms))
    p90_ms = float(np.percentile(timings_ms, 90))
    peak_allocated_mib = torch.cuda.max_memory_allocated(0) / 2 ** 20
    peak_reserved_mib = torch.cuda.max_memory_reserved(0) / 2 ** 20

    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    trainable_count = sum(
        parameter.numel() for parameter in model.parameters()
        if parameter.requires_grad)
    result = {
        "contract": CONTRACT,
        "status": "ok",
        "target": target_name,
        "observed_at": time.time(),
        "bound_identity": {
            "model_class": target["name"],
            "model_source_sha256": model_source_sha256,
            "config_path": target["config"],
            "config_sha256": config_sha256,
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": checkpoint_sha256,
            "resolved_module": Network.__module__,
            "seed": SEED,
        },
        "protocol": {
            "input": "real_validation_batch",
            "forward_mode": "predict",
            "batch_size": 1,
            "lang_num_max": 1,
            "warmup": WARMUP,
            "repeat": REPEAT,
            "flops_counter": "fvcore.nn.FlopCountAnalysis",
            "latency_statistics": ["median", "p90"],
            "memory_counter": "torch.cuda.max_memory_allocated",
            "sample_identity": sample_identity,
        },
        "resources": {
            "params": parameter_count,
            "trainable_params": trainable_count,
            "flops": total_flops,
            "flops_g": total_flops / 1e9,
            "latency_ms_median": median_ms,
            "latency_ms_p90": p90_ms,
            "peak_allocated_mib": peak_allocated_mib,
            "peak_reserved_mib": peak_reserved_mib,
            "flops_analysis_seconds": flop_seconds,
            "unsupported_ops": dict(profile.unsupported_ops()),
            "flops_by_operator": dict(profile.by_operator()),
            "flops_by_module": dict(profile.by_module()),
        },
        "gpu": {
            "name": torch.cuda.get_device_name(0),
            "visible_devices": [visible_devices],
            "free_mib_before": free_mib,
            "total_mib": total_bytes / 1024 / 1024,
        },
        "boundary": {
            "real_validation_input": True,
            "checkpoint_loaded": True,
            "forward_executed": True,
            "optimizer_created": False,
            "optimizer_step": False,
            "training_started": False,
            "resources_verified": False,
            "admission": False,
        },
        "limitations": [
            "One deterministic real validation batch, not a validation-set sweep.",
            "The paired comparison requires both target outputs and a matching "
            "sample identity.",
            "fvcore omits the unsupported operations listed in the result.",
            "Resource compliance and admission are assigned only by compare mode.",
        ],
    }
    output, sha256 = _write_new(output, result)
    print("%s %s" % (output, sha256))


def _protocol_key(result):
    protocol = result["protocol"]
    return {
        "sample_identity": protocol["sample_identity"],
        "batch_size": protocol["batch_size"],
        "lang_num_max": protocol["lang_num_max"],
        "warmup": protocol["warmup"],
        "repeat": protocol["repeat"],
        "flops_counter": protocol["flops_counter"],
        "latency_statistics": protocol["latency_statistics"],
        "memory_counter": protocol["memory_counter"],
    }


def _compare_results(baseline_path, champion_path, output):
    baseline = json.loads(Path(baseline_path).read_text(encoding="ascii"))
    champion = json.loads(Path(champion_path).read_text(encoding="ascii"))
    for name, result in (("baseline", baseline), ("champion", champion)):
        if result.get("contract") != CONTRACT or result.get("status") != "ok":
            raise ValueError("Invalid %s result" % name)
        if result.get("target") != name:
            raise ValueError("Unexpected target in %s result" % name)
    if _protocol_key(baseline) != _protocol_key(champion):
        raise ValueError("Baseline and champion protocols are not paired")
    if baseline["gpu"]["name"] != champion["gpu"]["name"]:
        raise ValueError("Baseline and champion ran on different GPU types")

    baseline_resources = baseline["resources"]
    champion_resources = champion["resources"]
    champion_overage = (
        champion_resources["flops_g"] - ABSOLUTE_FLOP_LIMIT_G)
    latency_delta = (
        champion_resources["latency_ms_median"]
        - baseline_resources["latency_ms_median"])
    memory_delta = (
        champion_resources["peak_allocated_mib"]
        - baseline_resources["peak_allocated_mib"])
    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "protocol": _protocol_key(baseline),
        "results": {
            "baseline": baseline_resources,
            "champion": champion_resources,
        },
        "comparison": {
            "champion_minus_baseline_flops_g": (
                champion_resources["flops_g"]
                - baseline_resources["flops_g"]),
            "champion_minus_baseline_flops_percent": (
                100.0
                * (champion_resources["flops_g"]
                   - baseline_resources["flops_g"])
                / baseline_resources["flops_g"]),
            "champion_minus_baseline_latency_ms_median": latency_delta,
            "champion_minus_baseline_peak_allocated_mib": memory_delta,
            "absolute_flop_limit_g": ABSOLUTE_FLOP_LIMIT_G,
            "champion_absolute_flop_overage_g": champion_overage,
        },
        "gates": {
            "paired_real_validation": True,
            "absolute_flops_le_10g": champion_overage <= 0.0,
            "resources_verified": champion_overage <= 0.0,
            "admission": False,
        },
        "evidence": {
            "baseline": {
                "path": str(Path(baseline_path)),
                "sha256": _sha256(baseline_path),
            },
            "champion": {
                "path": str(Path(champion_path)),
                "sha256": _sha256(champion_path),
            },
        },
        "limitations": [
            "The champion inherits an absolute FLOPs overage if its measured "
            "fvcore total exceeds 10.0 G.",
            "The unsupported-operation counts limit exact interpretation of the "
            "fvcore total.",
            "This is resource evidence only and does not verify efficacy, "
            "independence or admission.",
        ],
    }
    output, sha256 = _write_new(output, result)
    print("%s %s" % (output, sha256))


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    measure_parser = subparsers.add_parser("measure")
    measure_parser.add_argument("target", choices=sorted(TARGETS))
    measure_parser.add_argument("--code-root", required=True)
    measure_parser.add_argument("--data-root", required=True)
    measure_parser.add_argument("--output", required=True)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--champion", required=True)
    compare_parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.command == "measure":
        _measure_target(
            args.target, args.code_root, args.data_root, args.output)
    else:
        _compare_results(args.baseline, args.champion, args.output)


if __name__ == "__main__":
    main()
