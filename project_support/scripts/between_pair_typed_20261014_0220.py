"""Separately frozen exact-native-class, two-direct-role coverage."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "between_pair_inventory_20261014_0209.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "a2f3cd1cc37bba4c21082c3f8243adc379d5f362234be0dc7ccd75ec25029be7")
module = ast.parse(SOURCE.read_text())
main = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "main")
for index, node in enumerate(main.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "annotations" for target in node.targets):
        main.body[index:index] = ast.parse(
            "dataset_ast = ast.parse(paths['dataset'].read_text())\n"
            "type_assignments = [node for node in ast.walk(dataset_ast) if isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute) and target.attr == 'type2class' for target in node.targets)]\n"
            "assert len(type_assignments) == 1\n"
            "native_types = ast.literal_eval(type_assignments[0].value)"
        ).body
        break
else:
    raise AssertionError("Missing original annotations load")
changes = 0
for node in ast.walk(main):
    if isinstance(node, ast.If) and ast.unparse(node.test) == "root_edges and len(objects) >= 2":
        node.test = ast.parse(
            "len(endpoint_ids) >= 2 and sum(nodes[n]['lemma_head'].lower().strip() in native_types for n in endpoint_ids) >= 2",
            mode="eval").body
        changes += 1
    if (isinstance(node, ast.For) and isinstance(node.target, ast.Name) and node.target.id == "node"
            and isinstance(node.iter, ast.Subscript) and isinstance(node.iter.slice, ast.Constant)
            and node.iter.slice.value == "nonroot_objects"):
        node.iter = ast.parse(
            "(n for n in row['nonroot_objects'] if n['node_id'] in row['direct_between_reference_node_ids'])",
            mode="eval").body
        changes += 1
for index, node in enumerate(main.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "dataset" for target in node.targets):
        main.body[index + 1:index + 1] = ast.parse(
            "assert dataset.type2class == native_types").body
        break
assert changes == 2
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value == "between_pair_inventory_":
            node.value = "between_pair_typed_inventory_"
        elif node.value == "between_pair_":
            node.value = "between_pair_typed_"
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__, "ast": ast})
