"""Support-distribution prototype and centroid control on one native forward."""
import ast
import copy
import hashlib
from pathlib import Path

SOURCE = Path("/data3/songcl/Project/Cluster_project/pipeline/"
              "between_pair_native_20261014_0235.py")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
    "b219d91a46c0801d47c4964b722d5bd8c3c311f028770a34db42dac157233c22")


def fixture(torch):
    points = torch.tensor([-2., 0, 2], dtype=torch.float64)
    target = torch.tensor([0., 1, 0], dtype=torch.float64)
    spread = torch.tensor([.5, 0, .5], dtype=torch.float64, requires_grad=True)
    costs = torch.stack([
        ((torch.relu(lower - points) + torch.relu(points - upper)) /
         (upper - lower)).square()
        for lower, upper in ((-3., .5), (-.5, 3.))], dim=-1)
    coherent = torch.relu(spread @ costs - target @ costs).min()
    fragmented = torch.relu(spread @ costs.min(-1).values - target @ costs.min(-1).values)
    gradient, = torch.autograd.grad(coherent, spread)
    assert float(spread @ points) == float(target @ points) == 0
    assert float(coherent) > 0 and float(fragmented) == 0
    assert bool(torch.isfinite(gradient).all()) and float(gradient.norm()) > 0
    return {"same_center": 0, "support_coherent": float(coherent.detach()),
            "support_fragmented": float(fragmented.detach()),
            "finite_nonzero_constructed_gradient": True,
            "scope": "Constructed operator separation, not native task evidence."}


module = ast.parse(SOURCE.read_text())
prototype = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "prototype")
center_control = copy.deepcopy(prototype)
center_control.name = "prototype_center"
module.body.insert(module.body.index(prototype), center_control)
new_values = ast.parse("""
def values(weights, events, flat=False, target_weights=None):
    assert target_weights is not None
    def measure(value):
        result = value.double() * masses
        return result / result.sum(-1, keepdim=True).clamp_min(1e-12)
    prediction, target_measure = measure(weights), measure(target_weights)
    losses = []
    for pairs in events:
        costs = torch.stack([
            ((torch.relu(lower - constants @ axis) + torch.relu(constants @ axis - upper)) /
             (upper - lower)).square()
            for axis, lower, upper in pairs], dim=-1)
        if flat:
            point_cost = costs.min(-1).values
            losses.append(torch.relu(prediction @ point_cost - target_measure @ point_cost))
        else:
            losses.append(torch.relu(prediction @ costs - target_measure @ costs).min(-1).values)
    return torch.stack(losses, dim=-1).mean(-1)
""").body[0]
for index, node in enumerate(prototype.body):
    if isinstance(node, ast.FunctionDef) and node.name == "values":
        prototype.body[index] = new_values
        break
else:
    raise AssertionError("Missing original value operator")
replacements = 0
for node in ast.walk(prototype):
    if isinstance(node, ast.FunctionDef) and node.name == "values":
        continue
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "values":
        first = node.args[0]
        if isinstance(first, ast.Call) and isinstance(first.func, ast.Name) and first.func.id == "center":
            node.args[0] = first.args[0]
        elif isinstance(first, ast.Name) and first.id == "gt_center":
            node.args[0] = ast.parse("target[0].double()", mode="eval").body
        inside_objective = any(
            isinstance(arg, ast.Name) and arg.id == "flat" for arg in node.args)
        target = "targets[bi]['masks'][0]" if inside_objective else "target[0]"
        node.keywords.append(ast.keyword(arg="target_weights",
                                         value=ast.parse(target, mode="eval").body))
        replacements += 1
    if isinstance(node, ast.Constant) and node.value == "flat_union":
        node.value = "fragmented_witness"
assert replacements == 4
for index, node in enumerate(prototype.body):
    if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "structures" for target in node.targets):
        prototype.body[index + 1:index + 1] = ast.parse("disjoint_structures = {}").body
        break
for node in ast.walk(prototype):
    if isinstance(node, ast.If) and ast.unparse(node.test) == "events":
        node.body += ast.parse("""
reference_ids = {oid for ref in metadata['references'].values() for oid in ref['candidate_ids']}
pool = [int(oid) for oid in np.unique(labels) if oid >= 0 and oid != 199
        and int(oid) not in reference_ids and int(oid) not in metadata['target_ids']]
wrong_pairs = []
needed = max(map(len,events))
for a,b in itertools.combinations(pool,2):
    pa,pb=xyz[point_labels==a],xyz[point_labels==b]
    delta=pb.mean(0)-pa.mean(0)
    norm=float(np.linalg.norm(delta))
    if norm == 0: continue
    axis=delta/norm
    lower,upper=float((pa@axis).max()),float((pb@axis).min())
    if lower >= upper: continue
    wrong_pairs.append((torch.as_tensor(axis,dtype=torch.float64,device=device),lower,upper))
    if len(wrong_pairs) >= needed: break
cases[-1]['disjoint_control_requested_per_event'] = list(map(len,events))
cases[-1]['disjoint_control_available_pairs'] = len(wrong_pairs)
cases[-1]['disjoint_control_status'] = 'matched' if len(wrong_pairs)>=needed else 'missing'
if len(wrong_pairs)>=needed:
    disjoint_structures[bi]=[wrong_pairs[:len(pairs)] for pairs in events]
""").body
    if isinstance(node, ast.FunctionDef) and node.name == "objective":
        node.args.args.append(ast.arg(arg="reference_override"))
        node.args.defaults.append(ast.Constant(value=None))
        for child in ast.walk(node):
            if isinstance(child, ast.For) and ast.unparse(child.iter) == "structures.items()":
                child.iter = ast.parse(
                    "(structures if reference_override is None else reference_override).items()",
                    mode="eval").body
    if (isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
            and any(isinstance(value, ast.Name) and value.id == "name" for value in node.target.elts)):
        node.iter.elts += [ast.Tuple(elts=[ast.Constant(value="matched_reference_subset"),
                                         ast.Constant(value=False)], ctx=ast.Load()),
                          ast.Tuple(elts=[ast.Constant(value="disjoint_reference"),
                                         ast.Constant(value=False)], ctx=ast.Load())]
        for child in ast.walk(node):
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                    and child.func.id == "objective"):
                child.keywords.append(ast.keyword(arg="reference_override", value=ast.parse(
                    "disjoint_structures if name=='disjoint_reference' else "
                    "{bi:structures[bi] for bi in disjoint_structures} if name=='matched_reference_subset' else None",
                    mode="eval").body))
for index, node in enumerate(prototype.body):
    if isinstance(node, ast.Return):
        prototype.body[index:index] = ast.parse(
            "center_readout = prototype_center(model, native, held, batch, selection, torch)\n"
            "operator_fixture = fixture(torch)\n"
            "assert all(abs(case.get('gt_mask_proxy_loss',0)) <= 1e-6 for case in cases)").body
        node.value.keys.extend([ast.Constant(value="center_control"),
                                ast.Constant(value="operator_fixture")])
        node.value.values.extend([ast.Name(id="center_readout", ctx=ast.Load()),
                                  ast.Name(id="operator_fixture", ctx=ast.Load())])
        break
for node in ast.walk(module):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value == "between_pair_native_":
            node.value = "between_support_excess_"
    if isinstance(node, ast.Dict) and any(
            isinstance(key, ast.Constant) and key.value == "prototype"
            for key in node.keys if key is not None):
        node.keys.extend([ast.Constant(value="prototype_center"), ast.Constant(value="fixture")])
        node.values.extend([ast.Name(id="prototype_center", ctx=ast.Load()),
                            ast.Name(id="fixture", ctx=ast.Load())])
exec(compile(ast.fix_missing_locations(module), str(SOURCE), "exec"),
     {"__name__": "__main__", "__file__": __file__, "fixture": fixture})
