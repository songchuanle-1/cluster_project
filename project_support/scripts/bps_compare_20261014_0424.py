"""Actual native preparation/operator equivalence against immutable V2."""
import argparse
from datetime import datetime, timezone
import gc
import importlib.util
import json
from pathlib import Path
import sys

from bps_runtime_20261014_0424 import (
    PIPE, NAME, fingerprint, get_batch, setup, sha)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    torch, gorilla, dataset, model, state, frozen, _, full_name = setup(args.token)
    stage = PIPE / ("bps_staging_" + args.token + "_v3")
    manifest = json.loads((stage / "source_manifest.json").read_text())
    path = stage / NAME / "between_support.py"
    assert sha(path) == manifest["package"]["between_support.py"]
    spec = importlib.util.spec_from_file_location("bps_exact_prepare_comparison", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    optimized = module.BetweenSupportCatalog(model.between_support._path,
                                             model.between_support._expected_sha256)
    original = model.between_support
    loss_module = sys.modules[full_name + ".loss"]
    operator = loss_module.support_excess
    held = {}
    def capture(*values):
        value = operator(*values)
        held["args"] = values
        return value
    loss_module.support_excess = capture
    cases = [[r["native_group"]] for r in frozen]
    cases += [[5743], [7787], [0], [0, 44], [0, 452], [5743, 7787]]
    rows = []
    model.eval()
    progress = PIPE / ("bps_compare_" + args.token + ".progress.jsonl")
    try:
        with progress.open("x") as stream:
            for groups in cases:
                batch = get_batch(torch, gorilla, dataset, groups)
                gorilla.set_random_seed(1999)
                model.zero_grad(set_to_none=True)
                held.clear()
                total, parts = model(batch, mode="loss")
                masks, targets, indices, num_boxes, reference = held["args"]
                readout = original.last_readout
                optimized_support = optimized.prepare(
                    batch["ann_ids"], batch["scan_ids"], batch["scenes_len"],
                    batch["object_idss"], batch["superpoints"], batch["coords_float"],
                    batch["batch_offsets"], batch["sp_ins_labels"])
                assert optimized.last_readout == readout
                maximum = 0.
                for old, new in zip(reference, optimized_support):
                    assert len(old["costs"]) == len(new["costs"])
                    if old["costs"]:
                        assert torch.equal(old["counts"], new["counts"])
                        assert torch.equal(old["centers"], new["centers"])
                    for a, b, pa, pb in zip(old["costs"], new["costs"], old["pairs"], new["pairs"]):
                        assert a.shape == b.shape and len(pa) == len(pb)
                        maximum = max(maximum, float((a - b).abs().max()))
                        for left, right in zip(pa, pb):
                            for key in ("left_node", "right_node", "a", "b"):
                                assert left[key] == right[key]
                            maximum = max(maximum, abs(left["lower"] - right["lower"]),
                                          abs(left["upper"] - right["upper"]),
                                          max(abs(x - y) for x, y in zip(left["axis"], right["axis"])))
                leaf = [mask.detach().clone().requires_grad_() for mask in masks]
                old_loss = operator(leaf, targets, indices, num_boxes, reference)
                new_loss = module.support_excess(leaf, targets, indices, num_boxes, optimized_support)
                old_grad = torch.autograd.grad(old_loss, leaf)
                new_grad = torch.autograd.grad(new_loss, leaf)
                gradient_delta = max(float((a - b).abs().max()) for a, b in zip(old_grad, new_grad))
                loss_delta = abs(float(old_loss.detach()) - float(new_loss.detach()))
                assert all(bool(torch.isfinite(g).all()) for g in new_grad)
                row = {"groups": groups, "input_sha256": fingerprint(batch),
                       "readout_exact": True, "field_descriptor_max_delta": maximum,
                       "loss_delta": loss_delta, "gradient_max_delta": gradient_delta,
                       "work": optimized.last_work,
                       "pass1e6": max(maximum, loss_delta, gradient_delta) <= 1e-6}
                rows.append(row)
                stream.write(json.dumps(row) + "\n")
                stream.flush()
                print(json.dumps(row), flush=True)
                held.clear()
                del total, parts, masks, targets, reference, optimized_support, leaf
                del old_loss, new_loss, old_grad, new_grad, batch
                gc.collect()
                torch.cuda.empty_cache()
    finally:
        loss_module.support_excess = operator
    output = PIPE / ("bps_compare_" + args.token + ".json")
    result = {"tick_token": args.token, "observed_at": datetime.now(timezone.utc).isoformat(),
              "source_manifest": manifest, "script_sha256": sha(Path(__file__)),
              "rows": rows, "native_forward_count": len(rows), "optimizer_steps": 0,
              "scope": "Actual native V2/optimized preparation and mask-gradient comparison; no complete new-model gate or efficacy."}
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"result": str(output), "sha256": sha(output),
                      "all_pass": all(r["pass1e6"] for r in rows)}), flush=True)


if __name__ == "__main__":
    main()
