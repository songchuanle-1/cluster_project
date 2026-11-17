"""Native calibration coefficients and task readouts on a fixed capture."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "native_role_direction_v2_20261014_0010.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749")


def install_capture(model):
    state = {"masks": [], "indicators": [], "query": None}
    original_masks = model.criterion.loss_masks
    original_indi = model.criterion.loss_indi

    def masks(*args):
        result = original_masks(*args)
        state["masks"].append((args, result))
        return result

    def indi(*args):
        result = original_indi(*args)
        state["indicators"].append((args, result))
        return result

    model.criterion.loss_masks = masks
    model.criterion.loss_indi = indi
    state["hook"] = model.dec.decoder_layers[-1].register_forward_hook(
        lambda module, inputs, output: state.update(query=output[0]))
    state.update(original_masks=original_masks, original_indi=original_indi)
    return state


def calibration(model, state, native, pred, gradients, batch, torch):
    tokens, queries, lang_masks, targets, indices, num_boxes = native
    logits = queries @ tokens.transpose(-1, -2) / model.criterion.temperature
    z = logits.detach().double()
    positive = torch.zeros_like(z)
    ends = lang_masks.sum(1) - 1
    positive[torch.arange(len(ends)), :, ends] = .5
    positive[torch.arange(len(ends)), :, ends - 1] = .5
    maps = {name: torch.zeros_like(z) for name in ("modify", "pron", "rel", "other")}
    sources = {"modify": "modify_positive_map", "pron": "pron_positive_map",
               "rel": "rel_positive_map", "other": "other_entity_map"}
    mask = torch.full(z.shape[:2], model.criterion.eos_coef, device=z.device,
                      dtype=torch.float64)
    for bi, (src, tgt) in enumerate(indices):
        positive[bi, src] = targets[bi]["positive_map"][tgt, :z.shape[-1]].double()
        mask[bi, src] = 1
        for name, field in sources.items():
            maps[name][bi, src] = targets[bi][field][tgt, :z.shape[-1]].double()
    positive = positive > 0
    supports = {name: value > 0 for name, value in maps.items()}
    attraction = positive.double() / (positive.sum(2, keepdim=True) + 1e-6)
    for name, weight in (("modify", .2), ("pron", .2), ("rel", .1)):
        attraction += weight * supports[name] / (supports[name].sum(2, keepdim=True) + 1e-6)
    amplification = 1 + supports["other"].double()
    effective_probability = (z * amplification).softmax(2)
    q_component = mask.unsqueeze(-1) * (effective_probability * amplification - attraction)
    q_component *= positive.any(2, keepdim=True)
    tmask = torch.full((len(z), z.shape[-1]), model.criterion.eos_coef,
                       device=z.device, dtype=torch.float64)
    tmask[torch.arange(len(ends)), ends] = 1
    tmask[positive.any(1)] = 1
    tmask[supports["modify"].any(1)] = .2
    tmask[supports["pron"].any(1)] = .2
    tmask[supports["rel"].any(1)] = .1
    tmask[torch.arange(len(ends)), ends - 1] = .1
    role_count = positive.double()
    mass = positive.sum(1).double()
    for name in ("modify", "pron", "rel"):
        role_count = role_count + supports[name]
        mass = mass + maps[name].sum(1)
    mass += 1e-6
    t_component = (z.softmax(1) - role_count / mass.unsqueeze(1))
    t_component *= role_count.any(1).unsqueeze(1) * tmask.unsqueeze(1)
    denominator = 2 * float(num_boxes)
    analytic = (q_component + t_component) / denominator
    analytic_error = float((analytic - gradients["original"].double()).abs().max())
    assert analytic_error <= 1e-6, ("analytic_gradient", analytic_error)

    expected_masks = [
        value.masked_select((~padding).unsqueeze(0)).view(value.shape[0], -1)
        for value, padding in zip(pred["masks"], pred["batch_mask"])]
    mask_calls = [
        (args, values) for args, values in state["masks"]
        if len(args[0]) == len(expected_masks)
        and all(a.shape == b.shape and torch.equal(a, b)
                for a, b in zip(args[0], expected_masks))]
    indicator_calls = [(args, value) for args, value in state["indicators"]
                       if args[0] is pred["indis"]]
    assert len(mask_calls) == len(indicator_calls) == 1
    weights = model.criterion.loss_weight
    mask_loss = weights[0] * mask_calls[0][1][0] + weights[1] * mask_calls[0][1][1]
    indi_loss = weights[4] * indicator_calls[0][1]
    query = state["query"]
    objectives = {"mask": mask_loss, "indicator": indi_loss,
                  "mask_plus_indicator": mask_loss + indi_loss}
    task_grad = {name: torch.autograd.grad(value.sum(), query, retain_graph=True)[0]
                 for name, value in objectives.items()}
    fractional = torch.zeros_like(positive)
    for name in ("modify", "pron", "rel"):
        fractional |= (maps[name] > 0) & (maps[name] < 1)
    main_secondary = positive & (supports["modify"] | supports["pron"] | supports["rel"])
    relation_other = supports["rel"] & supports["other"]
    subsets = {"main_secondary": main_secondary, "relation_other": relation_other,
               "fractional_secondary": fractional,
               "fractional_repelling": fractional & (gradients["original"] > 0),
               "fractional_attracting": fractional & (gradients["original"] < 0)}
    role_grad = {}
    for name, subset in subsets.items():
        gradient = torch.autograd.grad(
            logits, query, grad_outputs=gradients["original"] * subset * weights[6],
            retain_graph=True)[0]
        assert bool(torch.isfinite(gradient).all())
        role_grad[name] = gradient.detach()
    expressions = []
    from importlib import import_module
    native_iou = import_module(type(model.criterion).__module__).get_iou
    for bi, (src, tgt) in enumerate(indices):
        assert targets[bi]["masks"].shape[0] == 1
        ious = native_iou(expected_masks[bi].detach(), targets[bi]["masks"][0]).detach()
        indicate = pred["indis"][bi].detach().softmax(-1)[:, 1]
        selected = int(indicate.argmax())
        alignment = {}
        for name, gradient in role_grad.items():
            own = gradient[bi].double()
            if not bool(subsets[name][bi].any()):
                continue
            alignment[name] = {
                objective: {
                    "dot": float((own * reference[bi].double()).sum()),
                    "role_query_gradient_norm": float(own.norm()),
                    "task_query_gradient_norm": float(reference[bi].double().norm())}
                for objective, reference in task_grad.items()}
        sites = []
        for qi, ti in zip(src.tolist(), tgt.tolist()):
            union = main_secondary[bi, qi] | fractional[bi, qi] | relation_other[bi, qi]
            for token in union.nonzero().flatten().tolist():
                sites.append({
                    "query": qi, "target": ti, "token": token,
                    "main": bool(positive[bi, qi, token]),
                    "modify": float(maps["modify"][bi, qi, token]),
                    "pron": float(maps["pron"][bi, qi, token]),
                    "rel": float(maps["rel"][bi, qi, token]),
                    "other": float(maps["other"][bi, qi, token]),
                    "fractional": bool(fractional[bi, qi, token]),
                    "query_to_token_probability": float(effective_probability[bi, qi, token]),
                    "attraction_coefficient": float(attraction[bi, qi, token]),
                    "calibration_threshold": float((attraction / amplification)[bi, qi, token]),
                    "query_to_token_derivative": float(q_component[bi, qi, token] / denominator),
                    "token_to_query_derivative": float(t_component[bi, qi, token] / denominator),
                    "total_derivative": float(gradients["original"][bi, qi, token]),
                    "matched_query_support_iou": float(ious[qi])})
        expressions.append({
            "batch": bi, "ann_id": int(batch["ann_ids"][bi]),
            "selected_query": selected, "selected_support_iou": float(ious[selected]),
            "best_support_iou": float(ious.max()),
            "selected_is_matched": selected in src.tolist(),
            "matched_queries": src.tolist(), "matched_support_ious": ious[src].tolist(),
            "role_task_alignment": alignment, "sites": sites})
    result = {"analytic_autograd_max_delta": analytic_error, "expressions": expressions,
              "weighted_original_task_losses": {name: float(value.detach())
                                                for name, value in objectives.items()},
              "scope": "TRAIN augmented support IoU and local task directions; not VAL mIoU, causal task harm, optimizer, efficacy or admission."}
    state["masks"].clear()
    state["indicators"].clear()
    state["query"] = None
    return result


module = ast.parse(SOURCE.read_text())
main = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "main")
for index, node in enumerate(main.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Attribute) and target.attr == "loss_sem_align"
            for target in node.targets):
        main.body[index + 1:index + 1] = ast.parse("task_capture = install_capture(model)").body
        break
else:
    raise AssertionError("Missing setup")
insertions = 0
for node in ast.walk(main):
    if isinstance(node, ast.With):
        for loop in node.body:
            if not isinstance(loop, ast.For):
                continue
            for index, statement in enumerate(loop.body):
                if isinstance(statement, ast.Assign) and any(
                        isinstance(target, ast.Name) and target.id == "row"
                        for target in statement.targets):
                    loop.body[index:index] = ast.parse(
                        "calibration_readout = calibration(model, task_capture, native, held['pred'], gradients, batch, torch)").body
                    insertions += 1
                    break
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "injected_original_loss_delta"
            for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="calibration_readout"))
        node.values.append(ast.Name(id="calibration_readout", ctx=ast.Load()))
    if isinstance(node, ast.Try) and node.finalbody:
        node.finalbody += ast.parse(
            "task_capture['hook'].remove()\n"
            "model.criterion.loss_masks = task_capture['original_masks']\n"
            "model.criterion.loss_indi = task_capture['original_indi']").body
assert insertions == 1
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        node.value = node.value.replace("native_role_direction_v2_", "native_role_calibration_")
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__,
      "install_capture": install_capture, "calibration": calibration})
