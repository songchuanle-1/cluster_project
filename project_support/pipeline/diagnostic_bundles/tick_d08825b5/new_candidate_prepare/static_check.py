"""Actual HPC production-function stdlib carrier checks; no Torch import/native claims."""
import ast, copy, hashlib, json, math
from fractions import Fraction as F
from pathlib import Path
BASE = Path(__file__).resolve().parent
MODEL = BASE / 'staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc'
CHECKS=[]
def need(ok, name):
    if not ok: raise AssertionError(name)
    CHECKS.append(name)
class T:
    def __init__(self, data): self.data=copy.deepcopy(data)
    @property
    def shape(self):
        s=[];x=self.data
        while isinstance(x,list):
            s.append(len(x));x=x[0] if x else None
        return tuple(s)
    ndim=property(lambda s:len(s.shape));device='cpu'
    def __getitem__(self,i): return T(self.data[i])
    def new_tensor(self,x): return T(x)
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return copy.deepcopy(self.data)
    def unsqueeze(self,d):
        assert d==-1
        return T([[v] for v in self.data])
    def index_select(self,d,ids):
        assert d==0
        return T([self.data[int(i)] for i in ids.data])
    def index_add(self,d,ids,other):
        assert d==0
        a=copy.deepcopy(self.data)
        for j,i in enumerate(ids.data):
            a[int(i)]=[u+v for u,v in zip(a[int(i)],other.data[j])]
        return T(a)
    def index_copy(self,d,ids,other):
        assert d==0
        a=copy.deepcopy(self.data)
        for j,i in enumerate(ids.data): a[int(i)]=copy.deepcopy(other.data[j])
        return T(a)
    def masked_fill(self,*args): return self
    def _binary(self,o,op):
        od=o.data if isinstance(o,T) else o
        def rec(a,b):
            if isinstance(a,list):
                if isinstance(b,list):
                    if len(b)==1 and len(a)!=1: return [rec(v,b[0]) for v in a]
                    assert len(a)==len(b)
                    return [rec(u,v) for u,v in zip(a,b)]
                return [rec(v,b) for v in a]
            return op(a,b)
        return T(rec(self.data,od))
    def __add__(s,o):return s._binary(o,lambda a,b:a+b)
    def __mul__(s,o):return s._binary(o,lambda a,b:a*b)
    def __truediv__(s,o):return s._binary(o,lambda a,b:a/b)
class Torch:
    long='long'
    @staticmethod
    def tensor(x,**kw):return T(x)
    @staticmethod
    def stack(rows,dim=0):assert dim==0;return T([x.data for x in rows])
source=(MODEL/'hierarchy_resolvent.py').read_text(encoding='utf-8')
tree=ast.parse(source)
ns={'torch':Torch}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),str(MODEL/'hierarchy_resolvent.py'),'exec'),ns)
planfn=ns['build_resolvent_plan']; solve=ns['solve_resolvent_levels']
def dense_oracle(banks,p,fm,mc):
    # Independent full SPD matrix from ORIGINAL edge membership, rational Gaussian elimination.
    nodes=sorted(set([(0,i) for i in p]+[(1,fm[i]) for i in p]+[(2,mc[fm[i]]) for i in p]))
    edges=set()
    for i in p: edges.add(((0,i),(1,fm[i])));edges.add(((1,fm[i]),(2,mc[fm[i]])))
    at={v:i for i,v in enumerate(nodes)};n=len(nodes);c=len(banks[0][0]) if banks[0] else 3
    A=[[F(int(i==j)) for j in range(n)] for i in range(n)]
    for u,v in edges:
        i,j=at[u],at[v];A[i][i]+=1;A[j][j]+=1;A[i][j]-=1;A[j][i]-=1
    rhs=[[F(str(v)) for v in banks[l][i]] for l,i in nodes]
    aug=[a+r for a,r in zip(A,rhs)]
    for k in range(n):
        pivot=aug[k][k];assert pivot>0
        aug[k]=[v/pivot for v in aug[k]]
        for i in range(n):
            if i==k:continue
            q=aug[i][k]
            aug[i]=[u-q*v for u,v in zip(aug[i],aug[k])]
    out=copy.deepcopy(banks)
    for i,(l,j) in enumerate(nodes):out[l][j]=aug[i][n:]
    return out

def bank_values(ks,offset=0):
    return [[[F((l+1)*13+(i+1)*5+c+offset,11) for c in range(3)] for i in range(k)] for l,k in enumerate(ks)]
def close_banks(actual,expected):
    return all(abs(float(a)-float(b))<1e-10 for aa,bb in zip(actual,expected) for ar,br in zip(aa,bb) for a,b in zip(ar,br))
cases=[]
# Distinct nonempty/holes/duplicate-point/uneven branch cases, plus empty.
for n in range(0,33):
    ks=[n+3,max(2,n//3+2)+2,5]
    fm=[(i*7+1)%(ks[1]-1) for i in range(ks[0]-1)]
    mc=[(j*3+1)%4 for j in range(ks[1]-1)]
    p=[i for i in range(n) if i%4!=2];p+=p[::3]
    cases.append((ks,p,fm,mc))
cases += [([1,1,1],[0],[0],[0]),([3,2,2],[0,1,2],[0,0,1],[0,1]),([6,4,3],[1,3,5,1],[0,2,0,2,1,3],[1,1,0,2])]
maxerr=0.0
for idx,(ks,p,fm,mc) in enumerate(cases):
    plan=planfn(p,fm,mc,ks);banks=bank_values(ks,idx)
    actual=[x.data[0] for x in solve([T([b]) for b in banks],[plan])]
    expected=dense_oracle(banks,p,fm,mc)
    need(close_banks(actual,expected),f'case_{idx}_production_solve_vs_fraction_dense')
    need(plan['edge_count']==len(set(p))+len(set(fm[i] for i in p)),f'case_{idx}_real_edge_count')
    active=[set(plan[k]) for k in ['fine_ids','middle_ids','coarse_ids']]
    need(all(actual[l][i]==banks[l][i] for l,k in enumerate(ks) for i in range(k) if i not in active[l]),f'case_{idx}_unsupported_pad_identity')
    # Two ACTUAL solver calls with a nonlinear scalar toy FFN, not a Tensor/GELU/autograd claim.
    nonlinear=[[[v*v+F(l+1,7) for v in row] for row in level] for l,level in enumerate(actual)]
    composed=[x.data[0] for x in solve([T([b]) for b in nonlinear],[plan])]
    expected2=dense_oracle([[[v*v+F(l+1,7) for v in row] for row in level] for l,level in enumerate(expected)],p,fm,mc)
    need(close_banks(composed,expected2),f'case_{idx}_nonlinear_sandwich_dense_reference')
    if p:
        const=[[[F(3) for _ in range(3)] for i in range(k)] for k in ks]
        ca=[x.data[0] for x in solve([T([b]) for b in const],[plan])]
        need(close_banks(ca,const),f'case_{idx}_constant_solver_property_not_admission_gate')
# Same-shaped batches use different plans and cannot mix features.
ks=[6,4,3];specs=[([0,1,2,2],[0,0,1,2,2,3],[0,1,1,2]),([3,5],[0,1,2,3,0,1],[2,0,1,1])]
bs=[bank_values(ks,80),bank_values(ks,900)];ps=[planfn(p,fm,mc,ks) for p,fm,mc in specs]
a=solve([T([bs[b][l] for b in range(2)]) for l in range(3)],ps)
need(all(close_banks([a[l].data[b] for l in range(3)],dense_oracle(bs[b],*specs[b])) for b in range(2)),'two_batch_no_cross_scene_or_parent_mixing')
need(solve([T([]),T([]),T([])],[]) and True,'zero_batch_identity')
invalid=[([-1],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([0],[1],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[0],[],[1,1,1]),([0],[0],[0],[1,1]),([0],[0],[0],[1,True,1])]
for i,args in enumerate(invalid):
    try:planfn(*args)
    except ValueError:need(True,f'invalid_{i}_rejected')
    else:raise AssertionError(f'invalid_{i}_accepted')
# AST wiring and unchanged-source protections.
root=BASE.parents[3];orig=root/'Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
hp=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'));old=ast.parse((orig/'hier_postprocess.py').read_text(encoding='utf-8'))
def cls(t,name):return next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==name)
def meth(c,name):return next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name)
for name in ['PointCloudPartitioner','SharedClusterBank','C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT']:
    need(ast.dump(cls(hp,name),include_attributes=False)==ast.dump(cls(old,name),include_attributes=False),'unchanged_AST_'+name)
ctf=cls(hp,'C2F_ClusterAttn_CTF');base=cls(old,'C2F_ClusterAttn_CTF')
need(ast.dump(meth(ctf,'__init__'),include_attributes=False)==ast.dump(meth(base,'__init__'),include_attributes=False),'all_original_parameter_construction_and_rng_unchanged')
forward=meth(ctf,'forward');calls=[n for n in ast.walk(forward) if isinstance(n,ast.Call)]
need(sum(isinstance(n.func,ast.Name) and n.func.id=='solve_resolvent_levels' for n in calls)==2,'exact_two_solvers_around_original_FFNs')
need(sum(isinstance(n.func,ast.Attribute) and n.func.attr=='_cluster_to_points' for n in calls)==1,'single_original_HCG_readback')
solve_ast=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='solve_resolvent_levels')
need(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['inverse','linalg','backward','manual_seed','cuda','detach','cpu','tolist'] for n in ast.walk(solve_ast)),'feature_solver_has_no_detach_CPU_dense_inverse_backward_seed_or_cuda')
# Execute the ACTUAL original-class forward function body with the same list carrier.
# Stub only FFN arithmetic/readback; this is software wiring, not Torch/GELU/HCG validation.
class Mask:
    def unsqueeze(self,*a):return self
class Operator:
    def __init__(self):
        self.num_scales=3;self.norm_calls=[0]*3;self.ffn_calls=[0]*3
        def norm(l):
            def f(x):self.norm_calls[l]+=1;return x
            return f
        def ff(l):
            def f(x):
                self.ffn_calls[l]+=1
                return T([[[v*v+F(l+1,7) for v in row] for row in batch] for batch in x.data])
            return f
        self.cluster_ffn_norm=[norm(l) for l in range(3)]
        self.cluster_ffn=[ff(l) for l in range(3)]
        self.delivered=None;self.message_norm=lambda x:x
    def _cluster_to_points(self,p,levels,ids,mask):self.delivered=levels;return levels[0]
forward_ns={'prepare_resolvent_plans':ns['prepare_resolvent_plans'],'solve_resolvent_levels':solve}
exec(compile(ast.Module(body=[forward],type_ignores=[]),'actual_CTF_forward','exec'),forward_ns)
ids=[[T(specs[b][l]) for b in range(2)] for l in range(3)]
operator=Operator();forward_ns['forward'](operator,None,None,Mask(),[T([bs[b][l] for b in range(2)]) for l in range(3)],None,ids)
need(operator.norm_calls==[1,1,1] and operator.ffn_calls==[1,1,1],'actual_forward_exact_three_original_norms_and_FFNs_once')
for b in range(2):
    z=dense_oracle(bs[b],*specs[b]);u=[[[v*v+F(l+1,7) for v in row] for row in z[l]] for l in range(3)];d=dense_oracle(u,*specs[b])
    expected=[[[bs[b][l][i][c]+d[l][i][c] for c in range(3)] for i in range(ks[l])] for l in range(3)]
    need(close_banks([operator.delivered[l].data[b] for l in range(3)],expected),f'actual_forward_batch_{b}_original_raw_skip_plus_two_solve_nonlinearity')
for f in orig.glob('*.py'):
    if f.name!='hier_postprocess.py':need((MODEL/f.name).read_bytes()==f.read_bytes(),'baseline_bytes_'+f.name)
for f in MODEL.glob('*.py'):compile(f.read_text(encoding='utf-8'),str(f),'exec')
need(True,'eight_source_compile_without_import')
y=BASE/'staged_repository/configs/Quard/ctf_hcg_csort_hpc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hpc.yaml'
need(hashlib.sha256(y.read_bytes()).hexdigest()=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a','original_YAML_byte_exact')
report={'status':'STDLIB_PRODUCTION_FUNCTION_CARRIER_AND_SOURCE_CHECKS_PASSED_NOT_NATIVE','actual_case_count':len(cases),'actual_multi_batch_cases':1,'invalid_cases':len(invalid),'assertion_count':len(CHECKS),'checks':CHECKS,'source_helper_sha256':hashlib.sha256((MODEL/'hierarchy_resolvent.py').read_bytes()).hexdigest(),'scope':'Actual production plan and solve function body extracted by AST; plain Python numeric/list carrier versus independent full Fraction Gaussian matrix oracle. Not Torch, Tensor, FP32, autograd, native TRAIN, resource, initialization or efficacy validation.','native':'NOT_RUN','resources':'NOT_RUN','torch_imported':False}
(BASE/'static_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
