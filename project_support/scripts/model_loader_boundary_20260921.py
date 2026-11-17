"""Exercise the model-loader/import boundary without loading weights or training.

This is a bounded, read-only diagnostic. It imports the framework packages that
``tools/train.py`` imports, parses the frozen champion config with the project's
own loader, and resolves the bound ``Network`` class. It deliberately does not
instantiate the network, load any checkpoint, build a dataset or start training.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


CONTRACT = "model-loader-import-boundary-v1"
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
    """Reproduce frozen_capture_contract_20260916.model_package_sha256 exactly.

    The helper is not present in the remote pipeline tree, so the documented
    length-prefixed digest over every Python source in the bound package is
    inlined here. Any divergence changes the digest and fails the check.
    """
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
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise ValueError("Native boundary check must run on POSIX")

    code_root = Path(args.code_root).resolve(strict=True)
    scripts = code_root / "scripts"
    lib_dir = code_root / "framework" / "lib"
    if not lib_dir.is_dir():
        raise ValueError("Missing framework/lib extension directory")
    # scripts/train.sh exports PYTHONPATH="${ROOT}:${ROOT}/framework/lib:...".
    for entry in (str(code_root), str(lib_dir), str(scripts)):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices != "7":
        raise ValueError("CUDA_VISIBLE_DEVICES must be 7")

    started = time.time()

    # Bound source identity: composite digest over the model package's sources.
    model_source_sha256 = _model_package_sha256(code_root, CHAMPION_CLASS)
    if model_source_sha256 != EXPECTED_MODEL_SOURCE_SHA256:
        raise ValueError("Bound model package source digest changed")

    config_path = code_root / CHAMPION_CONFIG
    config_sha256 = _sha256(config_path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError("Bound config digest changed")

    # Import boundary: exactly the modules tools/train.py imports at module scope.
    import gorilla
    import torch
    import framework
    from framework import resolve_network
    from framework.dataset import build_dataloader, build_dataset
    from framework.utils import AverageMeter, get_root_logger

    dataset_module = sys.modules["framework.dataset"]
    network_module = sys.modules["framework"]

    # Config loader boundary: parse with the project's own loader, no build.
    cfg = gorilla.Config.fromfile(str(config_path))
    cfg_model_type = None
    try:
        cfg_model_type = str(cfg.model.type)
    except (AttributeError, KeyError):
        cfg_model_type = None

    # Network resolution boundary: importing the package, not instantiating it.
    Network = resolve_network(str(config_path))
    if Network.__name__ != "Network":
        raise ValueError("Resolved class is not named Network")
    expected_module = "framework.model.Quard_model.%s.network" % CHAMPION_CLASS
    if Network.__module__ != expected_module:
        raise ValueError(
            "Resolved Network is not the bound champion package: %s"
            % Network.__module__)
    if not isinstance(Network, type):
        raise ValueError("Resolved Network is not a class")

    elapsed = time.time() - started
    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "elapsed_seconds": elapsed,
        "runtime": {
            "python": sys.executable,
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "visible_devices": [visible_devices],
            "cuda_runtime_queried": False,
        },
        "bound_identity": {
            "model_class": CHAMPION_CLASS,
            "model_source_sha256": model_source_sha256,
            "config_path": CHAMPION_CONFIG,
            "config_sha256": config_sha256,
        },
        "imports": {
            "framework_package": getattr(network_module, "__file__", None),
            "dataset_module": "framework.dataset",
            "dataset_module_file": getattr(dataset_module, "__file__", None),
            "gorilla_version": getattr(gorilla, "__version__", None),
            "pythonpath_entries_required": [
                str(code_root), str(lib_dir),
            ],
            "dataset_symbols": [
                build_dataset.__name__, build_dataloader.__name__,
                AverageMeter.__name__, get_root_logger.__name__,
            ],
        },
        "config_parse": {
            "loader": "gorilla.Config.fromfile",
            "model_type": cfg_model_type,
        },
        "network_resolution": {
            "resolver": "framework.resolve_network",
            "resolved_class": Network.__name__,
            "resolved_module": Network.__module__,
            "bound_to_champion_package": True,
        },
        "boundary": {
            "network_instantiated": False,
            "checkpoint_loaded": False,
            "dataset_built": False,
            "training_started": False,
            "cuda_context_allocated": False,
        },
        "limitations": [
            "This check imports and resolves only; it does not instantiate the network.",
            "It does not load a checkpoint, build a dataset or run a training step.",
            "A matching source digest does not prove runtime ABI compatibility.",
            "It is not efficacy evidence and grants no admission.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
