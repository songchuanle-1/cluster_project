"""Bounded independent NEC original-ID oracle; actual production AST, no Torch."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,json,math,hashlib,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'new_candidate_two'))
from author_guard import author_guard,sha,ROOT
MODEL=HERE/'new_candidate_one/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nec'
author_guard()
carrier=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare/static_check.py'
t=ast.parse(carrier.read_text(encoding='utf8'))
ns={'F':F,'math':math}
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name in ('T','Torch')],type_ignores=[]),'inert_carrier_classes','exec'),ns)
T,Torch=ns['T'],ns['Torch']
old_get=T.__getitem__
def get(self,item):
    if type(item) is not int:return old_get(self,item)
    n=math.prod(self.shape[1:]);return T(self.v[item*n:(item+1)*n],self.shape[1:])
def add(self,other):
    assert self.shape==other.shape;return T([a+b for a,b in zip(self.v,other.v)],self.shape)
def stack(values,dim=0):
    assert dim==0 and values and len({v.shape for v in values})==1
    return T([x for v in values for x in v.v],(len(values),)+values[0].shape)
T.__getitem__,T.__add__,Torch.stack=get,add,staticmethod(stack)
source=(MODEL/'node_edge_coupling.py').read_text(encoding='utf8');tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
cl=next(n for n in tree.body if isinstance(n,ast.ClassDef))
fw=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='forward');fw.name='actual_forward'
prod={'torch':Torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions+[fw],type_ignores=[])),'actual_NEC_forward_AST','exec'),prod)
checks=[]
def check(name,value):assert value,name;checks.append({'name':name,'passed':True})
class Cell:
    def __init__(self,kind):self.kind=kind;self.rows=[]
    def __call__(self,x):
        self.rows.append(x.shape[0]);assert x.shape[1]==2
        a,b,d=(2,3,11) if self.kind=='edge' else (5,7,17)
        bias=1 if self.kind=='edge' else 2
        return T([(a*x.v[2*i]+b*x.v[2*i+1]+bias)/d for i in range(x.shape[0])],(x.shape[0],1))
class Activation:
    def __init__(self):self.calls=0
    def __call__(self,x):self.calls+=1;return T([v*v for v in x.v],x.shape)

def reference(scene,values):
    points,fm,mc=scene;fine=sorted(set(points))
    nodes=set((0,i) for i in fine)|set((1,fm[i]) for i in fine)|set((2,mc[fm[i]]) for i in fine)
    edges=sorted({((0,i),(1,fm[i])) for i in fine}|{((1,fm[i]),(2,mc[fm[i]])) for i in fine})
    adj={v:[] for v in nodes};inc={v:[] for v in nodes}
    for e in edges:
        a,b=e;adj[a].append(b);adj[b].append(a);inc[a].append(e);inc[b].append(e)
    groups=[]
    for root in sorted(v for v in nodes if v[0]==2):
        component={root};pending=[root]
        for x in pending:
            for y in adj[x]:
                if y not in component:component.add(y);pending.append(y)
        diameter=0
        # All-source distances rather than author's two-BFS diameter method.
        for start in component:
            dist={start:0};q=[start]
            for x in q:
                for y in adj[x]:
                    if y not in dist:dist[y]=dist[x]+1;q.append(y)
            diameter=max(diameter,max(dist.values()))
        groups.append((component,[e for e in edges if e[0] in component],diameter))
    h={v:values[v[0]][v[1]] for v in nodes};state={e:F(0) for e in edges}
    for component,es,D in groups:
        for r in range(D):
            new_e={e:((2*state[e]+3*(h[e[0]]+h[e[1]])/2+1)/11)**2 for e in es}
            new_h={v:((5*h[v]+7*sum((new_e[e] for e in inc[v]),F(0))/len(inc[v])+2)/17)**2 for v in component}
            state.update(new_e);h.update(new_h)
    return h,groups,edges,inc

scenes=[([0],[0],[0]),([0,1,2],[0,0,0],[0]),
        ([0,1],[0,1],[0,0]),
        ([0,1,2],[0,1,2],[0,0,1]),
        ([0,0,2,4],[2,0,2,1,3],[1,0,2,1]),([],[],[])]
cases=[[scenes[0]],[scenes[1]],[scenes[2]],[scenes[3]],[scenes[5],scenes[4],scenes[0]],[scenes[5]],[]]
for case,batch in enumerate(cases):
    widths=[7,5,4];B=len(batch)
    values=[[[F(1+2*b+3*l+i,19) for i in range(k)] for b in range(B)] for l,k in enumerate(widths)]
    banks=[T(values[l],(B,widths[l],1)) for l in range(3)]
    ids=[[T(scene[l]) for scene in batch] for l in range(3)]
    ec,nc,act=Cell('edge'),Cell('node'),Activation()
    result=prod['actual_forward'](SimpleNamespace(channels=1,edge_cell=ec,node_cell=nc,activation=act),banks,ids)
    want=[[F(0)]*(B*k) for k in widths];groups=[]
    for b,scene in enumerate(batch):
        h,gs,edges,inc=reference(scene,[values[l][b] for l in range(3)])
        groups.extend(gs)
        for (l,i),v in h.items():want[l][b*widths[l]+i]=v
        plan=prod['build_node_edge_plan'](*scene,widths)
        observed={(tuple(plan['node_keys'][a]),tuple(plan['node_keys'][z])) for a,z in plan['edges']}
        assert observed==set(edges)
        assert sorted(x['diameter'] for x in plan['components'])==sorted(D for _,_,D in gs)
        assert all(len(plan['incident'][i])==len(inc[tuple(key)]) for i,key in enumerate(plan['node_keys']))
    D=max((d for _,_,d in groups),default=0)
    edge_rows=[sum(len(es) for _,es,d in groups if r<d) for r in range(D)]
    node_rows=[sum(len(vs) for vs,_,d in groups if r<d) for r in range(D)]
    check('actual_forward_original_ID_dual_state_oracle_%d'%case,all(x.v==want[l] for l,x in enumerate(result)))
    check('dynamic_D_active_rows_finished_both_carriers_%d'%case,ec.rows==edge_rows and nc.rows==node_rows and act.calls==2*D)
check('no_Torch_module_loaded','torch' not in sys.modules)
report={'status':'PASS_INDEPENDENT_METADATA_AND_FRACTION_CARRIER_ONLY','candidate_id':'hierarchy-node-edge-coupled-state-composition','recorded_at':datetime.now(timezone.utc).isoformat(),'producer_source':{'path':str((MODEL/'node_edge_coupling.py').relative_to(ROOT)).replace('\\','/'),'sha256':sha(MODEL/'node_edge_coupling.py')},'check_count':len(checks),'checks':checks,'actual_forward_cases':len(cases),'oracle':'Independent original-ID dictionary nodes/undirected edges, all-source BFS diameter, component-local Jacobi edge-then-node recurrence. Exact rational quadratic nonlinear substitute; distinct edge/node linear maps.','scope':'No Torch/GELU/autograd/native/resources, no new scientific or numerical gates. Does not execute author suite.','author':author_guard()}
target=HERE/'nec_independent_software.json';author_guard()
with target.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
author_guard();print(json.dumps({'report':str(target),'sha256':sha(target),'checks':len(checks)}))
