"""Replay captured entry-FPS tensors through the loaded native extension."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay(left, right, extension, repeats=5):
    import torch

    if set(left) != set(right):
        raise ValueError("Row coverage differs")
    rows = []
    for index in sorted(left):
        a, b = left[index], right[index]
        if a["native_input_sha256"] != b["native_input_sha256"]:
            raise ValueError("Native input differs for row %d" % index)
        if a["shape"] != b["shape"] or a["dtype"] != b["dtype"]:
            raise ValueError("FPS input contract differs for row %d" % index)
        records = []
        for entry in (a, b):
            coords = entry["coordinates"].cuda()
            if not coords.is_contiguous():
                raise ValueError("Captured coordinates are not contiguous")
            observed = [
                extension.furthest_point_sampling(
                    coords, len(entry["indices"])
                ).cpu().reshape(-1).tolist()
                for _ in range(repeats)
            ]
            records.append({
                "matches_native": observed[0] == entry["indices"],
                "repeat_identical": all(x == observed[0] for x in observed),
                "repeat_changed_count": [
                    sum(x != y for x, y in zip(observed[0], item))
                    for item in observed[1:]
                ],
                "output": observed[0],
            })
        rows.append({
            "manifest_index": index,
            "left_matches_native": records[0]["matches_native"],
            "right_matches_native": records[1]["matches_native"],
            "left_repeat_identical": records[0]["repeat_identical"],
            "right_repeat_identical": records[1]["repeat_identical"],
            "left_repeat_changed_count": records[0]["repeat_changed_count"],
            "right_repeat_changed_count": records[1]["repeat_changed_count"],
            "cross_input_changed_count": sum(
                x != y for x, y in zip(
                    records[0]["output"], records[1]["output"]
                )
            ),
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(args.root).resolve()))
    import torch
    import pointnet2._ext as extension

    binary = Path(extension.__file__).resolve()
    sha = digest(binary)

    def load(directory):
        directory = Path(directory)
        receipt = json.loads(
            (directory / "entry_fps_receipt.json").read_text(encoding="utf-8")
        )
        if receipt.get("contract") != "m95_entry_fps_input_capture_v1":
            raise ValueError("Wrong capture contract")
        if receipt["extension_sha256"] != sha:
            raise ValueError("Loaded extension identity differs")
        inputs = directory / "entry_fps_inputs.pt"
        if receipt["inputs_sha256"] != digest(inputs):
            raise ValueError("Captured input identity differs")
        return torch.load(inputs, map_location="cpu", weights_only=True)

    left, right = load(args.left), load(args.right)
    result = {
        "contract": "m95_entry_fps_replay_v1",
        "scope": "Captured coordinate replay; no model efficacy or strict full-scan claim",
        "extension_binary": str(binary),
        "extension_sha256": sha,
        "repeats_per_input": 5,
        "rows": replay(left, right, extension),
        "admission": False,
    }
    output = Path(args.output)
    if output.exists():
        raise ValueError("Require a new output path")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
