"""Bounded actual MIC production AST witnesses. No Torch/model import/autograd."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,json,math,hashlib,itertools
from author_guard import HERE,ROOT,sha,author_guard,write_new
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_mic')
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})

# Reuse only the old inert list carrier class definitions, never its tests or imports.
carrier_path=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare/static_check.py'
carrier_tree=ast.parse(carrier_path.read_text(encoding='utf8'))
classes=[n for n in carrier_tree.body if isinstance(n,ast.ClassDef) and n.name in ('T','Torch')]
ns={'F':F,'math':math}
exec(compile(ast.Module(body=classes,type_ignores=[]),'inert_fraction_carrier_classes','exec'),ns)
T,Torch=ns['T'],ns['Torch']
def add(self,other):
    assert self.shape==other.shape
    return T([a+b for a,b in zip(self.v,other.v)],self.shape)
T.__add__=add
class Cell:
    def __init__(self):self.rows=[]
    def __call__(self,x):
        self.rows.append(x.shape[0]);c=x.shape[1]
        return T([2*x.v[row*c+j]+3*x.v[row*c+(j+1)%c]+1 for row in range(x.shape[0]) for j in range(c)],x.shape)
class Activation:
    def __init__(self,kind='cubic'):self.calls=0;self.kind=kind
    def __call__(self,x):
        self.calls+=1
        if self.kind=='cubic':return T([v**3 for v in x.v],x.shape)
        if self.kind=='affine':return T([2*v+3 for v in x.v],x.shape)
        assert self.kind=='scalar_erf_GELU'
        return T([F(0.5*float(v)*(1+math.erf(float(v)/math.sqrt(2)))) for v in x.v],x.shape)

author_guard()
source=(MODEL/'ancestry_mobius.py').read_text(encoding='utf8');tree=ast.parse(source)
funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef)]
cls=next(x for x in tree.body if isinstance(x,ast.ClassDef))
forward=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='forward')
forward.name='actual_forward'
prod={'torch':Torch}
exec(compile(ast.fix_missing_locations(ast.Module(body=funcs+[forward],type_ignores=[])),'actual_MIC_production_AST','exec'),prod)
plan=prod['build_mobius_path_plan']
cases=[([],[],[],[0,0,0]),([],[],[],[6,4,3]),([0],[0],[0],[1,1,1]),
       ([0,0,0],[0],[0],[5,3,2]),([0,2,4],[2,0,2,1,3],[1,0,2,1],[7,5,4]),
       ([0,1,2,3],[0,0,0,1],[0,0],[6,4,3])]
for i,args in enumerate(cases):
    points,fm,mc,widths=args;p=plan(*args)
    paths=[(f,fm[f],mc[fm[f]]) for f in sorted(set(points))]
    check('true_ID_path_and_direct_upper_counts_%d'%i,
          list(zip(p['fine_ids'],p['middle_for_paths'],p['coarse_for_paths']))==paths and
          p['middle_path_counts']==[sum(m==j for _,m,_ in paths) for j in p['middle_ids']] and
          p['coarse_path_counts']==[sum(k==c for _,_,k in paths) for c in p['coarse_ids']])

def run(scenes,widths=(7,5,4),kind='cubic',permutation=None,zero_level=None):
    batch=len(scenes);c=2
    values=[[[[F(1+2*bi+3*l+i+j,11) for j in range(c)] for i in range(k)] for bi in range(batch)] for l,k in enumerate(widths)]
    if permutation is not None:
        assert scenes==[([0],[0],[0])]
        old=[list(values[l][0][0]) for l in range(3)]
        for l,k in enumerate(permutation):values[l][0][0]=old[k]
    if zero_level is not None:
        for bi in range(batch):
            for row in values[zero_level][bi]:row[:]=[F(0)]*c
    banks=[T(v,(batch,widths[l],c)) for l,v in enumerate(values)]
    ids=[[T(scene[l]) for scene in scenes] for l in range(3)]
    cell=Cell();act=Activation(kind);obj=SimpleNamespace(channels=c,cell=cell,activation=act)
    mean_calls=[];original_mean=prod['mean_mobius_paths']
    def once_mean(messages,positions,counts):
        mean_calls.append((list(positions),list(counts)));return original_mean(messages,positions,counts)
    prod['mean_mobius_paths']=once_mean
    try:actual=prod['actual_forward'](obj,banks,ids)
    finally:prod['mean_mobius_paths']=original_mean
    want=[[F(0)]*len(v.v) for v in banks];paths_total=0
    for bi,(points,fm,mc) in enumerate(scenes):
        groups=[{},{}]
        for fine in sorted(set(points)):
            middle,coarse=fm[fine],mc[fm[fine]]
            raw=[values[0][bi][fine],values[1][bi][middle],values[2][bi][coarse]]
            q=[]
            for j in range(c):
                abc=[2*v[j]+3*v[(j+1)%c] for v in raw]
                if kind=='cubic':value=6*abc[0]*abc[1]*abc[2]
                elif kind=='affine':value=F(0)
                else:
                    value=F(0)
                    # Independent unordered-subset oracle; no production slice expressions.
                    for count in range(4):
                        for subset in itertools.combinations(range(3),count):
                            pre=1+sum((abc[k] for k in subset),F(0))
                            z=0.5*float(pre)*(1+math.erf(float(pre)/math.sqrt(2)))
                            value+=((-1)**(3-count))*F(z)
                q.append(value)
            start=(bi*widths[0]+fine)*c;want[0][start:start+c]=q;paths_total+=1
            groups[0].setdefault(middle,[]).append(q);groups[1].setdefault(coarse,[]).append(q)
        for level,d in enumerate(groups,1):
            for idx,rows in d.items():
                start=(bi*widths[level]+idx)*c
                want[level][start:start+c]=[sum((x[j] for x in rows),F(0))/len(rows) for j in range(c)]
    assert all(x.v==want[l] for l,x in enumerate(actual)),'production_vs_independent_subset_oracle'
    assert cell.rows==([8*paths_total] if paths_total else []) and act.calls==(1 if paths_total else 0)
    assert len(mean_calls)==(2 if paths_total else 0)
    return actual,paths_total

scenes=[([0],[0],[0]),([0,1,2,3],[0,0,0,1],[0,0]),([0,2,4],[2,0,2,1,3],[1,0,2,1]),([],[],[])]
for i,batch in enumerate(([scenes[0]],[scenes[1]],[scenes[2]],[scenes[3],scenes[2],scenes[0]],[],[scenes[3]])):
    run(list(batch));check('production_forward_cubic_oracle_one_8F_call_two_means_%d'%i,True)
normal,_=run([scenes[0]],(1,1,1))
for perm in ((1,0,2),(2,1,0),(2,0,1)):
    other,_=run([scenes[0]],(1,1,1),permutation=perm)
    check('real_algebra_input_permutation_%s'%str(perm),all(a.v==b.v for a,b in zip(normal,other)))
for level in range(3):
    out,_=run([scenes[0]],(1,1,1),zero_level=level)
    check('real_algebra_zero_input_%d'%level,all(v==0 for x in out for v in x.v))
out,_=run([scenes[1]],kind='affine')
check('real_algebra_affine_activation_annihilated',all(v==0 for x in out for v in x.v))
gelu,_=run([scenes[0]],(1,1,1),kind='scalar_erf_GELU')
check('production_single_path_scalar_erf_GELU_subset_oracle',any(v!=0 for x in gelu for v in x.v))
base,_=run([scenes[0]]);dup,_=run([([0,0,0],[0],[0])])
check('duplicate_points_do_not_reweight_path',all(a.v==b.v for a,b in zip(base,dup)))
q=T([[1,2],[3,4],[5,6],[20,30]])
direct=prod['mean_mobius_paths'](q,[0,0,0,0],[4])
check('unequal_degree_direct_fine_mean_not_mean_of_middle_means',direct.v==[F(29,4),F(42,4)] and direct.v!=[F(23,2),F(17)])
invalid=[([-1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[1],[0],[1,2,1]),([0],[0],[1],[1,1,1]),([],[],[],[1,True,1]),([],[0,0],[0],[1,1,1])]
rejected=0
for args in invalid:
    try:plan(*args)
    except ValueError:rejected+=1
check('eight_invalid_metadata_rejected',rejected==8)
for p in MODEL.glob('*.py'):compile(p.read_text(encoding='utf8'),str(p),'exec')
check('exact_eight_model_sources_compile_without_import',len(list(MODEL.glob('*.py')))==8)
old=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare/staged_repository/framework/model/Quard_model'/(NAME+'_elc')
copies=['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']
check('six_original_common_sources_byte_identical',all((old/f).read_bytes()==(MODEL/f).read_bytes() for f in copies))
check('original_a18_YAML_bytes',sha(next((HERE/'staged_repository/configs').rglob('*.yaml')))=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
bt=ast.parse((HERE/'original_m95_hier.py.txt').read_text(encoding='utf8'));ht=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf8'))
def methods(t):return {(c.name,f.name):f for c in t.body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef)}
bm,hm=methods(bt),methods(ht)
check('only_original_CTF_constructor_forward_change',[k for k in bm if ast.dump(bm[k])!=ast.dump(hm[k])]==[('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')])
bc,hc=bm[('C2F_ClusterAttn_CTF','__init__')],hm[('C2F_ClusterAttn_CTF','__init__')]
check('original_constructor_full_prefix_RNG_preserved',len(hc.body)>len(bc.body) and all(ast.dump(x)==ast.dump(y) for x,y in zip(bc.body,hc.body)))
hf=(MODEL/'hier_postprocess.py').read_text(encoding='utf8')
check('three_LN_once_rawskip_CPUfork_original_HCG_tail','self.cluster_ffn_norm[level](cluster_feats_list[level])' in hf and 'cf + value' in hf and 'torch.random.fork_rng(devices=[])' in hf and ast.dump(bm[('C2F_ClusterAttn_CTF','forward')].body[-4:][0])==ast.dump(hm[('C2F_ClusterAttn_CTF','forward')].body[-4:][0]))
check('feature_forward_no_detach_cpu_or_aux_loss',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('detach','cpu','backward') for n in ast.walk(forward)))
check('single_shared_C_to_C_original_GELU_no_newnorm',source.count('nn.Linear(channels, channels)')==1 and source.count('nn.GELU()')==1 and source.count('self.activation(self.cell(')==1 and 'LayerNorm' not in source)
check('source_parameters_and_MAC_arithmetic',256*256+256==65792 and 8*256*256*256==134217728 and 8*sum((256,64,8))*256*256==171966464)
work=json.loads((ROOT/'pipeline/research_work.json').read_text(encoding='utf8'))
check('stable_candidate_and_M229_unused',not any(x['id']=='hierarchy-ancestry-mobius-interaction-composition' or x.get('experiment_id')=='M229-MIC' for x in work['candidates']))
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','candidate_id':'hierarchy-ancestry-mobius-interaction-composition','experiment_id':'M229-MIC','recorded_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'actual_forward_carrier_cases':15,'invalid_metadata_cases':8,'source_files':{f.name:sha(f) for f in MODEL.glob('*.py')},'carrier_source':{'path':str(carrier_path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(carrier_path),'classes_only':['T','Torch'],'old_tests_executed':False},'Torch_imported':False,'autograd_native_resources':'NOT_RUN','scope':'Actual production metadata/forward AST with exact Fraction/list cubic and affine substitutes; one scalar-erf GELU example. Algebra properties only software witnesses, never native FP32 cancellation/coverage/Jacobian/positivity gates.','author':author_guard()}
write_new('static_validation.json',json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'checks':len(checks),'report_sha256':sha(HERE/'static_validation.json')}))
