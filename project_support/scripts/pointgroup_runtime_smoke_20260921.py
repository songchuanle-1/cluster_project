"""Run a tiny native pointgroup_ops forward/backward smoke test."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


CONTRACT = "pointgroup-ops-runtime-smoke-v1"


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if os.name != "posix":
        raise ValueError("Native smoke test must run on POSIX")

    code_root = Path(args.code_root).resolve(strict=True)
    extension = (
        code_root / "framework" / "lib" / "pointgroup_ops"
        / "pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so")
    if not extension.is_file():
        raise ValueError("Missing native extension")
    sys.path.insert(0, str(code_root / "framework" / "lib"))

    import pointgroup_ops
    import torch

    visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible_devices != "7":
        raise ValueError("CUDA_VISIBLE_DEVICES must be 7")

    started = time.time()
    coords = torch.tensor([
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
    ], dtype=torch.long)
    out_coords, input_map, output_map = pointgroup_ops.voxelization_idx(
        coords, 1, 4)
    feats = torch.tensor([
        [1.0, 2.0],
        [3.0, 4.0],
        [5.0, 6.0],
        [7.0, 8.0],
    ], dtype=torch.float32, device="cuda", requires_grad=True)
    out = pointgroup_ops.voxelization(feats, output_map.cuda(), 4)
    loss = out.square().mean()
    loss.backward()
    elapsed = time.time() - started

    if tuple(out_coords.shape) != (3, 4):
        raise ValueError("Unexpected output coordinate shape")
    if tuple(input_map.shape) != (4,):
        raise ValueError("Unexpected input map shape")
    if tuple(output_map.shape) != (3, 3):
        raise ValueError("Unexpected output map shape")
    if tuple(out.shape) != (3, 2):
        raise ValueError("Unexpected output feature shape")
    if feats.grad is None or not bool(torch.isfinite(feats.grad).all().item()):
        raise ValueError("Missing or nonfinite input gradient")

    result = {
        "contract": CONTRACT,
        "status": "ok",
        "observed_at": time.time(),
        "elapsed_seconds": elapsed,
        "runtime": {
            "python": sys.executable,
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": torch.cuda.device_count(),
            "visible_devices": [visible_devices],
        },
        "extension": {
            "path": str(extension),
            "sha256": _sha256(extension),
            "exports": sorted([
                "ballquery_batch_p", "bfs_cluster", "get_iou",
                "point_recover", "roipool", "sec_max", "sec_mean",
                "sec_min", "voxelization", "voxelization_idx",
            ]),
        },
        "execution": {
            "coordinates_device": "cpu",
            "feature_device": "cuda",
            "output_coords_shape": list(out_coords.shape),
            "input_map_shape": list(input_map.shape),
            "output_map_shape": list(output_map.shape),
            "output_feats_shape": list(out.shape),
            "loss": float(loss.detach().cpu()),
            "grad_present": True,
            "grad_finite": True,
            "grad_abs_sum": float(feats.grad.abs().sum().cpu()),
            "max_allocated_mb": (
                torch.cuda.max_memory_allocated() / 1024 / 1024),
        },
        "limitations": [
            "This smoke test exercises one tiny operator path only.",
            "It does not load model weights or dataset inputs.",
            "It does not establish full-model gradient or efficacy.",
        ],
    }
    output, sha256 = _write_new(args.output, result)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
