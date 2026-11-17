"""Independent exact-rational hierarchy oracle for frozen LFT AST, no Torch."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import product
from types import SimpleNamespace
import argparse, ast, hashlib, json, math

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREP=HERE/'lft_candidate_prepare'
MODEL=PREP/'staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_lft/nonlinear_lifting.py'
CARRIER=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare/static_check.py'
CHECKS=[]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def check(name,value):
    if not value:raise AssertionError(name)
    CHECKS.append(name)

def load_functions():
    tree=ast.parse(CARRIER.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('size','T','stack','cat')]
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'list_primitives_only','exec'),globals())
    def sub(self,other):
        assert self.shape==other.shape
        return T([a-b for a,b in zip(self.data,other.data)],self.shape)
    T.__sub__=sub
    tree=ast.parse(MODEL.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef))
    nodes.append(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward'))
    ns={'torch':SimpleNamespace(tensor=lambda x,**kw:T(x),stack=stack,cat=cat,long='long')}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual_frozen_LFT_functions_only','exec'),ns)
    return ns

def map_vector(role,row,zero=False):
    if zero:return [Q(0),Q(0)]
    return [Q(role+1,23)+Q(role+2,11)*row[0]+Q(3-role,13)*row[1],
            Q(-role-2,29)+Q(-role-1,17)*row[0]+Q(role+4,19)*row[1]]

def activation_value(value):return value+value*value/Q(37)

class Map:
    def __init__(self,role,zero=False):self.role=role;self.zero=zero;self.calls=[]
    def __call__(self,values):
        self.calls.append(values.shape)
        return T([v for i in range(values.shape[0])
                  for v in map_vector(self.role,values.data[2*i:2*i+2],self.zero)],values.shape)

def ffn_vector(level,row,identity=False):
    if identity:return list(row)
    return [row[k]+Q(level+1,41)*row[k]*row[k]+row[1-k]/43 for k in range(2)]

class FFN:
    def __init__(self,level,identity=False):self.level=level;self.identity=identity;self.calls=[]
    def __call__(self,values):
        self.calls.append(values.shape)
        return T([v for i in range(values.shape[0])
                  for v in ffn_vector(self.level,values.data[2*i:2*i+2],self.identity)],values.shape)

def activate(values):return T([activation_value(v) for v in values.data],values.shape)
def plus(a,b):return [x+y for x,y in zip(a,b)]
def minus(a,b):return [x-y for x,y in zip(a,b)]
def mean(rows):return [sum((row[k] for row in rows),Q(0))/len(rows) for k in range(2)]

def oracle(values,scene,identity=False,zero=False):
    points,fm,mc=scene
    fine=sorted(set(points));middle=sorted({fm[i] for i in fine});coarse=sorted({mc[j] for j in middle})
    P=lambda role,row:[activation_value(v) for v in map_vector(role,row,zero)]
    df={i:minus(values[0][i],P(0,values[1][fm[i]])) for i in fine}
    bt={j:plus(values[1][j],P(1,mean([df[i] for i in fine if fm[i]==j]))) for j in middle}
    dm={j:minus(bt[j],P(2,values[2][mc[j]])) for j in middle}
    ct={k:plus(values[2][k],P(3,mean([dm[j] for j in middle if mc[j]==k]))) for k in coarse}
    Ff={i:ffn_vector(0,df[i],identity) for i in fine}
    Fm={j:ffn_vector(1,dm[j],identity) for j in middle}
    Fc={k:ffn_vector(2,ct[k],identity) for k in coarse}
    cp={k:minus(Fc[k],P(3,mean([Fm[j] for j in middle if mc[j]==k]))) for k in coarse}
    bp={j:minus(plus(Fm[j],P(2,cp[mc[j]])),P(1,mean([Ff[i] for i in fine if fm[i]==j]))) for j in middle}
    ap={i:plus(Ff[i],P(0,bp[fm[i]])) for i in fine}
    return (ap,bp,cp),(fine,middle,coarse)

def run_case(ns,label,scenes,identity=False,zero=False):
    widths=(6,4,3);batch=len(scenes)
    values=[[[[Q(61*b+11*l+3*i+2*k+1,53) for k in range(2)]
               for i in range(width)] for b in range(batch)] for l,width in enumerate(widths)]
    levels=[T([v for scene in rows for row in scene for v in row],(batch,width,2))
            for rows,width in zip(values,widths)]
    ids=[[T(scene[level]) for scene in scenes] for level in range(3)]
    maps=[Map(i,zero) for i in range(4)];ffns=[FFN(i,identity) for i in range(3)]
    obj=SimpleNamespace(channels=2,predict_fine=maps[0],update_middle=maps[1],
                        predict_middle=maps[2],update_coarse=maps[3],activation=activate)
    actual=ns['forward'](obj,levels,ids,ffns)
    expected=[[] for _ in widths];totals=[0,0,0]
    for b,scene in enumerate(scenes):
        result,support=oracle([values[l][b] for l in range(3)],scene,identity,zero)
        plan=ns['build_lifting_plan'](*scene,widths)
        check(label+': real original support', tuple(plan[k] for k in ('fine_ids','middle_ids','coarse_ids'))==support)
        fm,mc=scene[1:]
        check(label+': equal-child original parent counts',
              plan['middle_fine_counts']==[sum(fm[i]==j for i in support[0]) for j in support[1]]
              and plan['coarse_middle_counts']==[sum(mc[j]==k for j in support[1]) for k in support[2]])
        for l,width in enumerate(widths):
            rows=[[Q(0)]*2 for _ in range(width)]
            for i,row in result[l].items():rows[i]=row
            expected[l].extend(v for row in rows for v in row)
            totals[l]+=len(support[l])
        if identity:
            check(label+': identity inner FFNs exact rational inverse only',
                  all(result[l][i]==values[l][b][i] for l in range(3) for i in support[l]))
        if zero:
            check(label+': zero P/U original FFN path only',
                  all(result[l][i]==ffn_vector(l,values[l][b][i],identity) for l in range(3) for i in support[l]))
    check(label+': actual packed production forward equals independent keyed hierarchy oracle',
          all(a.data==b for a,b in zip(actual,expected)))
    for i,count in enumerate((totals[1],totals[1],totals[2],totals[2])):
        check(label+': same P/U map used twice '+str(i),maps[i].calls==([(count,2)]*2 if totals[0] else []))
    for l in range(3):
        check(label+': original FFN once packed true rows '+str(l),ffns[l].calls==([(totals[l],2)] if totals[0] else []))
    check(label+': original output bank shapes', [a.shape for a in actual]==[(batch,w,2) for w in widths])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preparation-sha256',required=True);args=ap.parse_args()
    check('actual final prep SHA',sha(PREP/'preparation.json')==args.preparation_sha256)
    prep=json.loads((PREP/'preparation.json').read_text(encoding='utf-8'))
    for name,digest in prep['prepared_file_hashes'].items():check('frozen map '+name,sha(PREP/name)==digest)
    ns=load_functions()
    chain=([1],[0,2],[0,0,1]);mixed=([0,1,2,4,4],[0,0,1,1,3],[0,1,1,2]);holes=([1,4],[0,3,1,1,3],[0,0,1,2])
    for label,scenes,identity,zero in [('chain',[chain],False,False),('unequal-multiroot',[mixed],False,False),
                                     ('mixed-empty',[([],[],[]),mixed,holes],False,False),('zero-batch',[],False,False),
                                     ('identity-inner',[mixed,holes],True,False),('zero-predict-update',[mixed],False,True)]:
        run_case(ns,label,scenes,identity,zero)
    for label,scene,widths in [('bad-point',([6],[],[]),(6,4,3)),('missing-parent',([4],[0],[0]),(6,4,3)),
                                ('boolean-id',([True],[0],[0]),(6,4,3))]:
        try:ns['build_lifting_plan'](*scene,widths)
        except ValueError:check(label+' refused',True)
        else:raise AssertionError(label+' accepted')
    result={'status':'INDEPENDENT_LFT_PRODUCTION_AST_RATIONAL_ORIGINAL_ID_ORACLE_CHECKED_NOT_TORCH',
            'candidate_id':'hierarchy-nonlinear-lifting-analysis-synthesis','experiment_id':'M227-LFT',
            'preparation':{'path':(PREP/'preparation.json').relative_to(ROOT).as_posix(),'sha256':sha(PREP/'preparation.json')},
            'helper_sha256':sha(MODEL),'generic_list_carrier_sha256':sha(CARRIER),
            'check_count':len(CHECKS),'checks':CHECKS,'material_concerns':[],
            'scope':'Only frozen production function AST/list primitives with independent original-ID dictionary equations. Six rational cases including identity-inner and zero-P/U algebraic controls; no Torch/GELU/autograd/data/model/remote/GPU or old checker main. Identity exactness is Fraction algebra only, not a native FP32 or admission gate.'}
    out=HERE/'lft_independent_software.json'
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'passed':len(CHECKS),'sha256':sha(out)}))

if __name__=='__main__':main()
