"""Independent pure-stdlib AEF source topology and symbolic-call checks.
No torch/tensor library, model execution, gradients, GPU, or resource measurement.
"""
import argparse,ast,copy,hashlib,itertools,json,math,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
SUFFIX='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aef'
REL='framework/model/Quard_model/'+SUFFIX+'/middle_flux.py'
SOURCE=HERE.parent/'new_candidate_prepare/staged_repository'/REL

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(a,b,sign=1):
    out=Counter(a)
    for k,v in b.items():out[k]+=sign*v
    return Counter({k:v for k,v in out.items() if v})
def frozen(c):return tuple(sorted(c.items(),key=lambda v:repr(v[0])))

class Metadata:
    def __init__(self,values,shape=None):
        self.values=copy.deepcopy(values);self.shape=tuple(shape) if shape is not None else (len(values),);self.ndim=len(self.shape)
    def numel(self):return math.prod(self.shape)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return copy.deepcopy(self.values)
class Index:
    def __init__(self,values):self.values=list(values)
class Carrier:
    """Shape plus exact formal-expression coefficients; not a numeric tensor."""
    def __init__(self,data,shape):
        self.shape=tuple(shape);self.ndim=len(self.shape);self.device='STDLIB_SYMBOLS_ONLY';self.data=[Counter(v) for v in data]
        assert len(self.data)==math.prod(self.shape)
    def new_zeros(self,shape):return Carrier([Counter() for _ in range(math.prod(shape))],shape)
    def reshape(self,*shape):
        if len(shape)==1 and isinstance(shape[0],tuple):shape=shape[0]
        assert math.prod(shape)==len(self.data)
        return Carrier(self.data,shape)
    def rows(self):
        assert self.ndim==2
        c=self.shape[1];return [self.data[i*c:(i+1)*c] for i in range(self.shape[0])]
    def index_select(self,dim,index):
        assert dim==0 and self.ndim==2
        rr=self.rows();chosen=[rr[i] for i in index.values]
        return Carrier([x for row in chosen for x in row],(len(chosen),self.shape[1]))
    def __getitem__(self,key):
        assert isinstance(key,slice) and self.ndim==2
        rr=self.rows()[key];return Carrier([x for row in rr for x in row],(len(rr),self.shape[1]))
    def __sub__(self,other):
        assert self.shape==other.shape
        return Carrier([add(a,b,-1) for a,b in zip(self.data,other.data)],self.shape)
    def __neg__(self):return Carrier([{k:-v for k,v in c.items()} for c in self.data],self.shape)
    def index_add(self,dim,index,source):
        assert dim==0 and self.ndim==source.ndim==2 and self.shape[1]==source.shape[1] and len(index.values)==source.shape[0]
        rr=self.rows();ss=source.rows()
        for i,row in zip(index.values,ss):rr[i]=[add(a,b) for a,b in zip(rr[i],row)]
        return Carrier([x for row in rr for x in row],self.shape)
def cat(values,dim):
    assert len(values)==2 and all(v.ndim==2 for v in values)
    a,b=values
    if dim==0:
        assert a.shape[1]==b.shape[1]
        return Carrier(a.data+b.data,(a.shape[0]+b.shape[0],a.shape[1]))
    assert dim==-1 and a.shape[0]==b.shape[0]
    rr=[ra+rb for ra,rb in zip(a.rows(),b.rows())]
    return Carrier([x for row in rr for x in row],(a.shape[0],a.shape[1]+b.shape[1]))
class Module:
    def __call__(self,*args):return self.forward(*args)
class Linear:
    def __init__(self,nin,nout):self.nin=nin;self.nout=nout;self.calls=[]
    def __call__(self,x):
        assert x.ndim==2 and x.shape[1]==self.nin
        keys=[tuple(frozen(v) for v in row) for row in x.rows()];self.calls.append(keys)
        return Carrier([Counter({('LINEAR',row,j):1}) for row in keys for j in range(self.nout)],(len(keys),self.nout))
class Activation:
    def __init__(self):self.calls=[]
    def __call__(self,x):
        self.calls.append(x.shape);out=[]
        for item in x.data:
            assert len(item)==1
            (key,value),=item.items();assert value==1 and key[0]=='LINEAR'
            out.append(Counter({('GELU',key[1],key[2]):1}))
        return Carrier(out,x.shape)

def all_edges(xyz,nodes):
    return [((sum((xyz[a][k]-xyz[b][k])**2 for k in range(3)),a,b),(a,b)) for a,b in itertools.combinations(nodes,2)]
def connected(nodes,edges):
    if not nodes:return True
    seen={nodes[0]}
    while True:
        new=seen|{v for a,b in edges for v in (a,b) if a in seen or b in seen}
        if new==seen:return seen==set(nodes)
        seen=new

def exhaustive_mst(xyz,parents,support):
    result=[]
    for parent in sorted(set(p for p,v in zip(parents,support) if v)):
        nodes=[i for i,(p,v) in enumerate(zip(parents,support)) if p==parent and v]
        candidates=all_edges(xyz,nodes);best=None
        for choice in itertools.combinations(candidates,max(0,len(nodes)-1)):
            edges=[e for _,e in choice]
            if not connected(nodes,edges):continue
            # All test coordinates are small integers: exact distance sum and
            # lexicographic edge-key tie-break, no floating error threshold.
            score=(sum(k[0] for k,_ in choice),tuple(sorted(k for k,_ in choice)))
            if best is None or score<best[0]:best=(score,edges)
        assert best is not None
        result.append({'parent_id':parent,'node_ids':nodes,'edges':sorted(best[1])})
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preparation-sha256',required=True);args=parser.parse_args()
    prep_path=HERE.parent/'new_candidate_prepare/preparation.json';assert sha(prep_path)==args.preparation_sha256
    prep=json.loads(prep_path.read_text(encoding='utf-8'));assert prep['source_files'][REL]==sha(SOURCE)
    events=[]
    def audit(event,arg):
        if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.fork','os.posix_spawn'):
            events.append(event);raise AssertionError('Network/process forbidden')
    sys.addaudithook(audit)
    tree=ast.parse(SOURCE.read_text(encoding='utf-8'));selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    assert {n.name for n in selected}=={'build_parent_mst','ParentAntisymmetricEdgeFlux'}
    namespace={'math':math,'torch':SimpleNamespace(tensor=lambda values,**kw:Index(values),cat=cat,long='NO_TORCH_LONG'),'nn':SimpleNamespace(Module=Module,Linear=Linear,GELU=Activation)}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(SOURCE),'exec'),namespace)
    plan=namespace['build_parent_mst'];cls=namespace['ParentAntisymmetricEdgeFlux'];checks=[]
    def yes(label,value):
        if not value:raise AssertionError(label)
        checks.append({'name':label,'result':'SOFTWARE_PROPERTY_CONFIRMED'})
    def rejected(label,call):
        try:call()
        except ValueError:checks.append({'name':label,'result':'INVALID_METADATA_REFUSED'})
        else:raise AssertionError(label)
    cases=[('empty',[],[],[]),('singleton',[(3,4,5)],[7],[True]),('zero_distance_distinct',[(0,0,0)]*2,[0,0],[True]*2),('line3',[(0,0,0),(1,0,0),(2,0,0)],[0]*3,[True]*3),('tied_triangle',[(0,0,0),(1,1,0),(1,0,1)],[0]*3,[True]*3),('tied_square',[(0,0,0),(1,0,0),(0,1,0),(1,1,0)],[0]*4,[True]*4),('all_coincident5',[(0,0,0)]*5,[0]*5,[True]*5),('parent_support_holes',[(i,0,0) for i in range(6)],[0,1,0,1,0,1],[True,True,False,True,True,False]),('two_parent_forest',[(0,0,0),(1,0,0),(1,1,0),(4,0,0),(5,0,0)],[7,7,2,2,2],[True]*5)]
    for name,xyz,pa,su in cases:
        actual=plan(xyz,pa,su);expected=exhaustive_mst(xyz,pa,su)
        groups=[dict(v,edges=sorted(map(tuple,v['edges']))) for v in actual['groups']]
        yes(name+'_actual_Prim_equals_independent_exhaustive_MST',groups==expected)
        yes(name+'_edge_list_original_ID_parent_support_consistent',sorted(map(tuple,actual['edges']))==sorted(e for g in expected for e in g['edges']))
    xyz=[(i%7,i//7,0) for i in range(64)];pa=[i%8 for i in range(64)];su=[True]*64
    full=plan(xyz,pa,su)
    yes('native64_metadata_only_eight_connected_parent_trees_56edges',len(full['groups'])==8 and len(full['edges'])==56 and all(connected(g['node_ids'],g['edges']) and len(g['edges'])==len(g['node_ids'])-1 for g in full['groups']))
    invalid=[('length',[],[0],[True]),('xyz_width',[(0,0)],[0],[True]),('nan_xyz',[(float('nan'),0,0)],[0],[True]),('infinite_xyz',[(0,float('inf'),0)],[0],[True]),('negative_parent',[(0,0,0)],[-1],[True]),('bool_parent',[(0,0,0)],[False],[True]),('nonbool_support',[(0,0,0)],[0],[1])]
    for name,x,p,s in invalid:rejected(name,lambda x=x,p=p,s=s:plan(x,p,s))
    forward_cases=[('all_unsupported',[[(0,0,0),(1,0,0)]],[[0,0]],[[False,False]],3),('singleton_plus_pad',[[(0,0,0)]],[[0]],[[True]],3),('degree2_line3',[[(0,0,0),(1,0,0),(2,0,0)]],[[0,0,0]],[[True]*3],4),('two_batches_parent_holes',[[(i,0,0) for i in range(5)],[(0,i,0) for i in range(3)]],[[0,0,0,1,1],[2,2,2]],[[True,True,True,False,True],[True]*3],6)]
    for name,xyz,pa,su,width in forward_cases:
        batch=len(xyz);channels=2
        features=Carrier([Counter({('INPUT',b,i,c):1}) for b in range(batch) for i in range(width) for c in range(channels)],(batch,width,channels));original=copy.deepcopy(features.data)
        model=cls(channels,64,8)
        output=model(features,[Metadata(v,(len(v),3)) for v in xyz],[Metadata(v) for v in pa],[Metadata(v) for v in su])
        expected=[Counter() for _ in features.data];edges=[]
        for b in range(batch):
            for group in exhaustive_mst(xyz[b],pa[b],su[b]):
                for i,j in group['edges']:
                    edges.append((b,i,j))
                    pair=tuple(frozen(features.data[(b*width+i)*channels+c]) for c in range(channels))+tuple(frozen(features.data[(b*width+j)*channels+c]) for c in range(channels))
                    reverse=pair[channels:]+pair[:channels]
                    for c in range(channels):
                        q=Counter({('GELU',pair,c):1,('GELU',reverse,c):-1})
                        expected[(b*width+i)*channels+c]=add(expected[(b*width+i)*channels+c],q)
                        expected[(b*width+j)*channels+c]=add(expected[(b*width+j)*channels+c],q,-1)
        yes(name+'_actual_forward_matches_dual_orientation_GELU_signed_incidence',output.data==expected and output.shape==features.shape)
        yes(name+'_original_feature_symbols_unchanged_no_recurrence',features.data==original)
        yes(name+'_shared_Linear_and_GELU_single_batched_2E_call',model.edge_map.calls==[] and model.activation.calls==[] if not edges else len(model.edge_map.calls)==len(model.activation.calls)==1 and len(model.edge_map.calls[0])==2*len(edges) and model.activation.calls[0]==(2*len(edges),channels))
        charges=[]
        for b in range(batch):
            for parent in sorted(set(pa[b])):
                nodes=[i for i,(p,v) in enumerate(zip(pa[b],su[b])) if p==parent and v]
                for c in range(channels):
                    charge=Counter()
                    for i in nodes:charge=add(charge,output.data[(b*width+i)*channels+c])
                    charges.append(charge)
        yes(name+'_exact_formal_unweighted_group_charge_zero_not_FP32',all(not q for q in charges))
    narrow=cls(2,64,8)
    rejected('native_width65_module_guard',lambda:narrow(Carrier([Counter()]*130,(1,65,2)),[],[],[]))
    rejected('native_parent8_module_guard',lambda:narrow(Carrier([Counter()]*2,(1,1,2)),[Metadata([(0,0,0)],(1,3))],[Metadata([8])],[Metadata([True])]))
    yes('Torch_never_imported',not any(k=='torch' or k.startswith('torch.') for k in sys.modules))
    yes('no_process_network_audit_events',events==[])
    assert sha(SOURCE)==prep['source_files'][REL]
    result={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'INDEPENDENT_AEF_STDLIB_PRODUCTION_TOPOLOGY_AND_SYMBOLIC_SOURCE_FLOW_CONFIRMED_NOT_NATIVE_PASS','candidate_id':'hierarchy-parent-antisymmetric-edge-flux','preparation':{'path':prep_path.relative_to(ROOT).as_posix(),'sha256':sha(prep_path)},'helper_source':{'path':SOURCE.relative_to(ROOT).as_posix(),'sha256':sha(SOURCE)},'test_source':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(__file__)},'checks':checks,'check_count':len(checks),'exhaustive_small_topology_cases':len(cases),'native64_geometry_metadata_case':1,'invalid_plan_cases':len(invalid),'production_forward_symbolic_cases':len(forward_cases),'native_module_capacity_refusals':2,'scope':'Actual production pure function and class forward AST executed only against independent stdlib metadata/formal-expression carriers. nn.Linear/GELU are opaque call-order symbols, not torch implementations. Small-n exhaustive spanning-tree oracle is separate from production Prim. No numerical tensor, native FP32, autodiff, optimizer, loss, resource or accuracy assertion. Algebraic charge check is exact symbolic cancellation, not a floating error tolerance.','Torch_imported':False,'subprocess_network_audit_events':events,'model_GPU_native_execution':False,'real_gradients_or_updates_measured':False,'native_TRAIN2':'NOT_RUN','resources':'NOT_RUN','material_concerns':[]}
    dest=HERE/'independent_software_validation.json'
    with dest.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'proof':str(dest),'sha256':sha(dest)}))
if __name__=='__main__':main()
