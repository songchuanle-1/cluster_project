"""Physical-SP-aligned context interchange on fixed same-target TRAIN pairs."""
import copy
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("same_target_native_20260916.py")
source = parent.read_text().split("model.expand_and_fps = expand")[0]
env = {"__file__": str(parent)}
exec(compile(source, str(parent), "exec"), env)
torch, model, ns = env["torch"], env["model"], env["ns"]
state = env["state"]
reports = []


def expand(*args, **kwargs):
    out = env["native_expand"](*args, **kwargs)
    if state["branch"] == "base":
        state["fps"] = out[2][:1].expand_as(out[2]).clone()
    return (*out[:2], state["fps"], *out[3:])


def sampling(module, args, output):
    indices, scores = output
    if state["branch"] == "base":
        state["samples"] = indices.detach().clone()
    return state["samples"], scores


def exchange(module, args, output):
    language, visual = output
    n = len(visual)
    assert n == 4
    if state["branch"] in ("base", "repeat"):
        return output
    donor = torch.arange(n, device=visual.device)
    if state["branch"] in ("same", "shuffle"):
        donor = donor ^ 1
    else:
        donor = (donor + 2) % n
    changed = visual[donor]
    if state["branch"] == "shuffle":
        changed = changed.roll(1, dims=1)
    return language, changed


def collect(module, args):
    env["results"].clear()
    env["collect"](module, args)
    state["rows"] = copy.deepcopy(env["results"])
    state["support"] = args[7].long().gather(1, args[0]["sample_inds"].long()).cpu().tolist()
    state["logits"] = (args[0]["indis"][..., 1] - args[0]["indis"][..., 0]).cpu().tolist()


model.expand_and_fps = expand
model.dec.sampling_module.register_forward_hook(sampling)
model.dec.encoder_layers[-1].register_forward_hook(exchange)
model.criterion.register_forward_pre_hook(collect)
ns["gorilla"].set_random_seed(1999)
with torch.no_grad():
    for step, batch in enumerate(env["loader"]):
        state["step"] = step
        ns["current"].update(step=step, batch=batch)
        rng, cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
        branches = {}
        for branch in ("base", "repeat", "same", "different", "shuffle"):
            state["branch"] = branch
            torch.set_rng_state(rng)
            torch.cuda.set_rng_state_all(cuda_rng)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            if branch == "base":
                end_rng, end_cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
            branches[branch] = dict(rows=copy.deepcopy(state["rows"]),
                support=copy.deepcopy(state["support"]), logits=copy.deepcopy(state["logits"]))
        torch.set_rng_state(end_rng)
        torch.cuda.set_rng_state_all(end_cuda_rng)
        assert all(b["support"] == branches["base"]["support"] for b in branches.values())
        reports.append(dict(batch=step, branches=branches))
        print(json.dumps(dict(batch=step, complete=True)), flush=True)
destination = env["root"] / "scene_interchange_20260916"
destination.mkdir(exist_ok=True)
(destination / "result.json").write_text(json.dumps(dict(batches=reports,
    manifest=env["manifest"],
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (parent, env["base"], Path(__file__), ns["checkpoint"])},
    limitations="Final encoder visual state only. Own language/query/FPS/samples retained. "
    "Same scene all4rows have equal SP lengths,no padding rolled into real support. "
    "Pretrained intervention is not training efficacy or novelty proof."), indent=2))
