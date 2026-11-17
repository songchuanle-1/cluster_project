"""Whole native loss/gradient boundary: catalog full versus absent."""
import argparse
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import sys

from bps_native_20261014_0319 import (
    PIPE, fingerprint, get_batch, parameters, setup, sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch, gorilla, dataset, model, state, frozen, sources, full_name = setup(args.token)
    model.eval()
    catalog = model.between_support.catalog
    loss_module = sys.modules[full_name + ".loss"]
    operator = loss_module.support_excess
    held = {}
    def capture(*values):
        value = operator(*values)
        held["component"] = value
        return value
    loss_module.support_excess = capture
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs, kwargs: held.update(pred=inputs[0]), with_kwargs=True)
    cases = [{"groups": [r["native_group"]], "batch_size": 1} for r in frozen]
    cases += [{"groups": [r["native_group"] for r in frozen[i:i + 2]], "batch_size": 2}
              for i in range(0, 8, 2)]
    rows = []
    torch.cuda.reset_peak_memory_stats()
    progress = PIPE / ("bps_loss_boundary_" + args.token + ".progress.jsonl")
    try:
        with progress.open("x") as stream:
            for case in cases:
                captures = {}
                for condition in ("full", "empty"):
                    model.load_state_dict(state, strict=True)
                    model.eval()
                    model.between_support.catalog = (catalog if condition == "full" else
                                                     {"schema_version": 1, "records": {}, "instances": {}})
                    batch = get_batch(torch, gorilla, dataset, case["groups"])
                    held.clear()
                    model.zero_grad(set_to_none=True)
                    gorilla.set_random_seed(1999)
                    total, parts = model(batch, mode="loss")
                    assert parts["between_support_loss"] is held["component"]
                    named = parameters(model)
                    direct = torch.autograd.grad(parts["between_support_loss"].to(total.dtype),
                                                 [p for _, p in named],
                                                 retain_graph=True, allow_unused=True)
                    direct = {name: value.detach().cpu().clone()
                              for (name, _), value in zip(named, direct) if value is not None}
                    fields = {key: held["pred"][key].detach().cpu().clone()
                              for key in ("masks", "indis", "scores", "proj_queries", "proj_tokens")}
                    total.backward()
                    gradients = {name: p.grad.detach().cpu().clone()
                                 for name, p in named if p.grad is not None}
                    assert all(bool(torch.isfinite(g).all()) for g in gradients.values())
                    captures[condition] = {
                        "input_sha256": fingerprint(batch), "fields": fields,
                        "parts": {key: value.detach().cpu().clone() for key, value in parts.items()},
                        "total": total.detach().cpu().clone(),
                        "gradients": gradients, "direct": direct,
                        "readout": model.between_support.last_readout}
                    held.clear()
                    del batch, named, total, parts, direct, gradients, fields
                    gc.collect()
                    torch.cuda.empty_cache()
                full, empty = captures["full"], captures["empty"]
                assert full["input_sha256"] == empty["input_sha256"]
                output_delta = {key: float((value - empty["fields"][key]).abs().max())
                                for key, value in full["fields"].items()}
                original_part_delta = {
                    key: float((value - empty["parts"][key]).abs().max())
                    for key, value in full["parts"].items()
                    if key not in ("loss", "between_support_loss")}
                component = full["parts"]["between_support_loss"].to(full["total"].dtype)
                loss_error = float((full["total"] - (empty["total"] + component)).abs().max())
                assert full["gradients"].keys() == empty["gradients"].keys()
                gradient_error = increment_norm = direct_norm = 0.
                direct_nonzero = 0
                for name, value in full["gradients"].items():
                    increment = value - empty["gradients"][name]
                    direct = full["direct"].get(name, torch.zeros_like(value))
                    gradient_error = max(gradient_error, float((increment - direct).abs().max()))
                    increment_norm += float(increment.double().square().sum())
                    direct_norm += float(direct.double().square().sum())
                    direct_nonzero += bool((direct != 0).any())
                row = {**case, "input_sha256": full["input_sha256"],
                       "final_tensor_delta": output_delta, "original_part_delta": original_part_delta,
                       "total_loss_addition_max_error": loss_error,
                       "parameter_gradient_addition_max_error": gradient_error,
                       "full_loss": float(full["total"]), "empty_loss": float(empty["total"]),
                       "component_loss": float(component),
                       "direct_component_nonzero_tensors": direct_nonzero,
                       "gradient_increment_l2": increment_norm ** .5,
                       "direct_component_gradient_l2": direct_norm ** .5,
                       "readout": full["readout"],
                       "boundary_pass1e6": max([loss_error, gradient_error] +
                                                list(output_delta.values()) +
                                                list(original_part_delta.values())) <= 1e-6}
                rows.append(row)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(json.dumps({**case, "component": row["component_loss"],
                                  "gradient_addition_error": gradient_error,
                                  "pass": row["boundary_pass1e6"]}), flush=True)
                del captures, full, empty
                gc.collect()
    finally:
        hook.remove()
        loss_module.support_excess = operator
        model.between_support.catalog = catalog
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "source_manifest": sources,
              "rows": rows, "native_forward_count": len(rows) * 2,
              "native_backward_count": len(rows) * 2, "optimizer_steps": 0,
              "allocator_peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
              "allocator_peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
              "scope": "Actual full-loss and parameter-gradient intervention boundary, not efficacy."}
    output = PIPE / ("bps_loss_boundary_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "all_boundary_pass": all(r["boundary_pass1e6"] for r in rows)}), flush=True)


if __name__ == "__main__":
    main()
