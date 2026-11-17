"""Compare two matched diagnostic entry-FPS captures without tolerance relaxation."""
import argparse
import hashlib
import json
from pathlib import Path


TARGET_ROWS = frozenset((83, 95, 174, 178, 193))
CONTRACT = "m95_entry_fps_input_capture_v1"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(left, right):
    if set(left) != TARGET_ROWS or set(right) != TARGET_ROWS:
        raise ValueError("Target row coverage differs")
    rows = []
    for index in sorted(TARGET_ROWS):
        a, b = left[index], right[index]
        for field in ("scene_id", "ann_id", "native_input_sha256"):
            if a[field] != b[field]:
                raise ValueError("Row %d %s identity differs" % (index, field))
        if a["shape"] != b["shape"] or a["dtype"] != b["dtype"]:
            raise ValueError("Row %d FPS tensor contract differs" % index)
        if len(a["indices"]) != len(b["indices"]):
            raise ValueError("Row %d FPS output axis differs" % index)
        coords_a, coords_b = a["coordinates"], b["coordinates"]
        rows.append({
            "manifest_index": index,
            "native_input_sha256": a["native_input_sha256"],
            "coordinate_exact": bool((coords_a == coords_b).all()),
            "coordinate_max_abs_delta": float((coords_a - coords_b).abs().max()),
            "coordinate_bytes_equal": a["input_sha256"] == b["input_sha256"],
            "stride_equal": a["stride"] == b["stride"],
            "fps_changed_indices": sum(
                x != y for x, y in zip(a["indices"], b["indices"])
            ),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    import torch

    def load(directory):
        directory = Path(directory)
        receipt_path = directory / "entry_fps_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("contract") != CONTRACT:
            raise ValueError("Capture contract differs")
        if receipt["inputs_sha256"] != sha256(directory / "entry_fps_inputs.pt"):
            raise ValueError("Input artifact hash differs")
        capture_path = directory / "capture.json"
        if receipt["capture_sha256"] != sha256(capture_path):
            raise ValueError("Native capture hash differs")
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        if capture.get("capture_mode") != "manifest_subset":
            raise ValueError("Capture mode differs")
        return (
            receipt,
            capture,
            torch.load(directory / "entry_fps_inputs.pt", map_location="cpu",
                       weights_only=True),
        )

    left_receipt, left_capture, left = load(args.left)
    right_receipt, right_capture, right = load(args.right)
    if left_receipt["producer_sha256"] != right_receipt["producer_sha256"]:
        raise ValueError("Producer identity differs")
    if left_receipt["extension_sha256"] != right_receipt["extension_sha256"]:
        raise ValueError("Extension identity differs")
    for field in ("checkpoint_sha256", "config_sha256", "model_source_sha256"):
        if left_capture.get(field) != right_capture.get(field):
            raise ValueError("%s differs" % field)
    if left_capture.get("manifest", {}).get("sha256") != right_capture.get(
        "manifest", {}
    ).get("sha256"):
        raise ValueError("Manifest identity differs")
    result = {
        "contract": "m95_entry_fps_pair_compare_v1",
        "scope": "Two diagnostic manifest subsets; not strict full-scan replay",
        "left_receipt_sha256": sha256(Path(args.left) / "entry_fps_receipt.json"),
        "right_receipt_sha256": sha256(Path(args.right) / "entry_fps_receipt.json"),
        "producer_sha256": left_receipt["producer_sha256"],
        "extension_sha256": left_receipt["extension_sha256"],
        "checkpoint_sha256": left_capture["checkpoint_sha256"],
        "manifest_sha256": left_capture["manifest"]["sha256"],
        "rows": compare(left, right),
        "admission": False,
    }
    output = Path(args.output)
    if output.exists():
        raise ValueError("Require a new output path")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
