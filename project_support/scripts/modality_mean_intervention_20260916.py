"""GT-defined modality path intervention, strictly diagnostic."""
import copy
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("modality_cancellation_20260916.py")
ns = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nmodel.dec.input_proj.register_forward_hook")[0],
             str(parent), "exec"), ns)
torch, model, base = ns["torch"], ns["model"], ns["ns"]
state, records = {}, []
native_expand = model.expand_and_fps


def expand(*args, **kwargs):
    out = native_expand(*args, **kwargs)
    if state["branch"] == "base":
        state["fps"] = out[2].clone()
    return (*out[:2], state["fps"], *out[3:])


def sampling(module, args, output):
    if state["branch"] == "base":
        state["sample"] = output[0].clone()
    return state["sample"], output[1]


def intervention(name):
    def hook(module, args, output):
        if state["branch"] not in (name, "both"):
            return output
        modified = output.clone()
        for lo, hi, target, neighbor in state["pairs"]:
            original = output[lo:hi]
            delta = original[neighbor].mean(0) - original[target].mean(0)
            modified[lo:hi][target] = original[target] + delta
            modified[lo:hi][neighbor] = original[neighbor] - delta
        return modified
    return hook


def collect(module, args):
    base["rows"].clear()
    base["capture"](module, args)
    if state["branch"] == "base":
        state["pairs"] = []
    state["rows"] = []
    for b, row in enumerate(base["rows"]):
        old = ns["lookup"][(row["scene"], row["ann_id"])]
        if state["branch"] == "base":
            lo, hi = int(args[9][b]), int(args[9][b + 1])
            labels = args[4][b]
            target = labels == old["target"]
            neighbor = labels == old["nearest_clip"][0][0]
            assert target.any() and neighbor.any()
            assert not (target & neighbor).any()
            state["pairs"].append((lo, hi, target, neighbor))
        state["rows"].append(dict(scene=row["scene"], ann_id=row["ann_id"],
            iou=row["layers"][-1]["selected"], query=row["layers"][-1]["selected_query"],
            oracle=row["layers"][-1]["best"]))
    state["physical"] = args[7].long().gather(1, args[0]["sample_inds"].long()).cpu().tolist()


model.expand_and_fps = expand
model.dec.sampling_module.register_forward_hook(sampling)
model.dec.input_proj.register_forward_hook(intervention("three_d"))
model.dec.input_proj_2d.register_forward_hook(intervention("two_d"))
model.criterion.register_forward_pre_hook(collect)
with torch.no_grad():
    for step, batch in enumerate(base["batches"]):
        base["current"].update(step=step, batch=batch)
        branches = {}
        for branch in ("base", "repeat", "three_d", "two_d", "both"):
            state["branch"] = branch
            base["gorilla"].set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            branches[branch] = dict(rows=copy.deepcopy(state["rows"]),
                                    physical=state["physical"])
        assert all(v["physical"] == branches["base"]["physical"] for v in branches.values())
        records.append(dict(batch=step, branches=branches))
        print(json.dumps(dict(batch=step, complete=True)), flush=True)
out = ns["pipeline"] / "modality_mean_intervention_20260916"
out.mkdir(exist_ok=True)
(out / "result.json").write_text(json.dumps(dict(batches=records,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, base["checkpoint"], ns["inventory_path"])},
    limitations="GT instance-centroid exchange preserves within-instance residuals, "
    "coordinates, language, weights and fixed physical sampling. Not deployable or "
    "label-preserving; measures path sensitivity,not efficacy or universal causality. "
    "Nearest raw2D neighbor selected independently of outcomes."), indent=2))
