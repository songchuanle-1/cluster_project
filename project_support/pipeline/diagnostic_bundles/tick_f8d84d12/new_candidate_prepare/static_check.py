"""Small actual FCB source/forward software witnesses, without Torch or old suites."""
from pathlib import Path
from fractions import Fraction as F
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,hashlib,json,math
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_fcb')
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Reuse only a small plain-list interface definition, never execute its old suite.
old=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare/static_check.py'
carrier=[n for n in ast.parse(old.read_text(encoding='utf-8')).body if isinstance(n,ast.ClassDef) and n.name in ('T','Torch')]
ns={'F':F,'math':math};exec(compile(ast.Module(body=carrier,type_ignores=[]),'list_interface_definitions_only','exec'),ns)
T,Torch=ns['T'],ns['Torch']
class Map:
    def __init__(self,own,other,bias):self.own,self.other,self.bias=own,other,bias;self.rows=[]
    def __call__(self,x):
        self.rows.append(x.shape[0]);c=x.shape[1]//2
        return T([self.own*x.v[r*2*c+j]+self.other*x.v[r*2*c+c+(j+1)%c]+self.bias for r in range(x.shape[0]) for j in range(c)],(x.shape[0],c))
class Activation:
    def __init__(self):self.calls=0
    def __call__(self,x):self.calls+=1;return T([v*v+v for v in x.v],x.shape)
tree=ast.parse((MODEL/'fine_coarse_bipartite.py').read_text(encoding='utf-8'))
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward');forward.name='actual_forward'
core={'torch':Torch};exec(compile(ast.fix_missing_locations(ast.Module(body=functions+[forward],type_ignores=[])),'actual_FCB_production','exec'),core)
plan=core['build_fine_coarse_plan']
cases=[([],[],[],[0,0,0]),([],[],[],[7,5,4]),([0],[0],[0],[1,1,1]),
       ([0,0,0],[0],[0],[7,5,4]),([0,2,4],[2,0,2,1,3],[1,0,2,1],[7,5,4]),
       ([0,1,2,3],[0,0,0,1],[0,1],[7,5,4])]
for case_id,(points,fm,mc,widths) in enumerate(cases):
    got=plan(points,fm,mc,widths);fine=sorted(set(points));middle=sorted({fm[f] for f in fine});coarse=sorted({mc[m] for m in middle})
    want_pairs=[(f,c) for f in fine for c in coarse]
    actual_pairs=[(got['fine_ids'][f],got['coarse_ids'][c]) for f,c in zip(got['pair_fine_positions'],got['pair_coarse_positions'])]
    check('original_true_support_and_Cartesian_product_%d'%case_id,[got[k] for k in ('fine_ids','middle_ids','coarse_ids')]==[fine,middle,coarse] and actual_pairs==want_pairs and got['pair_count']==len(want_pairs))
    check('marginal_and_original_parent_counts_%d'%case_id,got['fine_pair_counts']==[len(coarse)]*len(fine) and got['coarse_pair_counts']==[len(fine)]*len(coarse) and got['middle_fine_counts']==[sum(fm[f]==m for f in fine) for m in middle] and [middle[p] for p in got['fine_parent_positions']]==[fm[f] for f in fine])
native_cap=plan(list(range(256)),[i//4 for i in range(256)],[i//8 for i in range(64)],[256,64,8])
check('native_capacity_metadata_2048_real_pairs',native_cap['pair_count']==2048 and len(native_cap['middle_ids'])==64 and len(native_cap['coarse_ids'])==8)

def vector_map(a,b,own,other,bias):
    out=[own*a[j]+other*b[(j+1)%len(a)]+bias for j in range(len(a))]
    return [x*x+x for x in out]
def mean_rows(rows,c):return [sum(row[j] for row in rows)/len(rows) for j in range(c)]
def actual_vs_oracle(scenes,widths):
    batch=len(scenes);c=2
    values=[[[[F(1+5*bi+3*level+2*i+j,11) for j in range(c)] for i in range(k)] for bi in range(batch)] for level,k in enumerate(widths)]
    banks=[T(value,(batch,widths[level],c)) for level,value in enumerate(values)]
    ids=[[T(scene[level]) for scene in scenes] for level in range(3)]
    pair_map=Map(2,3,1);middle_map=Map(4,5,7);activation=Activation()
    owner=SimpleNamespace(channels=c,pair_map=pair_map,middle_map=middle_map,activation=activation)
    actual=core['actual_forward'](owner,banks,ids)
    want=[[F(0)]*len(x.v) for x in banks];total_pairs=0;total_middle=0;coupled=True
    for bi,(points,fm,mc) in enumerate(scenes):
        fine=sorted(set(points));middle=sorted({fm[f] for f in fine});coarse=sorted({mc[m] for m in middle})
        if not fine:continue
        # Direct original-ID nested loop, independent from production packed maps.
        q={(f,co):vector_map(values[0][bi][f],values[2][bi][co],2,3,1) for f in fine for co in coarse}
        fd={f:mean_rows([q[f,co] for co in coarse],c) for f in fine}
        cd={co:mean_rows([q[f,co] for f in fine],c) for co in coarse}
        md={m:vector_map(values[1][bi][m],mean_rows([fd[f] for f in fine if fm[f]==m],c),4,5,7) for m in middle}
        for level,rows in enumerate((fd,md,cd)):
            for original_id,row in rows.items():
                start=(bi*widths[level]+original_id)*c;want[level][start:start+c]=row
        total_pairs+=len(q);total_middle+=len(middle)
        coupled&=mean_rows(list(fd.values()),c)==mean_rows(list(cd.values()),c)
    correct_calls=pair_map.rows==([total_pairs] if total_pairs else []) and middle_map.rows==([total_middle] if total_pairs else []) and activation.calls==(2 if total_pairs else 0)
    return actual,want,correct_calls,coupled
scenes=[([0],[0],[0]),([0,1,2,3],[0,0,0,1],[0,1]),([0,2,4],[2,0,2,1,3],[1,0,2,1]),([],[],[])]
for i,batch in enumerate(([scenes[0]],[scenes[1]],[scenes[2]],[scenes[3],scenes[1],scenes[2]],[],[scenes[3]])):
    actual,want,calls,coupled=actual_vs_oracle(list(batch),(7,5,4))
    check('actual_forward_independent_scene_original_ID_oracle_%d'%i,all(x.v==want[level] for level,x in enumerate(actual)) and calls)
    if i in (1,3):check('same_q_marginal_real_algebra_description_%d'%i,coupled)
single=actual_vs_oracle([scenes[0]],(7,5,4))[0]
duplicate=actual_vs_oracle([([0,0,0],[0],[0])],(7,5,4))[0]
check('point_multiplicity_does_not_reweight_messages',all(x.v==y.v for x,y in zip(single,duplicate)))
q=T([[1,3],[5,7],[9,11],[20,30]])
fmean=core['equal_message_means'](q,[0,0,1,1],[2,2])
cmean=core['equal_message_means'](q,[0,1,0,1],[2,2])
check('fine_coarse_mean_axes_are_distinct',fmean.v==[F(3),F(5),F(29,2),F(41,2)] and cmean.v==[F(5),F(7),F(25,2),F(37,2)])
invalid=[([-1],[0],[0],[1,1,1]),([True],[0],[0],[1,1,1]),([1],[0],[0],[1,1,1]),([0],[],[0],[1,1,1]),([0],[1],[0],[1,2,1]),([0],[0],[1],[1,1,1]),([],[],[],[1,True,1]),([],[0,0],[0],[1,1,1])]
rejected=0
for args in invalid:
    try:plan(*args)
    except ValueError:rejected+=1
check('eight_invalid_metadata_cases_rejected',rejected==len(invalid))
for p in MODEL.glob('*.py'):compile(p.read_text(encoding='utf-8'),str(p),'exec')
check('eight_model_sources_compile_without_import',len(list(MODEL.glob('*.py')))==8)
copies=['__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py']
check('six_original_model_sources_byte_identical',all((MODEL/name).read_bytes()==(BASE/name).read_bytes() for name in copies))
config=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_fcb'/(NAME+'_fcb.yaml')
check('native_YAML_byte_identical',config.read_bytes()==(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml')).read_bytes())
bt=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'));nt=ast.parse((MODEL/'hier_postprocess.py').read_text(encoding='utf-8'))
def methods(tree):return {(cl.name,fn.name):ast.dump(fn) for cl in tree.body if isinstance(cl,ast.ClassDef) for fn in cl.body if isinstance(fn,ast.FunctionDef)}
bm,nm=methods(bt),methods(nt)
check('only_CTF_constructor_and_forward_changed',[key for key in bm if bm[key]!=nm[key]]==[('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')])
def ctor(tree):return next(fn for cl in tree.body if isinstance(cl,ast.ClassDef) and cl.name=='C2F_ClusterAttn_CTF' for fn in cl.body if isinstance(fn,ast.FunctionDef) and fn.name=='__init__')
bctor,nctor=ctor(bt),ctor(nt)
check('original_constructor_prefix_RNG_consumption',all(ast.dump(x)==ast.dump(y) for x,y in zip(bctor.body,nctor.body)) and len(nctor.body)>len(bctor.body))
hsource=(MODEL/'hier_postprocess.py').read_text(encoding='utf-8')
check('CPU_fork_original_three_LN_and_raw_skips','torch.random.fork_rng(devices=[])' in hsource and 'self.cluster_ffn_norm[lvl](cf)' in hsource and 'cf + deltas[lvl]' in hsource)
check('features_not_detached',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('detach','cpu') for n in ast.walk(forward)))
check('source_parameter_MAC_arithmetic',2*(2*256*256+256)==262656 and (256*8+64)*2*256*256==276824064 and (256+64+8)*8*256*256==171966464)
index=json.loads((HERE.parent/'candidate_route_index.json').read_text(encoding='utf-8'))
check('M223_and_unique_CID_unused',not any(x.get('id')=='hierarchy-fine-coarse-complete-bipartite-composition' or str(x.get('experiment_id','')).startswith('M223') for x in index))
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','candidate_id':'hierarchy-fine-coarse-complete-bipartite-composition','recorded_at':datetime.now(timezone.utc).isoformat(),
    'check_count':len(checks),'checks':checks,'actual_forward_carrier_cases':6,'invalid_metadata_cases':8,
    'source_files':{p.name:sha(p) for p in MODEL.glob('*.py')},'Torch':False,'GELU_FP32_autograd_native_resources':'NOT_RUN',
    'scope':'Actual production plan and forward AST use a Fraction/list numerical carrier compared with independent scene-local original-ID Cartesian pair/original-parent dictionary formulas. Coupled marginal algebra is descriptive, not a new native numerical gate. Only old carrier definitions were read; old suites were not executed.'}
(HERE/'static_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'check_count':len(checks),'report':str(HERE/'static_validation.json')}))
