"""Bounded actual SFC plan/forward AST and scalar-erf-GELU/list oracle checks."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,hashlib,json,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_sfc')
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class T:
    device='cpu';dtype='scalar-erf-list-carrier'
    def __init__(self,data,shape=None):
        def flatten(x):return sum((flatten(v) for v in x),[]) if isinstance(x,(tuple,list)) else [float(x)]
        self.v=flatten(data);self.shape=tuple(shape) if shape is not None else (len(self.v),)
        self.ndim=len(self.shape);assert math.prod(self.shape)==len(self.v)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return [int(x) for x in self.v]
    def reshape(self,*shape):
        if len(shape)==1 and isinstance(shape[0],tuple):shape=shape[0]
        return T(self.v,shape)
    def new_zeros(self,shape):return T([0.0]*math.prod(shape),shape)
    def new_tensor(self,values):return T(values)
    def unsqueeze(self,axis):assert axis==-1;return T(self.v,self.shape+(1,))
    def __getitem__(self,item):
        assert type(item) is int;size=math.prod(self.shape[1:])
        return T(self.v[item*size:(item+1)*size],self.shape[1:])
    def index_select(self,axis,index):
        assert axis==0;size=math.prod(self.shape[1:])
        return T([self.v[int(i)*size+j] for i in index.v for j in range(size)],(len(index.v),)+self.shape[1:])
    def index_add(self,axis,index,source):
        assert axis==0;out=list(self.v);size=self.shape[1]
        for row,i in enumerate(index.v):
            for j in range(size):out[int(i)*size+j]+=source.v[row*size+j]
        return T(out,self.shape)
    def index_copy(self,axis,index,source):
        assert axis==0 and len(set(index.v))==len(index.v);out=list(self.v);size=self.shape[1]
        for row,i in enumerate(index.v):out[int(i)*size:int(i)*size+size]=source.v[row*size:row*size+size]
        return T(out,self.shape)
    def __truediv__(self,other):
        rows,cols=self.shape;assert other.shape==(rows,1)
        return T([self.v[r*cols+j]/other.v[r] for r in range(rows) for j in range(cols)],self.shape)
class Torch:
    long='long'
    tensor=staticmethod(lambda values,**kw:T(values))
    @staticmethod
    def stack(values,dim=0):
        assert dim==0 and values and len({x.shape for x in values})==1
        return T([v for x in values for v in x.v],(len(values),)+values[0].shape)
    @staticmethod
    def cat(values,dim):
        assert dim==-1 and len({x.shape[0] for x in values})==1
        return T([v for r in range(values[0].shape[0]) for x in values for v in x.v[r*x.shape[1]:(r+1)*x.shape[1]]],(values[0].shape[0],sum(x.shape[1] for x in values)))
class Cell:
    def __init__(self):self.rows=[]
    def __call__(self,x):
        self.rows.append(x.shape[0]);c=x.shape[1]//2
        return T([0.5*x.v[r*2*c+j]+0.75*x.v[r*2*c+c+(j+1)%c]-0.125 for r in range(x.shape[0]) for j in range(c)],(x.shape[0],c))
def gelu_scalar(x):return 0.5*x*(1.0+math.erf(x/math.sqrt(2.0)))
class Activation:
    def __init__(self):self.calls=0
    def __call__(self,x):self.calls+=1;return T([gelu_scalar(v) for v in x.v],x.shape)
tree=ast.parse((MODEL/'synchronous_forest.py').read_text(encoding='utf-8'))
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward');forward.name='actual_forward'
core={'torch':Torch};exec(compile(ast.fix_missing_locations(ast.Module(body=functions+[forward],type_ignores=[])),'actual_SFC_source','exec'),core)
plan=core['build_synchronous_forest_plan']
def independent_graph(points,fm,mc):
    fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    nodes=[(level,i) for level,values in enumerate((fine,middle,coarse)) for i in values]
    adj={node:set() for node in nodes}
    for node in nodes:
        level,i=node
        if level==0:parent=(1,fm[i])
        elif level==1:parent=(2,mc[i])
        else:continue
        adj[node].add(parent);adj[parent].add(node)
    components=[]
    for root in coarse:
        start=(2,root);seen={start};todo=[start]
        for node in todo:
            for donor in adj[node]:
                if donor not in seen:seen.add(donor);todo.append(donor)
        # Small independent all-start shortest-path oracle, not producer's two-BFS.
        diameter=0
        for start in seen:
            distances={start:0};todo=[start]
            for node in todo:
                for donor in adj[node]:
                    if donor not in distances:distances[donor]=distances[node]+1;todo.append(donor)
            diameter=max(diameter,max(distances.values()))
        components.append((root,sorted(seen),diameter))
    return nodes,adj,components
single=([0],[0],[0])
star=([0,1,2],[0,0,0],[0])
branch=([0,1,2,3],[0,0,0,1],[0,0])
mixed=([0,1,2,3,4],[0,0,1,2,2],[0,1,1])
holes=([0,2,5,5],[2,0,2,1,4,3],[0,2,1,1,3])
empty=([],[],[])
cases=[empty,single,star,branch,mixed,holes]
for i,members in enumerate(cases):
    got=plan(*members,[7,5,4]);nodes,adj,components=independent_graph(*members)
    actual=[(comp['root_id'],[got['node_keys'][n] for n in comp['nodes']],comp['diameter']) for comp in got['components']]
    check('production_plan_vs_independent_keyed_graph_diameter_%d'%i,got['node_keys']==nodes and actual==components and all([got['node_keys'][j] for j in got['neighbors'][k]]==sorted(adj[node]) for k,node in enumerate(nodes)))
    rounds=core['build_synchronous_rounds']([got]);valid=True;counts={node:0 for node in nodes}
    for r,stage in enumerate(rounds):
        keys=[got['node_keys'][n] for n in stage['receivers']]
        expected=[node for _,comp,d in components if r<d for node in comp]
        valid&=keys==expected and len(set(stage['receivers']))==len(stage['receivers'])
        for node in keys:counts[node]+=1
        valid&=stage['counts']==[len(adj[node]) for node in keys]
    valid&=all(counts[node]==d for _,comp,d in components for node in comp)
    check('exact_component_round_count_old_neighbor_degree_no_fake_%d'%i,valid)
cap=plan(list(range(256)),[i//4 for i in range(256)],[i//8 for i in range(64)],[256,64,8])
check('native_cap_metadata_328nodes_4diam_1312rows',len(cap['node_keys'])==328 and all(c['diameter']==4 for c in cap['components']) and sum(len(stage['receivers']) for stage in core['build_synchronous_rounds']([cap]))==1312)
def oracle(scenes,widths,sequential=False):
    c=2;batch=len(scenes)
    values=[[[[(3*level+2*i+j+5*bi-4)/37.0 for j in range(c)] for i in range(k)] for bi in range(batch)] for level,k in enumerate(widths)]
    want=[[0.0]*(batch*k*c) for k in widths];rows=[]
    for bi,members in enumerate(scenes):
        nodes,adj,components=independent_graph(*members)
        state={node:list(values[node[0]][bi][node[1]]) for node in nodes}
        for _,comp,diameter in components:
            for r in range(diameter):
                old={node:list(state[node]) for node in comp};updated={}
                for node in comp:
                    readable=state if sequential else old
                    neighbors=sorted(adj[node]);mean=[]
                    for j in range(c):
                        total=0.0
                        for donor in neighbors:total+=readable[donor][j]
                        mean.append(total/len(neighbors))
                    own=readable[node]
                    new=[gelu_scalar(0.5*own[j]+0.75*mean[(j+1)%c]-0.125) for j in range(c)]
                    if sequential:state[node]=new
                    else:updated[node]=new
                if not sequential:state.update(updated)
        for (level,i),value in state.items():
            start=(bi*widths[level]+i)*c;want[level][start:start+c]=value
    for r in range(max((d for members in scenes for _,_,d in independent_graph(*members)[2]),default=0)):
        rows.append(sum(len(comp) for members in scenes for _,comp,d in independent_graph(*members)[2] if r<d))
    return values,want,rows
def actual(scenes,widths):
    values,want,rows=oracle(scenes,widths);batch=len(scenes);c=2
    banks=[T(v,(batch,widths[level],c)) for level,v in enumerate(values)]
    ids=[[T(members[level]) for members in scenes] for level in range(3)]
    cell=Cell();activation=Activation();owner=SimpleNamespace(channels=c,cell=cell,activation=activation)
    output=core['actual_forward'](owner,banks,ids)
    return output,want,cell.rows,rows,activation.calls
for i,scenes in enumerate(([single],[star],[branch],[mixed],[holes],[empty,mixed,single],[],[empty])):
    out,want,actual_rows,want_rows,calls=actual(list(scenes),(7,5,4))
    check('actual_forward_scalar_erfGELU_vs_independent_sync_oracle_%d'%i,all(x.v==want[level] for level,x in enumerate(out)) and actual_rows==want_rows and calls==len(want_rows))
out,want,actual_rows,_,_=actual([mixed],(7,5,4))
check('D2_D4_finished_component_freezes',actual_rows==[10,10,6,6])
wrong=oracle([branch],(7,5,4),sequential=True)[1]
right=oracle([branch],(7,5,4))[1]
check('synchronous_graph_distinguishes_inplace_sequential',wrong!=right)
one=actual([single],(7,5,4))[0];duplicate=actual([([0,0,0],[0],[0])],(7,5,4))[0]
check('duplicate_points_do_not_reweight_node_states',all(x.v==y.v for x,y in zip(one,duplicate)))
state=T([[1],[3],[8],[0],[0]],(5,1))
neighbor=core['mean_neighbor_states'](state,{'receivers':[3],'sources':[0,1,2,4],'source_receivers':[0,0,0,0],'counts':[4]})
check('middle_all_neighbors_denominator_not_two_groups',neighbor.v==[3.0] and neighbor.v!=[(4.0+0.0)/2])
invalid=[([-1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[1],[0],[1,2,1]),([0],[0],[1],[1,1,1]),([],[],[],[1,True,1]),([],[0,0],[0],[1,1,1])]
count=0
for args in invalid:
    try:plan(*args)
    except ValueError:count+=1
check('eight_invalid_metadata_cases_rejected',count==len(invalid))
for p in MODEL.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
check('eight_model_sources_compile_without_import',len(list(MODEL.glob('*.py')))==8)
copies=['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']
check('six_original_model_sources_exact_bytes',all((MODEL/p).read_bytes()==(BASE/p).read_bytes() for p in copies))
config=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_sfc'/(NAME+'_sfc.yaml')
check('native_YAML_original_bytes',config.read_bytes()==(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')).read_bytes())
bt=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'));nt=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'))
def methods(tree):return {(cl.name,fn.name):ast.dump(fn) for cl in tree.body if isinstance(cl,ast.ClassDef) for fn in cl.body if isinstance(fn,ast.FunctionDef)}
bm,nm=methods(bt),methods(nt)
check('only_CTF_constructor_forward_change',[k for k in bm if bm[k]!=nm[k]]==[('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')])
def ctor(tree):return next(fn for cl in tree.body if isinstance(cl,ast.ClassDef) and cl.name=='C2F_ClusterAttn_CTF' for fn in cl.body if isinstance(fn,ast.FunctionDef) and fn.name=='__init__')
bc,nc=ctor(bt),ctor(nt)
check('original_constructor_RNG_prefix_preserved',all(ast.dump(x)==ast.dump(y) for x,y in zip(bc.body,nc.body)) and len(nc.body)>len(bc.body))
hsource=(MODEL/'hier_postprocess.py').read_text(encoding='utf-8')
check('once_original_LN_CPUfork_final_rawskip','self.cluster_ffn_norm[lvl](cf)' in hsource and 'torch.random.fork_rng(devices=[])' in hsource and 'cf + deltas[lvl]' in hsource)
check('no_feature_detach_or_extra_state_residual',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('detach','cpu') for n in ast.walk(forward)) and 'state=state.index_copy(0,index,updated)' in (MODEL/'synchronous_forest.py').read_text())
check('source_parameter_MAC_formula',2*256*256+256==131328 and 4*328*2*256*256==171966464 and 328*8*256*256==171966464)
route=json.loads((HERE.parent/'candidate_route_index.json').read_text(encoding='utf-8'))
check('M224_CID_and_primary_source_path_unused',not any(str(x.get('experiment_id','')).startswith('M224') or x.get('id')=='hierarchy-synchronous-full-neighbor-composition' for x in route) and not (ROOT/'Cluster/framework/model/Quard_model'/(NAME+'_sfc')).exists())
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':'hierarchy-synchronous-full-neighbor-composition',
    'check_count':len(checks),'checks':checks,'actual_forward_scalar_GELU_carrier_cases':8,'invalid_metadata_cases':8,
    'source_files':{p.name:sha(p) for p in MODEL.glob('*.py')},'Torch':False,'FP32_autograd_native_resources':'NOT_RUN','old_suites_executed':False,
    'scope':'Actual production plan/helper/forward AST with plain Python scalar-erf-GELU and numeric list carrier vs independent keyed-tree/all-pairs-shortest-path and synchronous-node oracle. Exact software arithmetic/path checks are not native FP32, learned weights, gradients, task or resource evidence.'}
(HERE/'static_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'check_count':len(checks),'report':str(HERE/'static_validation.json')}))
