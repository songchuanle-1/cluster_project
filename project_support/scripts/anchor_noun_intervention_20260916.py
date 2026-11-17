"""Matched-length noun intervention on fixed native TRAIN scene tensors."""
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("anchor_attention_probe_20260916.py")
scope = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nreference_path=")[0], str(parent), "exec"), scope)
torch, model, ns = scope["torch"], scope["model"], scope["ns"]
current, binding = scope["current"], scope["binding"]
tokenizer = ns["dataset"].tokenizer
vocabulary = sorted({
    s["text"] for r in binding.values() for e in r["entities"]
    for s in e["spans"]["target_char_span"]
    if s["valid"] and s["text"].isalpha()
})
rows = []
for step, batch in enumerate(ns["batches"]):
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    changed = dict(batch)
    changed["lang_tokenss"] = batch["lang_tokenss"].clone()
    interventions = []
    for b, scene in enumerate(scenes):
        record = binding[(scene, int(batch["ann_ids"][b]))]
        text = record["caption"] + " . not mentioned"
        original = tokenizer(text, return_tensors="pt")
        length = int(batch["lang_masks"][b].sum())
        assert original["input_ids"][0].tolist() == batch["lang_tokenss"][b, :length].tolist()
        main_words = {s["text"] for e in record["entities"] if e["node_id"] == 0
                      for s in e["spans"]["target_char_span"]}
        candidate = None
        for entity in record["entities"]:
            spans = entity["spans"]["target_char_span"]
            if entity["node_id"] == 0 or len(spans) != 1:
                continue
            span = spans[0]
            if not span["valid"] or span["text"] in main_words:
                continue
            start, end = map(int, span["span"])
            tokens = sorted({original.char_to_token(c) for c in range(start, end)}
                            - {None})
            if not tokens:
                continue
            for noun in vocabulary:
                if noun in text.split() or noun == span["text"]:
                    continue
                altered = tokenizer(text[:start] + noun + text[end:], return_tensors="pt")
                ids = altered["input_ids"][0]
                old = original["input_ids"][0]
                if ids.shape != old.shape:
                    continue
                different = (ids != old).nonzero().flatten().tolist()
                if not different or not set(different).issubset(tokens):
                    continue
                candidate = dict(b=b, scene=scene, ann_id=record["ann_id"],
                                 old=span["text"], new=noun, tokens=tokens,
                                 target=record["target"], node_id=entity["node_id"])
                changed["lang_tokenss"][b, :length] = ids
                break
            if candidate:
                interventions.append(candidate)
                break
    outputs = []
    for branch, data in (("original", batch), ("replacement", changed), ("repeat", batch)):
        current.update(attention={})
        ns["gorilla"].set_random_seed(1999)
        with torch.no_grad():
            loss, _ = model(data, mode="loss")
        assert torch.isfinite(loss).all()
        outputs.append({i: a.clone() for i, a in current["attention"].items()})
    for item in interventions:
        b, tokens = item["b"], item["tokens"]
        measurements = []
        for layer in range(6):
            a = outputs[0][layer][b, tokens].mean(0)
            c = outputs[1][layer][b, tokens].mean(0)
            repeat = outputs[2][layer][b, tokens].mean(0)
            noise = float((repeat-a).abs().sum()/2)
            assert noise < 1e-5
            measurements.append(dict(layer=layer, tv=float((c-a).abs().sum()/2),
                                     repeat_tv=noise,
                                     same_peak=int(a.argmax()) == int(c.argmax())))
        rows.append(dict(**item, layers=measurements))
    print(json.dumps(dict(batch=step, interventions=len(rows))), flush=True)
summary = {i: dict(n=len(rows), mean_tv=sum(r["layers"][i]["tv"] for r in rows)/max(1,len(rows)),
                   max_repeat=max((r["layers"][i]["repeat_tv"] for r in rows), default=0))
           for i in range(6)}
out = ns["ROOT"].parent/"pipeline/anchor_noun_intervention_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(dict(
    rows=rows, summary=summary, vocabulary=vocabulary,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent)},
    limitations="Fixed geometry and target labels; only matched-length non-target noun "
    "tokens replaced. Existing TRAIN noun vocabulary, deterministic lexical order. "
    "Counterfactual sentences need not have a real referent. Parser supervision "
    "retained only to execute native path; loss is not an efficacy metric. "
    "No optimization. Semantic sensitivity is not correct anchor identity or novelty."
), indent=2))
print(json.dumps(summary), flush=True)
