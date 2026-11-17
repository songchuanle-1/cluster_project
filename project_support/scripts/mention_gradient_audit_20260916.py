"""Measure native semantic-loss gradients at repeated noun mentions."""
import ast
import hashlib
import inspect
import json
from pathlib import Path
import textwrap
import types

parent = Path(__file__).with_name("coverage_stage_capture_20260916.py")
scope = {"__file__": str(parent)}
exec(compile(parent.read_text().split("\nmodel.criterion.register_forward_pre_hook")[0],
             str(parent), "exec"), scope)
torch, model = scope["torch"], scope["model"]
root = scope["ROOT"].parent / "pipeline"
binding_path = root / "entity_binding_20260916/result.json"
binding = {(r["scene"], r["ann_id"]): r
           for r in json.loads(binding_path.read_text())["rows"]}
criterion = model.criterion
original = criterion.loss_sem_align
tree = ast.parse(textwrap.dedent(inspect.getsource(original)))
replaced = 0
for node in tree.body[0].body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "logits" for t in node.targets
    ):
        node.value = ast.Name(id="audit_logits", ctx=ast.Load())
        replaced += 1
assert replaced == 1
ast.fix_missing_locations(tree)
namespace = {"torch": torch}
exec(compile(tree, "<native_loss_logit_probe>", "exec"), namespace)
probe = types.MethodType(namespace["loss_sem_align"], criterion)
rows = []
current = {}


def wrapper(self, proj_tokens, proj_queries, lang_masks, targets, indices, num_boxes):
    result = original(proj_tokens, proj_queries, lang_masks, targets, indices, num_boxes)
    # Only the final invocation for this batch is retained below.
    with torch.enable_grad():
        logits = (torch.matmul(proj_queries, proj_tokens.transpose(-1, -2))
                  / self.temperature).detach().requires_grad_(True)
        namespace["audit_logits"] = logits
        measured = probe(proj_tokens, proj_queries, lang_masks, targets, indices, num_boxes)
        assert torch.allclose(measured.detach(), result, atol=1e-5, rtol=1e-5)
        grad = torch.autograd.grad(measured, logits)[0]
    batch = current["batch"]
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"]) for _ in range(int(n))]
    layer_rows = []
    tokenizer = scope["dataset"].tokenizer
    for b, (query_ids, target_ids) in enumerate(indices):
        record = binding[(scenes[b], int(batch["ann_ids"][b]))]
        entities = record["entities"]
        target_node = next((e for e in entities if e["node_id"] == 0), None)
        if target_node is None:
            continue
        noun = " ".join(s["text"] for s in target_node["spans"]["target_char_span"]).lower()
        encoded = tokenizer(record["caption"], return_tensors="pt")
        mentions = []
        for entity in entities:
            name = " ".join(s["text"] for s in entity["spans"]["target_char_span"]).lower()
            if entity["node_id"] == 0 or name != noun:
                continue
            tokens = set()
            for span in entity["spans"]["target_char_span"]:
                for char in range(*map(int, span["span"])):
                    token = encoded.char_to_token(char)
                    if token is not None and token < logits.shape[-1]:
                        tokens.add(token)
            values = []
            for q, t in zip(query_ids.tolist(), target_ids.tolist()):
                for token in sorted(tokens):
                    if targets[b]["other_entity_map"][t, token] > 0:
                        values.append(float(grad[b, q, token]))
            mentions.append(dict(node_id=entity["node_id"], noun=name,
                                 other_token_gradients=values))
        if mentions:
            layer_rows.append(dict(scene=record["scene"], ann_id=record["ann_id"],
                caption=record["caption"], success=record["success"],
                confident_wrong=record["confident_wrong"], mentions=mentions))
    current["final_rows"] = layer_rows
    return result


criterion.loss_sem_align = types.MethodType(wrapper, criterion)
with torch.no_grad():
    for step, batch in enumerate(scope["batches"]):
        current.update(batch=batch, final_rows=[])
        scope["gorilla"].set_random_seed(1999)
        loss, _ = model(batch, mode="loss")
        assert torch.isfinite(loss).all()
        rows.extend(current["final_rows"])
        print(json.dumps(dict(batch=step, repeated_mentions=len(rows))), flush=True)
values = [v for r in rows for m in r["mentions"] for v in m["other_token_gradients"]]
summary = dict(expressions=len(rows), confident_wrong=sum(r["confident_wrong"] for r in rows),
               success=sum(r["success"] for r in rows),
               gradient_entries=len(values), positive=sum(v > 0 for v in values),
               negative=sum(v < 0 for v in values))
out = root / "mention_gradient_20260916"
out.mkdir(exist_ok=True)
(out / "result.json").write_text(json.dumps(dict(
    summary=summary, rows=rows,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), parent, binding_path)},
    limitations="Actual final semantic alignment loss differentiated with respect "
    "to detached native logits. Exact noun equality is not coreference truth. "
    "Positive partial gradient discourages that logit; shared parameter gradients "
    "and total loss can differ. Eval-mode TRAIN diagnostic; no optimizer or training."
), indent=2))
print(json.dumps(summary), flush=True)
