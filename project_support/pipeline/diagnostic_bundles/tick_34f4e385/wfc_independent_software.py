"""Bounded independent production-AST/list oracle; no Torch/model entry."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import combinations, product
from types import SimpleNamespace
import argparse, ast, hashlib, json, math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREP = HERE / 'new_candidate_prepare'
CARRIER = ROOT / 'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare/static_check.py'
MODEL = PREP / 'staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc/wedge_factor.py'
CHECKS = []

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    CHECKS.append(name)

def load_functions():
    carrier = ast.parse(CARRIER.read_text(encoding='utf-8'))
    nodes = [n for n in carrier.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))
             and n.name in ('size', 'T', 'stack', 'cat')]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 'list_value_primitives_only', 'exec'), globals())
    source = ast.parse(MODEL.read_text(encoding='utf-8'))
    nodes = [n for n in source.body if isinstance(n, ast.FunctionDef)]
    cls = next(n for n in source.body if isinstance(n, ast.ClassDef))
    nodes.append(next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'forward'))
    namespace = {'torch': SimpleNamespace(tensor=lambda x, **kw: T(x), stack=stack, cat=cat, long='long')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 'actual_frozen_WFC_functions_only', 'exec'), namespace)
    return namespace

class Linear:
    weights = ((Q(3,7), Q(-2,5), Q(4,9), Q(1,3)),
               (Q(-5,11), Q(2,3), Q(-1,4), Q(3,8)))
    bias = (Q(1,17), Q(-2,19))
    def __init__(self):
        self.calls = []
    def vector(self, row):
        return [sum((w*x for w,x in zip(weights, row)), bias)
                for weights,bias in zip(self.weights, self.bias)]
    def __call__(self, values):
        self.calls.append(values.shape)
        return T([v for i in range(values.shape[0])
                  for v in self.vector(values.data[i*4:(i+1)*4])], (values.shape[0],2))

def nonlinear_value(x):
    return x + x*x*x/Q(23)

def nonlinear_tensor(values):
    return T([nonlinear_value(v) for v in values.data], values.shape)

def gelu_value(x):
    x = float(x)
    return 0.5*x*(1.0 + math.erf(x/math.sqrt(2.0)))

def gelu_tensor(values):
    return T([gelu_value(v) for v in values.data], values.shape)

def original_id_oracle(scene):
    points, fm, mc = scene
    fine = set(points)
    middle = {fm[f] for f in fine}
    coarse = {mc[m] for m in middle}
    keys = sorted([(0,f) for f in fine] + [(1,m) for m in middle] + [(2,c) for c in coarse])
    edges = {frozenset(((0,f),(1,fm[f]))) for f in fine}
    edges |= {frozenset(((1,m),(2,mc[m]))) for m in middle}
    adjacent = lambda a,b: frozenset((a,b)) in edges
    # Enumerate complete triples independently, then discover the unique tree center.
    factors = []
    for triple in combinations(keys, 3):
        for center in triple:
            ends = sorted(k for k in triple if k != center)
            if adjacent(center, ends[0]) and adjacent(center, ends[1]):
                factors.append((ends[0], center, ends[1]))
    return keys, edges, factors

def run_case(ns, label, scenes, scalar_gelu=False, zeros=False):
    widths = (6,4,3)
    batch = len(scenes)
    values = [[[[Q(0) if zeros else Q(97*b + 13*l + 3*i + 2*k + 1, 31)
                  for k in range(2)] for i in range(width)] for b in range(batch)]
              for l,width in enumerate(widths)]
    levels = [T([v for scene in rows for row in scene for v in row], (batch,width,2))
              for rows,width in zip(values,widths)]
    ids = [[T(scene[level]) for scene in scenes] for level in range(3)]
    operator = Linear()
    activation = gelu_tensor if scalar_gelu else nonlinear_tensor
    object_ = SimpleNamespace(channels=2, factor_map=operator, activation=activation)
    actual = ns['forward'](object_, levels, ids)
    expected = [[] for _ in widths]
    factor_count = 0
    for b,scene in enumerate(scenes):
        keys, edges, factors = original_id_oracle(scene)
        plan = ns['build_wedge_factor_plan'](*scene, widths)
        observed = [(plan['node_keys'][a],plan['node_keys'][m],plan['node_keys'][c])
                    for a,m,c in plan['wedges']]
        check(label+': original-ID triple incidence plan', set(observed)==set(factors))
        check(label+': true support deduplicated, no padding', set(map(tuple,plan['node_keys']))==set(keys))
        check(label+': original edge set', {frozenset((plan['node_keys'][a],plan['node_keys'][c]))
                                         for a,c in plan['edges']}==edges)
        received = {key: [] for key in keys}
        for left,center,right in factors:
            own = values[center[0]][b][center[1]]
            endpoints = [a+c for a,c in zip(values[left[0]][b][left[1]], values[right[0]][b][right[1]])]
            q = [gelu_value(v) if scalar_gelu else nonlinear_value(v)
                 for v in operator.vector(own+endpoints)]
            for node in (left,center,right):
                received[node].append(q)
        result = [[[Q(0)]*2 for _ in range(width)] for width in widths]
        for (level,index), messages in received.items():
            check(label+': all true nodes have a real incident factor', len(messages)>0)
            result[level][index] = [sum((row[k] for row in messages),Q(0))/len(messages) for k in range(2)]
        for level in range(3):
            expected[level].extend(v for row in result[level] for v in row)
        factor_count += len(factors)
    check(label+': actual production forward equals independent triple oracle',
          all(a.data==b for a,b in zip(actual,expected)))
    check(label+': one global learned map iff supported wedges',
          operator.calls==([(factor_count,4)] if factor_count else []))
    check(label+': output banks retained', [x.shape for x in actual]==[(batch,w,2) for w in widths])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--preparation-sha256', required=True)
    args=ap.parse_args()
    check('final preparation SHA', sha(PREP/'preparation.json')==args.preparation_sha256)
    prep=json.loads((PREP/'preparation.json').read_text(encoding='utf-8'))
    for name,digest in prep['prepared_file_hashes'].items():
        check('frozen map '+name, sha(PREP/name)==digest)
    ns=load_functions()
    chain=([1],[0,2],[0,0,1])
    siblings=([1,4,4],[0,3,1,1,3],[0,0,1,2])
    roots=([0,3],[1,1,2,3],[0,1,1,1])
    mixed=([0,1,2,4,4],[0,0,1,1,3],[0,1,1,2])
    for label,scenes in [('chain',[chain]),('siblings',[siblings]),('middle-siblings',[roots]),
                         ('unequal-degree-multiroot',[mixed]),('mixed-empty-scene',[([],[],[]),mixed]),
                         ('zero-feature-true-support',[siblings]),('zero-batch',[])]:
        run_case(ns,label,scenes,zeros=label.startswith('zero-feature'))
    run_case(ns,'chain-scalar-erf-GELU',[chain],scalar_gelu=True)
    for label,scene,widths in [('bad-point',([6],[],[]),(6,4,3)),
                                ('missing-parent',([4],[0],[0]),(6,4,3)),
                                ('boolean-id',([True],[0],[0]),(6,4,3)),
                                ('bad-width',([],[],[]),(6,4))]:
        try: ns['build_wedge_factor_plan'](*scene,widths)
        except ValueError: check(label+' rejected',True)
        else: raise AssertionError(label+' accepted')
    result={'status':'INDEPENDENT_WFC_PRODUCTION_AST_LIST_AND_ORIGINAL_ID_ORACLE_CHECKED_NOT_TORCH',
            'candidate_id':'hierarchy-wedge-factor-incidence-composition','experiment_id':'M226-WFC',
            'preparation':{'path':(PREP/'preparation.json').relative_to(ROOT).as_posix(),'sha256':sha(PREP/'preparation.json')},
            'production_helper_sha256':sha(MODEL),'carrier_source_sha256':sha(CARRIER),
            'check_count':len(CHECKS),'checks':CHECKS,'material_concerns':[],
            'scope':'Only frozen production function AST plus four generic list primitives; no old checker main/assertions, Torch/model import, autograd, dataset, remote or GPU. Oracle independently enumerates complete original-ID triples, not production adjacency-pair loops. Seven rational nonlinear forward cases and one Python scalar-erfGELU chain; neither establishes Torch numerical/gradient/resource behavior.'}
    with (HERE/'wfc_independent_software.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'passed':len(CHECKS),'sha256':sha(HERE/'wfc_independent_software.json')}))

if __name__=='__main__':main()
