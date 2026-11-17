"""Native loss invariance to appended padding; no production changes."""
import copy
import ast
import hashlib
import inspect
import json
from pathlib import Path
import textwrap
import types

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
ns = {"__file__": str(base)}
exec(compile(base.read_text().split(
    "model.criterion.register_forward_pre_hook(capture)")[0], str(base), "exec"), ns)
torch, model = ns["torch"], ns["model"]
original = model.criterion.loss_sem_align
records, current = [], {}
tree = ast.parse(textwrap.dedent(inspect.getsource(original)))
replacements = 0
for node in ast.walk(tree):
    if (isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "neg_term" for t in node.targets)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "logsumexp"
            and isinstance(node.value.args[0], ast.Constant)
            and node.value.args[0].value == 2):
        expression = ast.unparse(node.value.func.value)
        node.value = ast.parse(
            f"({expression}).masked_fill(~lang_masks.bool()[:, None, :], "
            "float('-inf')).logsumexp(2)", mode="eval").body
        replacements += 1
assert replacements == 1
ast.fix_missing_locations(tree)
scope = {"torch": torch}
exec(compile(tree, "<padding_mask_diagnostic>", "exec"), scope)
masked = types.MethodType(scope["loss_sem_align"], model.criterion)


def wrapped(self, text, queries, valid, targets, indices, count):
    value = original(text, queries, valid, targets, indices, count)
    if current["called"]:
        return value
    current["called"] = True
    with torch.enable_grad():
        q = queries.detach().clone().requires_grad_(True)
        t = text.detach().clone().requires_grad_(True)
        native = original(t, q, valid, targets, indices, count)
        gq, gt = torch.autograd.grad(native, (q, t))
        torch.testing.assert_close(native.detach(), value.detach(), atol=1e-4, rtol=1e-4)
        fixed = masked(t, q, valid, targets, indices, count)
        fq, ft = torch.autograd.grad(fixed, (q, t))
        pad = ~valid.bool()
        variants = []
        for kind, extra in (("zero", 1), ("zero", 8), ("existing_pad", 8)):
            addition = torch.zeros(*t.shape[:1], extra, t.shape[-1],
                                   device=t.device, dtype=t.dtype)
            if kind == "existing_pad":
                for b in range(len(t)):
                    found = pad[b].nonzero().flatten()
                    if len(found):
                        addition[b] = t.detach()[b, found[0]]
            expanded = torch.cat([t.detach(), addition], 1)
            expanded.requires_grad_(True)
            q2 = q.detach().clone().requires_grad_(True)
            mask = torch.cat([valid, torch.zeros(
                valid.shape[0], extra, device=valid.device, dtype=valid.dtype)], 1)
            padded_targets = copy.deepcopy(targets)
            for target in padded_targets:
                for key in ("positive_map", "modify_positive_map", "pron_positive_map",
                            "other_entity_map", "rel_positive_map"):
                    source = target[key]
                    needed = max(0, expanded.shape[1] - source.shape[1])
                    if needed:
                        target[key] = torch.nn.functional.pad(source, (0, needed))
            changed = original(expanded, q2, mask, padded_targets, indices, count)
            gq2, gt2 = torch.autograd.grad(changed, (q2, expanded))
            fixed2 = masked(expanded, q2, mask, padded_targets, indices, count)
            fq2, ft2 = torch.autograd.grad(fixed2, (q2, expanded))
            assert torch.isfinite(gq2).all() and torch.isfinite(gt2).all()
            torch.testing.assert_close(fixed2, fixed, atol=1e-6, rtol=1e-6)
            torch.testing.assert_close(fq2, fq, atol=1e-6, rtol=1e-6)
            torch.testing.assert_close(ft2[:, :t.shape[1]], ft, atol=1e-6, rtol=1e-6)
            assert torch.count_nonzero(ft2[:, t.shape[1]:]) == 0
            variants.append(dict(kind=kind, extra=extra, loss=float(changed.detach()),
                loss_delta=float((changed-native).detach()),
                query_gradient_max_delta=float((gq2-gq).abs().max()),
                existing_token_gradient_max_delta=float(
                    (gt2[:, :t.shape[1]]-gt).abs().max()),
                appended_padding_gradient_l1=float(gt2[:, t.shape[1]:].abs().sum()),
                masked_loss_delta=float((fixed2-fixed).detach()),
                masked_query_gradient_max_delta=float((fq2-fq).abs().max()),
                masked_appended_gradient_l1=float(ft2[:, t.shape[1]:].abs().sum())))
        records.append(dict(batch=current["step"], expressions=len(text),
            padded_length=text.shape[1], lengths=valid.sum(1).tolist(),
            existing_padding_tokens=int(pad.sum()),
            existing_padding_gradient_l1=float(gt[pad].abs().sum()),
            masked_existing_padding_gradient_l1=float(ft[pad].abs().sum()),
            masked_minus_native_loss=float((fixed-native).detach()),
            original_loss=float(native.detach()), variants=variants))
    return value


model.criterion.loss_sem_align = types.MethodType(wrapped, model.criterion)
with torch.no_grad():
    for step, batch in enumerate(ns["batches"][:4]):
        current.update(step=step, called=False)
        ns["gorilla"].set_random_seed(1999)
        loss, _ = model(copy.deepcopy(batch), mode="loss")
        assert torch.isfinite(loss).all()
        print(json.dumps(records[-1]), flush=True)

result = dict(records=records,
    scope="Actual native TRAIN model embeddings, original semantic loss. "
          "Only detached loss inputs extended with zero padding and false mask. "
          "Not a full-forward batch intervention, optimizer step or efficacy test.",
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), base, ns["checkpoint"])})
out = ns["ROOT"].parent / "pipeline/padding_alignment_20260916"
out.mkdir(exist_ok=True)
(out / "result.json").write_text(json.dumps(result, indent=2))
