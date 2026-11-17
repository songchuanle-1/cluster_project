"""Isolate repeatability at ordered U-Net leaves without production edits."""
import ast
from pathlib import Path

source = Path("/tmp/component_fixed_support_20260915.py")
tree = ast.parse(source.read_text())
for node in tree.body:
    if isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "out" in names:
            node.value = ast.parse(
                'Path("/tmp/component_unet_leaf_20260915-2210")', mode="eval"
            ).body
        elif "names" in names:
            node.value = ast.parse(
                '["input_conv.0"] + [name for name, module in '
                'model.named_modules() if name.startswith("unet.") '
                'and not list(module.children())] + ["unet", "output_layer"]',
                mode="eval",
            ).body
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        if any(isinstance(t, ast.Name) and t.id == "batch_id"
               for t in node.target.elts):
            node.iter = ast.parse('enumerate(env["batches"][:1])', mode="eval").body
    if isinstance(node, ast.FunctionDef) and node.name == "observe":
        node.body = ast.parse('''
for key, tensor in tensors(value, name):
    key = key + "#" + str(len(comparisons))
    current = tensor.detach()
    if repeat == 0:
        reference[key] = current.clone()
        comparisons.append(dict(activation=key, equal=True))
    else:
        previous = reference[key]
        same_shape = current.shape == previous.shape
        equal = same_shape and torch.equal(current, previous)
        comparisons.append(dict(
            activation=key, equal=equal, shape=list(current.shape),
            max_absolute=float((current.float() - previous.float()).abs().max())
            if same_shape and current.numel() else None))
''').body
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "report" for t in node.targets
    ):
        for keyword in node.value.keywords:
            if keyword.arg == "scope":
                keyword.value = ast.Constant(
                    "One native TRAIN batch; three restored initial-state AMP "
                    "global-loss forwards; ordered leaf hooks and fixed sampling. "
                    "Activation tensors held on GPU to avoid per-hook CPU copies. "
                    "Earliest leaf divergence is not kernel proof. No optimizer, "
                    "production edit, efficacy or admission claim."
                )
ast.fix_missing_locations(tree)
exec(compile(tree, str(source), "exec"), {"__name__": "__main__", "__file__": __file__})
