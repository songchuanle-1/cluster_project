"""Opt-in entry-FPS input capture around the frozen M95 manifest producer.

This is a diagnostic wrapper, never a strict full-scan reproducibility run.
The wrapped producer and model source remain unchanged.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys


TARGET_ROWS = frozenset((83, 95, 174, 178, 193))


def bind_fps_calls(rows, calls):
    selected = {}
    for row in rows:
        index = int(row["manifest_index"])
        if index not in TARGET_ROWS:
            continue
        matches = [
            call for call in calls
            if call["indices"] == row["fps_superpoints"]
            and call["step"] == row["step"]
        ]
        if len(matches) != 1:
            raise ValueError(
                "Entry FPS row %d has %d matching calls" % (index, len(matches))
            )
        selected[index] = matches[0]
    if set(selected) != TARGET_ROWS:
        raise ValueError("Target manifest coverage differs")
    return selected


def main():
    if "--manifest-only" not in sys.argv:
        raise ValueError("Wrapper is bound to a diagnostic manifest subset")
    if "--output" not in sys.argv:
        raise ValueError("Producer output is required")
    if "--root" not in sys.argv:
        raise ValueError("Producer root is required")
    output = Path(sys.argv[sys.argv.index("--output") + 1]).resolve()
    root = Path(sys.argv[sys.argv.index("--root") + 1]).resolve()
    producer = Path(__file__).with_name("native_manifest_capture_20260922.py")
    if not producer.is_file():
        raise ValueError("Frozen producer must be staged beside wrapper")

    sys.path.insert(0, str(root))
    import torch
    import pointnet2._ext as extension
    from pointnet2.pointnet2_utils import FurthestPointSampling

    binary = Path(extension.__file__).resolve()
    binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    original_apply = FurthestPointSampling.apply
    calls = []
    step = 0

    def capture_apply(coords, count):
        nonlocal step
        caller = sys._getframe(1)
        if caller.f_code.co_name != "expand_and_fps" or not caller.f_code.co_filename.endswith("network.py"):
            return original_apply(coords, count)
        if coords.ndim != 3 or coords.shape[0] != 1 or coords.shape[2] != 3:
            raise ValueError("Unexpected entry FPS input axis")
        if coords.dtype != torch.float32:
            raise ValueError("Unexpected entry FPS dtype")
        result = original_apply(coords, count)
        exact = coords.detach().cpu().contiguous()
        indices = result.detach().cpu().reshape(-1).tolist()
        calls.append({
            "step": step,
            "shape": list(coords.shape),
            "stride": list(coords.stride()),
            "dtype": str(coords.dtype),
            "input_sha256": hashlib.sha256(exact.numpy().tobytes()).hexdigest(),
            "coordinates": exact,
            "indices": indices,
        })
        return result

    # The frozen producer calls FPS once per scene in each native batch. Its
    # progress line is printed after forward; count those lines to bind steps.
    original_print = print

    def capture_print(*args, **kwargs):
        nonlocal step
        if len(args) == 1 and isinstance(args[0], str):
            try:
                progress = json.loads(args[0])
            except (ValueError, TypeError):
                progress = None
            if isinstance(progress, dict) and progress.get("step") == step:
                step += 1
        original_print(*args, **kwargs)

    import builtins
    previous_print = builtins.print
    try:
        FurthestPointSampling.apply = staticmethod(capture_apply)
        builtins.print = capture_print
        runpy.run_path(str(producer), run_name="__main__")
    finally:
        FurthestPointSampling.apply = original_apply
        builtins.print = previous_print

    capture_path = output / "capture.json"
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    if capture.get("capture_mode") != "manifest_subset":
        raise ValueError("Not a diagnostic manifest subset")
    selected = bind_fps_calls(capture["rows"], calls)
    payload = {}
    for index, call in selected.items():
        row = next(r for r in capture["rows"] if r["manifest_index"] == index)
        payload[index] = {
            **call,
            "native_input_sha256": row["native_input_sha256"],
            "scene_id": row["scene"],
            "ann_id": row["ann_id"],
        }
    torch.save(payload, output / "entry_fps_inputs.pt")
    receipt = {
        "contract": "m95_entry_fps_input_capture_v1",
        "scope": "Diagnostic subset; not strict full-scan replay or efficacy",
        "producer_sha256": hashlib.sha256(producer.read_bytes()).hexdigest(),
        "capture_sha256": hashlib.sha256(capture_path.read_bytes()).hexdigest(),
        "extension_path": str(binary),
        "extension_sha256": binary_sha,
        "calls": len(calls),
        "target_rows": sorted(payload),
        "inputs_sha256": hashlib.sha256(
            (output / "entry_fps_inputs.pt").read_bytes()
        ).hexdigest(),
        "admission": False,
    }
    (output / "entry_fps_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
