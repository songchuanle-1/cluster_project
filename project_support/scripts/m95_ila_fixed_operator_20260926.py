"""Checkpoint-free repeat control for the M95 final-layer ila operator."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys


def digest(tensor):
    return hashlib.sha256(
        tensor.detach().cpu().contiguous().numpy().tobytes()
    ).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=32)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "7":
        raise ValueError("Authorized physical GPU7 required")
    if not 2 <= args.repeats <= 128:
        raise ValueError("Bounded repeats required")
    output = Path(args.output)
    if output.exists():
        raise ValueError("Output already exists")
    root = Path(args.root).resolve()
    sys.path[:0] = [str(Path(args.bundle).resolve()), str(root),
                    str(root / "framework/lib")]

    import torch
    from frozen_capture_contract_20260916 import model_package_sha256

    model_name = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
    expected = "cf4ce01548cecf186ba4677f5c13977f9fa527b2e33af6c82f564a7150a4c1d0"
    if model_package_sha256(root, model_name) != expected:
        raise ValueError("M95 source identity differs")
    dec = importlib.import_module(
        "framework.model.Quard_model." + model_name + ".dec"
    )
    torch.manual_seed(1999)
    torch.cuda.manual_seed_all(1999)
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.08)
    ila = dec.CrossAttentionLayer(256, 8, 0.0).cuda().eval()
    source = torch.randn(1, 48, 256, device="cuda")
    query = torch.randn(1, 1332, 256, device="cuda")
    mask = torch.zeros(1, 48, dtype=torch.bool, device="cuda")
    mask[:, -8:] = True
    inputs = {
        "source": digest(source), "query": digest(query),
        "mask": digest(mask),
    }
    rows = []
    first = None
    with torch.no_grad():
        for repeat in range(args.repeats):
            result = ila(source, query, mask, None)
            values = [value.detach() for value in result if torch.is_tensor(value)]
            if not values or not bool(torch.isfinite(values[0]).all()):
                raise ValueError("Nonfinite primary operator output")
            if first is None:
                first = [value.clone() for value in values]
            rows.append({
                "repeat": repeat,
                "sha256": [digest(value) for value in values],
                "finite": [bool(torch.isfinite(value).all()) for value in values],
                "max_abs_from_first": [
                    float((value - origin).abs().max())
                    if bool(torch.isfinite(value).all()) else None
                    for value, origin in zip(values, first)
                ],
            })
    result = {
        "contract": "m95_ila_fixed_operator_v1",
        "scope": "Synthetic fixed tensors and freshly initialized M95 ila; "
                 "not a checkpoint or historical TRAIN-item replay",
        "model_source_sha256": expected,
        "physical_gpu": 7,
        "inputs_sha256": inputs,
        "output_shapes": [list(value.shape) for value in first],
        "rows": rows,
        "unique_output_hashes": [
            len({row["sha256"][i] for row in rows})
            for i in range(len(first))
        ],
        "strict_reproducibility_status": "fail",
        "admission": False,
    }
    output.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="ascii"
    )


if __name__ == "__main__":
    main()
