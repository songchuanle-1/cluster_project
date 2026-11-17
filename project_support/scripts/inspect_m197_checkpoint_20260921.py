"""Inspect M197 checkpoint metadata without moving tensors to GPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time


CONTRACT = "m197-checkpoint-inspection-v1"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
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


def _checkpoint(path):
    import torch

    obj = torch.load(
        path, map_location="cpu", weights_only=False, mmap=True)
    if not isinstance(obj, dict):
        raise ValueError("Checkpoint root must be a mapping")
    meta = obj.get("meta")
    optimizer = obj.get("optimizer")
    scheduler = obj.get("scheduler")
    model = obj.get("model")
    result = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
        "sha256": _sha256(path),
        "keys": sorted(str(key) for key in obj),
        "model_entry_count": len(model) if isinstance(model, dict) else None,
        "meta": {
            str(key): value for key, value in meta.items()
            if isinstance(value, (str, int, float, bool, type(None)))
        } if isinstance(meta, dict) else None,
    }
    if isinstance(optimizer, dict):
        state = optimizer.get("state")
        groups = optimizer.get("param_groups")
        result["optimizer"] = {
            "keys": sorted(str(key) for key in optimizer),
            "state_count": len(state) if isinstance(state, dict) else None,
            "param_group_count": len(groups) if isinstance(groups, list) else None,
        }
    if isinstance(scheduler, dict):
        result["scheduler"] = {
            "keys": sorted(str(key) for key in scheduler),
            "last_epoch": scheduler.get("last_epoch"),
            "step_count": scheduler.get("_step_count"),
            "max_iters": scheduler.get("max_iters"),
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise ValueError("Checkpoint inspection must run on POSIX")

    run_dir = Path(args.run_dir).resolve(strict=True)
    paths = {"best": run_dir / "best.pth", "last": run_dir / "last.pth"}
    for path in paths.values():
        if not path.is_file() or path.is_symlink():
            raise ValueError("Missing regular checkpoint: " + str(path))

    torch_before = os.environ.get("CUDA_VISIBLE_DEVICES")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    try:
        checkpoints = {
            name: _checkpoint(path) for name, path in paths.items()
        }
    finally:
        if torch_before is None:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        else:
            os.environ["CUDA_VISIBLE_DEVICES"] = torch_before

    result = {
        "contract": CONTRACT,
        "observed_at": time.time(),
        "run_dir": str(run_dir),
        "checkpoints": checkpoints,
        "limitations": [
            "Checkpoint metadata inspection does not validate model quality.",
            "The stopped_unknown terminal state is preserved.",
            "No restart or successor is authorized by this receipt.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
