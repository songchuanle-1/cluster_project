"""CPU-only provenance audit; never infer historical identity from shape matches."""
import argparse
import gc
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def log_metrics(path):
    rows, epoch = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.search(r"Epoch \[(\d+)/(\d+)\]", line)
        if match:
            epoch = int(match[1])
        match = re.search(r"\bmIoU : ([0-9.]+)", line)
        if match:
            rows.append(dict(epoch=epoch, miou=float(match[1]), time=line.split(" - ")[0]))
        elif rows:
            acc = re.search(r"\bmIOU:.*?Acc_50: ([0-9.]+)", line)
            spm = re.search(r"\bspmIOU: ([0-9.]+)", line)
            if acc:
                rows[-1]["acc50"] = float(acc[1].rstrip("."))
            if spm:
                rows[-1]["spmiou"] = float(spm[1].rstrip("."))
    return dict(log_sha256=digest(path), validations=rows,
                best=max(rows, key=lambda r: r["miou"]) if rows else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-root", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.code_root)
    sys.path[:0] = [str(root), str(root / "framework/lib")]
    import torch
    import yaml

    torch.set_num_threads(1)
    ckpt_path, cfg_path = Path(args.checkpoint), Path(args.config)
    output = dict(checkpoint=str(ckpt_path), checkpoint_sha256=digest(ckpt_path),
                  config=str(cfg_path), config_sha256=digest(cfg_path),
                  explicit_module=args.module, cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                  torch_version=torch.__version__, log=log_metrics(Path(args.log)),
                  code_head=subprocess.check_output(
                      ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip())
    # Project-owned checkpoint; deserialize on CPU only, no inference or optimizer step.
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    output["checkpoint_top_keys"] = list(ckpt)
    output["meta"] = ckpt.get("meta", {})
    state = ckpt.get("state_dict", ckpt.get("model"))
    if state is None:
        raise ValueError("No recognized state dict")
    output["state_key_count"] = len(state)
    output["state_shapes"] = {k: list(v.shape) for k, v in state.items() if torch.is_tensor(v)}
    output["nonfinite_tensors"] = [k for k, v in state.items()
                                  if torch.is_tensor(v) and v.is_floating_point()
                                  and not bool(torch.isfinite(v).all())]
    cfg = yaml.safe_load(cfg_path.read_text())
    output["saved_config"] = cfg
    module = importlib.import_module(args.module)
    package_dir = Path(module.__file__).parent
    output["package_sha256"] = {p.name: digest(p) for p in sorted(package_dir.glob("*.py"))}
    network = module.Network(**cfg["model"])
    expected = network.state_dict()
    missing = sorted(set(expected) - set(state))
    unexpected = sorted(set(state) - set(expected))
    mismatches = {k: dict(checkpoint=list(state[k].shape), model=list(expected[k].shape))
                  for k in expected.keys() & state.keys()
                  if state[k].shape != expected[k].shape}
    output["compatibility"] = dict(missing=missing, unexpected=unexpected, mismatches=mismatches)
    output["strict_load_passed"] = False
    if not missing and not unexpected and not mismatches:
        network.load_state_dict(state, strict=True)
        output["strict_load_passed"] = True
    buffer_names = {
        "text_encoder.embeddings.position_ids",
        "text_encoder.embeddings.token_type_ids",
    }
    buffers = {}
    for key in buffer_names:
        if key in state:
            saved = state[key]
            current = getattr(network.text_encoder.embeddings, key.rsplit(".", 1)[1], None)
            buffers[key] = dict(
                shape=list(saved.shape), dtype=str(saved.dtype),
                matches_runtime_buffer=current is not None and torch.equal(saved, current))
    output["legacy_buffers"] = buffers
    output["adapted_strict_load_passed"] = False
    if (not missing and not mismatches and set(unexpected) == buffer_names
            and all(b["matches_runtime_buffer"] for b in buffers.values())):
        adapted = {k: v for k, v in state.items() if k not in buffer_names}
        network.load_state_dict(adapted, strict=True)
        output["adapted_strict_load_passed"] = True
        output["adaptation"] = "In-memory omission of exactly two equal nonpersistent runtime buffers; no checkpoint/model file writes."
    output["cuda_initialized"] = torch.cuda.is_initialized()
    output["limitation"] = "State compatibility is not proof of historical forward identity or metric replay."
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items()
                      if k not in ("state_shapes", "saved_config", "package_sha256", "log")}, indent=2, default=str))
    print("Exact log best:", output["log"]["best"])
    del network, state, ckpt
    gc.collect()
    assert not output["cuda_initialized"]


if __name__ == "__main__":
    main()
