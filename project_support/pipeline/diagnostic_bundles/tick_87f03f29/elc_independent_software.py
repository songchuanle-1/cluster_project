"""Focused ELC production AST controls. Stdlib only, no Torch/native evidence."""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
from fractions import Fraction as Q
import ast, hashlib, json, math

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SOURCE=HERE/'new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_elc/edge_line_graph.py'
tree=ast.parse(SOURCE.read_text('utf8'))
# Reuse only transparent container definitions, never any previous suite body.
carrier=ROOT/'pipeline/diagnostic_bundles/tick_01d9102a/dce_independent_software.py'
old=ast.parse(carrier.read_text('utf8'));base={'product':product}
defs=[n for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('prod','T')]
exec(compile(ast.Module(defs,[]),'transparent_container_definitions_only','exec'),base)
T=base['T'];prod=base['prod']
def offset(coords,shape):
    out=0
    for x,k in zip(coords,shape):out=out*k+x
    return out
def getitem(self,key):
    key=key if isinstance(key,tuple) else (key,)
    key=key+(slice(None),)*(self.ndim-len(key));choices=[];shape=[]
    for k,n in zip(key,self.shape):
        if isinstance(k,int):choices.append([k if k>=0 else n+k])
        else:choices.append(list(range(n))[k]);shape.append(len(choices[-1]))
    return T([self.v[offset(c,self.shape)] for c in product(*choices)],shape)
def cumsum(self,dim):
    out=[]
    for coords in product(*(range(k) for k in self.shape)):
        s=Q(0)
        for i in range(coords[dim]+1):
            c=list(coords);c[dim]=i;s+=self.v[offset(c,self.shape)]
        out.append(s)
    return T(out,self.shape)
def flip(self,axes):
    return T([self.v[offset([self.shape[i]-1-x if i in axes else x for i,x in enumerate(c)],self.shape)] for c in product(*(range(k) for k in self.shape))],self.shape)
T.__getitem__=getitem;T.cumsum=cumsum;T.flip=flip
T.new_zeros=lambda self,shape:T([Q(0)]*prod(shape),shape)
def cat(values,dim):
    dim=dim if dim>=0 else values[0].ndim+dim
    shape=list(values[0].shape);shape[dim]=sum(x.shape[dim] for x in values)
    out=[]
    for coords in product(*(range(k) for k in shape)):
        at=coords[dim]
        for value in values:
            if at<value.shape[dim]:
                c=list(coords);c[dim]=at;out.append(value.v[offset(c,value.shape)]);break
            at-=value.shape[dim]
    return T(out,shape)
def stack(values,dim=0):
    assert dim==0 and values and all(v.shape==values[0].shape for v in values)
    return T([x for v in values for x in v.v],(len(values),)+values[0].shape)
torch=SimpleNamespace(tensor=lambda x,**kw:T(x),stack=stack,cat=cat,long='original-ID')
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
ns={'torch':torch};exec(compile(ast.Module(functions+[forward],[]),str(SOURCE),'exec'),ns)
checks=[];rows=[];mean_calls=[]
def ck(cond,label):assert cond,label;checks.append(label)
def phi(x):return x*x/Q(5)+x/Q(3)
def gelu(x):return x*(1+math.erf(x/math.sqrt(2)))/2
def init(x,y):return Q(3,10)*x-Q(1,5)*y+Q(1,30)
def update(x,y):return Q(2,5)*x+Q(1,4)*y-Q(1,40)
class Owner:
    channels=1
    def __init__(self,activation):self.nonlinear=activation;self.init_rows=[];self.round_rows=[]
    def initialize(self,t):
        self.init_rows.append(t.shape[0]);return T([init(*t.v[i:i+2]) for i in range(0,len(t.v),2)],(t.shape[0],1))
    def cell(self,t):
        self.round_rows.append(t.shape[0]);return T([update(*t.v[i:i+2]) for i in range(0,len(t.v),2)],(t.shape[0],1))
    def activation(self,t):return T([self.nonlinear(x) for x in t.v],t.shape)
def graph(ids):
    points,fm,mc=ids;fine=set(points)
    # Keyed original-ID edges, not production local-index/bucket metadata.
    edges={((0,f),(1,fm[f])) for f in fine}|{((1,fm[f]),(2,mc[fm[f]])) for f in fine}
    edges=sorted(edges);adj={e:{d for d in edges if d!=e and set(d)&set(e)} for e in edges}
    remaining=set(edges);components=[]
    while remaining:
        start=min(remaining);seen={start};todo=[start]
        for e in todo:
            for d in adj[e]:
                if d not in seen:seen.add(d);todo.append(d)
        remaining-=seen;diameter=0
        # All-pairs line-graph BFS, not production's two tree sweeps minus1.
        for start in seen:
            distances={start:0};todo=[start]
            for e in todo:
                for d in adj[e]:
                    if d not in distances:distances[d]=distances[e]+1;todo.append(d)
            diameter=max(diameter,max(distances.values()))
        components.append((seen,diameter))
    return edges,adj,components
def oracle(ids,values,widths,activation):
    edges,adj,components=graph(ids)
    state={e:activation(init(values[e[0][0]][e[0][1]],values[e[1][0]][e[1][1]])) for e in edges};active_rounds=[]
    for r in range(max((d for nodes,d in components),default=0)):
        active=set().union(*(nodes for nodes,d in components if r<d));old=dict(state)
        state.update({e:activation(update(old[e],sum((old[d] for d in sorted(adj[e])),Q(0))/len(adj[e]))) for e in active});active_rounds.append(active)
    output=[[Q(0)]*n for n in widths]
    for node in {v for e in edges for v in e}:
        incident=[e for e in edges if node in e];output[node[0]][node[1]]=sum((state[e] for e in incident),Q(0))/len(incident)
    return output,edges,adj,components,active_rounds
original_mean=ns['mean_adjacent_edge_states']
def observed_mean(old,rp):
    before=list(old.v);out=original_mean(old,rp);mean_calls.append((old,before,rp,out));return out
ns['mean_adjacent_edge_states']=observed_mean
records=[]
def run(batch_ids,widths,label,activation=phi):
    mean_calls.clear();owner=Owner(activation)
    values=[[[Q(2*i+3*l-4+5*b,23) for i in range(k)] for l,k in enumerate(widths)] for b in range(len(batch_ids))]
    levels=[T([[[x] for x in values[b][l]] for b in range(len(batch_ids))]) if batch_ids else T([],(0,k,1)) for l,k in enumerate(widths)]
    memberships=[[T(ids[l]) for ids in batch_ids] for l in range(3)]
    actual=ns['forward'](owner,levels,memberships);wanted=[oracle(ids,values[b],widths,activation) for b,ids in enumerate(batch_ids)]
    plans=[ns['build_edge_line_graph_plan'](*ids,widths) for ids in batch_ids]
    keys=[(b,e) for b,w in enumerate(wanted) for e in w[1]]
    for l,k in enumerate(widths):
        ck(actual[l].shape==(len(batch_ids),k,1),label+': original bank shapes')
        ck(actual[l].v==[x for w in wanted for x in w[0][l]],label+': direct original-ID oracle exact output')
    expected=[]
    for r in range(max((len(w[4]) for w in wanted),default=0)):
        expected.append({(b,e) for b,w in enumerate(wanted) if r<len(w[4]) for e in w[4][r]})
    ck(owner.init_rows==([len(keys)] if keys else []),label+': exactly one actual global initialization')
    ck(owner.round_rows==[len(x) for x in expected] and len(mean_calls)==len(expected),label+': exact active line-diameter rounds and finished freeze')
    for r,(old,before,rp,out) in enumerate(mean_calls):
        ck(old.v==before,label+': functional OLD carrier never overwritten')
        actual_keys=[keys[i] for i in rp['receivers']]
        ck(set(actual_keys)==expected[r] and len(set(actual_keys))==len(actual_keys),label+': active receiver identities unique scene-local')
        donors=[[] for _ in actual_keys]
        for bucket in rp['endpoint_buckets']:
            degree=bucket['degree']
            for start in range(0,len(bucket['edges']),degree):
                group=bucket['edges'][start:start+degree]
                for j,e in enumerate(group):donors[bucket['receiver_rows'][start+j]].extend(d for d in group if d!=e)
        ck(all(set(keys[i] for i in donors[j])=={(b,d) for d in wanted[b][2][e]} and len(donors[j])==rp['counts'][j]==len(wanted[b][2][e]) for j,(b,e) in enumerate(actual_keys)),label+': each OTHER endpoint-neighbor edge once and true combined degree, no own/cross-scene')
    for b,(plan,w) in enumerate(zip(plans,wanted)):
        actual_edges=[tuple(plan['node_keys'][i] for i in e) for e in plan['edges']]
        ck(actual_edges==w[1],label+': true support deduplicated, endpoint child-parent identity')
        actual_comp={frozenset(actual_edges[i] for i in c['edges']):c['line_diameter'] for c in plan['components']}
        ck(actual_comp=={frozenset(es):d for es,d in w[3]},label+': treeD-minus1 equals independent all-pairs line diameter')
    records.append({'label':label,'batch':len(batch_ids),'edge_initialization_rows':owner.init_rows,'actual_update_rows':owner.round_rows,'numeric_carrier':'exact Fraction polynomial nonlinear' if activation is phi else 'scalar erf-GELU, software only'})
    return [list(x.v) for x in actual],values
chain=([2,2],[0,0,3],[0,0,0,1]);branch=([0,0,2,5],[1,0,1,2,0,4],[0,2,0,0,2]);mixed=([0,1,3,5,7],[0,0,0,2,0,4,0,4],[0,0,1,0,1])
run([chain],(6,5,4),'single sparse true chain')
run([branch],(6,5,4),'unequal endpoint degrees Dline3')
run([mixed],(8,5,4),'mixed Dline1 and3 components')
run([([],[],[]),mixed,branch],(8,5,4),'three scenes including empty and unequal components')
run([([],[],[])],(8,5,4),'all empty support')
run([],(8,5,4),'zero batch')
run([chain],(6,5,4),'single chain actual scalar erf-GELU',gelu)
before,_=run([branch],(6,5,4),'multiplicity reference');dedup=(list(reversed(sorted(set(branch[0])))),branch[1],branch[2]);after,_=run([dedup],(6,5,4),'point support duplicate/order control')
ck(before==after,'point occurrence count/order does not reweight edge topology')
bad=[([-1],[],[],(2,2,2)),([True],[0],[0],(2,2,2)),([1],[0],[0],(2,2,2)),([0],[1],[0],(2,2,2)),([0],[0],[2],(2,2,2)),([],[],[],(2,True,2)),([0],[0.],[0],(2,2,2))]
for args in bad:
    try:ns['build_edge_line_graph_plan'](*args)
    except ValueError:checks.append('invalid original-ID metadata rejected')
    else:raise AssertionError('invalid original-ID metadata accepted')
proof={'status':'ACTUAL_ELC_PRODUCTION_PLAN_ROUNDS_MEANS_FORWARD_AST_STDLIB_CHECKED_NOT_TORCH','helper_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'actual_checks':len(checks),'cases':records,'invalid_cases':len(bad),'only_reused_container_definitions':str(carrier.relative_to(ROOT)),'old_suite_bodies_executed':False,'scope':'Actual production function/forward AST with transparent fresh-return list carriers. Independent keyed edge graph/all-pairs line BFS, dict OLD-state barriers and direct OTHER-edge/incident means. Exact rational polynomial cases separate topology/arithmetic from FP association; one true chain uses scalar erf-GELU. No real Torch/nn modules/Tensor descriptors/FP32/autograd/backward/native/resource/model constructor, root/Git/SSH/GPU/shared action, or future numerical/coverage gate.'}
if __name__=='__main__':print(json.dumps(proof,indent=2,allow_nan=False))
