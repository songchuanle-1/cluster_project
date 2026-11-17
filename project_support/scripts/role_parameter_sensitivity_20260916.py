"""Same-forward native full-parameter role-tag diagnostic, not a variant."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import types

source = Path(__file__).with_name("role_gradient_capture_20260916.py")
tree = ast.parse(source.read_text())
prefix = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Attribute)
            and t.attr == "loss_sem_align" for t in node.targets):
        break
    prefix.append(node)
env = {"__file__": str(source)}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(source), "exec"), env)
torch, model, cfg = env["torch"], env["model"], env["namespace"]["cfg"]
gorilla = env["gorilla"]
original, criterion = env["original"], env["criterion"]
initial = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
state = {}
out = env["namespace"]["ROOT"].parent / "pipeline/role_parameter_sensitivity_20260916"
out.mkdir(parents=True, exist_ok=True)


def paired(self, text, image, language_masks, targets, indices, num_boxes):
    value = original(text, image, language_masks, targets, indices, num_boxes)
    if state.get("collect_gradient") and "alternative" not in state:
        changed = copy.deepcopy(targets)
        flags = []
        for b, info in enumerate(state["roles"]):
            repeat = info["mask"][:text.shape[1]].clone().to(text.device)
            protected = sum(targets[b][name].bool().any(0).int() for name in (
                "positive_map", "modify_positive_map", "pron_positive_map", "rel_positive_map"))
            repeat &= protected[:len(repeat)] == 0
            repeat &= targets[b]["other_entity_map"][:, :len(repeat)].bool().any(0)
            changed[b]["other_entity_map"][:, :len(repeat)][:, repeat] = 0
            flags.append(bool(repeat.any()))
        state["alternative"] = original(text, image, language_masks, changed, indices, num_boxes)
        state["original"] = value
        state["flags"] = flags
    return value


def readout(module, args):
    pred, masks = args[:2]
    fps = args[7].long()
    sampled = pred["sample_inds"].long()
    values = []
    for b, target in enumerate(masks):
        target = target.flatten().bool()
        logits = pred["masks"][b, :, :len(target)]
        hard = logits > 0
        iou = (hard & target).sum(-1) / (hard | target).sum(-1).clamp_min(1)
        chosen = int(pred["indis"][b].softmax(-1)[:, 1].argmax())
        probability = logits[chosen].sigmoid()
        soft = (probability * target).sum() / (
            probability + target - probability * target).sum().clamp_min(1e-8)
        values.append(dict(selected=float(iou[chosen]), best=float(iou.max()),
                           selected_soft=float(soft),
                           zero_logits=int((logits == 0).sum()),
                           physical_seeds=fps[b][sampled[b]].cpu().tolist()))
    state["readout"] = values


criterion.loss_sem_align = types.MethodType(paired, criterion)
criterion.register_forward_pre_hook(readout)
reports = []
for step, batch in enumerate(env["batches"]):
    model.load_state_dict(initial, strict=True)
    model.train().zero_grad(set_to_none=True)
    state.clear()
    state.update(collect_gradient=True, roles=env["masks_for_batch"](batch))
    gorilla.set_random_seed(1999)
    full, _ = model(copy.deepcopy(batch), mode="loss")
    alternative = full + criterion.loss_weight[6] * (state["alternative"] - state["original"])
    shared = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    gradients = {}
    losses = {}
    for branch, loss in (("native", full), ("neutral", alternative)):
        model.zero_grad(set_to_none=True)
        loss.backward(retain_graph=branch == "native")
        gradients[branch] = {k: p.grad.detach().cpu().clone()
                             for k, p in model.named_parameters() if p.grad is not None}
        assert all(torch.isfinite(g).all() for g in gradients[branch].values())
        assert any(k.startswith("unet.") and bool(g.abs().sum() > 0)
                   for k, g in gradients[branch].items())
        losses[branch] = float(loss.detach())
    del full, alternative, loss
    gradient_delta_sq = sum(float((gradients["neutral"][k]-g).double().square().sum())
                            for k, g in gradients["native"].items())
    state.pop("alternative")
    state.pop("original")
    state["collect_gradient"] = False
    branches = {}
    for branch in ("native", "neutral", "native_repeat"):
        model.load_state_dict(shared, strict=True)
        model.zero_grad(set_to_none=True)
        key = "native" if branch == "native_repeat" else branch
        optimizer = gorilla.build_optimizer(model, cfg.optimizer)
        assert not optimizer.state
        for name, p in model.named_parameters():
            p.grad = gradients[key][name].to(p.device) if name in gradients[key] else None
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
        assert torch.isfinite(norm)
        optimizer.step()
        if branch == "native":
            updated = {k: p.detach().cpu().clone() for k, p in model.named_parameters()}
        if branch == "native_repeat":
            assert all(torch.equal(p.detach().cpu(), updated[k]) for k, p in model.named_parameters())
        parameter_delta = (max(float((p.detach().cpu()-updated[k]).abs().max())
                           for k, p in model.named_parameters()) if branch == "neutral" else 0.0)
        model.zero_grad(set_to_none=True)
        del optimizer
        model.eval()
        gorilla.set_random_seed(1999)
        with torch.no_grad():
            check, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(check).all()
        branches[branch] = dict(rows=copy.deepcopy(state["readout"]), grad_norm=float(norm),
                               parameter_max_delta=parameter_delta)
    identities = [dict(scene=r["scene"], ann_id=r["ann_id"], repeated=flag)
                  for r, flag in zip(state["roles"], state["flags"])]
    reports.append(dict(batch=step, identities=identities, losses=losses, branches=branches,
                        gradient_delta_l2=gradient_delta_sq ** .5))
    (out / "partial.json").write_text(json.dumps(reports, indent=2))
    print(json.dumps(dict(batch=step, expressions=len(identities), finite=True)), flush=True)
    del gradients, shared, updated
result = dict(batches=reports, sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (Path(__file__), source, env["base"], env["namespace"]["checkpoint"])},
    scope="Final-semantic other-tag removal only;not positive relabeling. Same-forward TRAIN "
          "full gradients,identical buffers,fresh native AdamW/clip;eval free-sampling readout. "
          "Selected expression outcomes valid without query alignment;not efficacy/admission.")
(out / "result.json").write_text(json.dumps(result, indent=2))
