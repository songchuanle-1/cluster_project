"""Small actual WFC production AST/list checks; never import Torch or run an old suite."""
from pathlib import Path
from fractions import Fraction as Q
from copy import deepcopy
from itertools import product,combinations
from types import SimpleNamespace
import ast,hashlib,json,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
DEST=HERE/'staged_repository/framework/model/Quard_model'/(BASE+'_wfc')
CHECKS=[]
def check(name,value):
    if not value:raise AssertionError(name)
    CHECKS.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

# Reuse definitions of four generic list-value primitives only. No old checker
# top-level bindings, production helper or old test main is executed.
carrier_ast=ast.parse((FROZEN/'static_check.py').read_text(encoding='utf-8'))
carrier=[n for n in carrier_ast.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('size','T','stack','cat')]
exec(compile(ast.fix_missing_locations(ast.Module(body=carrier,type_ignores=[])),'generic_list_carrier_definitions_only','exec'))

class FactorMap:
    def __init__(self):self.calls=[]
    def vector(self,row):
        out=[]
        for k in range(len(row)//2):
            value=Q(k+1,13)
            for j,x in enumerate(row):value+=Q((k+1)*(j+2),29)*x
            out.append(value)
        return out
    def __call__(self,x):
        self.calls.append(deepcopy(x));c=x.shape[1]//2
        return T([v for i in range(x.shape[0]) for v in self.vector(x.data[i*2*c:(i+1)*2*c])],(x.shape[0],c))
def nonlinear(x):return T([v+v*v/Q(20) for v in x.data],x.shape)
def gelu(x):return T([float(v)*0.5*(1+math.erf(float(v)/math.sqrt(2))) for v in x.data],x.shape)
def left_mean(rows,c):
    total=[Q(0)]*c
    for row in rows:total=[a+b for a,b in zip(total,row)]
    return [v/len(rows) for v in total]

source=(DEST/'wedge_factor.py').read_text(encoding='utf-8');tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
klass=next(n for n in tree.body if isinstance(n,ast.ClassDef));forward=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
ns={'torch':SimpleNamespace(tensor=lambda x,**kw:T(x),stack=stack,cat=cat,long='long')}
exec(compile(ast.fix_missing_locations(ast.Module(body=functions+[forward],type_ignores=[])),'actual_WFC_production_AST','exec'),ns)
WIDTHS=(6,4,3);CHANNELS=2
SCENES=[([1],[0,2],[0,0,1]),([0,1],[0,0],[0]),([0,1],[0,1],[0,0]),([1,3,4],[0,2,1,0,2],[1,0,1]),([],[],[])]

def oracle(values,scene,operator,activation):
    points,fm,mc=scene;fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    keys=[(l,i) for l,ids in enumerate((fine,middle,coarse)) for i in ids];adj={key:set() for key in keys}
    for a,b in ([( (0,i),(1,fm[i]) ) for i in fine]+[( (1,j),(2,mc[j]) ) for j in middle]):adj[a].add(b);adj[b].add(a)
    received={key:[] for key in keys};count=0
    for center in sorted(keys):
        for a,c in combinations(sorted(adj[center]),2):
            cv=values[center[0]][center[1]];av=values[a[0]][a[1]];zv=values[c[0]][c[1]]
            q=activation(T(operator.vector(cv+[x+y for x,y in zip(av,zv)]))).data;count+=1
            for node in (a,center,c):received[node].append(q)
    result=[[[Q(0)]*CHANNELS for _ in range(w)] for w in WIDTHS]
    for (level,i),messages in received.items():result[level][i]=left_mean(messages,CHANNELS)
    return result,count

def run_case(label,scenes,activation=nonlinear,swap_fine=False,perturb=False):
    batch=len(scenes);c=CHANNELS
    values=[[[[Q((b+1)*7+(l+1)*3+i+k,41) for k in range(c)] for i in range(w)] for b in range(batch)] for l,w in enumerate(WIDTHS)]
    if swap_fine:values[0][0][0],values[0][0][1]=values[0][0][1],values[0][0][0]
    if perturb:values[0][0][1]=[v+Q(1,3) for v in values[0][0][1]]
    levels=[T([v for scene in rows for row in scene for v in row],(batch,w,c)) for rows,w in zip(values,WIDTHS)]
    ids=[[T(scene[level]) for scene in scenes] for level in range(3)]
    op=FactorMap();obj=SimpleNamespace(channels=c,factor_map=op,activation=activation)
    actual=ns['forward'](obj,levels,ids);expected=[[] for _ in WIDTHS];wedges=0
    for b,scene in enumerate(scenes):
        out,n=oracle([values[l][b] for l in range(3)],scene,op,activation);wedges+=n
        for l in range(3):expected[l].extend(v for row in out[l] for v in row)
    check(label+':actual production forward equals original-ID direct wedge oracle',all(v.data==e for v,e in zip(actual,expected)))
    check(label+':one global learned map iff nonempty true factors',len(op.calls)==int(wedges>0) and (not op.calls or op.calls[0].shape==(wedges,2*c)))
    return actual,op

def main():
    outputs=[]
    for i,scene in enumerate(SCENES):outputs.append(run_case('single'+str(i),[scene])[0])
    run_case('mixed hole/nonempty/empty batches',[SCENES[0],SCENES[4],SCENES[3]])
    run_case('zero batch',[])
    run_case('scalar erf GELU branched star',[SCENES[1]],gelu)
    chain=outputs[0]
    check('single true chain has one shared q in all three delta roles',chain[0].data[2:4]==chain[1].data[4:6]==chain[2].data[2:4])
    original=outputs[1];swapped,_=run_case('swap two fine endpoints',[SCENES[1]],swap_fine=True)
    check('endpoint feature swap permutes fine outputs and preserves center/coarse',swapped[0].data[:2]==original[0].data[2:4] and swapped[0].data[2:4]==original[0].data[:2] and swapped[1].data==original[1].data and swapped[2].data==original[2].data)
    altered,_=run_case('controlled other-fine bank variable',[SCENES[1]],perturb=True)
    check('controlled nonlinear carrier fine readout sees sibling even with ancestors fixed',altered[0].data[:2]!=original[0].data[:2])
    duplicate,_=run_case('duplicate original point IDs',[([1,1,1],[0,2],[0,0,1])])
    check('duplicate physical points do not duplicate or reweight a factor',all(a.data==b.data for a,b in zip(duplicate,chain)))
    p=ns['build_wedge_factor_plan'](list(range(256)),[i//4 for i in range(256)],[i//8 for i in range(64)],[256,64,8])
    check('native-cap balanced metadata factor count and three-node incidence',p['factor_count']==864 and sum(map(len,p['incidence']))==3*864 and all(p['incidence']))
    check('all factors have distinct nodes and original center-neighbor relation',all(len(set(w))==3 and w[0] in p['neighbors'][w[1]] and w[2] in p['neighbors'][w[1]] for w in p['wedges']))
    invalid=[([True],[0],[0],WIDTHS),([-1],[0],[0],WIDTHS),([6],[0],[0],WIDTHS),([1],[0],[0],WIDTHS),([0],[4],[0],WIDTHS),([0],[0],[],WIDTHS),([0],[0],[0],(6,4,True)),([0],[0],[0],(6,4))]
    for args in invalid:
        try:ns['build_wedge_factor_plan'](*args)
        except ValueError:pass
        else:raise AssertionError('invalid metadata accepted')
    check('eight invalid ID/membership/bank metadata cases reject',True)
    for pth in DEST.glob('*.py'):compile(pth.read_bytes(),str(pth),'exec')
    check('exact eight independent model files compile without import',len(list(DEST.glob('*.py')))==8)
    old=FROZEN/'staged_repository/framework/model/Quard_model'/(BASE+'_elc')
    check('six untouched model files byte-equal frozen originals',all((DEST/n).read_bytes()==(old/n).read_bytes() for n in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py')))
    yaml=next((HERE/'staged_repository/configs').rglob('*.yaml'))
    check('native YAML remains exact original a18 bytes',sha(yaml)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    author=ast.parse((HERE/'author_packet.py').read_text(encoding='utf-8'));scope={'Path':Path,'ast':ast,'hashlib':hashlib,'FROZEN':FROZEN,'OLD':old,'ORIGINAL_HIER_SHA':'7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'}
    restore=next(n for n in author.body if isinstance(n,ast.FunctionDef) and n.name=='restored_original_hier');exec(compile(ast.fix_missing_locations(ast.Module(body=[restore],type_ignores=[])),'frozen_M95_restore_only','exec'),scope)
    original,_=scope['restored_original_hier']();actual=(DEST/'hier_postprocess.py').read_text(encoding='utf-8')
    def methods(s):return {(c.name,f.name):ast.dump(f,include_attributes=False) for c in ast.parse(s).body if isinstance(c,ast.ClassDef) for f in c.body if isinstance(f,ast.FunctionDef)}
    a,b=methods(original),methods(actual);allowed={('C2F_ClusterAttn_CTF','__init__'),('C2F_ClusterAttn_CTF','forward')}
    check('original M95 recovery pinned; only CTF ctor/forward method AST changes',a.keys()==b.keys() and all(a[k]==b[k] for k in a if k not in allowed))
    check('original constructor FFN/LN order then CPUfork then Identity replacement',actual.index('self.cluster_ffn_norm')<actual.index('with torch.random.fork_rng(devices=[])')<actual.index('self.cluster_ffn = nn.ModuleList([nn.Identity()'))
    check('source parameter/MAC conservative arithmetic only',2*256*256+256==131328 and 864*2*256*256==113246208 and (math.comb(257,2)+math.comb(64,2))==34912)
    result={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(CHECKS),'checks':CHECKS,'actual_forward_carrier_cases':11,'invalid_metadata_cases':len(invalid),'Torch':False,'native':'NOT_RUN','resources':'NOT_RUN',
        'carrier_scope':'Actual production plan/mean/forward AST with exact rational nonlinear/list carrier and one scalar-erf-GELU/list case, against direct original-ID keyed neighbor-pair oracle. Generic list definitions reused only; no old test main/production helper/test suite executed. Not actual Torch/Linear/GELU/FP32/autograd/native behavior.',
        'primary_or_user_dirty_files_read':False,'source_file_hashes':{p.relative_to(HERE).as_posix():sha(p) for p in sorted((HERE/'staged_repository').rglob('*')) if p.is_file()}}
    (HERE/'static_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'check_count':len(CHECKS),'actual_forward_carrier_cases':11,'Torch':False}))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        p=HERE/'static_validation_failed.json';assert not p.exists(),'Preserve prior failure and create a versioned result'
        p.write_text(json.dumps({'status':'FAILED_SOFTWARE_CHECK','error':type(exc).__name__+': '+str(exc),'checks_before_failure':CHECKS,'Torch':False,'source_file_hashes':{q.relative_to(HERE).as_posix():sha(q) for q in sorted((HERE/'staged_repository').rglob('*')) if q.is_file()}},indent=2)+'\n',encoding='utf-8');raise
