"""Reuse the frozen extension manifest with the unchanged head diagnostic."""
import ast
import hashlib
import json
from pathlib import Path

PIPE = Path("/data3/songcl/Project/Cluster_project/pipeline")
SOURCE = PIPE / "native_role_head_20261014_0126.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "684244f76a8e81abb7679a1af7c958262e376888ba18a00e149a6bca2584af4c")


def load_frozen(dataset, original):
    manifest = PIPE / "native_calibration_extension_3aabc8207fea49ffb20003340e9bdfb9.manifest.json"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == (
        "dfe4c3b33a9d706ae5cc6679f3086dfc6bf37f599673a9c0276fa1781a405833")
    rows = json.loads(manifest.read_text())["groups"]
    assert len(rows) == 81
    selection = {}
    for row in rows:
        group = row["group"]
        assert [int(a["ann_id"]) for a in dataset.scene_inputs[group]] == row["ann_ids"]
        assert all(a["scene_id"] == row["scene"] for a in dataset.scene_inputs[group])
        selection[group] = row
    assert selection[4804] == original[4804]
    return selection


def extend_main(main):
    for index, node in enumerate(main.body):
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "dataset" for target in node.targets):
            main.body[index + 1:index + 1] = ast.parse(
                "cohort = load_frozen(dataset, cohort)").body
            return
    raise AssertionError("Missing original dataset")


def patch_lower(module):
    for index, node in enumerate(module.body):
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "main" for target in node.targets):
            module.body[index + 1:index + 1] = ast.parse("extend_main(main)").body
            break
    else:
        raise AssertionError("Missing original native AST")
    for node in ast.walk(module):
        if isinstance(node, ast.Constant) and node.value == "native_role_head_":
            node.value = "native_extension_head_"
        if isinstance(node, ast.Dict) and any(
                isinstance(key, ast.Constant) and key.value == "calibration"
                for key in node.keys if key is not None):
            node.keys.append(ast.Constant(value="load_frozen"))
            node.values.append(ast.Name(id="load_frozen", ctx=ast.Load()))


module = ast.parse(SOURCE.read_text())
for index, node in enumerate(module.body):
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(
            node.value.func, ast.Name) and node.value.func.id == "exec":
        module.body[index:index] = ast.parse("patch_lower(module)").body
        break
else:
    raise AssertionError("Missing original executor")
for node in ast.walk(module):
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "head_effects"
            for key in node.keys if key is not None):
        node.keys.extend([ast.Constant(value="extend_main"), ast.Constant(value="load_frozen")])
        node.values.extend([ast.Name(id="extend_main", ctx=ast.Load()),
                            ast.Name(id="load_frozen", ctx=ast.Load())])
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__, "patch_lower": patch_lower,
      "extend_main": extend_main, "load_frozen": load_frozen})
