"""Native semantic-logit gradients for existing repeated-head role candidates."""
import ast
import copy
import hashlib
import inspect
import json
from pathlib import Path
import textwrap
import types

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
namespace = {"__file__": str(base)}
exec(compile(base.read_text().split(
    "model.criterion.register_forward_pre_hook(capture)")[0], str(base), "exec"), namespace)
torch, model = namespace["torch"], namespace["model"]
dataset, batches, gorilla = namespace["dataset"], namespace["batches"], namespace["gorilla"]
out = namespace["ROOT"].parent / "pipeline/role_gradient_20260916"
out.mkdir(parents=True, exist_ok=True)
criterion = model.criterion
original = criterion.loss_sem_align
tree = ast.parse(textwrap.dedent(inspect.getsource(original)))
replaced = 0
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "logits" for target in node.targets):
        node.value = ast.Name(id="_audit_logits", ctx=ast.Load())
        replaced += 1
assert replaced == 1
ast.fix_missing_locations(tree)
audit_globals = {"torch": torch}
exec(compile(tree, "<native_semantic_logit_audit>", "exec"), audit_globals)
audit = audit_globals["loss_sem_align"]
state, records = {}, []


def masks_for_batch(batch):
    scenes = [s for s, n in zip(batch["scan_ids"], batch["scenes_len"])
              for _ in range(int(n))]
    masks = []
    for b, (scene, ann) in enumerate(zip(scenes, batch["ann_ids"])):
        graph = dataset.scene_graphs[scene][str(int(ann))]
        nodes = graph["graph_node"]
        lemma = nodes[0].get("lemma_head")
        spans = [span for node in nodes[1:]
                 if lemma and node.get("lemma_head") == lemma and node["node_type"] == "Object"
                 for span in node["target_char_span"]]
        caption = " ".join(graph["utterance"].replace(",", " ,").split())
        tokens = dataset.tokenizer(caption, return_offsets_mapping=True)
        ids = tokens["input_ids"]
        actual = batch["lang_tokenss"][b].tolist()
        # Source appends '. not mentioned' before tokenization; prefix remains exact.
        assert ids[:-1] == actual[:len(ids)-1]
        mask = torch.zeros(batch["lang_masks"].shape[1], dtype=torch.bool)
        for j, (left, right) in enumerate(tokens["offset_mapping"]):
            if right > left and any(left < end and right > start for start, end in spans):
                mask[j] = True
        masks.append(dict(mask=mask, scene=scene, ann_id=int(ann),
                          lemma=lemma, spans=spans))
    return masks


def wrapped(self, queries_text, queries_image, language_masks, targets, indices, num_boxes):
    value = original(queries_text, queries_image, language_masks, targets, indices, num_boxes)
    # Only final layer is retained; source calls this six times per native forward.
    state["calls"] += 1
    with torch.enable_grad():
        logits = (queries_image.detach() @ queries_text.detach().transpose(-1, -2)
                  / self.temperature).float().requires_grad_(True)
        audit_globals["_audit_logits"] = logits
        ref = audit(self, queries_text, queries_image, language_masks, targets, indices, num_boxes)
        torch.testing.assert_close(ref.detach(), value.detach().float(), atol=1e-4, rtol=1e-4)
        gradient = torch.autograd.grad(ref, logits)[0]
        alternative_targets = copy.deepcopy(targets)
        candidate_masks = []
        for b, info in enumerate(state["roles"]):
            repeat = info["mask"][:logits.shape[-1]].to(logits.device)
            target = targets[b]
            protected = sum(target[name].bool().any(0).int() for name in (
                "positive_map", "modify_positive_map", "pron_positive_map", "rel_positive_map"))
            repeat &= protected[:len(repeat)] == 0
            repeat &= target["other_entity_map"][:, :len(repeat)].bool().any(0)
            candidate_masks.append(repeat)
            alternative_targets[b]["other_entity_map"][:, :len(repeat)][:, repeat] = 0
        audit_globals["_audit_logits"] = logits
        alt = audit(self, queries_text, queries_image, language_masks,
                    alternative_targets, indices, num_boxes)
        alt_gradient = torch.autograd.grad(alt, logits)[0]
        assert torch.isfinite(gradient).all() and torch.isfinite(alt_gradient).all()
        rows = []
        for b, (info, mask) in enumerate(zip(state["roles"], candidate_masks)):
            query_ids = indices[b][0]
            g = gradient[b, query_ids][:, mask]
            ag = alt_gradient[b, query_ids][:, mask]
            rows.append(dict(scene=info["scene"], ann_id=info["ann_id"],
                             repeat_tokens=int(mask.sum()), matched_queries=len(query_ids),
                             observations=g.numel(),
                             positive_gradients=int((g > 0).sum()),
                             negative_gradients=int((g < 0).sum()),
                             original_sum=float(g.sum()), without_other_sum=float(ag.sum()),
                             other_increment=float((g-ag).sum())))
        state["layers"].append(dict(call=state["calls"], rows=rows,
                                    original_loss=float(ref.detach()),
                                    without_other_loss=float(alt.detach())))
    return value


criterion.loss_sem_align = types.MethodType(wrapped, criterion)
with torch.no_grad():
    for step, batch in enumerate(batches):
        state.update(roles=masks_for_batch(batch), calls=0, layers=[])
        gorilla.set_random_seed(1999)
        loss, _ = model(copy.deepcopy(batch), mode="loss")
        assert torch.isfinite(loss).all()
        # Criterion computes final semantic loss before looping auxiliary outputs.
        records.append(dict(batch=step, layers=state["layers"]))
        print(json.dumps(dict(batch=step, calls=state["calls"])), flush=True)
result = dict(batches=records,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), base, namespace["checkpoint"])},
    scope="Same native semantic-logit function AST-extracted,original equality checked. "
          "Repeated lemma is candidate ambiguity,not confirmed coreference. "
          "Removing only other tag is diagnostic;not target relabeling or training efficacy.")
(out / "result.json").write_text(json.dumps(result, indent=2))
