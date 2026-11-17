"""Matched fresh-optimizer parameter steps on fixed TRAIN batches, not admission."""
import ast
import copy
import hashlib
import json
from pathlib import Path

import torch


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


source = Path("/tmp/component_full_loss_20260915.py")
tree = ast.parse(source.read_text())
prefix = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "out" for t in node.targets
    ):
        break
    prefix.append(node)
env = {"__name__": "paired_setup"}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(source), "exec"), env)
model, cfg = env["model"], env["cfg"]
capture, loss_module = env["capture"], env["loss_module"]
gorilla = env["gorilla"]
paired = env["paired"]
extra = {}


def observe(pred, targets, indices, contacts, lengths, denominator):
    extra["targets"] = targets
    extra["contacts"] = contacts
    extra["lengths"] = lengths
    return paired(pred, targets, indices, contacts, lengths, denominator)


loss_module.boundary_loss = observe
initial = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
out = Path("/tmp/component_parameter_step_20260915-1810")
out.mkdir(exist_ok=False)
results = []
for step, batch in enumerate(env["batches"]):
    branches = {}
    model.load_state_dict(initial, strict=True)
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    full, _ = model(copy.deepcopy(batch), mode="loss")
    alternative = full + capture["component_loss"] - capture["global_loss"]
    before = [p.detach().cpu().clone() for p in capture["pred"]]
    records = copy.deepcopy(capture["records"])
    targets = [None if t["masks"] is None else t["masks"].detach().cpu()
               for t in extra["targets"]]
    contacts = [torch.as_tensor(e).cpu() for e in extra["contacts"]]
    lengths = [int(n) for n in extra["lengths"]]
    shared_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    gradient_files = {}
    loss_values = {}
    for mode, loss in (("global", full), ("component", alternative)):
        model.zero_grad(set_to_none=True)
        loss.backward(retain_graph=mode == "global")
        gradients = {k: p.grad.detach().cpu().clone() for k, p in model.named_parameters()
                     if p.grad is not None}
        assert gradients and all(torch.isfinite(g).all() for g in gradients.values())
        artifact = out / f"batch_{step}_{mode}_gradients.pth"
        torch.save(gradients, artifact)
        gradient_files[mode] = dict(path=str(artifact), sha256=digest(artifact))
        loss_values[mode] = float(loss.detach())
        del gradients
    del full, alternative, loss
    capture.clear()
    model.zero_grad(set_to_none=True)
    for mode in ("global", "component", "global_repeat"):
        base_mode = "global" if mode == "global_repeat" else mode
        model.load_state_dict(shared_state, strict=True)
        optimizer = gorilla.build_optimizer(model, cfg.optimizer)
        assert not optimizer.state
        gradients = torch.load(gradient_files[base_mode]["path"], weights_only=True)
        for k, p in model.named_parameters():
            p.grad = gradients[k].to(p.device) if k in gradients else None
        del gradients
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
        assert torch.isfinite(norm)
        optimizer.step()
        changed = sum(not torch.equal(p.detach().cpu(), initial[k])
                      for k, p in model.named_parameters())
        assert changed > 0
        if mode == "global":
            global_updated = {k: p.detach().cpu().clone()
                              for k, p in model.named_parameters()}
        if mode == "global_repeat":
            assert all(torch.equal(p.detach().cpu(), global_updated[k])
                       for k, p in model.named_parameters())
        model.zero_grad(set_to_none=True)
        capture.clear()
        del optimizer
        gorilla.set_random_seed(1999)
        with torch.no_grad():
            model(copy.deepcopy(batch), mode="loss")
        after = [p.detach().cpu().clone() for p in capture["pred"]]
        rows = []
        scene_by_expression = [s for s, n in enumerate(lengths) for _ in range(n)]
        for r in records:
            b, q, t = r["expression"], r["query"], r["target"]
            y = targets[b][t].bool()
            edges = contacts[scene_by_expression[b]].long()
            edges = edges[y[edges[:, 0]] != y[edges[:, 1]]]
            pos = torch.where(y[edges[:, 0]], edges[:, 0], edges[:, 1])
            neg = torch.where(y[edges[:, 0]], edges[:, 1], edges[:, 0])
            values = []
            for logits in (before[b][q], after[b][q]):
                p = logits.sigmoid()
                hard = p > .5
                values.append({
                    "hard_iou": float((hard & y).sum() / (hard | y).sum().clamp_min(1)),
                    "soft_iou": float((p * y).sum() / (p + y - p * y).sum().clamp_min(1e-8)),
                    "inversions": int((logits[pos] <= logits[neg]).sum()),
                    "crossing_edges": len(edges),
                })
            rows.append(dict(expression=b, query=q, target=t,
                             components=len(r["groups"]), before=values[0], after=values[1]))
        artifact = out / f"batch_{step}_{mode}.pth"
        torch.save(dict(before=before, after=after, targets=targets, records=records,
                        rows=rows, scenes=batch["scan_ids"], ann_ids=batch["ann_ids"],
                        object_ids=batch["object_idss"]), artifact)
        branches[mode] = dict(loss=loss_values[base_mode], gradient_norm=float(norm),
                              changed_parameters=changed, finite_backward=True,
                              artifact=str(artifact), sha256=digest(artifact), rows=rows)
        capture.clear()
    comparisons = {}
    for subset in ("all", "connected", "disconnected"):
        pairs = [(g, c) for g, c in zip(branches["global"]["rows"], branches["component"]["rows"])
                 if subset == "all" or (g["components"] == 1 if subset == "connected"
                                        else g["components"] > 1)]
        comparisons[subset] = dict(
            queries=len(pairs),
            component_minus_global={
                key: sum(c["after"][key] - g["after"][key] for g, c in pairs) / max(1, len(pairs))
                for key in ("hard_iou", "soft_iou", "inversions")
            })
    noise = {}
    for key in ("hard_iou", "soft_iou", "inversions"):
        differences = [r["after"][key] - g["after"][key] for g, r in
                       zip(branches["global"]["rows"], branches["global_repeat"]["rows"])]
        noise[key] = dict(mean=sum(differences) / max(1, len(differences)),
                          max_absolute=max(map(abs, differences), default=0))
    global_after = torch.load(branches["global"]["artifact"], weights_only=False)["after"]
    noise["logits_max_absolute"] = max(float((g - r).abs().max())
                                     for g, r in zip(global_after, after))
    results.append(dict(batch=step, branches=branches, comparisons=comparisons,
                        duplicate_update_noise=noise, gradient_files=gradient_files))
    print(json.dumps(dict(batch=step, comparisons=comparisons)), flush=True)
report = dict(
    results=results,
    controls="Both parameter gradients from ONE shared forward graph/matches; identical post-forward model/buffers, empty AdamW, native groups/clipping. Global repeated update parameters bitwise equal; post-forward noise measured. Finite backward both branches.",
    scope="FP32 two fixed TRAIN batches, one fresh AdamW step per branch; fixed pre-step matching. Same-batch superpoint IoU diagnostics, not point-weighted validation mIoU or efficacy. No restored training optimizer, AMP, generalization or novelty claim.",
    sources={str(p): digest(p) for p in (
        Path(__file__), source, env["cfg_path"], env["checkpoint"], Path(env["helper"].__file__))})
(out / "result.json").write_text(json.dumps(report, indent=2))
