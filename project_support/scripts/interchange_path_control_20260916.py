"""Disentangle final scene-state attention and mask-feature causal paths."""
import copy
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("scene_interchange_20260916.py")
scope = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nmodel.expand_and_fps = expand\n")[0],
             str(parent), "exec"), scope)
torch, model, env, ns = (scope[k] for k in ("torch", "model", "env", "ns"))
state = scope["state"]
lookup = {(m["scene"], int(r["ann_id"])): r for m in env["manifest"] for r in m["selected"]}
records = []
layer = model.dec.decoder_layers[-1]
original_prediction = layer.prediction_head


def donor_indices(n, device):
    index = torch.arange(n, device=device)
    return index ^ 1 if "same" in state["branch"] else (index + 2) % n


def read_input(module, args):
    if not state["branch"].startswith("read_"):
        return args
    features = args[0]
    return (features[donor_indices(len(features), features.device)], *args[1:])


def prediction(query, features, padding):
    if state["branch"].startswith("mask_"):
        features = features[donor_indices(len(features), features.device)]
    return original_prediction(query, features, padding)


def collect(module, args):
    scope["collect"](module, args)
    for row in state["rows"]:
        annotation = lookup[(row["scene"], row["ann_id"])]
        assert row["target_ids"] == [int(annotation["object_id"])]
        row["utterance"] = annotation["description"]


model.expand_and_fps = scope["expand"]
model.dec.sampling_module.register_forward_hook(scope["sampling"])
layer.qia.register_forward_pre_hook(read_input)
layer.prediction_head = prediction
model.criterion.register_forward_pre_hook(collect)
ns["gorilla"].set_random_seed(1999)
with torch.no_grad():
    for step, batch in enumerate(env["loader"]):
        state["step"] = step
        ns["current"].update(step=step, batch=batch)
        rng, cuda_rng = torch.get_rng_state(), torch.cuda.get_rng_state_all()
        branches = {}
        for branch in ("base", "repeat", "read_same", "read_different", "mask_same", "mask_different"):
            state["branch"] = branch
            torch.set_rng_state(rng)
            torch.cuda.set_rng_state_all(cuda_rng)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            if branch == "base":
                end_rng, end_cuda = torch.get_rng_state(), torch.cuda.get_rng_state_all()
            branches[branch] = dict(rows=copy.deepcopy(state["rows"]),
                support=copy.deepcopy(state["support"]), logits=copy.deepcopy(state["logits"]))
        torch.set_rng_state(end_rng)
        torch.cuda.set_rng_state_all(end_cuda)
        assert all(v["support"] == branches["base"]["support"] for v in branches.values())
        # Mask feature substitutions cannot affect the separate query-score branch.
        for branch in ("mask_same", "mask_different"):
            error = max(abs(x-y) for a, b in zip(branches["base"]["logits"],
                        branches[branch]["logits"]) for x, y in zip(a, b))
            assert error < 1e-3, error
        records.append(dict(batch=step, branches=branches))
        print(json.dumps(dict(batch=step, complete=True)), flush=True)
destination = env["root"] / "interchange_path_control_20260916"
destination.mkdir(exist_ok=True)
(destination / "result.json").write_text(json.dumps(dict(batches=records,
    manifest=env["manifest"],
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, env["base"], ns["checkpoint"])},
    limitations="Read-only causal path control. No encoder-output swap:QIA source "
    "versus prediction-head mask features isolated. Own language/query retained; "
    "mask-only score invariance checked. No learned mechanism or admission."), indent=2))
