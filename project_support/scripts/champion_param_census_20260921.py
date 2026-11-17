"""CPU-only parameter census for the bound champion Network.

Constructs the champion model on CPU to attribute parameters to top-level
modules. No CUDA device is touched, no checkpoint is loaded, no dataset is built
and no forward/backward is executed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


CONTRACT = "champion-parameter-census-v1"
CHAMPION_CLASS = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
CHAMPION_CONFIG = (
    "configs/Quard/ctf_hcg_csort/"
    "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort.yaml")
EXPECTED_MODEL_SOURCE_SHA256 = (
    "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0")
EXPECTED_CONFIG_SHA256 = (
    "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a")


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_package_sha256(code_root, model_class):
    package = Path(code_root) / "framework/model/Quard_model" / model_class
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
        raise ValueError("Native census must run on POSIX")

    code_root = Path(args.code_root).resolve(strict=True)
    for entry in (str(code_root), str(code_root / "framework" / "lib"),
                  str(code_root / "scripts")):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    started = time.time()
    model_source_sha256 = _model_package_sha256(code_root, CHAMPION_CLASS)
    if model_source_sha256 != EXPECTED_MODEL_SOURCE_SHA256:
        raise ValueError("Bound model package source digest changed")
    config_path = code_root / CHAMPION_CONFIG
    config_sha256 = _sha256(config_path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError("Bound config digest changed")

    import gorilla
    from framework import resolve_network

    cfg = gorilla.Config.fromfile(str(config_path))
    model_kwargs = dict(cfg.model)
    model_kwargs["data_root"] = args.data_root
    Network = resolve_network(str(config_path))
    model = Network(**model_kwargs)

    groups = {}
    for name, param in model.named_parameters():
        top = name.split(".")[0]
        entry = groups.setdefault(
            top, {"tensors": 0, "params": 0, "trainable": 0})
        entry["tensors"] += 1
        entry["params"] += param.numel()
        if param.requires_grad:
            entry["trainable"] += param.numel()

    total = sum(v["params"] for v in groups.values())
    trainable = sum(v["trainable"] for v in groups.values())

    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "elapsed_seconds": time.time() - started,
        "bound_identity": {
            "model_class": CHAMPION_CLASS,
            "model_source_sha256": model_source_sha256,
            "config_sha256": config_sha256,
        },
        "totals": {
            "params": total,
            "trainable": trainable,
            "frozen": total - trainable,
            "param_tensors": sum(v["tensors"] for v in groups.values()),
        },
        "by_top_level_module": dict(sorted(groups.items())),
        "boundary": {
            "cuda_used": False,
            "checkpoint_loaded": False,
            "dataset_built": False,
            "forward_executed": False,
            "backward_executed": False,
            "training_started": False,
        },
        "limitations": [
            "CPU construction only; no device placement or native execution.",
            "Parameter counts are not FLOPs, latency or activation memory.",
            "This is not efficacy evidence and grants no admission.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
