"""Bounded stdlib production DCE plan/helpers/forward checks; no Torch import."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
from itertools import accumulate
import ast,json,hashlib,math
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
MODEL=HERE/'staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_dce'
checks=[]
def check(n,v):
    assert v,n
    checks.append({'name':n,'passed':True})
class T:
    device='cpu';dtype='fraction-list'
    def __init__(self,data,shape=None):
        def flat(x):return sum((flat(a) for a in x),[]) if isinstance(x,(list,tuple)) else [F(x)]
        self.v=flat(data);self.shape=shape or ((len(data),len(data[0])) if data and isinstance(data[0],list) else (len(data),));self.ndim=len(self.shape)
        assert math.prod(self.shape)==len(self.v)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return [int(x) for x in self.v]
    def reshape(self,*shape):
        if len(shape)==1 and isinstance(shape[0],(list,tuple)):shape=tuple(shape[0])
        shape=list(shape)
        if -1 in shape:shape[shape.index(-1)]=len(self.v)//math.prod(x for x in shape if x!=-1)
        return T(self.v,tuple(shape))
    def new_zeros(self,shape):return T([0]*math.prod(shape),tuple(shape))
    def new_tensor(self,data):return T(data)
    def unsqueeze(self,axis):assert axis==-1;return T(self.v,self.shape+(1,))
    def index_select(self,axis,index):
        assert axis==0;n=math.prod(self.shape[1:]);return T([self.v[int(i)*n+j] for i in index.v for j in range(n)],(len(index.v),)+self.shape[1:])
    def index_add(self,axis,index,source):
        assert axis==0;out=list(self.v);n=self.shape[1]
        for r,i in enumerate(index.v):
            for j in range(n):out[int(i)*n+j]+=source.v[r*n+j]
        return T(out,self.shape)
    def index_copy(self,axis,index,source):
        assert axis==0;out=list(self.v);n=self.shape[1]
        for r,i in enumerate(index.v):out[int(i)*n:int(i)*n+n]=source.v[r*n:r*n+n]
        return T(out,self.shape)
    def flip(self,dims):assert dims==[0];n=self.shape[1];return T([x for i in reversed(range(self.shape[0])) for x in self.v[i*n:(i+1)*n]],self.shape)
    def __getitem__(self,item):
        n=self.shape[1];ids=list(range(self.shape[0]))[item];return T([x for i in ids for x in self.v[i*n:(i+1)*n]],(len(ids),n))
    def op(self,other,fn):
        assert self.shape[0]==other.shape[0]
        rows,cols=self.shape;return T([fn(self.v[r*cols+c],other.v[r*other.shape[1]+(0 if other.shape[1]==1 else c)]) for r in range(rows) for c in range(cols)],self.shape)
    def __add__(self,o):return self.op(o,lambda a,b:a+b)
    def __mul__(self,o):return self.op(o,lambda a,b:a*b)
    def __truediv__(self,o):return self.op(o,lambda a,b:a/b)
class Torch:
    long='long'
    tensor=staticmethod(lambda data,**kw:T(data))
    @staticmethod
    def cat(values,dim):
        if dim==0:return T([a for x in values for a in x.v],(sum(x.shape[0] for x in values),values[0].shape[1]))
        assert dim==-1;rows=values[0].shape[0];return T([a for r in range(rows) for x in values for a in x.v[r*x.shape[1]:(r+1)*x.shape[1]]],(rows,sum(x.shape[1] for x in values)))
    @staticmethod
    def cumsum(x,dim):
        assert dim==0;rows,cols=x.shape;return T([sum(x.v[i*cols+c] for i in range(r+1)) for r in range(rows) for c in range(cols)],x.shape)
source=(MODEL/'directed_cavity.py').read_text('utf8');tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)];forward=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='forward')
ns={'torch':Torch};exec(compile(ast.Module(body=functions+[forward],type_ignores=[]),'actual_DCE_production','exec'),ns)
# Independent original-ID graph oracle (does not use plan/cumsum/mean helper).
def oracle(banks,members):
    outputs=[[[F(0)]*len(x) for x in level] for level in banks]
    def G(role,a,b):return (a+(role+2)*b+role)**2
    for batch,(pts,f2m,m2c) in enumerate(members):
        fine=sorted(set(pts));middle=sorted({f2m[i] for i in fine});coarse=sorted({m2c[j] for j in middle})
        avg=lambda vals:sum(vals,F(0))/len(vals) if vals else F(0)
        U={j:G(0,banks[1][batch][j],avg([banks[0][batch][i] for i in fine if f2m[i]==j])) for j in middle}
        D={j:G(1,banks[2][batch][m2c[j]],avg([U[k] for k in middle if k!=j and m2c[k]==m2c[j]])) for j in middle}
        for i in fine:
            j=f2m[i];ctx=avg([D[j]]+[banks[0][batch][h] for h in fine if h!=i and f2m[h]==j]);down=G(2,banks[1][batch][j],ctx)
            outputs[0][batch][i]=G(3,banks[0][batch][i],down)
        for j in middle:outputs[1][batch][j]=G(4,banks[1][batch][j],avg([D[j]]+[banks[0][batch][i] for i in fine if f2m[i]==j]))
        for k in coarse:outputs[2][batch][k]=G(5,banks[2][batch][k],avg([U[j] for j in middle if m2c[j]==k]))
    return outputs
cases=[([0], [0],[0],[2,2,2]),([0,1],[0,0],[0],[3,2,2]),([0,1,2],[0,0,1],[0,0],[4,3,2]),([4,1,4,2],[0,2,1,0,2],[1,0,1],[6,4,3]),([],[],[],[2,2,2]),([0,1,2,3],[0,1,2,2],[0,0,1],[5,4,3])]
for i,case in enumerate(cases):
    pts,f2m,m2c,widths=case;plan=ns['build_cavity_plan'](pts,f2m,m2c,widths)
    check('plan_original_ids_'+str(i),plan['fine_ids']==sorted(set(pts)) and sum(plan['fine_counts'])==len(set(pts)))
for i,batchcases in enumerate([[x] for x in cases]+[[cases[4],cases[2]],[cases[3],cases[5]]]):
    widths=[max(x[3][l] for x in batchcases) for l in range(3)];b=len(batchcases)
    banks=[[[F(1+100*bb+10*l+j) for j in range(widths[l])] for bb in range(b)] for l in range(3)]
    levels=[T([x for row in banks[l] for x in row],(b,widths[l],1)) for l in range(3)]
    members=[x[:3] for x in batchcases];ids=[[T(member[l]) for member in members] for l in range(3)]
    module=SimpleNamespace(channels=1,activation=lambda x:T([a*a for a in x.v],x.shape))
    for role,name in enumerate(('up','down_root','down_middle','read_fine','read_middle','read_coarse')):
        setattr(module,name,lambda x,role=role:T([x.v[2*r]+(role+2)*x.v[2*r+1]+role for r in range(x.shape[0])],(x.shape[0],1)))
    actual=ns['forward'](module,levels,ids);expected=oracle(banks,members)
    check('actual_forward_independent_graph_'+str(i),all(actual[l].v==[x for row in expected[l] for x in row] for l in range(3)))
for i,bad in enumerate([([-1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([1],[0],[0],[2,1,1]),([0],[1],[0],[1,2,1]),([0],[0],[2],[1,1,1]),([],[0,0],[0],[1,1,1]),([],[],[],[True,1,1])]):
    try:ns['build_cavity_plan'](*bad)
    except ValueError:check('invalid_metadata_'+str(i),True)
    else:raise AssertionError('invalid accepted')
for f in MODEL.glob('*.py'):compile(f.read_bytes(),str(f),'exec')
check('eight_model_compile',len(list(MODEL.glob('*.py')))==8)
config=next((HERE/'staged_repository/configs').rglob('*.yaml'));check('original_YAML_bytes',hashlib.sha256(config.read_bytes()).hexdigest()=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'BOUNDED_PRODUCTION_SOFTWARE_CHECKS_PASSED_NOT_NATIVE','count':len(checks),'checks':checks,'torch_imported':False,'actual_forward_scope':'Actual production forward AST with stdlib Fraction/list interfaces and toy nonlinear square, compared to independent original-ID directed-edge oracle; not Torch/GELU/FP32/autograd/native.', 'native':'NOT_RUN','resources':'NOT_RUN'}
(HERE/'static_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({'count':len(checks),'status':result['status']}))
