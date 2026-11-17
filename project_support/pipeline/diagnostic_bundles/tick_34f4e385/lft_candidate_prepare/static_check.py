"""Actual production plan/forward with Fraction/list carriers, never Torch/native."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,copy,hashlib,json,math,traceback
HERE=Path(__file__).resolve().parent
STAGE=HERE/'staged_repository'
MODEL=next((STAGE/'framework/model/Quard_model').iterdir())
SOURCE=MODEL/'nonlinear_lifting.py'
CHECKS=[]
def check(label,ok):
    if not ok:raise AssertionError(label)
    CHECKS.append(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_hashes():return {p.relative_to(STAGE).as_posix():sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file()}

class Tensor:
    device='symbolic_cpu';dtype='Fraction'
    def __init__(self,values,shape):
        self.values=[F(v) for v in values];self.shape=tuple(shape);self.ndim=len(shape)
        assert len(self.values)==math.prod(shape)
    def reshape(self,*shape):
        if len(shape)==1 and isinstance(shape[0],tuple):shape=shape[0]
        return Tensor(self.values,shape)
    def new_zeros(self,shape):return Tensor([0]*math.prod(shape),shape)
    def new_tensor(self,values):return Tensor(values,(len(values),))
    def unsqueeze(self,dim):
        shape=list(self.shape);shape.insert(len(shape) if dim==-1 else dim,1);return Tensor(self.values,shape)
    def index_select(self,dim,index):
        assert dim==0;stride=math.prod(self.shape[1:]);return Tensor([v for i in index for v in self.values[i*stride:(i+1)*stride]],(len(index),*self.shape[1:]))
    def index_add(self,dim,index,other):
        assert dim==0;stride=math.prod(self.shape[1:]);values=list(self.values)
        for row,i in enumerate(index):
            for j in range(stride):values[i*stride+j]+=other.values[row*stride+j]
        return Tensor(values,self.shape)
    def index_copy(self,dim,index,other):
        assert dim==0;stride=math.prod(self.shape[1:]);values=list(self.values)
        for row,i in enumerate(index):values[i*stride:(i+1)*stride]=other.values[row*stride:(row+1)*stride]
        return Tensor(values,self.shape)
    def __add__(self,b):assert self.shape==b.shape;return Tensor([a+c for a,c in zip(self.values,b.values)],self.shape)
    def __sub__(self,b):assert self.shape==b.shape;return Tensor([a-c for a,c in zip(self.values,b.values)],self.shape)
    def __truediv__(self,b):assert self.shape==b.shape;return Tensor([a/c for a,c in zip(self.values,b.values)],self.shape)
    def mapped(self,fn):return Tensor([fn(x) for x in self.values],self.shape)
class IDs:
    def __init__(self,v):self.v=v
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return list(self.v)

tree=ast.parse(SOURCE.read_text('utf8'))
forward=copy.deepcopy(next(n for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='forward'))
body=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef)]+[forward]
NS={'torch':SimpleNamespace(tensor=lambda values,**kw:list(values),long='symbolic_long')}
exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(SOURCE),'exec'),NS)

LINEARS=[(F(1,3),F(1,7)),(F(-1,5),F(1,11)),(F(1,4),F(-1,13)),(F(1,6),F(1,17))]
def effective(k,x,zero=False):
    a,b=(F(0),F(0)) if zero else LINEARS[k]
    return (a*x+b)**2
def core(k,x,identity):return x if identity else x*x/F((7,11,13)[k])+F((1,-1,1)[k],(5,3,7)[k])

def oracle(levels,members,widths,identity,zero):
    outputs=[[F(0)]*len(x.values) for x in levels]
    for batch,(points,fm,mc) in enumerate(members):
        fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[i] for i in middle})
        a={i:levels[0].values[batch*widths[0]+i] for i in fine};b={i:levels[1].values[batch*widths[1]+i] for i in middle};c={i:levels[2].values[batch*widths[2]+i] for i in coarse}
        mean=lambda values,keys:sum((values[i] for i in keys),F(0))/len(keys)
        df={i:a[i]-effective(0,b[fm[i]],zero) for i in fine}
        bt={j:b[j]+effective(1,mean(df,[i for i in fine if fm[i]==j]),zero) for j in middle}
        dm={j:bt[j]-effective(2,c[mc[j]],zero) for j in middle}
        ct={q:c[q]+effective(3,mean(dm,[j for j in middle if mc[j]==q]),zero) for q in coarse}
        ff={i:core(0,x,identity) for i,x in df.items()};mf={i:core(1,x,identity) for i,x in dm.items()};cf={i:core(2,x,identity) for i,x in ct.items()}
        co={q:cf[q]-effective(3,mean(mf,[j for j in middle if mc[j]==q]),zero) for q in coarse}
        bo={j:mf[j]+effective(2,co[mc[j]],zero)-effective(1,mean(ff,[i for i in fine if fm[i]==j]),zero) for j in middle}
        ao={i:ff[i]+effective(0,bo[fm[i]],zero) for i in fine}
        for level,values in enumerate((ao,bo,co)):
            for key,value in values.items():outputs[level][batch*widths[level]+key]=value
    return outputs

def run_case(label,members,widths,identity=False,zero=False):
    batch=len(members);levels=[Tensor([F(10*b+3*l+i+1,9) for b in range(batch) for i in range(width)],(batch,width,1)) for l,width in enumerate(widths)]
    ids=[[IDs(member[l]) for member in members] for l in range(3)];calls=[]
    def op(name,fn):
        def apply(value):calls.append((name,value.shape));return value.mapped(fn)
        return apply
    self=SimpleNamespace(channels=1,predict_fine=op('P0',lambda x:0 if zero else LINEARS[0][0]*x+LINEARS[0][1]),update_middle=op('U0',lambda x:0 if zero else LINEARS[1][0]*x+LINEARS[1][1]),predict_middle=op('P1',lambda x:0 if zero else LINEARS[2][0]*x+LINEARS[2][1]),update_coarse=op('U1',lambda x:0 if zero else LINEARS[3][0]*x+LINEARS[3][1]),activation=op('toy_activation',lambda x:x*x))
    ffns=[op('F'+str(k),lambda x,k=k:core(k,x,identity)) for k in range(3)]
    result=NS['forward'](self,levels,ids,ffns);expected=oracle(levels,members,widths,identity,zero)
    check(label+':production_forward_vs_independent_originalID_oracle',[x.values for x in result]==expected)
    if any(member[0] for member in members):
        check(label+':actual_call_order',[n for n,_ in calls if n!='toy_activation']==['P0','U0','P1','U1','F0','F1','F2','U1','P1','U0','P0'])
        check(label+':eight_new_activations',sum(n=='toy_activation' for n,_ in calls)==8)
    else:check(label+':empty_no_operator_or_FFN_calls',not calls)
    if identity:
        for batch,member in enumerate(members):
            fine=set(member[0]);middle={member[1][i] for i in fine};coarse={member[2][j] for j in middle}
            check(label+':identity_core_real_algebra',all(result[l].values[batch*widths[l]+i]==levels[l].values[batch*widths[l]+i] for l,keys in enumerate((fine,middle,coarse)) for i in keys))

def run():
    cases=[('singleton',[([2],[0,0,3,0],[0,0,0,2])],[6,5,4]),('unequal',[([0,1,2,3,4],[2,2,4,4,4],[0,0,1,0,1])],[7,5,3]),('multi_root',[([0,1,2,3,4],[0,0,2,2,3],[0,2,1,2])],[6,4,3]),('duplicate_points',[([4,0,4,2,0],[1,0,1,0,3],[0,0,0,1])],[7,4,3]),('empty',[([],[0,1],[0,1])],[4,3,3]),('mixed_batch',[([2],[0,0,3,0],[0,0,0,2]),([0,1,3],[1,1,2,4],[0,1,0,0,1])],[6,5,4]),('mixed_empty',[([],[0],[0]),([0,2],[1,0,3],[0,0,0,2])],[5,4,3]),('zero_batch',[],[5,4,3])]
    for label,members,widths in cases:
        run_case(label+':nonlinear_core',members,widths)
        run_case(label+':identity_core',members,widths,identity=True)
    run_case('zero_coupling_supported_M95_control',cases[1][1],cases[1][2],zero=True)
    bad=[([],[],[],[1,1]),([],[],[],[1,-1,1]),([True],[0],[0],[1,1,1]),([-1],[0],[0],[1,1,1]),([2],[0],[0],[2,1,1]),([1],[0],[0],[2,1,1]),([0],[1],[0],[1,2,1]),([],[0,0],[0],[1,1,1]),([0],[False],[0],[1,1,1]),([0],[2],[0],[1,2,1])]
    for i,args in enumerate(bad):
        try:NS['build_lifting_plan'](*args)
        except ValueError:check('invalid_metadata_'+str(i),True)
        else:raise AssertionError('Invalid metadata accepted '+str(i))
    original=ast.parse((HERE/'original_m95_hier_postprocess.py.txt').read_text('utf8'));current=ast.parse((MODEL/'hier_postprocess.py').read_text('utf8'))
    methods=lambda t:{c.name+'.'+n.name:n for c in t.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
    a,b=methods(original),methods(current);changed=[k for k in a if ast.dump(a[k],include_attributes=False)!=ast.dump(b[k],include_attributes=False)]
    check('only_CTF_ctor_forward_changed',changed==['C2F_ClusterAttn_CTF.__init__','C2F_ClusterAttn_CTF.forward'])
    check('original_constructor_full_prefix_preserved',all(ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False) for x,y in zip(a[changed[0]].body,b[changed[0]].body)))
    check('old_FFNs_remain_passed_once_not_registered_inside_core','self.cluster_ffn)' in (MODEL/'hier_postprocess.py').read_text('utf8') and not any(isinstance(n,ast.Attribute) and n.attr in ('ffns','cluster_ffn') and isinstance(n.ctx,ast.Store) for n in ast.walk(tree)))
    check('forward_feature_no_detach_cpu_or_tolist',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('detach','cpu','tolist') for n in ast.walk(forward)))
    check('YAML_a18',sha(next((STAGE/'configs').rglob('*.yaml')))=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    for source in MODEL.glob('*.py'):compile(source.read_text('utf8'),str(source),'exec')
    check('eight_independent_sources_compile_without_import',len(list(MODEL.glob('*.py')))==8)
    return {'status':'ACTUAL_STDLIB_PRODUCTION_PLAN_FORWARD_AND_SOURCE_CHECKS_PASSED_NOT_NATIVE_PASS','recorded_at':datetime.now(timezone.utc).isoformat(),'checks_count':len(CHECKS),'checks':CHECKS,'valid_forward_cases':17,'invalid_metadata_cases':10,'source_files':source_hashes(),'helper_sha256':sha(SOURCE),'checker_sha256':sha(Path(__file__)),'scope':'Actual production plan/mean/forward AST with Fraction/list carriers vs independent original-ID dictionary oracle. Toy squared activation/affine maps are not Tensor, actual GELU, FP32, autograd, initialization pairing or resource execution. Identity core is software real algebra only.','native':'NOT_RUN','resources':'NOT_RUN'}

if __name__=='__main__':
    try:result=run()
    except Exception as error:
        result={'status':'FAILED_STDLIB_CHECK','recorded_at':datetime.now(timezone.utc).isoformat(),'error':repr(error),'traceback':traceback.format_exc(),'completed_checks':CHECKS,'source_files':source_hashes(),'helper_sha256':sha(SOURCE),'checker_sha256':sha(Path(__file__))}
        with (HERE/'static_validation_failed.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
        (HERE/'static_check_failed.py.txt').write_bytes(Path(__file__).read_bytes())
        raise
    with (HERE/'static_validation.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':result['status'],'checks_count':result['checks_count'],'source9':len(result['source_files'])}))
