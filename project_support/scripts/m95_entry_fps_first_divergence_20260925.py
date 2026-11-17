"""Locate the first changed FPS choice and its distance margin."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def first_divergence(a, b):
    import torch

    if a["native_input_sha256"] != b["native_input_sha256"]:
        raise ValueError("Native item identity differs")
    left, right = a["indices"], b["indices"]
    if len(left) != len(right):
        raise ValueError("FPS output axis differs")
    first = next((i for i, (x, y) in enumerate(zip(left, right)) if x != y),
                 None)
    if first is None:
        return {"first_changed_position": None, "changed_indices": 0}

    def distances(entry):
        xyz = entry["coordinates"][0].float()
        selected = torch.tensor(entry["indices"][:first], dtype=torch.long)
        if not torch.equal(
            selected, torch.tensor(left[:first], dtype=torch.long)
        ):
            raise ValueError("Common FPS prefix differs")
        # Mirror the native kernel's running minimum, including its skip for
        # near-zero coordinate magnitude.
        valid = (xyz * xyz).sum(-1) > 1e-3
        minimum = torch.full((len(xyz),), 1e10)
        for index in selected:
            delta = xyz - xyz[int(index)]
            minimum = torch.minimum(minimum, (delta * delta).sum(-1))
        minimum[~valid] = float("-inf")
        chosen = int(entry["indices"][first])
        other = int(b["indices"][first] if entry is a else a["indices"][first])
        return {
            "chosen_index": chosen,
            "other_index": other,
            "chosen_distance2": float(minimum[chosen]),
            "other_distance2": float(minimum[other]),
            "chosen_minus_other_distance2": float(
                minimum[chosen] - minimum[other]
            ),
        }

    return {
        "first_changed_position": first,
        "changed_indices": sum(x != y for x, y in zip(left, right)),
        "left": distances(a),
        "right": distances(b),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    import torch

    def load(directory):
        directory = Path(directory)
        receipt = json.loads(
            (directory / "entry_fps_receipt.json").read_text(encoding="utf-8")
        )
        source = directory / "entry_fps_inputs.pt"
        if receipt["inputs_sha256"] != sha(source):
            raise ValueError("Captured tensor identity differs")
        return receipt, torch.load(source, map_location="cpu", weights_only=True)

    left_receipt, left = load(args.left)
    right_receipt, right = load(args.right)
    if left_receipt["extension_sha256"] != right_receipt["extension_sha256"]:
        raise ValueError("Extension identity differs")
    if set(left) != set(right):
        raise ValueError("Manifest rows differ")
    result = {
        "contract": "m95_entry_fps_first_divergence_v1",
        "scope": "Matched diagnostic subsets, not historical full-scan replay",
        "left_receipt_sha256": sha(Path(args.left) / "entry_fps_receipt.json"),
        "right_receipt_sha256": sha(Path(args.right) / "entry_fps_receipt.json"),
        "rows": [
            {"manifest_index": index, **first_divergence(left[index], right[index])}
            for index in sorted(left)
        ],
        "admission": False,
    }
    path = Path(args.output)
    if path.exists():
        raise ValueError("Require new output")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
