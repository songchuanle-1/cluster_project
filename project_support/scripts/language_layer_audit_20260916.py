"""Native layerwise token discrimination diagnostic, no model changes."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, batches = ns["torch"], ns["model"], ns["batches"]
state, rows = {}, []


def capture(label, tensor):
    batch = state["batch"]
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    for i, scene in enumerate(scenes):
        # Dataset's final two valid tokens are its no-object target;
        # exclude them and the BOS token consistently, report actual tokens.
        n = int(batch["lang_masks"][i].sum())
        x = tensor[i, 1:n-2].float()
        x = torch.nn.functional.normalize(x, dim=-1)
        gram = x @ x.T
        centered = x - x.mean(0)
        values = torch.linalg.eigvalsh(centered @ centered.T).clamp_min(0)
        total = values.sum()
        probabilities = values / total.clamp_min(1e-20)
        entropy = -(probabilities * probabilities.clamp_min(1e-20).log()).sum()
        mean_cosine = (gram.sum() - gram.diagonal().sum()) / max(len(x)*(len(x)-1), 1)
        rows.append(dict(scene=scene, ann_id=int(batch["ann_ids"][i]),
            batch=state["step"], layer=label, tokens=len(x),
            mean_pair_cosine=float(mean_cosine), centered_energy=float(total/len(x)),
            centered_effective_rank=float(entropy.exp()) if total > 0 else 0,
            leading_fraction=float(values[-1]/total) if total > 0 else 0))


model.dec.lang_norm.register_forward_hook(lambda m, a, o: capture("input", o))
for i, layer in enumerate(model.dec.encoder_layers):
    layer.register_forward_hook(lambda m, a, o, i=i: capture(f"encoder{i}", o[0]))
with torch.no_grad():
    for step, batch in enumerate(batches):
        state.update(step=step, batch=batch)
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(batch, mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, rows=len(rows))), flush=True)
destination = ns["ROOT"].parent / "pipeline/language_layer_20260916"
destination.mkdir(exist_ok=True)
report = dict(rows=rows,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (base, Path(__file__), ns["config"], ns["checkpoint"])},
    limitations="L2-normalized contextual token geometry,not loss projections. Excludes BOS "
    "and finaltwo null-target tokens;punctuation and remaining suffix retained. No token "
    "label truth,causality,rank threshold,novelty or training admission.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
