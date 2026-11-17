"""Use the immutable bounded launcher with an additional diagnostic label."""

import ast
from pathlib import Path

source = Path(__file__).parent / "run_remote.py"
tree = ast.parse(source.read_text())
changed = 0
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument":
        for keyword in node.keywords:
            if keyword.arg == "choices" and isinstance(keyword.value, ast.Tuple):
                assert [item.value for item in keyword.value.elts] == ["task_head", "mask_direction"]
                keyword.value.elts.append(ast.Constant(value="parameter_transport"))
                changed += 1
assert changed == 1
exec(compile(ast.fix_missing_locations(tree), str(source), "exec"),
     {"__name__": "__main__", "__file__": str(source)})
