"""Independent optimized package full native repeat/backward and bypass."""
import argparse
from datetime import datetime, timezone
import gc
import json
import os
from pathlib import Path
import sys

from bps_runtime_20261014_0424 import (
    PIPE, fingerprint, get_batch, parameters, setup, sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    os.environ["BPS_PACKAGE_STAGE"] = str(PIPE / ("bps_staging_" + args.token + "_v3"))
    torch, gorilla, dataset, model, state, frozen, sources, full_name = setup(args.token)
    expected = Path(os.environ["BPS_PACKAGE_STAGE"])
    assert Path(sys.modules[full_name + ".network"].__file__).is_relative_to(expected)
    cases = [[r["native_group"]] for r in frozen]
    cases += [[r["native_group"] for r in frozen[i:i + 2]] for i in range(0, 8, 2)]
    cases += [[5743], [7787], [5743, 7787], [0], [0, 44], [0, 452]]
    held = {}
    hook = model.criterion.register_forward_pre_hook(
        lambda module, inputs, kwargs: held.update(pred=inputs[0]), with_kwargs=True)
    def snapshot(value, prefix=""):
        fields = {}
        if isinstance(value, torch.Tensor):
            fields[prefix] = value.detach().cpu().clone()
        elif isinstance(value, dict):
            for key, part in value.items():
                fields.update(snapshot(part, prefix + "/" + key))
        elif isinstance(value, (list, tuple)):
            for i, part in enumerate(value):
                fields.update(snapshot(part, prefix + "/" + str(i)))
        return fields
    rows = []
    torch.cuda.reset_peak_memory_stats()
    progress = PIPE / ("bps_native_current_" + args.token + ".progress.jsonl")
    try:
        with progress.open("x") as stream:
            for groups in cases:
                trials = []
                prior = None
                max_fields = max_grad = 0.
                input_shas = []
                for repeat in (0, 1):
                    model.load_state_dict(state, strict=True)
                    model.train()
                    batch = get_batch(torch, gorilla, dataset, groups)
                    input_shas.append(fingerprint(batch))
                    model.zero_grad(set_to_none=True)
                    held.clear()
                    gorilla.set_random_seed(1999)
                    loss, parts = model(batch, mode="loss")
                    component = parts["between_support_loss"]
                    named = parameters(model)
                    direct = torch.autograd.grad(component, [p for _, p in named],
                                                 retain_graph=True, allow_unused=True)
                    assert all(g is None or bool(torch.isfinite(g).all()) for g in direct)
                    component_nonzero = sum(g is not None and bool((g != 0).any()) for g in direct)
                    del direct
                    fields = snapshot(held["pred"])
                    fields["/loss"] = loss.detach().cpu().clone()
                    fields["/component"] = component.detach().cpu().clone()
                    loss.backward()
                    gradients = {name: p.grad.detach().cpu().clone()
                                 for name, p in named if p.grad is not None}
                    assert all(bool(torch.isfinite(g).all()) for g in gradients.values())
                    if prior is not None:
                        assert fields.keys() == prior[0].keys()
                        assert gradients.keys() == prior[1].keys()
                        max_fields = max(float((value.double() - prior[0][key].double()).abs().max())
                                         if value.numel() else 0. for key, value in fields.items())
                        max_grad = max(float((value - prior[1][name]).abs().max())
                                       for name, value in gradients.items())
                    prior = fields, gradients
                    trials.append({"trial": repeat, "full_loss": float(loss.detach()),
                                   "component_loss": float(component.detach()),
                                   "component_nonzero_original_tensors": component_nonzero,
                                   "all_full_gradients_finite": True,
                                   "full_nonzero_original_tensors": sum(bool((g != 0).any()) for g in gradients.values()),
                                   "readout": model.between_support.last_readout,
                                   "work": model.between_support.last_work,
                                   "prediction_tensor_fields": len(fields)})
                    held.clear()
                    del loss, parts, component, batch, named
                    gc.collect()
                    torch.cuda.empty_cache()
                row = {"groups": groups, "input_sha256": input_shas,
                       "input_equal": len(set(input_shas)) == 1, "trials": trials,
                       "all_tensor_fields_max_repeat_delta": max_fields,
                       "full_parameter_gradient_max_repeat_delta": max_grad,
                       "pass1e6": len(set(input_shas)) == 1 and max(max_fields, max_grad) <= 1e-6}
                rows.append(row)
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                print(json.dumps({"groups": groups, "pass": row["pass1e6"],
                                  "max_delta": max(max_fields, max_grad),
                                  "component": trials[0]["component_loss"]}), flush=True)
                del prior, fields, gradients
    finally:
        hook.remove()
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "source_manifest": sources, "rows": rows,
              "native_forward_count": len(rows) * 2, "native_backward_count": len(rows) * 2,
              "optimizer_steps": 0, "new_trainable_tensors": 0,
              "allocator_peak_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
              "allocator_peak_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
              "scope": "Independent optimized package native train loss, all-output/gradient repeat and exact inactive-path regression, not efficacy."}
    output = PIPE / ("bps_native_current_" + args.token + ".json")
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "all_pass": all(r["pass1e6"] for r in rows)}), flush=True)


if __name__ == "__main__":
    main()
