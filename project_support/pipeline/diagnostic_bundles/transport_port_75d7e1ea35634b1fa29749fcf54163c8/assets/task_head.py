"""Versioned adapter for native fixed-head diagnostics; no parameter update."""

import ast
import hashlib
import json
from pathlib import Path
import sys

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
TEMPLATE = PIPE / "diagnostics/bps_native_16d02ebf70a846bdad7f1c4f4d30b0c9/scalar_checkpoint.py"
CALIBRATION = PIPE / "native_role_calibration_20261014_0115.py"
HEAD = PIPE / "native_role_head_20261014_0126.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(TEMPLATE) == "70055ed9aa157347ca045e536bfef9412dea0447ab1ab0fb6145f9095ee1bc60"
assert sha(CALIBRATION) == "0ad3570f4aaf40a4122f92287b4bb88a69a8d387ed5ea917af3c409231fab67b"
assert sha(HEAD) == "684244f76a8e81abb7679a1af7c958262e376888ba18a00e149a6bca2584af4c"
calibration_tree = ast.parse(CALIBRATION.read_text())
install = next(n for n in calibration_tree.body if isinstance(n, ast.FunctionDef) and n.name == "install_capture")
calibration = next(n for n in calibration_tree.body if isinstance(n, ast.FunctionDef) and n.name == "calibration")
head = next(n for n in ast.parse(HEAD.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "head_effects")
for node in ast.walk(install):
    if isinstance(node, ast.Lambda):
        node.body = ast.parse(
            "state.update(query=output[0], inst_feats=inputs[2], batch_mask=inputs[3])", mode="eval"
        ).body
mask_repairs = 0
for node in ast.walk(calibration):
    if isinstance(node, ast.For):
        for index, statement in enumerate(node.body):
            if (isinstance(statement, ast.Assert)
                    and ast.unparse(statement.test) == "targets[bi]['masks'].shape[0] == 1"):
                node.body[index:index + 1] = ast.parse(
                    "assert len(batch['object_idss'][bi]) == 1\n"
                    "assert targets[bi]['masks'].shape[0] == len(tgt)\n"
                    "assert torch.equal(targets[bi]['masks'], targets[bi]['masks'][:1].expand_as(targets[bi]['masks']))"
                ).body
                mask_repairs += 1
head_insertions = 0
for index, node in enumerate(calibration.body):
    if (isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "result" for target in node.targets)):
        calibration.body[index:index] = ast.parse(
            "head_readout = head_effects(model, state, pred, mask_calls, indicator_calls, native, logits, role_grad, task_grad, query, torch)"
        ).body
        node.value.keys.append(ast.Constant(value="fixed_head"))
        node.value.values.append(ast.Name(id="head_readout", ctx=ast.Load()))
        head_insertions += 1
        break
assert mask_repairs == head_insertions == 1
tree = ast.parse(TEMPLATE.read_text())
changes = {"capture": 0, "enable": 0, "readout": 0}
for node in ast.walk(tree):
    if isinstance(node, ast.With):
        for item in node.items:
            if ast.unparse(item.context_expr) == "torch.no_grad()":
                item.context_expr = ast.parse("torch.enable_grad()", mode="eval").body
                changes["enable"] += 1
    if isinstance(node, ast.Call) and ast.unparse(node.func) == "trials.append":
        node.args[0].keys.append(ast.Constant(value="task_calibration"))
        node.args[0].values.append(ast.Name(id="task_calibration", ctx=ast.Load()))

for node in ast.walk(tree):
    for field in ("body",):
        statements = getattr(node, field, None)
        if not isinstance(statements, list):
            continue
        for index in reversed(range(len(statements))):
            statement = statements[index]
            if isinstance(statement, ast.Expr) and ast.unparse(statement.value) == "model.cuda().train()":
                statements[index + 1:index + 1] = ast.parse("task_capture = install_capture(model)").body
                changes["capture"] += 1
            elif (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
                  and ast.unparse(statement.value.func) == "trials.append"):
                statements[index:index] = ast.parse(
                    "task_calibration = calibration(model, task_capture, values, pred, "
                    "{name: value.to(raw.device) for name, value in gradients.items()}, batch, torch)\n"
                    "assert all(parameter.grad is None for parameter in model.parameters())"
                ).body
                changes["readout"] += 1
assert changes == {"capture": 1, "enable": 1, "readout": 1}
tree.body[:0] = [install, head, calibration]
namespace = {"__name__": "__main__", "__file__": __file__}
exec(compile(ast.fix_missing_locations(tree), str(TEMPLATE), "exec"), namespace)
