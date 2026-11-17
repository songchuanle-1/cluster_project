"""Versioned format adapter; original runner and checkpoint stay immutable."""
import argparse
from collections.abc import Mapping
import importlib.util
import json
from pathlib import Path


def main():
    path = Path(__file__).parent / "native_capture.py"
    spec = importlib.util.spec_from_file_location("immutable_native_capture_v1", path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    assert native.digest(path) == (
        "f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9")
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", required=True)
    parser.add_argument("--checkpoint", required=True)
    args, rest = parser.parse_known_args()
    frozen = Path(args.output).parent / "checkpoint_snapshot.pth"
    original_load = native.torch.load

    def project_checkpoint_load(file, *positional, **keywords):
        value = original_load(file, *positional, **keywords)
        if isinstance(file, (str, Path)) and Path(file) == frozen:
            assert isinstance(value, Mapping) and isinstance(value["model"], Mapping)
            value = {**value, "state_dict": value["model"]}
        return value

    native.torch.load = project_checkpoint_load
    try:
        native.main()
        result = json.loads(Path(args.output).read_text())
        result.update(adapter_sha256=native.digest(__file__),
                      checkpoint_payload_key="model",
                      frozen_input_checkpoint_origin=args.checkpoint,
                      prior_adapter_failure="KeyError state_dict, before model forward")
        native.save(Path(args.output), result)
        print(json.dumps(dict(adapter_sha256=result["adapter_sha256"],
                              result_sha256=native.digest(args.output))), flush=True)
    finally:
        native.torch.load = original_load


if __name__ == "__main__":
    main()
