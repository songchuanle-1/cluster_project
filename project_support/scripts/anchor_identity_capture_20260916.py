"""Bounded four-branch QLA token deletion using existing annotation maps."""
from pathlib import Path
import copy
import hashlib
import json
import runpy

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, batches = ns["torch"], ns["model"], ns["batches"]
gorilla = ns["gorilla"]
out = ns["ROOT"].parent / "pipeline/anchor_identity_20260916"
out.mkdir(parents=True, exist_ok=True)
state = {}
collected, eligibility = {}, []


def prepare(batch, step):
    valid = batch["lang_masks"].bool()
    anchor, control = torch.zeros_like(valid), torch.zeros_like(valid)
    for b, maps in enumerate(batch["dense_maps"]):
        def support(name):
            value = torch.as_tensor(maps[name]).bool()
            if value.ndim > 1:
                value = value.any(0)
            result = torch.zeros(valid.shape[1], dtype=torch.bool)
            count = min(len(result), len(value))
            result[:count] = value[:count].cpu()
            return result
        protect = support("positive_map") | support("modify_positive_map")
        protect |= support("pron_positive_map") | support("rel_positive_map")
        other = support("other_entity_map")
        candidate = other & ~protect & valid[b]
        candidates_control = torch.where(valid[b] & ~protect & ~other)[0]
        n = int(candidate.sum())
        eligible = n > 0 and len(candidates_control) >= n and n < int(valid[b].sum())
        if eligible:
            anchor[b] = candidate
            control[b, candidates_control[:n]] = True
        eligibility.append(dict(batch=step, expression=b, ann_id=int(batch["ann_ids"][b]),
                                anchor_tokens=n, control_available=len(candidates_control),
                                overlap=int((other & protect & valid[b]).sum()),
                                eligible=eligible,
                                anchor_positions=torch.where(candidate)[0].tolist(),
                                anchor_tokens_decoded=ns["dataset"].tokenizer.convert_ids_to_tokens(
                                    batch["lang_tokenss"][b][candidate].tolist())))
    return anchor.cuda(), control.cuda()


def qla_hook(module, args):
    if state["branch"] in ("base", "repeat"):
        return
    source, query, mask = args[:3]
    replacement = mask | state[state["branch"]]
    assert (~replacement).any(1).all()
    return (source, query, replacement, *args[3:])


def collector(module, args):
    ns["capture"](module, args)
    pred = args[0]
    labels = args[4]
    for b, row in enumerate(ns["rows"]):
        selected = row["layers"][-1]["selected_query"]
        instance = labels[b].long()
        mask = pred["masks"][b, selected, :len(instance)] >= 0
        ids = instance.unique()
        # Dataset uses 199 for unassigned SPs; negative IDs are also invalid.
        ids = ids[(ids >= 0) & (ids != 199)]
        overlaps = []
        for identity in ids.tolist():
            truth = instance == identity
            intersection = int((mask & truth).sum())
            union = int((mask | truth).sum())
            overlaps.append(dict(instance_id=identity, iou=intersection / max(union, 1)))
        overlaps.sort(key=lambda r: (-r["iou"], r["instance_id"]))
        row["selected_instance_overlaps"] = overlaps[:3]
        row["selected_zero_logits"] = int((pred["masks"][b, selected, :len(instance)] == 0).sum())
    state["sampling"] = dict(fps=args[7].detach().cpu().tolist(),
                             sampled=pred["sample_inds"].detach().cpu().tolist())


model.criterion.register_forward_pre_hook(collector)
for layer in model.dec.decoder_layers:
    layer.qla.register_forward_pre_hook(qla_hook)
with torch.no_grad():
    for step, batch in enumerate(batches):
        anchor, control = prepare(batch, step)
        state.update(anchor=anchor, control=control)
        ns["current"].update(step=step, batch=batch)
        collected[step] = {}
        for branch in ("base", "repeat", "anchor", "control"):
            state["branch"] = branch
            ns["rows"].clear()
            gorilla.set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            collected[step][branch] = dict(rows=copy.deepcopy(ns["rows"]),
                                          sampling=state["sampling"])
        for branch in ("repeat", "anchor", "control"):
            a = collected[step][branch]["sampling"]
            b = collected[step]["base"]["sampling"]
            collected[step][branch]["same_physical_sampling"] = [
                [fa[j] for j in sa] == [fb[j] for j in sb]
                for fa, sa, fb, sb in zip(a["fps"], a["sampled"], b["fps"], b["sampled"])
            ]
        (out / "partial.json").write_text(json.dumps(dict(
            batches=collected, eligibility=eligibility), indent=2))
        print(json.dumps(dict(batch=step, branches=4)), flush=True)
report = dict(batches=collected, eligibility=eligibility,
              sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), base, ns["checkpoint"], ns["config"])},
              scope="QLA-local deletion, physical sampling equality explicitly recorded, M95 eval on "
                    "fixed TRAIN16batches. Not production change or efficacy/novelty admission.")
(out / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps(dict(expressions=len(eligibility),
                      eligible=sum(r["eligible"] for r in eligibility))), flush=True)
