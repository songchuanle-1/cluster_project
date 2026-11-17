"""Leave-scene-out token identity retrieval without fitting a probe."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("model.criterion.register_forward_pre_hook(capture)")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
torch, model, batches = ns["torch"], ns["model"], ns["batches"]
state, features, identities = {}, {}, []


def capture(layer, tensor):
    batch = state["batch"]
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    collected = []
    for i, scene in enumerate(scenes):
        n = int(batch["lang_masks"][i].sum())
        # Exclude BOS and exact native appended suffix, with a checked boundary.
        token_ids = batch["lang_tokenss"][i, :n].tolist()
        decoded = ns["dataset"].tokenizer.convert_ids_to_tokens(token_ids)
        assert decoded[-3:] == ["\u0120not", "\u0120mentioned", "</s>"], decoded[-5:]
        for j in range(1, n-4):
            if not decoded[j].lstrip("\u0120").isalpha():
                continue
            collected.append(tensor[i, j].detach().float().cpu())
            if layer == "input":
                identities.append(dict(scene=scene, ann_id=int(batch["ann_ids"][i]),
                    position=j, token_id=int(token_ids[j]), token=decoded[j]))
    features.setdefault(layer, []).extend(collected)


model.dec.lang_norm.register_forward_hook(lambda m, a, o: capture("input", o))
for i, layer in enumerate(model.dec.encoder_layers):
    layer.register_forward_hook(lambda m, a, o, i=i: capture(f"encoder{i}", o[0]))
with torch.no_grad():
    for step, batch in enumerate(batches):
        state["batch"] = batch
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(batch, mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, tokens=len(identities))), flush=True)

scenes = sorted({r["scene"] for r in identities})
scene_ids = torch.tensor([scenes.index(r["scene"]) for r in identities])
token_ids = torch.tensor([r["token_id"] for r in identities])
eligible = torch.tensor([any(r["token_id"] == s["token_id"] and r["scene"] != s["scene"]
                            for s in identities) for r in identities])
results = []
for layer, items in features.items():
    assert len(items) == len(identities)
    vectors = torch.nn.functional.normalize(torch.stack(items), dim=-1)
    guesses = []
    for start in range(0, len(vectors), 128):
        sim = vectors[start:start+128] @ vectors.T
        sim.masked_fill_(scene_ids[start:start+128, None] == scene_ids[None], -torch.inf)
        guesses.extend(sim.argmax(-1).tolist())
    correct = token_ids[guesses] == token_ids
    per_scene = []
    for i, scene in enumerate(scenes):
        keep = eligible & (scene_ids == i)
        per_scene.append(dict(scene=scene, eligible=int(keep.sum()),
                              correct=int(correct[keep].sum())))
    results.append(dict(layer=layer, eligible=int(eligible.sum()),
        correct=int(correct[eligible].sum()), per_scene=per_scene,
        retrieval=[dict(**r, eligible=bool(eligible[i]), correct=bool(correct[i]),
                        neighbor=identities[guesses[i]]) for i, r in enumerate(identities)]))
destination = ns["ROOT"].parent / "pipeline/lexical_retrieval_20260916"
destination.mkdir(exist_ok=True)
report = dict(results=results, tokens=len(identities),
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (base, Path(__file__), ns["config"], ns["checkpoint"])},
    limitations="Alphabetic BPE token ID retrieval,not word sense/phrase binding. "
    "All nearest neighbors exclude same scene;eligible requires another-scene same ID. "
    "No trained probe,no new annotations,no model change. Retrieval decline does not "
    "alone establish task-relevant information loss or novel corrective architecture.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps([{k: r[k] for k in ("layer", "eligible", "correct")} for r in results]))
