"""Matched input baseline/M95 TRAIN diagnosis, expression-level comparisons."""
import copy
import gc
import hashlib
import importlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, batches = ns["torch"], ns["batches"]
root = ns["ROOT"].parent / "pipeline"
results, state = {}, {}


def geometry(module, args, output):
    tensor = output[0]
    values = []
    for i, mask in enumerate(state["batch"]["lang_masks"]):
        n = int(mask.sum())
        x = torch.nn.functional.normalize(tensor[i, 1:n-2].float(), dim=-1)
        x = x - x.mean(0)
        eigen = torch.linalg.eigvalsh(x @ x.T).clamp_min(0)
        p = eigen / eigen.sum().clamp_min(1e-20)
        values.append(float((-(p * p.clamp_min(1e-20).log()).sum()).exp()))
    state["rank"] = values


def collect(module, args):
    ns["rows"].clear()
    ns["capture"](module, args)
    for row, rank in zip(ns["rows"], state["rank"]):
        row["language_rank"] = rank
    state["rows"] = copy.deepcopy(ns["rows"])


for label in ("champion", "baseline"):
    if label == "champion":
        model = ns["model"]
    else:
        config = root / "baseline_reference_20260916.yaml"
        checkpoint = root / "baseline_reference_20260916.pth"
        assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == (
            "dbc37e8fe8428f0f295121df61fae8a9ffd7dd98c10913ef911354345ff16745")
        cfg = ns["gorilla"].Config.fromfile(str(config))
        cfg.model.data_root = "/data3/songcl/data/data_cluster/"
        ns["gorilla"].LOSSES._obj_map.pop("Criterion", None)
        model = importlib.import_module("framework.model.Quard_model.model_base1").Network(**cfg.model)
        saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
        weights = saved["model"]
        for key in ("text_encoder.embeddings.position_ids", "text_encoder.embeddings.token_type_ids"):
            weights.pop(key, None)
        model.load_state_dict(weights, strict=True)
        del saved, weights
        model.cuda().eval()
    model.dec.encoder_layers[-1].register_forward_hook(geometry)
    model.criterion.register_forward_pre_hook(collect)
    rows = []
    with torch.no_grad():
        for step, batch in enumerate(batches):
            state["batch"] = batch
            ns["current"].update(step=step, batch=batch)
            ns["gorilla"].set_random_seed(1999)
            loss, _ = model(copy.deepcopy(batch), mode="loss")
            assert torch.isfinite(loss).all()
            rows.extend(state["rows"])
            print(json.dumps(dict(model=label, batch=step, rows=len(rows))), flush=True)
    results[label] = rows
    if label == "champion":
        del ns["model"]
    del model
    gc.collect()
    torch.cuda.empty_cache()
assert [(r["scene"], r["ann_id"]) for r in results["champion"]] == [
    (r["scene"], r["ann_id"]) for r in results["baseline"]]
destination = root / "baseline_matched_20260916"
destination.mkdir(exist_ok=True)
report = dict(results=results,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
             (base, Path(__file__), ns["config"], ns["checkpoint"], config, checkpoint)},
    limitations="Same cached augmented TRAIN batches,independently native sampling."
    "Compare expression outcomes,never query indices. Architecture and checkpoint "
    "both differ;not isolated cluster causal effect. SP IoU not validation point mIoU.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
