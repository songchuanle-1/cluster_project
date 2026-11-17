"""Inspect only bound M95 full-scan target artifacts, without model execution."""
import argparse
import hashlib
import json
from pathlib import Path

import torch


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe(value):
    if torch.is_tensor(value):
        return {"dtype": str(value.dtype), "shape": list(value.shape)}
    if isinstance(value, dict):
        return {str(key): describe(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return {"type": type(value).__name__, "length": len(value),
                "first": describe(value[0]) if value else None}
    return {"type": type(value).__name__, "value": value
            if isinstance(value, (str, int, float, bool, type(None))) else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    artifact = torch.load(args.artifact, map_location="cpu", weights_only=False)
    result = {"path": args.artifact, "sha256": sha256(args.artifact),
              "schema": describe(artifact)}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                      encoding="ascii")


if __name__ == "__main__":
    main()
