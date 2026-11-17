"""CPU arithmetic references for exactly one preregistered failed readout."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1",
                  OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True)
args = parser.parse_args()
root = Path(args.root)
manifest = json.loads((root / "cpu_manifest.json").read_text())
assert not torch.cuda.is_initialized()
torch.set_num_threads(1)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


source = manifest["prefix_source"]
assert digest(source["path"]) == source["sha256"]
assert digest(__file__) == manifest["script_sha256"]
data = np.load(source["path"], allow_pickle=False)
x = torch.from_numpy(data["points"].copy())
mask = torch.from_numpy(data["mask"].copy())
tokens = [torch.from_numpy(data["tokens_" + str(i)].copy()) for i in range(3)]
ids = [[torch.from_numpy(data["ids_" + str(level) + "_" + str(b)].copy()).long()
        for b in range(x.shape[0])] for level in range(3)]
names = ("level_gate_weight", "level_gate_bias", "point_out_proj_weight",
         "point_out_proj_bias", "message_norm_weight", "message_norm_bias")
weights = {name: torch.from_numpy(data[name].copy()) for name in names}
eps = float(data["message_norm_eps"])
b = 0
valid = int((~mask[b]).sum())
index = valid - 1
assert index == manifest["fixed_readout"]["point"] == 728
coarse = ids[0][b]
for level in (1, 2):
    coarse = ids[level][b][coarse]
remote = int((coarse != coarse[index]).nonzero().flatten()[0])
centered = weights["level_gate_weight"].double()[:, x.shape[-1]:]
centered = centered - centered.mean(0, keepdim=True)
_, s, vh = torch.linalg.svd(centered, full_matrices=False)
rank = int((s > torch.finfo(torch.float64).eps * max(centered.shape) * s.max()).sum())
assert rank <= 2
basis = vh[:rank]
d = x[b, remote].double() - x[b, index].double()
row = basis.T @ (basis @ d)
null = d - row
norm = x[b, remote].double().norm()
assert min(float(row.norm()), float(null.norm()), float(norm)) > 1e-12
row = row / row.norm() * norm
null = null / null.norm() * norm
assert float((centered @ null).abs().max()) <= 1e-12

counts = {"cpu_source_formula_forwards": 0}


def message(points, values):
    w = {name: value.to(points) for name, value in weights.items()}
    composed = []
    for batch in range(points.shape[0]):
        path = [ids[0][batch].clamp(0, values[0].shape[1] - 1)]
        for level in (1, 2):
            parents = ids[level][batch].clamp(0, values[level].shape[1] - 1)
            path.append(parents.gather(0, path[-1]))
        composed.append(path)
    messages = []
    for level in range(3):
        out = torch.zeros_like(points)
        for batch in range(points.shape[0]):
            positions = composed[batch][level]
            n = min(positions.shape[0], points.shape[1])
            out[batch, :n] = values[level][batch, positions[:n]]
        messages.append(out)
    stack = torch.stack(messages, dim=-1)
    mean = points.mean(dim=1, keepdim=True).expand_as(points)
    logits = F.linear(torch.cat([points, mean], dim=-1),
                      w["level_gate_weight"], w["level_gate_bias"])
    fused = (stack * logits.softmax(dim=-1).unsqueeze(-2)).sum(dim=-1)
    out = F.linear(fused, w["point_out_proj_weight"], w["point_out_proj_bias"])
    out = out.masked_fill(mask.unsqueeze(-1), 0)
    out = F.layer_norm(out, (out.shape[-1],), w["message_norm_weight"],
                       w["message_norm_bias"], eps)
    counts["cpu_source_formula_forwards"] += 1
    return out.masked_fill(mask.unsqueeze(-1), 0)


conditions = ("remote_null", "remote_row", "own_coarse_null")
actual = []
for label, direction in zip(conditions, (null, row, null)):
    px = x.clone()
    ts = [t.clone() for t in tokens]
    if label == "own_coarse_null":
        ts[-1][b, coarse[index]] += direction.to(ts[-1])
    else:
        px[b, remote] += direction.to(px)
    actual.append((px, ts))

records = {}
for precision in ("float32", "float64_ideal", "float64_actual_float32_inputs"):
    double = precision != "float32"
    px = x.double() if double else x
    ts = [t.double() if double else t for t in tokens]
    base = message(px, ts)
    observed = {"baseline_vs_saved_native_max": float(
        (base - torch.from_numpy(data["message"].copy()).to(base)).abs().max())}
    for n, (label, direction) in enumerate(zip(conditions, (null, row, null))):
        if precision == "float64_ideal":
            changed = px.clone()
            changed_tokens = [t.clone() for t in ts]
            if label == "own_coarse_null":
                changed_tokens[-1][b, coarse[index]] += direction
            else:
                changed[b, remote] += direction
        else:
            changed, changed_tokens = actual[n]
            if double:
                changed = changed.double()
                changed_tokens = [t.double() for t in changed_tokens]
        y = message(changed, changed_tokens)
        delta = (y[b, index] - base[b, index]).double()
        observed[label] = {"message_max_absolute_change": float(delta.abs().max()),
                           "message_l2_change": float(delta.norm()),
                           "original_1e_minus6_criterion": bool(delta.abs().max() <= 1e-6)}
    records[precision] = observed

changed = actual[0][0]
actual_change = (changed[b, remote].double() - x[b, remote].double())
exact_shift = actual_change / x.shape[1]
cpu_shift = (changed.mean(1)[b] - x.mean(1)[b]).double()
result = {"recording_completed": True, "native_gate_status": "PENDING_GPU",
          "original_native_failure": manifest["original_failure"],
          "observed_at": datetime.now(timezone.utc).isoformat(),
          "cuda_initialized": torch.cuda.is_initialized(), "native_forwards": 0,
          "native_backwards": 0, "optimizer_steps": 0, "scheduler_steps": 0,
          "new_training": False, "new_VAL": False, **counts,
          "expression": b, "point": index, "remote_point": remote,
          "shape": list(x.shape), "rank": rank, "direction_norm": float(norm),
          "ideal_null_residual": float((centered @ null).abs().max()),
          "cast_null_residual": float((centered @ null.to(x).double()).abs().max()),
          "assignment_null_residual": float((centered @ actual_change).abs().max()),
          "cpu_centered_actual_mean_shift_max": float((centered @ cpu_shift).abs().max()),
          "centered_exact_mean_shift_max": float((centered @ exact_shift).abs().max()),
          "cpu_mean_reduction_rounding_linf": float((cpu_shift - exact_shift).abs().max()),
          "records": records,
          "limitations": "CPU source-formula references only, not native GPU failure attribution, "
                         "new task loss, trained benefit or admission"}
assert not torch.cuda.is_initialized()
with (root / "cpu_channel_roundoff_result.json").open("x") as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
print(json.dumps(result))
