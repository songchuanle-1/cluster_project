"""Focused actual FCB production AST controls with stdlib scalar/list carriers.
No Torch/native/GPU/gradient/resource evidence is produced.
"""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
import ast, hashlib, json, math

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fcb/fine_coarse_bipartite.py'
# Container definitions only; do not execute any old DCE suite.
old = ast.parse((ROOT / 'pipeline/diagnostic_bundles/tick_01d9102a/dce_independent_software.py').read_text(encoding='utf-8'))
defs = [n for n in old.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in ('prod', 'T', 'cat')]
carriers = {'product': product}
exec(compile(ast.fix_missing_locations(ast.Module(defs, [])), 'transparent_carrier_definitions_only', 'exec'), carriers)
T, cat = carriers['T'], carriers['cat']
torch = SimpleNamespace(tensor=lambda values, **kw: T(values), cat=cat, long='original-index')
source_tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
nodes = [n for n in source_tree.body if isinstance(n, ast.FunctionDef)]
cls = next(n for n in source_tree.body if isinstance(n, ast.ClassDef))
nodes.append(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'forward'))
ns = {'torch': torch}
exec(compile(ast.fix_missing_locations(ast.Module(nodes, [])), str(SOURCE), 'exec'), ns)

def gelu(x): return x * (1 + math.erf(x / math.sqrt(2))) / 2
def pair(a, b): return gelu(.6 * a - .4 * b + .13)
def middle(a, context): return gelu(-.3 * a + .8 * context + .02)

def oracle(values, ids, widths):
    # Direct original-ID dictionaries, no producer pair positions or grouped mean.
    fine = sorted(set(ids[0])); mids = sorted({ids[1][i] for i in fine})
    roots = sorted({ids[2][j] for j in mids})
    messages = {(f, c): pair(values[0][f], values[2][c]) for f in fine for c in roots}
    fd = {f: sum(messages[f, c] for c in roots) / len(roots) for f in fine}
    cd = {c: sum(messages[f, c] for f in fine) / len(fine) for c in roots}
    md = {j: middle(values[1][j], sum(fd[f] for f in fine if ids[1][f] == j) / sum(ids[1][f] == j for f in fine)) for j in mids}
    out = [[0.] * k for k in widths]
    for level, delta in enumerate((fd, md, cd)):
        for original_id, value in delta.items(): out[level][original_id] = value
    return out

trace = []
means = []
original_mean = ns['equal_message_means']
def observed_mean(messages, positions, counts):
    result = original_mean(messages, positions, counts)
    trace.append('mean'); means.append((messages, result))
    return result
ns['equal_message_means'] = observed_mean

class Owner:
    channels = 1
    def pair_map(self, x):
        trace.append('pair_map'); self.last_role = 'pair'; self.pair_rows = x.shape[0]
        assert x.shape[1] == 2
        return T([.6*x.v[i]-.4*x.v[i+1]+.13 for i in range(0, len(x.v), 2)], (x.shape[0], 1))
    def middle_map(self, x):
        trace.append('middle_map'); self.last_role = 'middle'; self.middle_rows = x.shape[0]
        assert x.shape[1] == 2
        return T([-.3*x.v[i]+.8*x.v[i+1]+.02 for i in range(0, len(x.v), 2)], (x.shape[0], 1))
    def activation(self, x):
        trace.append('GELU_' + self.last_role)
        return T([gelu(v) for v in x.v], x.shape)

checks = 0
def check(condition, label):
    global checks
    assert condition, label
    checks += 1

def run(batch_ids, widths, label, values=None):
    trace.clear(); means.clear()
    if values is None: values = [[[.11*(i-2)+.37*l+.25*b for i in range(k)] for l,k in enumerate(widths)] for b in range(len(batch_ids))]
    levels = [T([[[v] for v in values[b][l]] for b in range(len(batch_ids))]) if batch_ids else T([], (0, k, 1)) for l,k in enumerate(widths)]
    ids = [[T(batch_ids[b][l]) for b in range(len(batch_ids))] for l in range(3)]
    owner = Owner(); actual = ns['forward'](owner, levels, ids)
    for l,k in enumerate(widths):
        want = [v for b in range(len(batch_ids)) for v in oracle(values[b], batch_ids[b], widths)[l]]
        check(actual[l].shape == (len(batch_ids), k, 1), label + ': original output shape')
        check(all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-14) for a,b in zip(actual[l].v,want)), label + ': direct original-ID oracle')
    plans = [ns['build_fine_coarse_plan'](*ids, widths) for ids in batch_ids]
    total_pairs = sum(p['pair_count'] for p in plans); total_mid = sum(len(p['middle_ids']) for p in plans)
    if total_pairs:
        check(trace == ['pair_map','GELU_pair','mean','mean','mean','middle_map','GELU_middle'], label + ': actual production phase order')
        check(owner.pair_rows == total_pairs and owner.middle_rows == total_mid, label + ': only real support rows')
        check(means[0][0] is means[1][0] and means[2][0] is means[0][1], label + ': sameq marginals then actual fine_delta to middle')
    else: check(not trace and not means, label + ': empty no maps/GELU/means')
    for ids,p in zip(batch_ids, plans):
        fine=sorted(set(ids[0])); roots=sorted({ids[2][ids[1][f]] for f in fine})
        pairs=[(p['fine_ids'][i],p['coarse_ids'][j]) for i,j in zip(p['pair_fine_positions'],p['pair_coarse_positions'])]
        check(pairs == [(f,c) for f in fine for c in roots], label + ': complete scene-local unique Cartesian product')
        check(p['fine_ids']==fine and p['point_count']==len(ids[0]), label + ': duplicate points do not multiply truefine')
        check(p['middle_fine_counts']==[sum(ids[1][f]==j for f in fine) for j in p['middle_ids']], label + ': original middle fine counts')
        check(p['fine_pair_counts']==[len(roots)]*len(fine) and p['coarse_pair_counts']==[len(fine)]*len(roots), label + ': marginal denominators')
        if fine:
            expected=oracle(values[batch_ids.index(ids)],ids,widths)
            check(math.isclose(sum(expected[0][f] for f in fine)/len(fine),sum(expected[2][c] for c in roots)/len(roots),rel_tol=1e-12,abs_tol=1e-14),label+': scalar marginal coupling descriptive')
    return actual, values, plans

cases = [
    ('empty', ([],[],[]), (4,3,3)),
    ('single_sparse_true_path', ([2,2],[2,0,1],[0,2,3]), (4,4,4)),
    ('unequal_middle_degrees_two_roots', ([0,0,1,3,5],[1,1,0,1,4,4],[0,2,0,0,3]), (6,5,4)),
    ('same_root_several_middle', ([0,2,4],[1,0,1,0,2],[0,2,2]), (5,4,4)),
    ('holes_three_roots', ([1,3,4,1],[0,2,1,0,3],[1,0,3,2]), (6,5,4)),
]
for label,ids,widths in cases: run([ids],widths,label)
run([([],[],[]),cases[2][1],([1,4],[0,2,0,1,2],[0,1,1])],(6,5,4),'mixed empty and disjoint scenes with unequal rootcounts')
run([], (6,5,4), 'zero batch')
# Point multiplicity/order invariance is a metadata contract, not a native numerical invariant gate.
a,values,_=run([cases[2][1]],cases[2][2],'duplicate reference')
ids=cases[2][1]; b,_,_=run([(list(reversed(sorted(set(ids[0])))),ids[1],ids[2])],cases[2][2],'reordered unique truefine',values)
check(all(x.v==y.v for x,y in zip(a,b)),'point multiplicity/order does not reweight fine paths')
# Nonancestor pair is actually in the production plan; this is topology, not a learned task-influence/Jacobian test.
p=ns['build_fine_coarse_plan'](*cases[2][1],cases[2][2]);ids=cases[2][1]
check(any(p['coarse_ids'][c] != ids[2][ids[1][p['fine_ids'][f]]] for f,c in zip(p['pair_fine_positions'],p['pair_coarse_positions'])),'nonancestor edge present in actual plan')
bad=[([-1],[],[],(2,2,2)),([True],[0],[0],(2,2,2)),([1],[0],[0],(2,2,2)),([0],[1],[0],(2,2,2)),([0],[0],[2],(2,2,2)),([],[],[],(2,True,2)),([0],[0.0],[0],(2,2,2))]
for args in bad:
    try: ns['build_fine_coarse_plan'](*args)
    except ValueError: checks += 1
    else: raise AssertionError(('invalid metadata accepted',args))
proof={'status':'ACTUAL_FCB_PRODUCTION_AST_LIST_FORWARD_AND_DIRECT_ORIGINAL_ID_ORACLE_VALIDATED_NOT_TORCH','helper_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'actual_checks':checks,'single_scene_cases':5,'mixed_batch_cases':1,'zero_batch_cases':1,'point_multiplicity_order_cases':2,'invalid_cases':len(bad),'controls':['true supported scene-local completeF x C including nonancestor pairs','sameactualq two marginals','middle reads actual fine_delta by original middleparent counts','no point multiplicity reweighting or padding interaction','globalbatch offset separation','sparse original-ID scatter','singleton/empty/zeroB','scalar marginal coupling descriptive only'],'scope':'Only actual production plan/mean/forward AST and transparent stdlib list carriers. Direct keyed original-ID nested-pair oracle with separate asymmetric scalar affine maps and scalar erf-GELU. No old suite executes. Not Tensor/torch.nn.Linear/GELU/FP32/autograd/native/resources/efficacy evidence; no future numerical or Jacobian gate.'}
if __name__=='__main__': print(json.dumps(proof,indent=2,allow_nan=False))
