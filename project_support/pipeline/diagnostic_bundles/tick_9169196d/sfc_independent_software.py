"""Focused actual SFC production AST checks against an independent keyed forest.
Stdlib scalar/list graph evidence only, not Tensor/FP32/autograd/native results.
"""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
import ast, json, math, hashlib

R=Path('D:/project/cluster_project');B=Path(__file__).resolve().parent
P=B/'new_candidate_prepare';S=P/'staged_repository'
PKG=S/'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_sfc'
SOURCE=PKG/'synchronous_forest.py'
prep=json.loads((P/'preparation.json').read_text(encoding='utf-8'))
sourcepath=next(k for k in prep['source_files'] if k.endswith('/synchronous_forest.py'))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==prep['source_files'][sourcepath]
# Extract only transparent containers; none of the older DCE controls execute.
old=ast.parse((R/'pipeline/diagnostic_bundles/tick_01d9102a/dce_independent_software.py').read_text(encoding='utf-8'))
env={'product':product}
defs=[n for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('prod','T','cat')]
exec(compile(ast.fix_missing_locations(ast.Module(defs,[])),'container_definitions_only','exec'),env)
T,cat=env['T'],env['cat'];oldget=T.__getitem__
def getitem(self,key):
    if isinstance(key,int):
        n=env['prod'](self.shape[1:]);return T(self.v[key*n:(key+1)*n],self.shape[1:])
    return oldget(self,key)
T.__getitem__=getitem
def stack(values,dim=0):
    assert dim==0 and values and all(x.shape==values[0].shape for x in values)
    return T([v for x in values for v in x.v],(len(values),)+values[0].shape)
torch=SimpleNamespace(tensor=lambda v,**kw:T(v),cat=cat,stack=stack,long='original-ID')
tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
ns={'torch':torch}
exec(compile(ast.fix_missing_locations(ast.Module(functions+[forward],[])),str(SOURCE),'exec'),ns)
checks=[]
def ck(value,label):
    assert value,label
    checks.append(label)
def gelu(v):return .5*v*(1+math.erf(v/math.sqrt(2)))
def cell(own,mean):return gelu(.72*own-.31*mean+.09)

def keyed_forest(ids):
    points,fm,mc=ids;fine=set(points);edges=[]
    for f in fine:edges.extend([((0,f),(1,fm[f])),((1,fm[f]),(2,mc[fm[f]]))])
    adjacency={}
    for a,b in set(edges):adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
    remaining=set(adjacency);components=[]
    while remaining:
        start=min(remaining);found={start};todo=[start]
        for a in todo:
            for b in adjacency[a]:
                if b not in found:found.add(b);todo.append(b)
        remaining-=found;diameter=0
        # Full all-pairs breadth-first distances, independent of production's two sweeps.
        for start in found:
            distances={start:0};todo=[start]
            for a in todo:
                for b in adjacency[a]:
                    if b not in distances:distances[b]=distances[a]+1;todo.append(b)
            diameter=max(diameter,max(distances.values()))
        components.append((found,diameter))
    return adjacency,components

def oracle(ids,values,widths):
    adjacency,components=keyed_forest(ids)
    state={key:values[key[0]][key[1]] for key in adjacency}
    stage_rows=[]
    for r in range(max((d for nodes,d in components),default=0)):
        active=set().union(*(nodes for nodes,d in components if r<d))
        old=dict(state)
        def mean(v):
            # Explicit original-ID left fold avoids interpreter-version changes
            # in builtin sum; this is only a stdlib carrier evaluation order.
            total=0.
            for u in sorted(adjacency[v]):total+=old[u]
            return total/len(adjacency[v])
        updates={v:cell(old[v],mean(v)) for v in active}
        state.update(updates);stage_rows.append(active)
    result=[[0.]*k for k in widths]
    for (level,i),v in state.items():result[level][i]=v
    return result,adjacency,components,stage_rows

records=[];mean_original=ns['mean_neighbor_states'];calls=[]
def observed_mean(old,plan):
    before=list(old.v);answer=mean_original(old,plan)
    ck(old.v==before,'actual mean leaves OLD state unchanged')
    records.append((old,before,plan,answer));return answer
ns['mean_neighbor_states']=observed_mean
class Owner:
    channels=1
    def cell(self,value):
        ck(value.shape[1]==2,'shared actual cell input two C blocks')
        calls.append(value.shape[0])
        return T([.72*value.v[i]-.31*value.v[i+1]+.09 for i in range(0,len(value.v),2)],(value.shape[0],1))
    def activation(self,value):return T([gelu(v) for v in value.v],value.shape)

def run(batch_ids,widths,label,values=None):
    records.clear();calls.clear()
    if values is None:values=[[[.17*(i-2)+.33*l+1.7*b for i in range(k)] for l,k in enumerate(widths)] for b in range(len(batch_ids))]
    levels=[T([[[v] for v in values[b][l]] for b in range(len(batch_ids))]) if batch_ids else T([],(0,k,1)) for l,k in enumerate(widths)]
    memberships=[[T(ids[l]) for ids in batch_ids] for l in range(3)]
    actual=ns['forward'](Owner(),levels,memberships)
    wanted=[oracle(ids,values[b],widths) for b,ids in enumerate(batch_ids)]
    plans=[ns['build_synchronous_forest_plan'](*ids,widths) for ids in batch_ids]
    flatkeys=[(b,*key) for b,plan in enumerate(plans) for key in plan['node_keys']]
    for l,k in enumerate(widths):
        expect=[v for out,adj,comp,stages in wanted for v in out[l]]
        ck(actual[l].shape==(len(batch_ids),k,1),label+': original shape')
        ck(actual[l].v==expect,label+': independent original-ID synchronous scalar oracle')
    expected_rounds=[]
    for r in range(max((len(x[3]) for x in wanted),default=0)):
        expected_rounds.append({(b,*key) for b,x in enumerate(wanted) if r<len(x[3]) for key in x[3][r]})
    ck(len(calls)==len(expected_rounds)==len(records),label+': only genuine active rounds')
    for r,(old,before,plan,mean) in enumerate(records):
        receivers=[flatkeys[i] for i in plan['receivers']]
        ck(set(receivers)==expected_rounds[r] and len(receivers)==len(set(receivers)) and calls[r]==len(receivers),label+': every active receiver exactly once; finished component not fake-updated')
        ck(old.v==before,label+': prior state object unchanged by later functional replacements')
        for row,key in enumerate(receivers):
            b,level,i=key;expected_neighbors=wanted[b][1][(level,i)]
            donors=[flatkeys[s] for s,to in zip(plan['sources'],plan['source_receivers']) if to==row]
            ck(set(donors)=={(b,*x) for x in expected_neighbors} and plan['counts'][row]==len(expected_neighbors),label+': all actual neighbor identities and exact degree, no cross-scene edge')
    for b,(plan,(_,adj,components,stages)) in enumerate(zip(plans,wanted)):
        ck(set(plan['node_keys'])==set(adj),label+': only true unique supported original nodes')
        observed={frozenset(plan['node_keys'][i] for i in c['nodes']):c['diameter'] for c in plan['components']}
        ck(observed=={frozenset(nodes):d for nodes,d in components},label+': actual two-sweep diameters vs independent all-pairs BFS')
    return [list(x.v) for x in actual],values,[len(x) for x in expected_rounds]

fixtures=[
 ('empty',([],[],[]),(8,5,4)),
 ('single_sparse_path',([3,3],[0,0,0,2],[0,1,3]),(6,4,4)),
 ('one_middle_unequal_degree',([1,2,4,6],[0,3,3,0,3,2,3],[0,1,1,2]),(7,5,4)),
 ('two_middle_unequal_degrees',([0,0,1,2,4],[1,1,1,0,3],[0,2,1,2]),(7,5,4)),
 ('mixed_D2_D4_components',([0,1,2,4,5,7],[0,0,0,2,1,2,3,2],[0,1,1,2]),(8,5,4)),
 ('sparse_two_roots',([1,5],[0,2,0,1,1,4],[0,0,3,1,2]),(8,5,4)),
]
round_counts={}
for label,ids,widths in fixtures:round_counts[label]=run([ids],widths,label)[2]
run([fixtures[0][1],fixtures[4][1],fixtures[5][1]],(8,5,4),'mixed three scenes with empty scene')
run([],(8,5,4),'zero batch')
before,values,_=run([fixtures[4][1]],fixtures[4][2],'point-multiplicity reference')
ids=fixtures[4][1];dedup=(list(reversed(sorted(set(ids[0])))),ids[1],ids[2]);after,_,_=run([dedup],fixtures[4][2],'reordered point support',values)
ck(before==after,'duplicate point multiplicity/order does not reweight adjacency states')
bad=[([-1],[],[],(2,2,2)),([True],[0],[0],(2,2,2)),([1],[0],[0],(2,2,2)),([0],[1],[0],(2,2,2)),([0],[0],[2],(2,2,2)),([],[],[],(2,True,2)),([0],[0.],[0],(2,2,2))]
for args in bad:
    try:ns['build_synchronous_forest_plan'](*args)
    except ValueError:checks.append('invalid original membership metadata rejected')
    else:raise AssertionError(('invalid metadata accepted',args))
proof={'status':'ACTUAL_SFC_PRODUCTION_PLAN_MEAN_FORWARD_AST_STDLIB_VALIDATED_NOT_TORCH','actual_checks':len(checks),'helper_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'single_scene_cases':len(fixtures),'mixed_scene_cases':1,'zero_batch_cases':1,'point_multiplicity_controls':2,'invalid_cases':len(bad),'actual_round_row_counts':round_counts,'scope':'Actual production plan/round/mean/forward AST with transparent list containers and scalar affine cell/erf-GELU; independent original-ID keyed undirected adjacency, all-pairs BFS diameter, and dict-barrier synchronous recurrence. No Torch/FP32/module constructor/actual gradient/resource/native execution; this adds no future numerical/coverage gate.'}
if __name__=='__main__':print(json.dumps(proof,indent=2,allow_nan=False))
