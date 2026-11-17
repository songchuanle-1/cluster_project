"""Native fixed-input LIA attention audit; attention is not grounding truth."""
import hashlib
import json
from pathlib import Path

parent = Path(__file__).with_name("coverage_stage_capture_20260916.py")
ns = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nmodel.criterion.register_forward_pre_hook")[0],
             str(parent), "exec"), ns)
torch, model = ns["torch"], ns["model"]
root = ns["ROOT"].parent / "pipeline"
binding_path = root / "entity_binding_20260916/result.json"
binding = {(r["scene"], int(r["ann_id"])): r
           for r in json.loads(binding_path.read_text())["rows"]}
current, rows = {}, []


def hook(layer):
    def capture(module, args, output):
        weights = output[1].detach()
        assert weights.ndim == 3
        current["attention"][layer] = weights
    return capture


for layer, encoder in enumerate(model.dec.encoder_layers):
    encoder.lia.register_forward_hook(hook(layer))


def collect(module, args):
    batch = current["batch"]
    pred, _, _, _, labels = args[:5]
    scenes = [s for s,n in zip(batch["scan_ids"],batch["scenes_len"]) for _ in range(int(n))]
    for b, scene in enumerate(scenes):
        record = binding[(scene,int(batch["ann_ids"][b]))]
        native_text = record["caption"] + " . not mentioned"
        encoded = ns["dataset"].tokenizer(native_text, return_tensors="pt")
        length = int(batch["lang_masks"][b].sum())
        assert encoded["input_ids"].shape[1] == length
        assert encoded["input_ids"][0,:length].tolist() == batch["lang_tokenss"][b,:length].tolist()
        entities = []
        for entity in record["entities"]:
            tokens = set()
            for span in entity["spans"]["target_char_span"]:
                for char in range(*map(int,span["span"])):
                    token = encoded.char_to_token(char)
                    if token is not None and token < length:
                        tokens.add(token)
            if tokens:
                entities.append((entity,sorted(tokens)))
        main = next((tokens for entity,tokens in entities if entity["node_id"]==0), None)
        if main is None:
            continue
        n = len(labels[b])
        for layer, attention in current["attention"].items():
            t = attention[b,main,:n].mean(0)
            assert torch.allclose(t.sum(), t.new_tensor(1.), atol=1e-5)
            for entity,tokens in entities:
                if entity["node_id"] == 0:
                    continue
                a = attention[b,tokens,:n].mean(0)
                assert torch.allclose(a.sum(), a.new_tensor(1.), atol=1e-5)
                targetmask = labels[b] == record["target"]
                rows.append(dict(
                    scene=scene, ann_id=record["ann_id"], layer=layer,
                    node_id=entity["node_id"],
                    noun=" ".join(s["text"] for s in entity["spans"]["target_char_span"]),
                    success=record["success"], confident_wrong=record["confident_wrong"],
                    total_variation=float((a-t).abs().sum()/2),
                    same_peak=int(a.argmax())==int(t.argmax()),
                    anchor_target_mass=float(a[targetmask].sum()),
                    main_target_mass=float(t[targetmask].sum())))
    ns["rows"].clear()
    ns["capture"](module,args)
    for result in ns["rows"]:
        key=(result["scene"],result["ann_id"])
        old=current["reference"][key]
        assert abs(result["layers"][-1]["selected"]-old["layers"][-1]["selected"]) < 1e-6


reference_path=root/"coverage_stage_20260916/result.json"
current["reference"]={(r["scene"],r["ann_id"]):r
                      for r in json.loads(reference_path.read_text())["rows"]}
model.criterion.register_forward_pre_hook(collect)
with torch.no_grad():
    for step,batch in enumerate(ns["batches"]):
        current.update(batch=batch,attention={})
        ns["current"].update(step=step,batch=batch)
        ns["gorilla"].set_random_seed(1999)
        loss,_=model(batch,mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(dict(batch=step,records=len(rows))),flush=True)
summary={}
for layer in range(6):
    items=[r for r in rows if r["layer"]==layer]
    summary[layer]=dict(mentions=len(items),same_peak=sum(r["same_peak"] for r in items),
                       mean_tv=sum(r["total_variation"] for r in items)/max(len(items),1))
out=root/"anchor_attention_20260916"
out.mkdir(exist_ok=True)
(out/"result.json").write_text(json.dumps(dict(
    summary=summary,rows=rows,
    sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__),parent,binding_path,reference_path)},
    limitations="Native mean-head LIA attention for different existing noun spans "
    "in the SAME unchanged expression and physical input. Not a full text replacement "
    "intervention,not anchor identity,not proof of grounding. All entity nodes "
    "retained;some repeated mentions refer to target. No optimizer/new annotations."
),indent=2))
print(json.dumps(summary),flush=True)
