"""Preserve native repeated masks while checking physical singleton identity."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "native_role_calibration_20261014_0115.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "0ad3570f4aaf40a4122f92287b4bb88a69a8d387ed5ea917af3c409231fab67b")
module = ast.parse(SOURCE.read_text())
function = next(node for node in module.body
                if isinstance(node, ast.FunctionDef) and node.name == "calibration")
repairs = 0
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
assert repairs == 1
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and node.value == "native_role_calibration_":
        node.value = "native_role_calibration_v2_"
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__})
