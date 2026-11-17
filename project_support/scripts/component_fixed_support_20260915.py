"""Diagnostic-only sampling replay and ordered activation comparison."""
import ast
import copy
import hashlib
import json
from pathlib import Path

import torch

source = Path("/tmp/component_full_loss_20260915.py")
prefix = []
for node in ast.parse(source.read_text()).body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "out" for t in node.targets
    ):
        break
    prefix.append(node)
env = {"__name__": "fixed_support_setup"}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(source), "exec"), env)
model = env["model"]
initial = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
out = Path("/tmp/component_fixed_support_20260915-2110")
out.mkdir(exist_ok=False)
capture, reference, comparisons = {}, {}, []
fixed = None
repeat = 0


def tensors(value, path=""):
    if isinstance(value, torch.Tensor):
        yield path, value
    elif hasattr(value, "features") and hasattr(value, "indices"):
        yield path + ".features", value.features
        yield path + ".indices", value.indices
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from tensors(item, path + "." + str(key))
    elif isinstance(value, (tuple, list)):
        for i, item in enumerate(value):
            yield from tensors(item, path + "." + str(i))


def observe(name, value):
    for key, tensor in tensors(value, name):
        current = tensor.detach().cpu().clone()
        if repeat == 0:
            reference[key] = current
        else:
            previous = reference[key]
            same_shape = current.shape == previous.shape
            equal = same_shape and torch.equal(current, previous)
            comparisons.append(dict(
                activation=key, equal=equal, shape=list(current.shape),
                max_absolute=float((current.float() - previous.float()).abs().max())
                if same_shape and current.numel() else None))


def hook(name):
    def run(module, args, result):
        observe(name + ".input", args)
        observe(name + ".output", result)
    return run


def sampling(module, args, result):
    global fixed
    observe("sampling.native", result)
    if fixed is None:
        fixed = result[0].detach().clone()
    return fixed.clone(), result[1]


def decoder(module, args, result):
    capture["fps"] = args[1].detach().cpu().clone()
    capture["samples"] = result["sample_inds"].detach().cpu().long().clone()


def boundary(pred, targets, indices, contacts, lengths, denominator):
    capture["logits"] = [p.detach().cpu().clone() for p in pred]
    capture["matches"] = [(q.cpu().clone(), t.cpu().clone()) for q, t in indices]
    return env["original"](pred, targets, indices, contacts, lengths, denominator)


names = ["input_conv.0", "unet", "output_layer", "dec.sampling_module.camap",
         "dec.decoder_layers.0"]
modules = dict(model.named_modules())
handles = [modules[name].register_forward_hook(hook(name)) for name in names]
handles += [model.dec.sampling_module.register_forward_hook(sampling),
            model.dec.register_forward_hook(decoder)]
env["loss_module"].boundary_loss = boundary
results = []
for batch_id, batch in enumerate(env["batches"]):
    fixed = None
    reference.clear()
    runs, rows = [], []
    for repeat in range(3):
        model.load_state_dict(initial, strict=True)
        model.train()
        env["gorilla"].set_random_seed(1999)
        capture.clear()
        comparisons.clear()
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16,
                                            cache_enabled=False):
            loss, _ = model(copy.deepcopy(batch), mode="loss")
        torch.cuda.synchronize()
        capture["seeds"] = capture["fps"].gather(1, capture["samples"])
        capture["loss"] = float(loss)
        runs.append(copy.deepcopy(capture))
        rows.append(copy.deepcopy(comparisons))
    pairs = []
    for left, right in ((0, 1), (1, 2)):
        a, b = runs[left], runs[right]
        aligned = []
        for i, (za, zb) in enumerate(zip(a["logits"], b["logits"])):
            sa, sb = a["seeds"][i], b["seeds"][i]
            common = sorted(set(sa.tolist()) & set(sb.tolist()))
            aligned.append(dict(
                expression=i, common=len(common),
                missing_a=len(set(sa.tolist()) - set(common)),
                missing_b=len(set(sb.tolist()) - set(common)),
                duplicate_a=len(sa) - len(sa.unique()),
                duplicate_b=len(sb) - len(sb.unique()),
                max_absolute=max((float((za[sa == s].float().mean(0) -
                                         zb[sb == s].float().mean(0)).abs().max())
                                  for s in common), default=0)))
        pairs.append(dict(left=left, right=right, aligned=aligned,
                          fps_equal=torch.equal(a["fps"], b["fps"]),
                          samples_equal=torch.equal(a["samples"], b["samples"]),
                          seeds_equal=torch.equal(a["seeds"], b["seeds"])))
    artifact = out / f"batch{batch_id}.pth"
    torch.save(dict(runs=runs, scenes=batch["scan_ids"], ann_ids=batch["ann_ids"],
                    object_ids=batch["object_idss"]), artifact)
    row = dict(batch=batch_id, pairs=pairs, activations_vs_first=rows,
               first_differences=[next((r for r in rows[i] if not r["equal"]), None)
                                  for i in (1, 2)],
               artifact=str(artifact),
               sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
    results.append(row)
    print(json.dumps(dict(batch=batch_id, pairs=pairs,
                         first_differences=row["first_differences"])), flush=True)
for handle in handles:
    handle.remove()
report = dict(results=results, scope="Two native TRAIN batches, three initial-state "
              "AMP forwards each; diagnostic-only sample replay; all global loss; "
              "repeat1 vs repeat2 is duplicate-global control. No optimizer or efficacy. "
              "First difference means earliest instrumented activation, not kernel proof.",
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), source, env["checkpoint"])})
(out / "result.json").write_text(json.dumps(report, indent=2))
