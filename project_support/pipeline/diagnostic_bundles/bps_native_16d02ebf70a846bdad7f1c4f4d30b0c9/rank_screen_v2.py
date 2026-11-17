"""Versioned scene-metadata adapter; immutable ranking and all native data."""

import ast
from pathlib import Path

source = Path(__file__).parent / "rank_screen.py"
tree = ast.parse(source.read_text())
repairs = 0
for node in ast.walk(tree):
    if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Subscript)
            and isinstance(node.value.value, ast.Name) and node.value.value.id == "group"
            and isinstance(node.value.slice, ast.Constant) and node.value.slice.value == "scan_ids"
            and isinstance(node.slice, ast.Name) and node.slice.id == "expression"):
        node.slice = ast.Constant(value=0)
        repairs += 1
assert repairs == 2
for node in tree.body:
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        if any(isinstance(child, ast.Name) and child.id == "group_index" for child in node.target.elts):
            node.body[:0] = ast.parse(
                "assert len(group['scan_ids']) == 1\n"
                "assert len(group['ann_ids']) == len(bank['rows'][2 * group_index]['expressions'])"
            ).body
for index, node in enumerate(tree.body):
    if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "save"):
        tree.body[index:index] = ast.parse(
            "result['metadata_adapter_sha256'] = tick.digest(Path(adapter_file))\n"
            "result['prior_failure'] = 'IndexError scan_ids per-expression indexing; raw failure preserved'"
        ).body
        break
else:
    raise AssertionError("Result persistence not found")
exec(compile(ast.fix_missing_locations(tree), str(source), "exec"),
     {"__name__": "__main__", "__file__": str(source), "adapter_file": __file__})
