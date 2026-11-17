"""FP32 end-to-end paired updates with exact seed-identity guard."""
import ast
from pathlib import Path

source = Path("/tmp/component_parameter_step_20260915.py")
tree = ast.parse(source.read_text())
setup = '''
seed_guard = {}
def fixed_sampling(module, args, result):
    if "sampling" not in seed_guard:
        seed_guard["sampling"] = result[0].detach().clone()
    return seed_guard["sampling"].clone(), result[1]
model.dec.sampling_module.register_forward_hook(fixed_sampling)
def decoder_identity(module, args, result):
    seeds = args[1].detach().gather(1, result["sample_inds"].detach().long())
    if "seeds" not in seed_guard:
        seed_guard["seeds"] = seeds.clone()
    else:
        assert torch.equal(seeds, seed_guard["seeds"]), "Physical seed alignment changed"
model.dec.register_forward_hook(decoder_identity)
'''
for node in list(tree.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "out" for t in node.targets):
        node.value = ast.parse('Path("/tmp/component_e2e_fixed_server4_20260915")', mode="eval").body
    if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple):
        if any(isinstance(t, ast.Name) and t.id == "step" for t in node.target.elts):
            tree.body[tree.body.index(node):tree.body.index(node)] = ast.parse(setup).body
            node.body.insert(0, ast.parse("seed_guard.clear()").body[0])
            # Check actual backbone gradients in each branch, not just total finiteness.
            for inner in node.body:
                if isinstance(inner, ast.For):
                    for position, statement in enumerate(inner.body):
                        if isinstance(statement, ast.Assign) and any(
                                isinstance(t, ast.Name) and t.id == "gradients"
                                for t in statement.targets):
                            inner.body[position + 1:position + 1] = ast.parse('''
backbone = [g for k,g in gradients.items() if k.startswith(("unet.", "input_conv."))]
assert backbone and any(torch.count_nonzero(g).item() for g in backbone)
''').body
                            break
ast.fix_missing_locations(tree)
exec(compile(tree, str(source), "exec"), {"__name__": "__main__", "__file__": __file__})
