"""Exact original semantic components on the frozen final native capture."""
import ast
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "native_role_direction_v2_20261014_0010.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "c5a9c1157421bd9cc386a2da160ac1cf0ae376948ddff5b7f0c6808be690d749")
module = ast.parse(SOURCE.read_text())
function = next(node for node in module.body
                if isinstance(node, ast.FunctionDef) and node.name == "logit_functions")
for index, statement in enumerate(function.body):
    if (isinstance(statement, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "functions"
                    for target in statement.targets)):
        function.body[index + 1:index + 1] = ast.parse(
            "functions['query_to_token'] = copy.deepcopy(original)\n"
            "functions['token_to_query'] = copy.deepcopy(original)\n"
            "assert isinstance(functions['query_to_token'].body[-1], ast.Return)\n"
            "functions['query_to_token'].body[-1] = ast.parse('return box_to_token_loss / 2 / num_boxes').body[0]\n"
            "functions['token_to_query'].body[-1] = ast.parse('return token_to_box_loss / 2 / num_boxes').body[0]").body
        break
else:
    raise AssertionError("Missing original function collection")
loops = 0
for node in ast.walk(module):
    if (isinstance(node, ast.For) and isinstance(node.target, ast.Name)
            and node.target.id == "name" and isinstance(node.iter, ast.Tuple)
            and any(isinstance(item, ast.Constant) and item.value == "remove_other_disjoint"
                    for item in node.iter.elts)):
        node.iter.elts.extend([ast.Constant(value="query_to_token"),
                              ast.Constant(value="token_to_query")])
        node.body.append(ast.parse(
            "if name == 'token_to_query':\n"
            "    component_delta = float((gradients['query_to_token'] + gradients['token_to_query'] - gradients['original']).abs().max())\n"
            "    assert component_delta <= 1e-6\n"
            "    conditions[name]['component_gradient_sum_max_delta'] = component_delta"
        ).body[0])
        loops += 1
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        node.value = node.value.replace("native_role_direction_v2_", "native_role_components_")
assert loops == 1
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__})
