"""Fixed-state AMP repeatability audit; no training or efficacy claim."""
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
env = {"__name__": "repeatability_setup"}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(source), "exec"), env)
model = env["model"]
initial = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
capture = {}


def observe(pred, targets, indices, contacts, lengths, denominator):
    capture["logits"] = [p.detach().cpu().clone() for p in pred]
    capture["matches"] = [(q.cpu().clone(), t.cpu().clone()) for q, t in indices]
    return env["original"](pred, targets, indices, contacts, lengths, denominator)


def decoder_hook(module, args, result):
    capture["fps"] = args[1].detach().cpu().clone()
    capture["samples"] = result["sample_inds"].detach().cpu().long().clone()


env["loss_module"].boundary_loss = observe
hook = model.dec.register_forward_hook(decoder_hook)
out = Path("/tmp/component_amp_repeatability_20260915-2010")
out.mkdir(exist_ok=False)
results = []
for batch_id, batch in enumerate(env["batches"]):
    for training, cache in ((True, True), (True, False), (False, False)):
        runs = []
        for repeat in range(2):
            model.load_state_dict(initial, strict=True)
            model.train(training)
            model.zero_grad(set_to_none=True)
            env["gorilla"].set_random_seed(1999)
            capture.clear()
            with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16,
                                                cache_enabled=cache):
                loss, _ = model(copy.deepcopy(batch), mode="loss")
            torch.cuda.synchronize()
            capture["loss"] = float(loss)
            capture["scenes"] = batch["scan_ids"]
            capture["ann_ids"] = batch["ann_ids"]
            capture["object_ids"] = batch["object_idss"]
            capture["buffers"] = {k: b.detach().cpu().clone()
                                  for k, b in model.named_buffers()}
            capture["seeds"] = capture["fps"].gather(1, capture["samples"])
            runs.append(copy.deepcopy(capture))
        a, b = runs
        aligned = []
        for i, (za, zb) in enumerate(zip(a["logits"], b["logits"])):
            # Duplicate FPS seeds are averaged, preserving physical seed identity.
            sa, sb = a["seeds"][i], b["seeds"][i]
            common = sorted(set(sa.tolist()) & set(sb.tolist()))
            differences = [(za[sa == seed].float().mean(0) -
                            zb[sb == seed].float().mean(0)).abs().max().item()
                           for seed in common]
            aligned.append(dict(expression=i, common_seeds=len(common),
                                unique_a=len(sa.unique()), unique_b=len(sb.unique()),
                                max_absolute=max(differences, default=0)))
        artifact = out / f"batch{batch_id}_train{training}_cache{cache}.pth"
        torch.save(runs, artifact)
        row = dict(
            batch=batch_id, training=training, autocast_cache=cache,
            raw_max_absolute=max((x.float() - y.float()).abs().max().item()
                                 for x, y in zip(a["logits"], b["logits"])),
            fps_equal=torch.equal(a["fps"], b["fps"]),
            samples_equal=torch.equal(a["samples"], b["samples"]),
            seeds_equal=torch.equal(a["seeds"], b["seeds"]),
            matches_equal=all(torch.equal(q, r) and torch.equal(t, u)
                              for (q, t), (r, u) in zip(a["matches"], b["matches"])),
            changed_buffers=[k for k in a["buffers"]
                             if not torch.equal(a["buffers"][k], b["buffers"][k])],
            aligned=aligned, losses=[a["loss"], b["loss"]],
            artifact=str(artifact),
            sha256=hashlib.sha256(artifact.read_bytes()).hexdigest())
        results.append(row)
        print(json.dumps(row), flush=True)
        del runs, a, b
hook.remove()
report = dict(
    results=results,
    scope="Two fixed native TRAIN batches, initial checkpoint restored before each "
          "forward, seed1999, no optimizer. AMP only. Train/eval and cache controls "
          "diagnose repeatability, not improvement or admission. Seed alignment "
          "mean-aggregates duplicates and reports intersection coverage.",
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), source, env["cfg_path"], env["checkpoint"])})
(out / "result.json").write_text(json.dumps(report, indent=2))
