"""Frozen native same-forward semantic versus task-query directions."""
import ast
import copy
import hashlib
from pathlib import Path
import runpy

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
SOURCE = PIPE / "native_role_direction_v2_20261014_0010.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749")


def install_task_capture(model, torch):
    state = {"masks": [], "indicators": [], "query": None}
    mask_function = model.criterion.loss_masks
    indicator_function = model.criterion.loss_indi

    def masks(*args):
        result = mask_function(*args)
        state["masks"].append((args, result))
        return result

    def indicators(*args):
        result = indicator_function(*args)
        state["indicators"].append((args, result))
        return result

    model.criterion.loss_masks = masks
    model.criterion.loss_indi = indicators
    hook = model.dec.decoder_layers[-1].register_forward_hook(
        lambda module, inputs, output: state.update(
            query=output[0], inst_feats=inputs[2], batch_mask=inputs[3]))
    state.update(hook=hook, original_masks=mask_function, original_indicators=indicator_function)
    return state


def task_gradients(model, state, native, pred, torch):
    expected_masks = [mask.masked_select((~padding).unsqueeze(0)).view(mask.shape[0], -1)
                      for mask, padding in zip(pred["masks"], pred["batch_mask"])]
    mask_calls = [(args, values) for args, values in state["masks"]
             if len(args[0]) == len(expected_masks)
             and all(a.shape == b.shape and torch.equal(a, b)
                     for a, b in zip(args[0], expected_masks))]
    indicator_calls = [(args, value) for args, value in state["indicators"]
                       if args[0] is pred["indis"]]
    masks = [values for args, values in mask_calls]
    indicators = [value for args, value in indicator_calls]
    assert len(masks) == len(indicators) == 1
    query = state["query"]
    assert query is not None
    weights = model.criterion.loss_weight
    mask_loss = weights[0] * masks[0][0] + weights[1] * masks[0][1]
    indicator_loss = weights[4] * indicators[0]
    task_losses = {"mask": mask_loss, "indicator": indicator_loss,
                   "mask_plus_indicator": mask_loss + indicator_loss}
    task = {name: torch.autograd.grad(value.sum(), query, retain_graph=True)[0]
            for name, value in task_losses.items()}
    layer = model.dec.decoder_layers[-1]

    def evaluate(counter_query):
        with torch.no_grad():
            scores, padded = layer.prediction_head(
                counter_query, state["inst_feats"], state["batch_mask"])
            unpadded = [mask.masked_select((~padding).unsqueeze(0)).view(mask.shape[0], -1)
                        for mask, padding in zip(padded, pred["batch_mask"])]
            mask_args = list(mask_calls[0][0])
            mask_args[0], mask_args[1] = unpadded, scores
            bce, dice, _ = state["original_masks"](*mask_args)
            indicator_args = list(indicator_calls[0][0])
            indicator_args[0] = layer.indi_embedding(counter_query)
            indicator = weights[4] * state["original_indicators"](*indicator_args)
            mask = weights[0] * bce + weights[1] * dice
            return {"mask": float(mask), "indicator": float(indicator),
                    "mask_plus_indicator": float(mask + indicator)}

    baseline = evaluate(query.detach())
    identity_loss_delta = max(abs(baseline[name] - float(value.detach()))
                              for name, value in task_losses.items())
    assert identity_loss_delta <= 1e-6
    helper = PIPE / "role_gradient_native_20261013_1012.py"
    assert hashlib.sha256(helper.read_bytes()).hexdigest() == (
        "d01eab84334844e45c83b9aa0af437848a255203e4aeaf32e72c146ce220c7a0")
    controls = runpy.run_path(str(helper), run_name="frozen_role_controls")["controls"](
        Path("/data3/songcl/Project/Cluster_project/Cluster/framework/model/Quard_model/"
             "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/loss.py"),
        model.criterion, torch)
    original = type(model.criterion).loss_sem_align.__get__(model.criterion)
    rows = {}
    original_gradient = None
    for name in ("original", "identity", "precedence", "mass",
                 "remove_other_overlap", "remove_relation_overlap", "remove_other_disjoint"):
        args = list(native)
        targets = copy.deepcopy(args[3])
        for bi, target in enumerate(targets):
            for ti in args[4][bi][1].tolist():
                overlap = (target["rel_positive_map"][ti] > 0) & (target["other_entity_map"][ti] > 0)
                if name == "remove_other_overlap":
                    target["other_entity_map"][ti, overlap] = 0
                elif name == "remove_relation_overlap":
                    target["rel_positive_map"][ti, overlap] = 0
                elif name == "remove_other_disjoint":
                    available = ((target["other_entity_map"][ti] > 0) & ~overlap).nonzero().flatten()[:int(overlap.sum())]
                    target["other_entity_map"][ti, available] = 0
        args[3] = targets
        function = controls.get(name, original)
        value = weights[6] * function(*args)
        gradient = torch.autograd.grad(value.sum(), query, retain_graph=True)[0]
        assert bool(torch.isfinite(gradient).all())
        if name == "original":
            original_gradient = gradient.detach()
        delta = float((gradient - original_gradient).abs().max())
        if name == "identity":
            assert delta <= 1e-6
        epsilon = 0.001
        gradient_norm = float(gradient.double().norm())
        finite_difference = None
        if gradient_norm > 0:
            direction = gradient.detach() / gradient_norm
            descent = evaluate(query.detach() - epsilon * direction)
            ascent = evaluate(query.detach() + epsilon * direction)
            finite_difference = {
                objective: {
                    "descent_loss_delta": descent[objective] - baseline[objective],
                    "ascent_loss_delta": ascent[objective] - baseline[objective],
                    "central_descent_derivative": (descent[objective] - ascent[objective]) / (2 * epsilon),
                } for objective in task_losses}
        alignment = {}
        for objective, reference in task.items():
            assert bool(torch.isfinite(reference).all())
            dot = float((gradient.double() * reference.double()).sum())
            norm = float(gradient.double().norm() * reference.double().norm())
            alignment[objective] = {
                "dot": dot, "cosine": dot / norm if norm > 0 else None,
                "first_order_task_loss_change_per_unit_semantic_step": -dot,
                "task_gradient_norm": float(reference.double().norm()),
            }
            if finite_difference:
                predicted = -dot / gradient_norm
                finite_difference[objective]["predicted_unit_descent_derivative"] = predicted
                finite_difference[objective]["central_derivative_absolute_error"] = abs(
                    finite_difference[objective]["central_descent_derivative"] - predicted)
        rows[name] = {"weighted_final_semantic_loss": float(value.detach()),
                      "semantic_gradient_norm": float(gradient.double().norm()),
                      "identity_gradient_max_delta": delta, "alignment": alignment,
                      "fixed_epsilon": epsilon, "head_identity_loss_delta": identity_loss_delta,
                      "finite_difference": finite_difference}
    state["masks"].clear()
    state["indicators"].clear()
    state["query"] = None
    state["inst_feats"] = None
    state["batch_mask"] = None
    return {"conditions": rows,
            "scope": "Local directional derivative at final common query, not an optimizer step, trained gain, all-layer effect or independent mechanism."}


module = ast.parse(SOURCE.read_text())
main = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "main")
for index, node in reversed(list(enumerate(main.body))):
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Attribute) and target.attr == "loss_sem_align" for target in node.targets):
        main.body[index + 1:index + 1] = ast.parse(
            "task_capture = install_task_capture(model, torch)").body
        break
else:
    raise AssertionError("Missing native setup assignment")
insertions = 0
for node in ast.walk(main):
    if isinstance(node, ast.With):
        for loop in node.body:
            if not isinstance(loop, ast.For):
                continue
            for index, statement in enumerate(loop.body):
                if (isinstance(statement, ast.Assign)
                        and any(isinstance(target, ast.Tuple)
                                and any(isinstance(item, ast.Name) and item.id == "num_boxes"
                                        for item in target.elts) for target in statement.targets)):
                    loop.body[index + 1:index + 1] = ast.parse(
                        "task_readout = task_gradients(model, task_capture, native, held['pred'], torch)").body
                    insertions += 1
                    break
assert insertions == 1
for node in ast.walk(main):
    if isinstance(node, ast.Dict) and any(
        isinstance(key, ast.Constant) and key.value == "injected_original_loss_delta"
        for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="task_readout"))
        node.values.append(ast.Name(id="task_readout", ctx=ast.Load()))
    if isinstance(node, ast.Try) and node.finalbody:
        node.finalbody += ast.parse(
            "task_capture['hook'].remove()\n"
            "model.criterion.loss_masks = task_capture['original_masks']\n"
            "model.criterion.loss_indi = task_capture['original_indicators']").body
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        node.value = node.value.replace("native_role_direction_v2_", "native_role_task_fd_")
namespace = {"__name__": "__main__", "__file__": __file__,
             "install_task_capture": install_task_capture, "task_gradients": task_gradients}
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"), namespace)
