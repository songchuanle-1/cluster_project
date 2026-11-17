"""Native same-weight cluster message intervention, not a training variant."""
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, batches = ns["torch"], ns["model"], ns["batches"]
state, reports = {}, []
native_expand = model.expand_and_fps


def expand(*args, **kwargs):
    result = native_expand(*args, **kwargs)
    if state["branch"] == "base":
        state["fps"] = result[2].detach().clone()
    return (*result[:2], state["fps"], *result[3:])


def sample(module, args, output):
    indices, scores = output
    if state["branch"] == "base":
        state["sample"] = indices.detach().clone()
    return state["sample"], scores


def message(module, args, output):
    result = dict(output)
    value = output["point"]
    if state["branch"] == "zero":
        result["point"] = torch.zeros_like(value)
    elif state["branch"] == "shift":
        changed = value.clone()
        valid = ~args[2]
        for b in range(len(value)):
            n = int(valid[b].sum())
            changed[b, :n] = value[b, :n].roll(1, dims=0)
        result["point"] = changed
    return result


def collect(module, args):
    ns["rows"].clear()
    ns["capture"](module, args)
    state["rows"] = copy.deepcopy(ns["rows"])
    state["support"] = (args[7].cpu().tolist(), args[0]["sample_inds"].cpu().tolist())


model.expand_and_fps = expand
model.dec.sampling_module.register_forward_hook(sample)
model.dec.cluster_att.register_forward_hook(message)
model.criterion.register_forward_pre_hook(collect)
with torch.no_grad():
    for step, batch in enumerate(batches):
        ns["current"].update(step=step, batch=batch)
        branches, supports = {}, {}
        for branch in ("base", "repeat", "zero", "shift"):
            state["branch"] = branch
            ns["gorilla"].set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            branches[branch] = copy.deepcopy(state["rows"])
            supports[branch] = copy.deepcopy(state["support"])
        assert all(s == supports["base"] for s in supports.values())
        reports.append(dict(batch=step, branches=branches, support_equal=True))
        print(json.dumps(dict(batch=step, support_equal=True)), flush=True)
destination = ns["ROOT"].parent / "pipeline/cluster_message_causal_20260916"
destination.mkdir(exist_ok=True)
report = dict(batches=reports,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
             (base, Path(__file__), ns["config"], ns["checkpoint"])},
    limitations="Same-weight forward message effect only. Does not undo training "
    "effects or isolate full cluster contribution relative to baseline. Zero/shuffle "
    "diagnostics are not novel variants. Frozen FPS/sampling all branches.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
