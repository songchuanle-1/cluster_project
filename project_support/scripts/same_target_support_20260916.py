"""Same-target native capture with frozen FPS and two symmetric support controls."""
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
native_expand = env["native_expand"]
old = json.loads((env["root"] / "same_target_native_20260916/result.json").read_text())
assert old["manifest"] == env["manifest"]


def expand(*args, **kwargs):
    out = native_expand(*args, **kwargs)
    if state["branch"] == "base":
        state["fps"] = out[2][:1].expand_as(out[2]).clone()
    return (*out[:2], state["fps"], *out[3:])


def sampling(module, args, output):
    indices, scores = output
    if state["branch"] == "base":
        state["samples"] = indices.detach().clone()
    selected = state["samples"].clone()
    if state["branch"].startswith("shared"):
        offset = 0 if state["branch"] == "shared_first" else 1
        for i in range(0, len(selected), 2):
            assert env["groups"][state["step"]][i]["object_id"] == (
                env["groups"][state["step"]][i + 1]["object_id"])
            selected[i:i + 2] = state["samples"][i + offset]
    return selected, scores


def collect(module, args):
    env["results"].clear()
    env["collect"](module, args)
    state["rows"] = copy.deepcopy(env["results"])
    pred = args[0]
    state["physical"] = args[7].long().gather(1, pred["sample_inds"].long()).cpu().tolist()
    state["logits"] = (pred["indis"][..., 1] - pred["indis"][..., 0]).cpu().tolist()


model.expand_and_fps = expand
model.dec.sampling_module.register_forward_hook(sampling)
model.criterion.register_forward_pre_hook(collect)
ns["gorilla"].set_random_seed(1999)
with torch.no_grad():
    for step, batch in enumerate(env["loader"]):
        state["step"] = step
        ns["current"].update(step=step, batch=batch)
        branches = {}
        initial_rng = torch.get_rng_state()
        cuda_rng = torch.cuda.get_rng_state_all()
        for branch in ("base", "repeat", "shared_first", "shared_second"):
            state["branch"] = branch
            torch.set_rng_state(initial_rng)
            torch.cuda.set_rng_state_all(cuda_rng)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            if branch == "base":
                final_rng = torch.get_rng_state()
                final_cuda_rng = torch.cuda.get_rng_state_all()
            branches[branch] = dict(rows=copy.deepcopy(state["rows"]),
                physical=copy.deepcopy(state["physical"]), logits=copy.deepcopy(state["logits"]))
        torch.set_rng_state(final_rng)
        torch.cuda.set_rng_state_all(final_cuda_rng)
        assert branches["base"]["physical"] == branches["repeat"]["physical"]
        for branch in ("shared_first", "shared_second"):
            support = branches[branch]["physical"]
            assert all(support[i] == support[i + 1] for i in range(0, len(support), 2))
        reports.append(dict(batch=step, branches=branches))
        print(json.dumps(dict(batch=step, completed=True)), flush=True)
destination = env["root"] / "same_target_support_20260916"
destination.mkdir(exist_ok=True)
result = dict(batches=reports, manifest=env["manifest"],
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (parent, Path(__file__), env["base"], ns["checkpoint"])},
    limitations="Same128expression manifest;matched within-run augmented inputs,FPS "
    "and symmetric physical support controls. RNG restored to base after controls. "
    "Compare old capture by identity only;no bitwise cross-run guarantee or efficacy claim.")
(destination / "result.json").write_text(json.dumps(result, indent=2))
