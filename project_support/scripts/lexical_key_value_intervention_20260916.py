"""Final QLA key/value provenance controls on fixed native TRAIN batches."""
import copy
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, batches = ns["torch"], ns["model"], ns["batches"]
state, results = {}, []

native_expand = model.expand_and_fps


def freeze_fps(*args, **kwargs):
    output = native_expand(*args, **kwargs)
    if state["branch"] == "base":
        state["fps"] = output[2].detach().clone()
    return (*output[:2], state["fps"], *output[3:])


def freeze_samples(module, args, output):
    indices, scores = output
    if state["branch"] == "base":
        state["samples"] = indices.detach().clone()
    else:
        indices = state["samples"]
    return indices, scores


def remember(module, args, output):
    state["lexical"] = output


def intervene(module, args):
    query, key, value = args[:3]
    lexical = state["lexical"]
    assert key.shape == lexical.shape == value.shape
    branch = state["branch"]
    if branch == "key":
        key = lexical
    elif branch == "value":
        value = lexical
    elif branch == "both":
        key = value = lexical
    elif branch == "shiftkey":
        key = lexical.clone()
        for b, mask in enumerate(state["batch"]["lang_masks"]):
            n = int(mask.sum())
            key[b, :n] = lexical[b, :n].roll(1, dims=0)
    return (query, key, value, *args[3:])


def collect(module, args):
    ns["rows"].clear()
    ns["capture"](module, args)
    state["rows"] = copy.deepcopy(ns["rows"])
    state["support"] = (args[7].detach().cpu().tolist(),
                        args[0]["sample_inds"].detach().cpu().tolist())


model.dec.lang_norm.register_forward_hook(remember)
model.expand_and_fps = freeze_fps
model.dec.sampling_module.register_forward_hook(freeze_samples)
model.dec.decoder_layers[-1].qla.attn.register_forward_pre_hook(intervene)
model.criterion.register_forward_pre_hook(collect)
with torch.no_grad():
    for step, batch in enumerate(batches):
        state["batch"] = batch
        ns["current"].update(step=step, batch=batch)
        branches, support = {}, {}
        for branch in ("base", "repeat", "key", "value", "both", "shiftkey"):
            state["branch"] = branch
            ns["gorilla"].set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            branches[branch] = copy.deepcopy(state["rows"])
            support[branch] = copy.deepcopy(state["support"])
        assert all(s == support["base"] for s in support.values())
        results.append(dict(batch=step, branches=branches, physical_support_equal=True))
        print(json.dumps(dict(batch=step, support_equal=True)), flush=True)
destination = ns["ROOT"].parent / "pipeline/lexical_key_value_20260916"
destination.mkdir(exist_ok=True)
report = dict(batches=results,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (base, Path(__file__), ns["config"], ns["checkpoint"])},
    limitations="Only final QLA attention inputs altered;no model training. Same "
    "M95 projections not calibrated for raw lexical keys/values;failure does not "
    "universally falsify training. No novel-memory or efficacy/admission claim.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
