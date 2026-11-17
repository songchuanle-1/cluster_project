"""Native original-parameter reachability and a GT-only spatial control."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "between_support_excess_20261014_0246.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "423a30f5423b48e77077afb46e8400493f9f3efc95079496441b6288420a9ad0")


def parameter_specificity(model, masks, attached, structures, targets, indices,
                          num_boxes, constants, masses, torch):
    named = [(name, value) for name, value in model.named_parameters() if value.requires_grad]
    first = torch.autograd.grad(attached, [value for _, value in named],
                                retain_graph=True, allow_unused=True)
    second = torch.autograd.grad(attached, [value for _, value in named],
                                 retain_graph=True, allow_unused=True)
    reached = nonzero = 0
    maximum = 0
    for a, b in zip(first, second):
        assert (a is None) == (b is None)
        if a is None:
            continue
        assert bool(torch.isfinite(a).all()) and bool(torch.isfinite(b).all())
        reached += 1
        nonzero += bool((a != 0).any())
        maximum = max(maximum, float((a - b).abs().max()))
    radial = masks.sum().double() * 0
    missing = []
    for bi in structures:
        gt = targets[bi]["masks"][0].double() * masses
        gt = gt / gt.sum()
        center = gt @ constants
        square = (constants - center).square().sum(-1)
        variance = float(gt @ square)
        if variance == 0:
            missing.append(bi)
            continue
        phi = square / variance
        weights = masks[bi, indices[bi][0], :len(masses)].sigmoid().double() * masses
        weights = weights / weights.sum(-1, keepdim=True)
        radial = radial + torch.relu(weights @ phi - gt @ phi).sum()
    radial = radial / num_boxes
    actual, = torch.autograd.grad(attached, masks, retain_graph=True)
    control, = torch.autograd.grad(radial, masks, retain_graph=True)
    assert bool(torch.isfinite(actual).all()) and bool(torch.isfinite(control).all())
    norm = float(actual.double().norm() * control.double().norm())
    return {
        "original_trainable_tensor_count": len(named),
        "original_reached_finite_tensors": reached, "original_nonzero_tensors": nonzero,
        "same_capture_original_parameter_repeat_max_delta": maximum,
        "same_capture_parameter_repeat_pass1e6": maximum <= 1e-6,
        "radial_gt_only_control_loss": float(radial.detach()),
        "radial_control_missing_zero_variance_batches": missing,
        "relational_mask_gradient_norm": float(actual.double().norm()),
        "radial_mask_gradient_norm": float(control.double().norm()),
        "mask_gradient_max_delta": float((actual - control).abs().max()),
        "mask_gradient_cosine": float((actual.double() * control.double()).sum()) / norm if norm > 0 else None,
        "scope": "Original-parameter same-capture/component control only; no independent model, full-forward repeat, efficacy or novelty certificate."}


def inject(function):
    for index, node in enumerate(function.body):
        if isinstance(node, ast.Return):
            function.body[index:index] = ast.parse(
                "parameter_readout = parameter_specificity(model, masks, attached, structures, targets, indices, num_boxes, constants, masses, torch)"
            ).body
            node.value.keys.append(ast.Constant(value="parameter_readout"))
            node.value.values.append(ast.Name(id="parameter_readout", ctx=ast.Load()))
            return
    raise AssertionError("Missing prototype return")


module = ast.parse(SOURCE.read_text())
for index, node in enumerate(module.body):
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(
            node.value.func, ast.Name) and node.value.func.id == "exec":
        module.body[index:index] = ast.parse("inject(prototype)").body
        break
else:
    raise AssertionError("Missing original executor")
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and node.value == "between_support_excess_":
        node.value = "between_parameter_readout_"
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "fixture"
            for key in node.keys if key is not None):
        node.keys.append(ast.Constant(value="parameter_specificity"))
        node.values.append(ast.Name(id="parameter_specificity", ctx=ast.Load()))
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__, "inject": inject,
      "parameter_specificity": parameter_specificity})
