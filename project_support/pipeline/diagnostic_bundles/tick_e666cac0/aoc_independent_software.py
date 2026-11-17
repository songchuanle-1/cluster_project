"""Focused production AOC AST/list controls; no Torch or native claims."""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
from fractions import Fraction
import ast, math, hashlib, json

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc/ancestral_commutator.py'
# Reuse transparent list containers only; never run the older DCE test suite.
prior = ast.parse((ROOT / 'pipeline/diagnostic_bundles/tick_01d9102a/dce_independent_software.py').read_text(encoding='utf-8'))
defs = [n for n in prior.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ('prod', 'T', 'cat')]
ns = {'product': product}
exec(compile(ast.fix_missing_locations(ast.Module(defs, [])), 'transparent_list_carriers_only', 'exec'), ns)
T, cat = ns['T'], ns['cat']
T.__sub__ = lambda self, other: self.op(other, lambda a, b: a - b)
torch = SimpleNamespace(tensor=lambda values, **kw: T(values), cat=cat, long='index')
tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
nodes.append(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'forward'))
production = {'torch': torch}
exec(compile(ast.fix_missing_locations(ast.Module(nodes, [])), str(SOURCE), 'exec'), production)

def gelu_scalar(x):
    return x * (1 + math.erf(x / math.sqrt(2))) / 2

def binary(x, y):
    return gelu_scalar(.7 * x - .4 * y + .15)

def contrast(a, b, c):
    return binary(binary(a, b), c) - binary(binary(a, c), b)

class Owner:
    channels = 1
    def __init__(self): self.calls = []; self.activations = 0
    def cell(self, x):
        assert x.ndim == 2 and x.shape[1] == 2
        self.calls.append(x.shape[0])
        return T([.7 * x.v[i] - .4 * x.v[i + 1] + .15 for i in range(0, len(x.v), 2)], (x.shape[0], 1))
    def activation(self, x):
        self.activations += 1
        return T([gelu_scalar(v) for v in x.v], x.shape)

def oracle(values, ids, widths):
    # Direct per-fine ancestry and dictionary reduction; no producer grouping or mean helper.
    fine = set(ids[0]); out = [[0.] * k for k in widths]
    mids, roots = {}, {}
    for i in fine:
        j = ids[1][i]; k = ids[2][j]
        q = contrast(values[0][i], values[1][j], values[2][k])
        out[0][i] = q
        mids.setdefault(j, []).append(q); roots.setdefault(k, []).append(q)
    for j, vals in mids.items(): out[1][j] = sum(vals) / len(vals)
    for k, vals in roots.items(): out[2][k] = sum(vals) / len(vals)
    return out

checks = 0
def check(condition, reason):
    global checks
    assert condition, reason
    checks += 1

def run_batch(batch_ids, widths, label):
    values = [[[.13 * (i - 2) + .19 * level + .23 * b for i in range(k)] for level, k in enumerate(widths)] for b in range(len(batch_ids))]
    levels = [T([[[v] for v in values[b][level]] for b in range(len(batch_ids))], (len(batch_ids), widths[level], 1)) if not batch_ids else T([[[v] for v in values[b][level]] for b in range(len(batch_ids))]) for level in range(3)]
    if not batch_ids: levels = [T([], (0, k, 1)) for k in widths]
    memberships = [[T(batch_ids[b][level]) for b in range(len(batch_ids))] for level in range(3)]
    owner = Owner(); actual = production['forward'](owner, levels, memberships)
    for level in range(3):
        wanted = [v for b in range(len(batch_ids)) for v in oracle(values[b], batch_ids[b], widths)[level]]
        check(actual[level].shape == (len(batch_ids), widths[level], 1), label + ': original shape')
        check(all(math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-14) for a, b in zip(actual[level].v, wanted)), label + ': direct fine-path oracle')
    paths = sum(len(set(ids[0])) for ids in batch_ids)
    check(owner.calls == ([2 * paths, 2 * paths] if paths else []), label + ': exactly two global 2F cell calls')
    check(owner.activations == (2 if paths else 0), label + ': exactly two activation calls')
    return actual, values

cases = [
    ('empty', ([], [], []), (4, 3, 2)),
    ('single_true_fine', ([2, 2], [0, 0, 1], [0, 1]), (4, 3, 2)),
    ('unequal_path_degrees', ([0, 1, 2, 3], [0, 0, 0, 2], [0, 1, 0]), (5, 4, 2)),
    ('holes_two_roots', ([1, 3, 4, 1], [0, 2, 1, 2, 3], [0, 1, 1, 0]), (6, 5, 3)),
    ('duplicate_point_order', ([3, 1, 1, 3], [0, 2, 1, 2], [1, 0, 1]), (5, 4, 3)),
]
for label, ids, widths in cases:
    run_batch([ids], widths, label)
    plan = production['build_ancestry_path_plan'](*ids, widths)
    check(plan['fine_ids'] == sorted(set(ids[0])), label + ': true support from IDs')
    check(sum(plan['middle_path_counts']) == sum(plan['coarse_path_counts']) == len(set(ids[0])), label + ': counts are fine paths')
run_batch([([], [], []), cases[3][1], ([0, 2], [1, 0, 1], [0, 2])], (6, 5, 3), 'mixed empty and disjoint scenes')
run_batch([], (4, 3, 2), 'zero batch')

# A direct signed-message example distinguishes path-weighted root means from mean-of-middle-means.
check(production['mean_path_messages'](T([[2.], [4.], [8.], [-6.]]), [0, 0, 0, 0], [4]).v == [2.], 'coarse mean weights all four fine paths equally')
check(production['mean_path_messages'](T([[2.], [4.], [8.], [-6.]]), [0, 0, 0, 1], [3, 1]).v == [14 / 3, -6.], 'unequal-degree middle direct means')
check(production['mean_path_messages'](T([[1.], [-1.]]), [0, 0], [2]).v == [0.], 'signed cancellation is legal')

# Algebraic architecture properties are descriptive software controls, not native gates.
for a, b, c in [(.2, -.5, .9), (-.4, .8, -.1), (1.2, .3, .3)]:
    check(math.isclose(contrast(a, b, c), -contrast(a, c, b), rel_tol=0, abs_tol=1e-15), 'ancestor swap sign')
    check(contrast(a, b, b) == 0., 'equal normalized ancestors give zero')
check(not math.isclose(contrast(.2, -.5, .9), contrast(1.1, -.5, .9), rel_tol=1e-12, abs_tol=1e-12), 'nonlinear scalar example permits fine dependence')
linear = lambda a, b: Fraction(2, 3) * a + Fraction(-3, 5) * b + Fraction(1, 7)
affine_q = lambda a, b, c: linear(linear(a, b), c) - linear(linear(a, c), b)
check(affine_q(Fraction(1), Fraction(2), Fraction(3)) == affine_q(Fraction(7), Fraction(2), Fraction(3)), 'affine degeneration cancels fine input')

bad = [([-1], [], [], (2, 2, 2)), ([True], [0], [0], (2, 2, 2)), ([1], [0], [0], (2, 2, 2)), ([0], [1], [0], (2, 2, 2)), ([0], [0], [2], (2, 2, 2)), ([], [], [], (2, True, 2)), ([0], [0.0], [0], (2, 2, 2))]
for args in bad:
    try: production['build_ancestry_path_plan'](*args)
    except ValueError: checks += 1
    else: raise AssertionError(('invalid metadata accepted', args))

proof = {
    'status': 'ACTUAL_AOC_PRODUCTION_AST_LIST_FORWARD_AND_DIRECT_ANCESTRY_ORACLE_VALIDATED_NOT_TORCH',
    'helper_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'actual_checks': checks, 'single_scene_cases': len(cases), 'mixed_batch_cases': 1, 'zero_batch_cases': 1,
    'invalid_cases': len(bad),
    'controls': ['sparse original IDs', 'duplicate point IDs do not reweight fine paths', 'direct fine-path upper means', 'two shared cell/GELU call sites and 4F transformed rows', 'empty and mixed batches', 'swap sign and equal-ancestor zero', 'affine fine cancellation and a nonlinear fine-dependent scalar example'],
    'scope': 'Executes actual production helper and forward AST with transparent stdlib list carriers, an asymmetric scalar affine cell and scalar erf-GELU formula. Independent direct per-fine dictionary oracle. These checks do not execute torch.nn.Linear/GELU, Tensor/FP32/autograd/native/data/optimizer/resources and do not create new scientific gates.'
}
if __name__ == '__main__': print(json.dumps(proof, indent=2, allow_nan=False))
