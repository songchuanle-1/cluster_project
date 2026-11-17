"""Fixed-head responses to original role-local diagnostic query directions."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "native_role_calibration_20261014_0115.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "0ad3570f4aaf40a4122f92287b4bb88a69a8d387ed5ea917af3c409231fab67b")


def head_effects(model, state, pred, mask_calls, indicator_calls, native,
                 logits, role_grad, task_grad, query, torch):
    weights = model.criterion.loss_weight
    _, _, _, targets, indices, _ = native
    layer = model.dec.decoder_layers[-1]
    loss_module = __import__(type(model.criterion).__module__, fromlist=["get_iou"])

    def evaluate(counter_query):
        with torch.no_grad():
            scores, padded = layer.prediction_head(
                counter_query, state["inst_feats"], state["batch_mask"])
            unpadded = [
                mask.masked_select((~padding).unsqueeze(0)).view(mask.shape[0], -1)
                for mask, padding in zip(padded, pred["batch_mask"])]
            mask_args = list(mask_calls[0][0])
            mask_args[0], mask_args[1] = unpadded, scores
            bce, dice, _ = state["original_masks"](*mask_args)
            indi = layer.indi_embedding(counter_query)
            indi_args = list(indicator_calls[0][0])
            indi_args[0] = indi
            indicator = weights[4] * state["original_indi"](*indi_args)
            mask = weights[0] * bce + weights[1] * dice
            expressions = []
            for bi, (src, tgt) in enumerate(indices):
                indication = indi[bi].softmax(-1)[:, 1]
                selected = int(indication.argmax())
                is_matched = torch.zeros_like(indication, dtype=torch.bool)
                is_matched[src] = True
                margin = float(indication[is_matched].max() - indication[~is_matched].max())
                expressions.append({
                    "batch": bi, "selected": selected,
                    "selected_support_iou": float(loss_module.get_iou(
                        unpadded[bi][selected], targets[bi]["masks"][0])),
                    "indicator_matched_unmatched_margin": margin})
            return {"losses": {"mask": float(mask), "indicator": float(indicator),
                              "mask_plus_indicator": float(mask + indicator)},
                    "expressions": expressions}

    baseline = evaluate(query.detach())
    assert baseline == evaluate(query.detach()), "Exact fixed-head repeat"
    expected_mask = weights[0] * mask_calls[0][1][0] + weights[1] * mask_calls[0][1][1]
    expected_indi = weights[4] * indicator_calls[0][1]
    identity_delta = max(
        abs(baseline["losses"]["mask"] - float(expected_mask.detach())),
        abs(baseline["losses"]["indicator"] - float(expected_indi.detach())))
    assert identity_delta <= 1e-6
    original_semantic = type(model.criterion).loss_sem_align.__get__(model.criterion)
    original = torch.autograd.grad(
        (weights[6] * original_semantic(*native)).sum(), query,
        retain_graph=True)[0].detach()
    directions = {"original": original, "identity": original.clone()}
    directions.update(role_grad)
    for name, gradient in role_grad.items():
        directions["complement_" + name] = original - gradient
    readouts = {}
    epsilon = .001
    for name, gradient in directions.items():
        norm = float(gradient.double().norm())
        if norm == 0:
            readouts[name] = {"gradient_norm": 0, "effects": None}
            continue
        direction = gradient / norm
        descent = evaluate(query.detach() - epsilon * direction)
        ascent = evaluate(query.detach() + epsilon * direction)
        assert descent == evaluate(query.detach() - epsilon * direction)
        assert ascent == evaluate(query.detach() + epsilon * direction)
        effects = {}
        for objective, reference in task_grad.items():
            predicted = -float((gradient.double() * reference.double()).sum()) / norm
            central = (descent["losses"][objective] - ascent["losses"][objective]) / (2 * epsilon)
            effects[objective] = {
                "descent_loss_delta": descent["losses"][objective] - baseline["losses"][objective],
                "ascent_loss_delta": ascent["losses"][objective] - baseline["losses"][objective],
                "central_derivative": central, "analytic_unit_descent_derivative": predicted,
                "central_absolute_error": abs(central - predicted)}
        readouts[name] = {"gradient_norm": norm, "effects": effects,
                          "descent_expression_readouts": descent["expressions"],
                          "ascent_expression_readouts": ascent["expressions"]}
    assert readouts["original"] == readouts["identity"]
    return {"epsilon": epsilon, "head_identity_max_loss_delta": identity_delta,
            "same_capture_head_repeat_exact": True, "baseline": baseline,
            "conditions": readouts,
            "scope": "Fixed-head readout only; no optimizer, parameter update, full-network intervention, strict derivative certification or trained efficacy."}


module = ast.parse(SOURCE.read_text())
install = next(node for node in module.body if isinstance(node, ast.FunctionDef)
               and node.name == "install_capture")
for node in ast.walk(install):
    if isinstance(node, ast.Lambda):
        node.body = ast.parse(
            "state.update(query=output[0], inst_feats=inputs[2], batch_mask=inputs[3])",
            mode="eval").body
function = next(node for node in module.body if isinstance(node, ast.FunctionDef)
                and node.name == "calibration")
repairs = insertions = 0
for node in ast.walk(function):
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        for index, statement in enumerate(node.body):
            if (isinstance(statement, ast.Assert)
                    and ast.unparse(statement.test) == "targets[bi]['masks'].shape[0] == 1"):
                node.body[index:index + 1] = ast.parse(
                    "assert len(batch['object_idss'][bi]) == 1\n"
                    "assert targets[bi]['masks'].shape[0] == len(tgt)\n"
                    "assert torch.equal(targets[bi]['masks'], targets[bi]['masks'][:1].expand_as(targets[bi]['masks']))"
                ).body
                repairs += 1
for index, node in enumerate(function.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "result" for target in node.targets):
        function.body[index:index] = ast.parse(
            "head_readout = head_effects(model, state, pred, mask_calls, indicator_calls, native, logits, role_grad, task_grad, query, torch)"
        ).body
        node.value.keys.append(ast.Constant(value="fixed_head"))
        node.value.values.append(ast.Name(id="head_readout", ctx=ast.Load()))
        insertions += 1
        break
assert repairs == insertions == 1
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and node.value == "native_role_calibration_":
        node.value = "native_role_head_"
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "calibration"
            for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="head_effects"))
        node.values.append(ast.Name(id="head_effects", ctx=ast.Load()))
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__, "head_effects": head_effects})
