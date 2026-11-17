"""Native FPS sensitivity along the measured pre-FPS coordinate difference."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(args.root).resolve()))
    import torch
    import pointnet2._ext as extension

    binary_sha = sha(extension.__file__)

    def load(directory):
        directory = Path(directory)
        receipt = json.loads(
            (directory / "entry_fps_receipt.json").read_text(encoding="utf-8")
        )
        if receipt["extension_sha256"] != binary_sha:
            raise ValueError("Extension identity differs")
        if receipt["producer_sha256"] != (
            "c76eae8906bc8abe136acd4df8fe5eb4e78a6755508d80a318a9371c4658d821"
        ):
            raise ValueError("Producer identity differs")
        path = directory / "entry_fps_inputs.pt"
        if receipt["inputs_sha256"] != sha(path):
            raise ValueError("Coordinate identity differs")
        return torch.load(path, map_location="cpu", weights_only=True)

    left, right = load(args.left), load(args.right)
    rows = []
    for index in (95, 193):
        a, b = left[index], right[index]
        if a["native_input_sha256"] != b["native_input_sha256"]:
            raise ValueError("Native item identity differs")
        if a["shape"] != b["shape"] or a["dtype"] != b["dtype"]:
            raise ValueError("FPS tensor contract differs")
        first = a["coordinates"].cuda()
        delta = b["coordinates"].cuda() - first
        sampled = []
        with torch.no_grad():
            for step in range(33):
                if step == 0:
                    coords = first
                elif step == 32:
                    coords = b["coordinates"].cuda()
                else:
                    coords = first + delta * (step / 32)
                output = extension.furthest_point_sampling(
                    coords.contiguous(), len(a["indices"])
                ).cpu().reshape(-1).tolist()
                sampled.append(output)
        if sampled[0] != a["indices"] or sampled[-1] != b["indices"]:
            raise ValueError("Endpoint native replay differs")
        rows.append({
            "manifest_index": index,
            "steps": 32,
            "unique_fps_outputs": len({tuple(x) for x in sampled}),
            "first_output_change_step": next(
                (i for i, x in enumerate(sampled) if x != sampled[0]), None
            ),
            "changed_indices_from_first": [
                sum(x != y for x, y in zip(sampled[0], item))
                for item in sampled
            ],
        })
    result = {
        "contract": "m95_entry_fps_interpolation_v1",
        "scope": "Native FPS on interpolated measured coordinates; diagnostic only",
        "left_receipt_sha256": sha(
            Path(args.left) / "entry_fps_receipt.json"
        ),
        "right_receipt_sha256": sha(
            Path(args.right) / "entry_fps_receipt.json"
        ),
        "extension_sha256": binary_sha,
        "rows": rows,
        "admission": False,
    }
    output = Path(args.output)
    if output.exists():
        raise ValueError("Require new report")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
