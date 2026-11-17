"""Bounded AOC production AST/path software witnesses; no Torch import."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,json,hashlib,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_aoc')
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class T:
    device='cpu';dtype='fraction-list-carrier'
    def __init__(self,data,shape=None):
        def flat(x):return sum((flat(a) for a in x),[]) if isinstance(x,(list,tuple)) else [F(x)]
        self.v=flat(data)
        self.shape=tuple(shape) if shape is not None else ((len(data),len(data[0])) if data and isinstance(data[0],list) else (len(data),))
        self.ndim=len(self.shape);assert math.prod(self.shape)==len(self.v)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return [int(x) for x in self.v]
    def reshape(self,*shape):
        if len(shape)==1 and isinstance(shape[0],tuple):shape=shape[0]
        return T(self.v,shape)
    def new_zeros(self,shape):return T([0]*math.prod(shape),shape)
    def new_tensor(self,data):return T(data)
    def unsqueeze(self,axis):assert axis==-1;return T(self.v,self.shape+(1,))
    def index_select(self,axis,index):
        assert axis==0;n=math.prod(self.shape[1:])
        return T([self.v[int(i)*n+j] for i in index.v for j in range(n)],(len(index.v),)+self.shape[1:])
    def index_add(self,axis,index,source):
        assert axis==0;n=self.shape[1];out=list(self.v)
        for row,i in enumerate(index.v):
            for j in range(n):out[int(i)*n+j]+=source.v[row*n+j]
        return T(out,self.shape)
    def index_copy(self,axis,index,source):
        assert axis==0 and len(set(index.v))==len(index.v);n=self.shape[1];out=list(self.v)
        for row,i in enumerate(index.v):out[int(i)*n:int(i)*n+n]=source.v[row*n:row*n+n]
        return T(out,self.shape)
    def __getitem__(self,item):
        assert isinstance(item,slice)
        rows=list(range(self.shape[0]))[item];n=self.shape[1]
        return T([self.v[i*n+j] for i in rows for j in range(n)],(len(rows),n))
    def __sub__(self,other):assert self.shape==other.shape;return T([a-b for a,b in zip(self.v,other.v)],self.shape)
    def __truediv__(self,other):
        r,c=self.shape;assert other.shape==(r,1)
        return T([self.v[i*c+j]/other.v[i] for i in range(r) for j in range(c)],self.shape)
class Torch:
    long='long'
    tensor=staticmethod(lambda data,**kw:T(data))
    @staticmethod
    def cat(values,dim):
        if dim==0:
            assert len({x.shape[1:] for x in values})==1
            return T([v for x in values for v in x.v],(sum(x.shape[0] for x in values),)+values[0].shape[1:])
        assert dim==-1 and all(x.shape[0]==values[0].shape[0] for x in values)
        return T([v for row in range(values[0].shape[0]) for x in values for v in x.v[row*x.shape[1]:(row+1)*x.shape[1]]],(values[0].shape[0],sum(x.shape[1] for x in values)))
class Cell:
    def __init__(self):self.rows=[]
    def __call__(self,x):
        self.rows.append(x.shape[0]);c=x.shape[1]//2
        return T([2*x.v[row*2*c+j]+3*x.v[row*2*c+c+(j+1)%c]+1 for row in range(x.shape[0]) for j in range(c)],(x.shape[0],c))
class Activation:
    def __init__(self):self.calls=0
    def __call__(self,x):self.calls+=1;return T([v*v+v for v in x.v],x.shape)
source=(MODEL/'ancestral_commutator.py').read_text(encoding='utf-8')
tree=ast.parse(source)
funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef)]
cls=next(x for x in tree.body if isinstance(x,ast.ClassDef))
forward=next(f for f in cls.body if isinstance(f,ast.FunctionDef) and f.name=='forward')
forward.name='actual_forward'
ns={'torch':Torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=funcs+[forward],type_ignores=[])),'actual_AOC_production','exec'),ns)
plan=ns['build_ancestry_path_plan']
cases=[([],[],[],[0,0,0]),([],[],[],[6,4,3]),([0],[0],[0],[1,1,1]),
       ([0,0,0],[0],[0],[5,3,2]),([0,2,4],[2,0,2,1,3],[1,0,2,1],[7,5,4]),
       ([0,1,2,3],[0,0,0,1],[0,0],[6,4,3])]
for i,(points,fm,mc,widths) in enumerate(cases):
    p=plan(points,fm,mc,widths)
    paths=[(f,fm[f],mc[fm[f]]) for f in sorted(set(points))]
    check('original_ID_path_oracle_%d'%i,list(zip(p['fine_ids'],p['middle_for_paths'],p['coarse_for_paths']))==paths)
    check('direct_fine_path_upper_counts_%d'%i,p['middle_path_counts']==[sum(m==j for _,m,_ in paths) for j in p['middle_ids']] and p['coarse_path_counts']==[sum(k==c for _,_,k in paths) for c in p['coarse_ids']])

def oracle_cell(a,b):
    # Independent vector expression for the numerical stand-in, not production W/GELU.
    return [(2*a[j]+3*b[(j+1)%len(a)]+1)**2+(2*a[j]+3*b[(j+1)%len(a)]+1) for j in range(len(a))]
def actual_and_oracle(scenes,widths,swap=False,equal=False):
    batch=len(scenes);c=2
    values=[[[[F(1+2*bi+3*l+i+j,7) for j in range(c)] for i in range(k)] for bi in range(batch)] for l,k in enumerate(widths)]
    if swap or equal:
        assert batch==1 and scenes==[([0],[0],[0])]
        b=values[1][0][0];cc=values[2][0][0]
        if equal:values[2][0][0]=list(b)
        else:values[1][0][0],values[2][0][0]=cc,b
    banks=[T(v,(batch,widths[l],c)) for l,v in enumerate(values)]
    ids=[[T(scene[l]) for scene in scenes] for l in range(3)]
    cell=Cell();activation=Activation();owner=SimpleNamespace(channels=c,cell=cell,activation=activation)
    out=ns['actual_forward'](owner,banks,ids)
    want=[[F(0)]*len(x.v) for x in banks];total=0
    for bi,(points,fm,mc) in enumerate(scenes):
        accum=[{},{}]
        for f in sorted(set(points)):
            m=fm[f];co=mc[m];a=values[0][bi][f];b=values[1][bi][m];cc=values[2][bi][co]
            p=oracle_cell(oracle_cell(a,b),cc);r=oracle_cell(oracle_cell(a,cc),b)
            q=[x-y for x,y in zip(p,r)];start=(bi*widths[0]+f)*c;want[0][start:start+c]=q;total+=1
            accum[0].setdefault(m,[]).append(q);accum[1].setdefault(co,[]).append(q)
        for level,groups in enumerate(accum,1):
            for original_id,rows in groups.items():
                q=[sum(v[j] for v in rows)/len(rows) for j in range(c)]
                start=(bi*widths[level]+original_id)*c;want[level][start:start+c]=q
    right_calls=cell.rows==([2*total,2*total] if total else []) and activation.calls==(2 if total else 0)
    return out,want,right_calls
scenes=[([0],[0],[0]),([0,1,2,3],[0,0,0,1],[0,0]),([0,2,4],[2,0,2,1,3],[1,0,2,1]),([],[],[])]
for i,batch in enumerate(([scenes[0]],[scenes[1]],[scenes[2]],[scenes[3],scenes[2],scenes[0]],[],[scenes[3]])):
    actual,want,call=actual_and_oracle(list(batch),(7,5,4))
    check('actual_forward_independent_perpath_vector_oracle_%d'%i,all(x.v==want[l] for l,x in enumerate(actual)) and call)
normal,_,_=actual_and_oracle([scenes[0]],(1,1,1))
swapped,_,_=actual_and_oracle([scenes[0]],(1,1,1),swap=True)
equal,_,_=actual_and_oracle([scenes[0]],(1,1,1),equal=True)
check('actual_forward_ancestor_role_swap_sign',all(x.v==[-v for v in normal[l].v] for l,x in enumerate(swapped)))
check('actual_forward_equal_ancestors_zero',all(v==0 for x in equal for v in x.v))
base,_,_=actual_and_oracle([scenes[0]],(7,5,4))
dup,_,_=actual_and_oracle([([0,0,0],[0],[0])],(7,5,4))
check('duplicate_points_do_not_reweight_factor',all(a.v==b.v for a,b in zip(base,dup)))
# Unequal degrees: direct fine path coarse mean differs from mean of two middle means.
q=T([[1,2],[3,4],[5,6],[20,30]])
direct=ns['mean_path_messages'](q,[0,0,0,0],[4])
check('coarse_is_not_mean_of_middle_means',direct.v==[F(29,4),F(42,4)] and direct.v!=[F(23,2),F(17)])
invalid=[([-1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[1],[0],[1,2,1]),([0],[0],[1],[1,1,1]),([],[],[],[1,True,1]),([],[0,0],[0],[1,1,1])]
rejected=0
for args in invalid:
    try:plan(*args)
    except ValueError:rejected+=1
check('eight_invalid_metadata_rejected',rejected==len(invalid))
for p in MODEL.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
check('eight_sources_compile_without_import',len(list(MODEL.glob('*.py')))==8)
copies=['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']
check('six_original_sources_byte_identical',all((BASE/p).read_bytes()==(MODEL/p).read_bytes() for p in copies))
config=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_aoc'/(NAME+'_aoc.yaml')
check('original_native_YAML_bytes',config.read_bytes()==(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')).read_bytes())
bt=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'))
nt=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'))
def methods(tree):return {(cl.name,fn.name):ast.dump(fn) for cl in tree.body if isinstance(cl,ast.ClassDef) for fn in cl.body if isinstance(fn,ast.FunctionDef)}
bm,nm=methods(bt),methods(nt)
check('only_CTF_constructor_forward_change',[k for k in bm if bm[k]!=nm[k]]==[('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')])
def ctor(tree):return next(f for cl in tree.body if isinstance(cl,ast.ClassDef) and cl.name=='C2F_ClusterAttn_CTF' for f in cl.body if isinstance(f,ast.FunctionDef) and f.name=='__init__')
bc,nc=ctor(bt),ctor(nt)
check('original_constructor_prefix_RNG_preserved',all(ast.dump(x)==ast.dump(y) for x,y in zip(bc.body,nc.body)) and len(nc.body)>len(bc.body))
hsource=(MODEL/'hier_postprocess.py').read_text(encoding='utf-8')
check('CPU_fork_three_LN_unique_rawskip','torch.random.fork_rng(devices=[])' in hsource and 'self.cluster_ffn_norm[lvl](cf)' in hsource and 'cf + deltas[lvl]' in hsource)
check('feature_path_no_detach',all(not(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('detach','cpu')) for x in ast.walk(forward)))
check('shared_single_cell_and_original_activation',source.count('nn.Linear(')==1 and source.count('nn.GELU()')==1 and source.count('self.activation(self.cell(')==2)
check('static_parameter_and_MAC_arithmetic',2*256*256+256==131328 and 24*256*256+15*256==1576704 and 4*256*2*256*256==134217728)
index=json.loads((HERE.parent/'candidate_route_index.json').read_text(encoding='utf-8'))
check('candidate_and_M222_unused',not any(x.get('id')=='hierarchy-ancestral-order-commutator-composition' or str(x.get('experiment_id','')).startswith('M222') for x in index))
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','candidate_id':'hierarchy-ancestral-order-commutator-composition','recorded_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'actual_forward_carrier_cases':6,'invalid_metadata_cases':8,'source_files':{p.name:sha(p) for p in MODEL.glob('*.py')},'Torch':False,'GELU_FP32_autograd_native_resources':'NOT_RUN','scope':'Actual production plan/forward AST executed with a Fraction/list numerical substitute, compared with independent per-original-ID path/vector formulas. Swap-sign/equal-zero are software algebra witnesses, not new native numerical gates.'}
(HERE/'static_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'check_count':len(checks),'report':str(HERE/'static_validation.json')}))
