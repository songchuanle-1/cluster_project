"""Small actual FCB observer metadata/transparent-mean controls, stdlib only."""
from pathlib import Path
import ast, copy, hashlib, json

R = Path('D:/project/cluster_project')
B = Path(__file__).resolve().parent
worker = B / 'fcb_native_prepare/worker.py'
t = ast.parse(worker.read_text(encoding='utf-8'))
functions = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name in ('fcb_plan_observation', 'fcb_coverage_preflight')]
smoke = next(n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == 'smoke')
mean = next(n for n in ast.walk(smoke) if isinstance(n, ast.FunctionDef) and n.name == 'observed_mean')
production = R / 'pipeline/diagnostic_bundles/tick_f8d84d12/new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fcb/fine_coarse_bipartite.py'
p = ast.parse(production.read_text(encoding='utf-8'))
plan_defs = [n for n in p.body if isinstance(n, ast.FunctionDef) and n.name in ('_original_ids', 'build_fine_coarse_plan')]
ns = {'copy': copy}
exec(compile(ast.fix_missing_locations(ast.Module(functions + plan_defs, [])), 'actual_fcb_metadata_only', 'exec'), ns)
checks = []
def ck(value, label):
    assert value, label
    checks.append(label)
fixtures = [
    (([], [], []), (4, 3, 3), (0, 0, 0, 0)),
    (([2, 2], [2, 0, 1], [0, 2, 3]), (4, 4, 4), (1, 1, 1, 0)),
    (([0, 0, 1, 3, 5], [1, 1, 0, 1, 4, 4], [0, 2, 0, 0, 3]), (6, 5, 4), (4, 2, 8, 4)),
    (([1, 3, 4, 1], [0, 2, 1, 0, 3], [1, 0, 3, 2]), (6, 5, 4), (3, 3, 9, 6)),
]
for members, widths, expected in fixtures:
    plan = ns['build_fine_coarse_plan'](*members, widths)
    observed = ns['fcb_plan_observation'](plan, members)
    ck((len(observed['fine_ids']), len(observed['coarse_ids']), observed['pair_count'], observed['observed_nonancestor_pairs']) == expected, 'actual observer metadata matches independently specified original-ID counts')
    ck(plan is not observed and 'observed_nonancestor_pairs' not in plan, 'metadata observer does not mutate original plan')
    coverage = ns['fcb_coverage_preflight']([members])
    ck(coverage['total_true_pairs'] == expected[2] and coverage['true_fine_coarse_pair_possible'] == bool(expected[2]), 'single batch core coverage without multiroot gate')
mixed = ns['fcb_coverage_preflight']([fixtures[0][0], fixtures[1][0], fixtures[2][0]])
ck(mixed['total_true_pairs'] == 9 and mixed['total_true_paths'] == 5, 'empty scene mixed with singleton and multiroot is coverage, not mandatory per-scene gate')
ck(not ns['fcb_coverage_preflight']([])['true_fine_coarse_pair_possible'], 'empty batch core absent')
tampered = ns['build_fine_coarse_plan'](*fixtures[2][0], fixtures[2][1])
tampered['middle_fine_counts'][0] += 1
try:
    ns['fcb_plan_observation'](tampered, fixtures[2][0])
except AssertionError:
    checks.append('actual observer refuses incorrect original middle-parent counts')
else:
    raise AssertionError('tampered plan accepted')

# Execute only the actual nested mean callback with opaque clone-distinct stand-ins.
class Opaque:
    def detach(self): return self
    def clone(self): return Opaque()
q, fine, coarse, mid = (Opaque() for _ in range(4))
context = {'mean_count':0, 'phase':'fine_mean', 'pair_fine':[0,0,1,1], 'pair_coarse':[0,1,0,1],
           'fine_parents':[0,0], 'fine_counts':[2,2], 'coarse_counts':[2,2], 'middle_counts':[2],
           'q_ref':q, 'mean_outputs':[], 'mean_snapshots':[], 'record':{'mean_calls':[]}}
calls=[]
def original_mean(messages, positions, counts):
    calls.append((messages,positions,counts))
    return (fine,coarse,mid)[len(calls)-1]
env={'state':{'fcb_context':context}, 'summary':lambda value:{'finite':True},
     'fingerprint':lambda torch,value:'opaque', 'torch':None, 'lite_watch':lambda value,record:None,
     'original_mean':original_mean}
exec(compile(ast.fix_missing_locations(ast.Module([mean], [])), 'actual_observed_mean_only', 'exec'), env)
for n,(message,pos,count,want,phase) in enumerate(((q,'pair_fine','fine_counts',fine,'coarse_mean'),(q,'pair_coarse','coarse_counts',coarse,'middle_mean'),(fine,'fine_parents','middle_counts',mid,'middle_map'))):
    out=env['observed_mean'](message,context[pos],context[count])
    ck(out is want and len(calls)==n+1, 'actual original mean called once and exact result object returned')
    ck(context['phase']==phase and context['mean_snapshots'][-1] is not out, 'actual callback phase and clone-distinct snapshot')
ck(calls[0][0] is calls[1][0] is q and calls[2][0] is fine, 'two actualq marginals then actualfine_delta parent mean identity')
proof={'status':'ACTUAL_FCB_NATIVE_METADATA_AND_TRANSPARENT_MEAN_CALLBACK_STDLIB_VALIDATED_NOT_NATIVE',
       'actual_checks':len(checks),'checks':checks,'tested_function_AST_sha256':hashlib.sha256('\n'.join(ast.dump(n,include_attributes=False) for n in functions+[mean]).encode()).hexdigest(),
       'scope':'Actual observer function ASTs, four explicit original-ID metadata fixtures, one tampered count rejection, and opaque clone-distinct mean callback object/phase controls only. No worker module import, Tensor, learned map, GELU, GPU, actual gradient/backward, optimizer, data or resource execution. Does not add future coverage/positivity gates.'}
if __name__=='__main__': print(json.dumps(proof,indent=2,allow_nan=False))
