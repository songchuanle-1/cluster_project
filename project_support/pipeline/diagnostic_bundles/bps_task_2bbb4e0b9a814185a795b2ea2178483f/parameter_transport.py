"""Versioned four-group parameter-gradient diagnostic; no optimizer or update."""

import ast
import hashlib
import json
from pathlib import Path
import sys

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/diagnostics/bps_task_2bbb4e0b9a814185a795b2ea2178483f/task_head.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == "5076dd523e638a650281ec0e77d4721367636505790f1f77073ad7248ab13ef3"
TRANSPORT = {"previous": None, "calls": 0}


def parameter_transport(model, logits, original_gradient, subsets, objectives, native_values, torch):
    named = [(name, p) for name, p in model.named_parameters() if p.requires_grad]
    parameters = tuple(p for _, p in named)
    task = torch.autograd.grad(objectives["mask_plus_indicator"].sum(), parameters,
                               retain_graph=True, allow_unused=True)
    TRANSPORT["calls"] += 1
    conditions = {}
    cpu = {}
    weight = model.criterion.loss_weight[6]
    for name in ("original", "identity", "main_secondary", "relation_other",
                 "fractional_secondary", "fractional_repelling"):
        if name == "identity":
            scalar = weight * type(model.criterion).loss_sem_align(model.criterion, *native_values)
            gradient = torch.autograd.grad(scalar.sum(), parameters, retain_graph=True, allow_unused=True)
        else:
            direction = original_gradient * weight
            if name != "original":
                direction = direction * subsets[name]
            gradient = torch.autograd.grad(logits, parameters, grad_outputs=direction,
                                           retain_graph=True, allow_unused=True)
        TRANSPORT["calls"] += 1
        assert all(g is None or bool(torch.isfinite(g).all()) for g in gradient)
        cpu[name] = [None if g is None else g.detach().cpu() for g in gradient]
        norm2 = sum(float(g.double().square().sum()) for g in gradient if g is not None)
        dot = sum(float((g.double() * t.double()).sum()) for g, t in zip(gradient, task)
                  if g is not None and t is not None)
        conditions[name] = {
            "gradient_norm": norm2 ** .5, "task_dot": dot,
            "nonzero_parameter_tensors": sum(g is not None and bool((g != 0).any()) for g in gradient),
            "unused_parameter_tensors": sum(g is None for g in gradient),
        }
    assert all(p.grad is None for p in parameters)
    identity = 0.0
    for a, b in zip(cpu["original"], cpu["identity"]):
        if a is None or b is None:
            assert a is b
        else:
            identity = max(identity, float((a - b).abs().max()))
    result = {
        "trainable_parameter_tensors": len(parameters),
        "task_nonzero_parameter_tensors": sum(t is not None and bool((t != 0).any()) for t in task),
        "conditions": conditions, "original_native_identity_max_delta": identity,
        "pass_original_native_identity1e6": identity <= 1e-6,
        "requested_parameter_gradient_calls_this_forward": 7,
        "parameter_grad_accumulated": False,
    }
    if TRANSPORT["previous"] is None:
        TRANSPORT["previous"] = cpu
    else:
        maximum = 0.0
        for name, gradients in cpu.items():
            for a, b in zip(TRANSPORT["previous"][name], gradients):
                if a is None or b is None:
                    assert a is b
                else:
                    maximum = max(maximum, float((a - b).abs().max()))
        result["parameter_repeat_max_delta"] = maximum
        result["pass_parameter_repeat1e6"] = maximum <= 1e-6
        TRANSPORT["previous"] = None
    return result


def attach_transport(tree):
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "calibration")
    inserted = 0
    for index, statement in enumerate(function.body):
        if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                and ast.unparse(statement.value.func) == "state['masks'].clear"):
            function.body[index:index] = ast.parse(
                "result['parameter_transport'] = parameter_transport(model, logits, gradients['original'], "
                "subsets, objectives, native, torch)"
            ).body
            inserted += 1
            break
    cohorts = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and ast.unparse(node.iter) == "cohort.values()":
            node.iter = ast.parse("list(cohort.values())[:4]", mode="eval").body
            cohorts += 1
    assert inserted == cohorts == 1


tree = ast.parse(SOURCE.read_text())
for index, statement in enumerate(tree.body):
    if (isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "namespace" for target in statement.targets)):
        tree.body[index:index] = ast.parse("attach_transport(tree)").body
        statement.value.keys.append(ast.Constant(value="parameter_transport"))
        statement.value.values.append(ast.Name(id="parameter_transport", ctx=ast.Load()))
        break
else:
    raise AssertionError("Native adapter namespace not found")
exec(compile(ast.fix_missing_locations(tree), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__,
      "attach_transport": attach_transport, "parameter_transport": parameter_transport})
output = Path(sys.argv[sys.argv.index("--output") + 1])
result = json.loads(output.read_text())
assert [row["selection"]["group"] for row in result["rows"]] == [0, 60, 101, 124]
result["requested_model_parameter_gradient_calls"] = TRANSPORT["calls"]
result["model_parameter_backward"] = "Explicit autograd.grad requests; no .backward, accumulation or optimizer"
result["scope"] = "Fixed four-group local parameter-gradient transport only; no optimizer update, causal training harm, efficacy or new structural admission."
output.write_text(json.dumps(result, indent=2) + "\n")
