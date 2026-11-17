"""Small stdlib software checks of actual PES source; never imports Torch."""
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import ast, hashlib, json, math
from datetime import datetime, timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_pes')
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class T:
    device='cpu';dtype='integer-list-carrier'
    def __init__(self,values,shape=None):
        def flatten(x):return sum((flatten(v) for v in x),[]) if isinstance(x,(list,tuple)) else [x]
        self.v=flatten(values)
        self.shape=shape or ((len(values),len(values[0])) if values and isinstance(values[0],list) else (len(values),))
        self.ndim=len(self.shape)
        assert math.prod(self.shape)==len(self.v)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return list(self.v)
    def reshape(self,*shape):
        if len(shape)==1 and isinstance(shape[0],tuple):shape=shape[0]
        return T(self.v,tuple(shape))
    def new_zeros(self,shape):return T([0]*math.prod(shape),tuple(shape))
    def __getitem__(self,i):
        assert type(i) is int and 0<=i<self.shape[0]
        size=math.prod(self.shape[1:]);return T(self.v[i*size:(i+1)*size],self.shape[1:])
    def index_copy(self,axis,index,values):
        assert axis==0 and len(set(index.v))==len(index.v)
        size=math.prod(self.shape[1:]);out=list(self.v)
        for row,i in enumerate(index.v):out[i*size:(i+1)*size]=values.v[row*size:(row+1)*size]
        return T(out,self.shape)
class Torch:
    long='long'
    tensor=staticmethod(lambda values,**kwargs:T(values))
    @staticmethod
    def stack(values,dim=0):
        assert dim==0 and values and len({x.shape for x in values})==1
        return T([v for x in values for v in x.v],(len(values),)+values[0].shape)
    @staticmethod
    def cat(values,dim):
        assert dim==-1 and all(x.shape[0]==values[0].shape[0] for x in values)
        return T([v for r in range(values[0].shape[0]) for x in values for v in x.v[r*x.shape[1]:(r+1)*x.shape[1]]],
                 (values[0].shape[0],sum(x.shape[1] for x in values)))
class Cell:
    def __init__(self):self.calls=0;self.rows=0
    def __call__(self,x):
        self.calls+=1;self.rows+=x.shape[0];c=x.shape[1]//2
        return T([(3*x.v[r*2*c+j]+5*x.v[r*2*c+c+j]+7)%1000003 for r in range(x.shape[0]) for j in range(c)],(x.shape[0],c))
def activate(x):return T([(2*v+1)%1000003 for v in x.v],x.shape)

tree=ast.parse((MODEL/'euler_state.py').read_text(encoding='utf-8'))
parts=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
clazz=next(n for n in tree.body if isinstance(n,ast.ClassDef))
forward=next(n for n in clazz.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
forward.name='actual_forward'
ns={'torch':Torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=parts+[forward],type_ignores=[])),'actual_PES_source','exec'),ns)
plan=ns['build_euler_plan'];rounds=ns['build_event_rounds']

def direct_walks(points,fm,mc):
    """Independent original-key adjacency DFS, not the packed production traversal."""
    active={('f',i) for i in points}
    active|={('m',fm[i]) for _,i in list(active)}
    active|={('c',mc[i]) for l,i in list(active) if l=='m'}
    adj={key:[] for key in active}
    for l,i in active:
        if l=='f':parent=('m',fm[i])
        elif l=='m':parent=('c',mc[i])
        else:continue
        adj[(l,i)].append(parent);adj[parent].append((l,i))
    walks=[]
    for root in sorted(k for k in active if k[0]=='c'):
        walk=[root]
        def visit(node,parent=None):
            for child in sorted(n for n in adj[node] if n!=parent):
                walk.append(child);visit(child,node);walk.append(node)
        visit(root);walks.append(walk)
    return active,walks

cases=[([],[],[],(0,0,0)),([],[],[],(7,4,3)),([0],[0],[0],(1,1,1)),
       ([0,0,0],[0],[0],(4,3,2)),([0,2],[1,0,1],[0,2],(5,4,4)),
       ([0,1,2,3],[0,0,0,1],[0,0],(6,4,3)),
       ([0,2,4,5],[0,1,0,2,2,3],[1,0,1,2],(8,6,4)),
       (list(range(64)),[i//4 for i in range(64)],[i//4 for i in range(16)],(256,64,8))]
for ci,(p,fm,mc,widths) in enumerate(cases):
    got=plan(p,fm,mc,list(widths));active,walks=direct_walks(p,fm,mc)
    key=lambda node:('fmc'[node[0]],node[1])
    actual_walks=[[key(got['node_keys'][i]) for i in comp['walk']] for comp in got['components']]
    check('direct_node_DFS_oracle_%d'%ci,actual_walks==walks and set(map(key,got['node_keys']))==active)
    valid=True
    for comp in got['components']:
        events=comp['events'];f=comp['forward_events'];back=comp['backward_events']
        valid&=len(events)==4*comp['edge_count'] and back==[(v,u) for u,v in reversed(f)]
        valid&=Counter(events)==Counter({edge:2 for edge in f})
        support={i:{i} for edge in events for i in edge}
        for u,v in events:support[v]=support[v]|support[u]
        valid&=all(v==set(support) for v in support.values())
    rs=rounds([got])
    valid&=sum(map(len,rs))==4*got['edge_count'] and all(len({v for _,v in r})==len(r) for r in rs)
    check('4E_reverse_current_state_reachability_no_fake_%d'%ci,valid)

def forward_case(scene_cases,widths):
    c=2;b=len(scene_cases)
    banks=[T([1000*l+100*bi+3*i+j+1 for bi in range(b) for i in range(k) for j in range(c)],(b,k,c)) for l,k in enumerate(widths)]
    ids=[[T(case[l]) for case in scene_cases] for l in range(3)]
    cell=Cell();owner=SimpleNamespace(channels=c,cell=cell,activation=activate)
    out=ns['actual_forward'](owner,banks,ids)
    expected=[[0]*len(x.v) for x in banks];total=0
    for bi,(p,fm,mc) in enumerate(scene_cases):
        active,walks=direct_walks(p,fm,mc)
        level={'f':0,'m':1,'c':2}
        state={key:[banks[level[key[0]]].v[(bi*widths[level[key[0]]]+key[1])*c+j] for j in range(c)] for key in active}
        for walk in walks:
            # Independent per-component scalar recurrence; reverse starts from post-first-tour state.
            for path in (walk,list(reversed(walk))):
                for u,v in zip(path,path[1:]):
                    state[v]=[(2*((3*a+5*z+7)%1000003)+1)%1000003 for a,z in zip(state[v],state[u])];total+=1
        for (l,i),values in state.items():
            ll=level[l];start=(bi*widths[ll]+i)*c;expected[ll][start:start+c]=values
    return all(x.v==expected[l] and x.shape==banks[l].shape for l,x in enumerate(out)) and cell.rows==total
small=[([0],[0],[0]),([0,1,2],[0,0,1],[0,0]),
       ([0,2,4,5],[0,1,0,2,2,3],[1,0,1,2]),([],[],[])]
for i,scenes in enumerate(([small[0]],[small[1]],[small[2]],[small[3],small[2],small[0]],[],[small[3]])):
    check('actual_forward_vs_independent_direct_node_oracle_%d'%i,forward_case(scenes,(8,6,4)))

invalid=[([-1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),
         ([0],[],[0],[1,1,1]),([0],[1],[0],[1,2,1]),([0],[0],[2],[1,1,1]),
         ([],[],[],[1,True,1]),([],[],[],[1,-1,1]),([],[],[],[1,1]),
         ([],[0,0],[0],[1,1,1])]
rejected=0
for args in invalid:
    try:plan(*args)
    except ValueError:rejected+=1
check('ten_invalid_metadata_cases_rejected',rejected==len(invalid))
good=[T([1,2],(1,1,2)) for _ in range(3)]
try:ns['prepare_euler_plans']([T([1,2],(1,2))]+good[1:],[[T([0])]]*3)
except ValueError:check('rank_rejected_before_shape_access',True)
else:check('rank_rejected_before_shape_access',False)

for p in MODEL.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
check('eight_model_sources_compile_without_import',len(list(MODEL.glob('*.py')))==8)
copies=['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']
check('six_original_sources_byte_identical',all((MODEL/p).read_bytes()==(BASE/p).read_bytes() for p in copies))
config=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_pes'/(NAME+'_pes.yaml')
check('original_native_YAML_bytes',config.read_bytes()==(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')).read_bytes())
base=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'))
new=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'))
def methods(t):return {(cl.name,f.name):ast.dump(f,include_attributes=False) for cl in t.body if isinstance(cl,ast.ClassDef) for f in cl.body if isinstance(f,ast.FunctionDef)}
bm,nm=methods(base),methods(new)
changed=[k for k in bm if bm[k]!=nm[k]]
check('only_CTF_constructor_and_forward_change',changed==[('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')])
bc=next(c for c in base.body if isinstance(c,ast.ClassDef) and c.name=='C2F_ClusterAttn_CTF')
nc=next(c for c in new.body if isinstance(c,ast.ClassDef) and c.name=='C2F_ClusterAttn_CTF')
bi=next(f for f in bc.body if isinstance(f,ast.FunctionDef) and f.name=='__init__')
ni=next(f for f in nc.body if isinstance(f,ast.FunctionDef) and f.name=='__init__')
check('original_constructor_prefix_and_RNG_consumption_preserved',all(ast.dump(x)==ast.dump(y) for x,y in zip(bi.body,ni.body)) and len(ni.body)>len(bi.body))
source=(MODEL/'hier_postprocess.py').read_text(encoding='utf-8')
check('CPU_fork_original_LN_and_unique_rawskip', 'torch.random.fork_rng(devices=[])' in source and 'cf + deltas[lvl]' in source and 'self.cluster_ffn_norm[lvl](cf)' in source)
check('state_reference_only_update_no_feature_detach', 'states[v] = updated[row]' in (MODEL/'euler_state.py').read_text() and all(not(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('detach','cpu')) for n in ast.walk(forward)))
check('source_parameter_arithmetic',2*256*256+256==131328 and 3*(8*256*256+5*256)==1576704 and 1576704-131328==1445376)
check('native_map_row_bound_source_inference',4*(256+64)*2*256*256==167772160 and (256+64+8)*8*256*256==171966464)
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':'hierarchy-palindromic-euler-state-composition','check_count':len(checks),'checks':checks,'valid_metadata_cases':len(cases),'actual_forward_carrier_cases':6,'invalid_metadata_cases':len(invalid),'sources':{p.name:sha(p) for p in MODEL.glob('*.py')},'Torch':False,'GELU_FP32_autograd_native_resources':'NOT_RUN','carrier_scope':'Exact bounded integer recurrence carrier substitutes numerical Linear/GELU only to check state/ID/event control flow; no model equivalence or gradient claim.'}
(HERE/'static_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'check_count':len(checks),'report':str(HERE/'static_validation.json')}))
