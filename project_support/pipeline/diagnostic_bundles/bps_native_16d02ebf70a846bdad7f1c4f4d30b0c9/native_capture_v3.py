"""Exact, narrowly checked checkpoint adapter for the immutable native runner."""

import argparse
from collections.abc import Mapping
import importlib.util
import json
from pathlib import Path
import sys

KEYS = (
    "text_encoder.embeddings.position_ids",
    "text_encoder.embeddings.token_type_ids",
)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--runner", required=True)
    args, rest = parser.parse_known_args()
    outputs = argparse.ArgumentParser(add_help=False)
    outputs.add_argument("--output", required=True)
    outputs.add_argument("--checkpoint", required=True)
    locations, _ = outputs.parse_known_args(rest)
    path = Path(args.runner)
    spec = importlib.util.spec_from_file_location("immutable_native_capture_v1", path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    assert native.digest(path) == (
        "f29e5f8dd8dd70a8cb7428f8facd7f8e37401ced27e01cdf1e0ef2db19c175e9"
    )
    output = Path(locations.output)
    audit_path = output.parent / "adapter_audit.json"
    frozen = output.parent / "checkpoint_snapshot.pth"
    original_load = native.torch.load
    original_state_load = native.torch.nn.Module.load_state_dict
    original_argv = sys.argv
    audit = {
        "adapter_sha256": native.digest(__file__),
        "original_runner_sha256": native.digest(path),
        "checkpoint_origin": locations.checkpoint,
        "allowed_buffer_keys": list(KEYS),
        "loads": [],
        "perturbed_buffer_negative_control": "not_run",
        "status": "running",
    }

    def check_buffers(module, state):
        current_state = module.state_dict()
        assert set(state) - set(current_state) == set(KEYS), "Unexpected keys not exactly allowed set"
        buffers = dict(module.named_buffers())
        records = {}
        for key in KEYS:
            assert key in buffers and key not in current_state
            left, right = state[key].detach().cpu(), buffers[key].detach().cpu()
            assert left.shape == right.shape and left.dtype == right.dtype
            assert native.torch.equal(left, right), "Named buffer value differs: " + key
            records[key] = {
                "shape": list(left.shape), "dtype": str(left.dtype),
                "checkpoint_hash": native.input_hash(left),
                "native_buffer_hash": native.input_hash(right),
            }
        return records

    def checkpoint_load(file, *positional, **keywords):
        value = original_load(file, *positional, **keywords)
        if isinstance(file, (str, Path)) and Path(file) == frozen:
            assert isinstance(value, Mapping) and isinstance(value["model"], Mapping)
            value = {**value, "state_dict": value["model"]}
        return value

    def strict_state_load(module, state, strict=True, assign=False):
        if module.__class__.__module__.startswith(
                "framework.model.Quard_model." + native.PACKAGE):
            assert module.__class__.__name__ == "Network" and strict is True and not assign
            records = check_buffers(module, state)
            if not audit["loads"]:
                altered = dict(state)
                altered[KEYS[0]] = state[KEYS[0]].clone()
                altered[KEYS[0]].view(-1)[0] += 1
                try:
                    check_buffers(module, altered)
                except AssertionError:
                    audit["perturbed_buffer_negative_control"] = "rejected_as_required"
                else:
                    raise AssertionError("Perturbed buffer control was not rejected")
            filtered = {key: value for key, value in state.items() if key not in KEYS}
            result = original_state_load(module, filtered, strict=True, assign=False)
            assert not result.missing_keys and not result.unexpected_keys
            audit["loads"].append({"buffers": records, "remaining_keys": len(filtered), "strict": True})
            native.save(audit_path, audit)
            return result
        return original_state_load(module, state, strict=strict, assign=assign)

    native.torch.load = checkpoint_load
    native.torch.nn.Module.load_state_dict = strict_state_load
    sys.argv = [original_argv[0], *rest]
    try:
        native.main()
        result = json.loads(output.read_text())
        assert result["checkpoint_sha256"] == native.digest(locations.checkpoint)
        audit["status"] = "completed"
        result["adapter_sha256"] = audit["adapter_sha256"]
        result["adapter_audit"] = str(audit_path)
        native.save(output, result)
        print(json.dumps({
            "result_sha256": native.digest(output),
            "strict_loads": len(audit["loads"]),
            "negative_control": audit["perturbed_buffer_negative_control"],
        }), flush=True)
    except BaseException as exc:
        audit["status"] = "failed"
        audit["error_type"] = type(exc).__name__
        audit["error"] = str(exc)
        raise
    finally:
        native.torch.load = original_load
        native.torch.nn.Module.load_state_dict = original_state_load
        sys.argv = original_argv
        native.save(audit_path, audit)


if __name__ == "__main__":
    main()
