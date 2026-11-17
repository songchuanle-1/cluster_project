"""Native noun-to-instance support diagnostic; exact names are not referents."""
import copy
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("anchor_attention_probe_20260916.py")
scope = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nreference_path=")[0], str(parent), "exec"), scope)
torch, model, ns = scope["torch"], scope["model"], scope["ns"]
current, binding = scope["current"], scope["binding"]
rows, names = [], {}


def collect(module, args):
    labels = args[4]
    batch = current["batch"]
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    for b, scene in enumerate(scenes):
        record = binding[(scene, int(batch["ann_ids"][b]))]
        if scene not in names:
            path = Path("/data3/songcl/data/data_cluster/scannetv2/train") / (
                scene + ".aggregation.json")
            names[scene] = {int(g["id"]): g["label"].lower()
                           for g in json.loads(path.read_text())["segGroups"]}
        text = record["caption"] + " . not mentioned"
        encoded = ns["dataset"].tokenizer(text, return_tensors="pt")
        length = int(batch["lang_masks"][b].sum())
        assert encoded["input_ids"][0].tolist() == batch["lang_tokenss"][b, :length].tolist()
        instance = labels[b].long()
        for entity in record["entities"]:
            if entity["node_id"] == 0:
                continue
            spans = entity["spans"]["target_char_span"]
            noun = " ".join(s["text"].lower() for s in spans)
            tokens = sorted({encoded.char_to_token(c) for span in spans
                             for c in range(*map(int, span["span"]))} - {None})
            if not tokens:
                continue
            # Keep target candidates: repeated mentions can refer to the target.
            candidate_ids = [i for i in instance.unique().tolist()
                             if i >= 0 and i != 199 and names[scene].get(i) == noun]
            candidate_mask = torch.zeros_like(instance, dtype=torch.bool)
            for i in candidate_ids:
                candidate_mask |= instance == i
            layer_rows = []
            for layer, attention in current["attention"].items():
                mass = attention[b, tokens, :len(instance)].mean(0)
                assert torch.allclose(mass.sum(), mass.new_tensor(1.), atol=1e-5)
                per_instance = {str(i): float(mass[instance == i].sum())
                                for i in candidate_ids}
                layer_rows.append(dict(layer=layer, exact_name_mass=float(mass[candidate_mask].sum()),
                    uniform_mass=float(candidate_mask.float().mean()),
                    target_mass=float(mass[instance == record["target"]].sum()),
                    per_instance=per_instance))
            rows.append(dict(scene=scene, ann_id=record["ann_id"], node_id=entity["node_id"],
                noun=noun, candidates=candidate_ids, target_in_candidates=record["target"] in candidate_ids,
                success=record["success"], confident_wrong=record["confident_wrong"],
                layers=layer_rows))


model.criterion.register_forward_pre_hook(collect)
with torch.no_grad():
    for step, batch in enumerate(ns["batches"]):
        current.update(batch=batch, attention={})
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(copy.deepcopy(batch), mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step, mentions=len(rows))), flush=True)
summary = {}
for kind in ("success", "confident_wrong"):
    selected = [r for r in rows if r[kind] and r["candidates"] and
                not r["target_in_candidates"]]
    final = [r["layers"][-1] for r in selected]
    summary[kind] = dict(mentions=len(selected),
        expressions=len({(r["scene"], r["ann_id"]) for r in selected}),
        mean_exact_mass=sum(r["exact_name_mass"] for r in final)/max(1, len(final)),
        mean_uniform_mass=sum(r["uniform_mass"] for r in final)/max(1, len(final)),
        above_uniform=sum(r["exact_name_mass"] > r["uniform_mass"] for r in final))
result = dict(summary=summary, rows=rows,
    scope="Fixed123TRAIN eval forward,222nonmain mentions expected. Exact raw names "
          "are category-compatible candidates,not intended anchor labels. Uniform "
          "reference is superpoint occupancy,not random-model performance. Descriptive "
          "groups are repeated expressions/instances;not independent or causal. No optimizer.",
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, ns["checkpoint"])})
out = ns["ROOT"].parent / "pipeline/mention_instance_support_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(summary, indent=2), flush=True)
