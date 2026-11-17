"""Strict vertical relation response; fixed target/support, no optimization."""
import hashlib
import json
import copy
from pathlib import Path

parent = Path(__file__).with_name("anchor_attention_probe_20260916.py")
scope = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nreference_path=")[0], str(parent), "exec"), scope)
torch, model, ns = scope["torch"], scope["model"], scope["ns"]
current, binding = scope["current"], scope["binding"]
tokenizer = ns["dataset"].tokenizer
root = ns["ROOT"].parent / "pipeline"
inventory_path = root / "relation_training_coverage_20260916/result.json"
inventory = {(r["scene"], int(r["ann_id"])): r
             for r in json.loads(inventory_path.read_text())["rows"]}
prior_path = root / "anchor_noun_intervention_20260916/result.json"
vocabulary = json.loads(prior_path.read_text())["vocabulary"]
primitive_path = Path(__file__).with_name("directional_distribution_probe_20260916.py")
primitive = {"__file__": str(primitive_path), "__name__": "primitive"}
exec(compile(primitive_path.read_text(), str(primitive_path), "exec"), primitive)
ordered_mass = primitive["ordered_mass"]
native = {}
fixed = {}
original_expand = model.expand_and_fps


def expand(*args, **kwargs):
    output = original_expand(*args, **kwargs)
    if fixed["branch"] == "original":
        fixed["coords"] = output[1].clone()
        fixed["fps"] = output[2].clone()
    return (output[0], fixed["coords"], fixed["fps"], *output[3:])


model.expand_and_fps = expand


def capture(module, args):
    native.update(pred=args[0], gt=args[1], labels=args[4],
                  coords=args[8].detach(), offsets=args[9].detach())


model.criterion.register_forward_pre_hook(capture)
rows, missing = [], []
for step, batch in enumerate(ns["batches"]):
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    selected = [(b, binding[(s, int(batch["ann_ids"][b]))],
                 inventory.get((s, int(batch["ann_ids"][b]))))
                for b, s in enumerate(scenes)]
    selected = [(b, r, inv) for b, r, inv in selected if inv]
    if not selected:
        continue
    # Separate runs isolate each edge even if several edges share an expression.
    for b, record, inv in selected:
        text = record["caption"] + " . not mentioned"
        encoded = tokenizer(text, return_tensors="pt")
        length = int(batch["lang_masks"][b].sum())
        assert encoded["input_ids"][0].tolist() == batch["lang_tokenss"][b, :length].tolist()
        for edge in inv["edges"]:
            entity = next(e for e in record["entities"] if e["node_id"] == edge["anchor_node"])
            spans = entity["spans"]["target_char_span"]
            reason = None
            replacement = None
            if len(spans) == 1 and spans[0]["valid"]:
                start, end = map(int, spans[0]["span"])
                tokens = sorted({encoded.char_to_token(c) for c in range(start, end)} - {None})
                for noun in vocabulary:
                    if noun in text.split() or noun == spans[0]["text"]:
                        continue
                    ids = tokenizer(text[:start]+noun+text[end:], return_tensors="pt")["input_ids"][0]
                    old = encoded["input_ids"][0]
                    if ids.shape != old.shape:
                        continue
                    changed = (ids != old).nonzero().flatten().tolist()
                    if changed and set(changed).issubset(tokens):
                        replacement = (noun, ids)
                        break
            if replacement is None:
                missing.append(dict(scene=record["scene"], ann_id=record["ann_id"],
                                    edge=edge, reason="no single-span matched-length replacement"))
                continue
            altered = dict(batch)
            altered["lang_tokenss"] = batch["lang_tokenss"].clone()
            altered["lang_tokenss"][b, :length] = replacement[1]
            results = []
            reference = None
            for branch, data in (("original", batch), ("replacement", altered), ("repeat", batch)):
                fixed["branch"] = branch
                assert torch.equal(data["coords_float"], batch["coords_float"])
                assert torch.equal(data["superpoints"], batch["superpoints"])
                current.update(attention={})
                ns["gorilla"].set_random_seed(1999)
                with torch.no_grad():
                    loss, _ = model(copy.deepcopy(data), mode="loss")
                assert torch.isfinite(loss).all()
                s, e = map(int, native["offsets"][b:b+2])
                xyz = native["coords"][s:e]
                gt = native["gt"][b].flatten().float().to(xyz.device)
                assert len(gt) == len(xyz)
                if reference is None:
                    reference = (xyz.clone(), gt.clone())
                else:
                    delta = float((xyz-reference[0]).abs().max())
                    print(json.dumps(dict(branch=branch, coordinate_delta=delta,
                                          labels_equal=torch.equal(gt, reference[1]))), flush=True)
                    assert torch.equal(gt, reference[1])
                    assert torch.equal(xyz, reference[0])
                # direction=+1 means target ABOVE anchor; ordered_mass wants target<anchor.
                z = reference[0][:, 2] * -edge["direction"]
                a = current["attention"][5][b, tokens, :len(gt)].mean(0)
                assert torch.allclose(a.sum(), a.new_tensor(1.), atol=1e-5)
                result = dict(branch=branch, relation=float(ordered_mass(z, gt, a)),
                              anchor_target_mass=float(a[gt.bool()].sum()))
                if branch == "original":
                    baseline_attention = a.clone()
                    uniform = torch.ones_like(a)
                    extremum = torch.zeros_like(a)
                    extremum[z.argmax()] = 1
                    controls = dict(uniform=float(ordered_mass(z, gt, uniform)),
                                    extreme=float(ordered_mass(z, gt, extremum)))
                result["attention_tv"] = float((a-baseline_attention).abs().sum()/2)
                results.append(result)
            assert abs(results[0]["relation"]-results[2]["relation"]) < 1e-5
            rows.append(dict(scene=record["scene"], ann_id=record["ann_id"],
                             edge=edge, old=spans[0]["text"], new=replacement[0],
                             success=record["success"], confident_wrong=record["confident_wrong"],
                             branches=results, controls=controls))
    print(json.dumps(dict(batch=step, rows=len(rows), missing=len(missing))), flush=True)
assert rows
summary = dict(n=len(rows), missing=len(missing),
               mean_abs_relation_change=sum(abs(r["branches"][1]["relation"]-r["branches"][0]["relation"])
                                            for r in rows)/len(rows),
               max_repeat=max(abs(r["branches"][2]["relation"]-r["branches"][0]["relation"])
                              for r in rows))
out = root / "anchor_relation_response_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(dict(
    summary=summary, rows=rows, missing=missing,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, primitive_path, inventory_path, prior_path)},
    limitations="Fixed123TRAIN manifest strict vertical edges. Ground-truth target mask "
    "is a diagnostic control, not inference input. No ground-truth anchor identity. "
    "Attention mass on target reported to expose self-reference shortcut. "
    "Counterfactual sentences may have no referent; change is not correctness. "
    "Augmented native SP coordinates; not gravity/viewpoint truth. No optimizer, "
    "novelty or training admission claim."
), indent=2))
print(json.dumps(summary), flush=True)
