"""Build the frozen adapter with checked AST changes to deployment locations."""

import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage

stage.guard(300)
bundle = stage.BUNDLE
assets = stage.ASSETS
manifest = stage.tick.load(bundle / "assets_manifest.json")
for name, row in manifest["assets"].items():
    assert stage.tick.digest(assets / name) == row["sha256"]
source = ast.parse((assets / "task_head.py").read_text(encoding="utf-8"))
namespace_index = next(i for i, node in enumerate(source.body) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "namespace" for target in node.targets))
prefix = copy.deepcopy(source.body[:namespace_index])
paths = {
    "PIPE": assets,
    "TEMPLATE": assets / "scalar_checkpoint.py",
    "CALIBRATION": assets / "native_role_calibration_20261014_0115.py",
    "HEAD": assets / "native_role_head_20261014_0126.py",
}
replaced = set()
for node in prefix:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in paths:
            node.value = ast.parse("Path(" + repr(str(paths[name])) + ")", mode="eval").body
            replaced.add(name)
assert replaced == set(paths)
namespace = {"__name__": "build_only", "__file__": str(assets / "task_head.py")}
exec(compile(ast.fix_missing_locations(ast.Module(body=prefix, type_ignores=[])),
             str(assets / "task_head.py"), "exec"), namespace)
tree = namespace["tree"]
parameter_source = ast.parse((assets / "parameter_transport.py").read_text(encoding="utf-8"))
parameter_function = next(node for node in parameter_source.body
                          if isinstance(node, ast.FunctionDef) and node.name == "parameter_transport")
attach = next(node for node in parameter_source.body
              if isinstance(node, ast.FunctionDef) and node.name == "attach_transport")
attach_namespace = {"ast": ast}
exec(compile(ast.Module(body=[attach], type_ignores=[]), "frozen_attach", "exec"), attach_namespace)
attach_namespace["attach_transport"](tree)
before_functions = {node.name: ast.dump(node, include_attributes=False)
                    for node in tree.body if isinstance(node, ast.FunctionDef) and node.name != "main"}
main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
new_body = []
changed = {"native_loader": 0, "root": 0, "old": 0, "generator_path": 0, "source": 0, "locks": 0}
for node in main.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name == "spec":
            continue
        if name == "native":
            node.value = ast.parse("get_native(args.runner)", mode="eval").body
            changed["native_loader"] += 1
        if name in ("root", "old"):
            value = stage.ROOT if name == "root" else stage.REMOTE + "/assets"
            node.value = ast.parse("Path(" + repr(value) + ")", mode="eval").body
            changed[name] += 1
    if isinstance(node, ast.Expr) and ast.unparse(node.value) == "spec.loader.exec_module(native)":
        continue
    new_body.append(node)
main.body = new_body
for node in ast.walk(main):
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name == "generator_path":
            node.value = ast.parse("old / 'native_role_direction_v2_20261014_0010.py'", mode="eval").body
            changed[name] += 1
        if name == "source" and ast.unparse(node.value) == "pipe / filename":
            node.value = ast.parse("old / filename", mode="eval").body
            changed[name] += 1
lock_map = {
    "/tmp/cluster_project_gpu7_exclusive.lock": "/tmp/cluster_project_gpu0_m201_migration.lock",
    "/tmp/cluster_project_gpu7_diagnostic.lock": "/tmp/cluster_project_gpu0_exclusive.lock",
    "/tmp/cluster_project_gpu7_slot2_diagnostic.lock": "/tmp/cluster_project_gpu0_parameter_transport.lock",
}
for node in ast.walk(main):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in lock_map:
        node.value = lock_map[node.value]
        changed["locks"] += 1
assert changed == {"native_loader": 1, "root": 1, "old": 1, "generator_path": 1, "source": 1, "locks": 3}
tree.body[:0] = ast.parse("from runtime import get_native\nTRANSPORT={'previous':None,'calls':0}\n").body + [copy.deepcopy(parameter_function)]
suffix_index = next(i for i, node in enumerate(parameter_source.body) if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "output" for target in node.targets))
entry = next(node for node in tree.body if isinstance(node, ast.If) and ast.unparse(node.test) == "__name__ == '__main__'")
entry.body.extend(copy.deepcopy(parameter_source.body[suffix_index:]))
assert before_functions == {node.name: ast.dump(node, include_attributes=False)
                            for node in tree.body if isinstance(node, ast.FunctionDef)
                            and node.name not in ("main", "parameter_transport")}
assert ast.dump(parameter_function, include_attributes=False) == ast.dump(
    next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "parameter_transport"),
    include_attributes=False)
rendered = ast.unparse(ast.fix_missing_locations(tree)) + "\n"
compile(rendered, "native_adapter.py", "exec")
output = bundle / "native_adapter.py"
assert not output.exists()
output.write_text(rendered, encoding="utf-8")
stage.save("ast_audit", {
    "source_checks_passed": True, "changes": changed,
    "parameter_function_ast_exact": True, "calibration_capture_head_ast_exact": True,
    "native_adapter_sha256": stage.tick.digest(output), "fixed_cohort": [0, 60, 101, 124],
    "repeats": 2, "absolute_repeat_tolerance": 1e-6, "allocator_fraction_unchanged": .25,
    "scope": "Static adapter preparation, not native execution. Host/path/lease observation only; no loss, cohort, checkpoint, seed, tolerance or model changes.",
})
print(json.dumps({"adapter": str(output), "ast_audit": "PASS", "fixed_cohort": [0, 60, 101, 124]}))
