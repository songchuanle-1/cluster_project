"""Matched first-validation-input profiling for baseline, M95, and SCM.

Run one model per process because legacy Gorilla registries are process-global.
This script is read-only with respect to checkpoints and the training queue.
"""

import argparse
import copy
import hashlib
import importlib
import json
import logging
import os
from pathlib import Path
import sys
import time


os.environ.update(
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
    TOKENIZERS_PARALLELISM="false",
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_value(digest, value):
    import numpy as np
    import torch

    if torch.is_tensor(value):
        array = value.detach().cpu().contiguous().numpy()
        digest.update(b"tensor\0")
        digest.update(str(array.dtype).encode())
        digest.update(str(tuple(array.shape)).encode())
        digest.update(array.tobytes())
    elif isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        digest.update(b"ndarray\0")
        digest.update(str(array.dtype).encode())
        digest.update(str(tuple(array.shape)).encode())
        digest.update(array.tobytes())
    elif isinstance(value, dict):
        digest.update(b"dict\0")
        for key in sorted(value, key=str):
            hash_value(digest, str(key))
            hash_value(digest, value[key])
    elif isinstance(value, (list, tuple)):
        digest.update(b"sequence\0")
        for item in value:
            hash_value(digest, item)
    else:
        digest.update(json.dumps(value, sort_keys=True, default=str).encode())
        digest.update(b"\0")


def json_value(value):
    import numpy as np
    import torch

    if torch.is_tensor(value):
        return value.detach().cpu().tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


def batch_manifest(batch):
    import numpy as np
    import torch

    digest = hashlib.sha256()
    hash_value(digest, batch)
    fields = {}
    for key, value in batch.items():
        if torch.is_tensor(value) or isinstance(value, np.ndarray):
            fields[key] = {
                "shape": list(value.shape),
                "dtype": str(value.dtype),
            }
        elif isinstance(value, (list, tuple)):
            fields[key] = {"type": type(value).__name__, "length": len(value)}
        else:
            fields[key] = {"type": type(value).__name__}
    return {"sha256": digest.hexdigest(), "fields": fields}


def load_state(model, checkpoint):
    import torch

    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    state = payload["model"]
    embeddings = getattr(getattr(model, "text_encoder", None), "embeddings", None)
    ignored = []
    for key in (
        "text_encoder.embeddings.position_ids",
        "text_encoder.embeddings.token_type_ids",
    ):
        if key not in state:
            continue
        name = key.rsplit(".", 1)[1]
        if embeddings is not None and hasattr(embeddings, name):
            current = getattr(embeddings, name)
            if current.shape == state[key].shape:
                ignored.append(key)
                del state[key]
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing or unexpected:
        raise RuntimeError(
            f"Checkpoint mismatch: missing={missing}, unexpected={unexpected}"
        )
    return payload.get("meta"), ignored


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    sys.path[:0] = [str(root), str(root / "framework/lib")]

    import numpy as np
    import torch
    import gorilla
    from fvcore.nn import FlopCountAnalysis
    from framework.dataset import build_dataset, build_dataloader
    import framework.model.Quard_model as packages

    if args.overlay:
        packages.__path__ = [str(args.overlay.resolve()), *packages.__path__]

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    gorilla.set_random_seed(1999)

    cfg = gorilla.Config.fromfile(str(args.config))
    cfg.model.data_root = args.data_root
    cfg.data.val.data_root = args.data_root
    cfg.data.val.lang_num_max = 1
    cfg.dataloader.val.batch_size = 1
    cfg.dataloader.val.num_workers = 0
    cfg.dataloader.val.persistent_workers = False

    module = importlib.import_module(
        "framework.model.Quard_model." + args.module
    )
    model = module.Network(**cfg.model)
    meta, ignored = load_state(model, args.checkpoint)
    model.cuda().eval()

    logger = logging.getLogger("matched_val_profile")
    dataset = build_dataset(copy.deepcopy(cfg.data.val), logger)
    loader = build_dataloader(
        dataset, training=False, **copy.deepcopy(cfg.dataloader.val)
    )
    batch = next(iter(loader))
    identity = [
        [str(batch["scan_ids"][0]), str(ids[0]), str(ann)]
        for ids, ann in zip(batch["object_idss"], batch["ann_ids"])
    ]
    if len(identity) != 1:
        raise RuntimeError(f"Expected one expression, got {identity}")

    input_manifest = batch_manifest(batch)
    with torch.inference_mode():
        flop = FlopCountAnalysis(model, (batch, "predict"))
        flop.unsupported_ops_warnings(False)
        flop.uncalled_modules_warnings(False)
        total = flop.total()
        for _ in range(20):
            model(batch, mode="predict")
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        durations = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            result = model(batch, mode="predict")
            torch.cuda.synchronize()
            durations.append((time.perf_counter() - start) * 1000)

    if not all(torch.isfinite(value).all() for value in result["piou"]):
        raise RuntimeError("Nonfinite prediction")

    report = {
        "schema_version": 1,
        "label": args.label,
        "module": args.module,
        "config": str(args.config),
        "config_sha256": sha256(args.config),
        "checkpoint": str(args.checkpoint),
        "checkpoint_sha256": sha256(args.checkpoint),
        "checkpoint_meta": json_value(meta),
        "ignored_checkpoint_buffers": ignored,
        "input": {"identity": identity, **input_manifest},
        "environment": {
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(),
            "python": sys.version,
        },
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "fvcore": {
            "flops": total,
            "flops_g": total / 1e9,
            "convention": "fvcore: one fused multiply-add counts as one",
            "unsupported_ops": dict(flop.unsupported_ops()),
            "by_module": dict(flop.by_module()),
        },
        "timing": {
            "batch_size": 1,
            "warmup": 20,
            "repeat": 100,
            "median_ms": float(np.median(durations)),
            "p90_ms": float(np.percentile(durations, 90)),
            "peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
            "peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
