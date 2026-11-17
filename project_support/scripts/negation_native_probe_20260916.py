"""One prespecified TRAIN cue intervention, not a candidate training run."""
import copy
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("coverage_stage_capture_20260916.py")
ns = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nmodel.criterion.register_forward_pre_hook")[0],
             str(parent), "exec"), ns)
torch, model = ns["torch"], ns["model"]
root = ns["ROOT"].parent/"pipeline"
bindings = json.loads((root/"entity_binding_20260916/result.json").read_text())["rows"]
record = next(r for r in bindings if r["scene"] == "scene0320_00" and r["ann_id"] == 19)
found = []
for step, batch in enumerate(ns["batches"]):
    scenes = [s for s,n in zip(batch["scan_ids"], batch["scenes_len"]) for _ in range(int(n))]
    for b,s in enumerate(scenes):
        if (s, int(batch["ann_ids"][b])) == ("scene0320_00", 19):
            found.append((step,b,batch))
assert len(found) == 1
step, b, batch = found[0]
text = record["caption"] + " . not mentioned"
assert text.count("no chair") == 1
tokenizer = ns["dataset"].tokenizer
original = tokenizer(text, return_tensors="pt")["input_ids"][0]
replacement = tokenizer(text.replace("no chair", "a chair"), return_tensors="pt")["input_ids"][0]
length = int(batch["lang_masks"][b].sum())
assert original.tolist() == batch["lang_tokenss"][b,:length].tolist()
assert original.shape == replacement.shape
changed = (original != replacement).nonzero().flatten().tolist()
assert len(changed) == 1
state = {}
expand_native = model.expand_and_fps


def expand(*args, **kwargs):
    out = expand_native(*args, **kwargs)
    if state["branch"] == "original":
        state["coords"], state["fps"] = out[1].clone(), out[2].clone()
    return out[0], state["coords"], state["fps"], *out[3:]


def sample(module, args, output):
    if state["branch"] == "original":
        state["sample"] = output[0].clone()
    return state["sample"], output[1]


def collect(module, args):
    ns["rows"].clear()
    ns["capture"](module, args)
    state["metrics"] = copy.deepcopy(ns["rows"][b])
    state["scores"] = args[0]["indis"][b].detach().cpu()
    state["masks"] = args[0]["masks"][b].detach().cpu()


model.expand_and_fps = expand
model.dec.sampling_module.register_forward_hook(sample)
model.criterion.register_forward_pre_hook(collect)
outputs = {}
for branch in ("original", "affirmative", "repeat"):
    state["branch"] = branch
    data = copy.deepcopy(batch)
    if branch == "affirmative":
        data["lang_tokenss"][b,:length] = replacement
    ns["current"].update(step=step,batch=data)
    ns["gorilla"].set_random_seed(1999)
    with torch.no_grad():
        loss,_ = model(data, mode="loss")
    assert torch.isfinite(loss).all()
    outputs[branch] = dict(metrics=state["metrics"], scores=state["scores"], masks=state["masks"])
    print(json.dumps(dict(branch=branch, final=state["metrics"]["layers"][-1])),flush=True)
base = outputs["original"]
report = {}
for branch, out in outputs.items():
    report[branch] = dict(
        metrics=out["metrics"],
        score_max_delta=float((out["scores"]-base["scores"]).abs().max()),
        mask_logit_max_delta=float((out["masks"]-base["masks"]).abs().max()),
        mask_hard_changes=int(((out["masks"]>=0) != (base["masks"]>=0)).sum()),
    )
assert report["repeat"]["score_max_delta"] < 1e-3
assert report["repeat"]["mask_logit_max_delta"] < 1e-3
outdir = root/"negation_native_probe_20260916"
outdir.mkdir(exist_ok=True)
(outdir/"result.json").write_text(json.dumps(dict(
    scene=record["scene"], ann_id=record["ann_id"], original_text=text,
    replacement_text=text.replace("no chair","a chair"), changed_token_positions=changed,
    branches=report,
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),parent)},
    limitations="Single prespecified TRAIN failure. Only cue token changed, fixed "
    "geometry/FPS/query sample support. Affirmative sentence changes semantics; original "
    "target label is not affirmative truth. Output sensitivity not accuracy improvement "
    "or proof of correct negation. No optimizer,new labels,candidate,or admission."
),indent=2))
