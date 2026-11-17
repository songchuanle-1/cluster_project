"""Stdlib-only checks of actual CTS production plan and preserved wiring.

No model mirror or torch import. Boolean source sets independently audit graph
support/reachability/minimum depth; native tensor/autograd values stay unknown.
"""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import math
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
BASE_NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(BASE_NAME+'_cts')
BASE=ROOT/'Cluster/framework/model/Quard_model'/BASE_NAME
CHECKS=[];ASSERTIONS=0;VALID_PLAN_CALLS=0;ALIASED_MINUS=0

def check(ok,label):
    global ASSERTIONS
    ASSERTIONS+=1
    if not ok:raise AssertionError(label)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def node(tree,name,owner=None):
    body=tree.body if owner is None else next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==owner).body
    return next(n for n in body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)

def same(a,b):return ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)

def build_function():
    t=ast.parse((MODEL/'middle_triad.py').read_text(encoding='utf-8'));env={'math':math}
    exec(compile(ast.Module(body=[node(t,'build_triadic_plan')],type_ignores=[]),str(MODEL/'middle_triad.py'),'exec'),env)
    return env['build_triadic_plan'],t

def valid(build,centers,parents,supported,cap,label):
    global VALID_PLAN_CALLS,ALIASED_MINUS
    plan=build(centers,parents,supported,cap);VALID_PLAN_CALLS+=1
    active={i for i,yes in enumerate(supported) if yes};flat=[i for g in plan['groups'] for i in g['order']]
    check(set(flat)==active and len(flat)==len(active),label+' original supported IDs once')
    owner={i:g for g in plan['groups'] for i in g['order']};rank={i:r for g in plan['groups'] for r,i in enumerate(g['order'])}
    deps={i:{i} for i in active}
    for g in plan['groups']:
        n=len(g['order']);k=len(g['offsets'])
        check(g['order']==tuple(sorted(g['order'],key=lambda i:(*centers[i],i))),label+' deterministic geometry/original-ID order')
        check(all(parents[i]==g['parent'] for i in g['order']),label+' original parent membership')
        check(tuple(g['offsets'])==tuple(3**r for r in range(k)),label+' fixed powers3 not tuned dilation')
        check((k==0 and n==1) or (3**(k-1)<n<=3**k),label+' minimum integer ternary coverage rounds')
    for r,rows in enumerate(plan['rounds']):
        receivers=[x[2] for x in rows]
        expected_receivers={i for g in plan['groups'] if r<len(g['offsets']) for i in g['order']}
        check(set(receivers)==expected_receivers and len(receivers)==len(set(receivers)),label+' all active-stage receivers once')
        old={i:set(v) for i,v in deps.items()}
        for parent,d,own,plus,minus in rows:
            g=owner[own];n=len(g['order']);position=rank[own]
            check(parent==g['parent'] and d==3**r and 0<d<n,label+' actual stage/parent/offset')
            actual=[x for x in (own,plus,minus) if x is not None]
            check(len(actual)==len(set(actual)) and all(x in active and parents[x]==parent for x in actual),label+' no repeated real source/fake padding/crossparent')
            expected_set={g['order'][position],g['order'][(position+d)%n],g['order'][(position-d)%n]}
            check(set(actual)==expected_set,label+' modulo-neighbor dedup preserves original dependency set')
            check(plus==g['order'][(position+d)%n],label+' positive slot kept')
            if 2*d==n:
                check(minus is None,label+' duplicate negative slot is private zero');ALIASED_MINUS+=1
            else:check(minus==g['order'][(position-d)%n],label+' distinct negative source kept')
            deps[own]=set().union(*(old[i] for i in actual))
        for i in receivers:
            n=len(owner[i]['order']);k=len(owner[i]['offsets'])
            check(len(deps[i])<=3**(r+1),label+' three-input dependency upper bound')
            if r<k-1:check(len(deps[i])<n,label+' coverage not falsely attained with too few rounds')
    for i in active:check(deps[i]=={j for j in active if parents[j]==parents[i]},label+' complete final same-parent support')
    check(set(plan['singleton_ids'])=={g['order'][0] for g in plan['groups'] if len(g['order'])==1},label+' exact singleton original IDs')
    return plan

def run():
    expected={'__init__.py','backbone.py','dec.py','hier_postprocess.py','loss.py','middle_triad.py','network.py','sample_model.py'}
    check({p.name for p in MODEL.glob('*.py')}==expected,'eight independent model files')
    trees={}
    for p in sorted(MODEL.glob('*.py')):
        trees[p.name]=ast.parse(p.read_text(encoding='utf-8'));compile(trees[p.name],str(p),'exec');CHECKS.append('AST+compile '+p.name)
    for n in ['__init__.py','backbone.py','loss.py','network.py','sample_model.py']:check((MODEL/n).read_bytes()==(BASE/n).read_bytes(),'unchanged original byte '+n)
    yaml=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_cts'/(BASE_NAME+'_cts.yaml')
    check(yaml.read_bytes()==(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(BASE_NAME+'.yaml')).read_bytes(),'all original native YAML bytes')
    baseline=ast.parse((BASE/'hier_postprocess.py').read_text(encoding='utf-8'));candidate=trees['hier_postprocess.py']
    for own,method in [('SharedClusterBank','build_cluster_feats'),('PointCloudPartitioner','partition_points'),('PointCloudPartitioner','cluster_layer')]:check(same(node(baseline,method,own),node(candidate,method,own)),'original '+own+'.'+method+' AST')
    for cls in ['C2F_ClusterAttn_CTF_HCG','C2F_ClusterAttn_CTF_HCG_CSORT']:check(same(node(baseline,cls),node(candidate,cls)),'entire original '+cls+' AST')
    bfc=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4/new_candidate_prepare/staged_repository/framework/model/Quard_model'/(BASE_NAME+'_bfc')
    for n in ['hier_postprocess.py','dec.py']:
        s=(bfc/n).read_text(encoding='utf-8').replace('ParentButterflyTokenComposition','ParentCyclicTriadicStateComposition').replace('middle_butterfly','middle_triad').replace('BFC','CTS')
        check((MODEL/n).read_text(encoding='utf-8')==s,'only accepted cache/operator-namespace integration '+n)
    init=ast.unparse(node(candidate,'__init__','C2F_ClusterAttn_CTF'));forward=ast.unparse(node(candidate,'forward','C2F_ClusterAttn_CTF'))
    check('self.cluster_ffn[1] = nn.Identity()' in init and 'torch.random.fork_rng(devices=[])' in init,'original middle parameters removed/common RNG progression kept')
    check('refined = cf + self.middle_triad' in forward and 'self.cluster_ffn_norm[1](cf)' in forward,'only original middle delta replaced with original skip/LN')
    build,helper=build_function();f=ast.unparse(node(helper,'forward','ParentCyclicTriadicStateComposition'));ci=ast.unparse(node(helper,'__init__','ParentCyclicTriadicStateComposition'))
    check(ci.count('nn.Linear(')==1 and 'nn.Linear(3 * channels, channels)' in ci and 'nn.GELU()' in ci,'one shared3C toC and original GELU')
    check('for slot in (3, 4)' in f and 'if row[slot] is not None' in f and 'field = features.new_zeros((len(rows), self.channels))' in f,'private zero donors never realID0 fallback')
    check(f.index('fields = [state.index_select(0, own_ids)]')<f.index('mixed = self.activation(self.mix(torch.cat(fields, dim=-1)))')<f.index('state = state.index_copy(0, own_ids, mixed)'),'all three old-state fields gathered before one functional all-receiver scatter')
    check('features.detach' not in f and 'register_buffer' not in ast.unparse(helper),'no feature detach or registered geometry buffers')
    check('output = features.new_zeros((slots, self.channels))' in f and 'output = output.index_copy(0, ids, state.index_select(0, ids))' in f,'original-ID inverse scatter/unsupported pad zero delta')
    for n in range(129):valid(build,[(float((i*17)%131),float(i%3),float(-i)) for i in range(n)],[0]*n,[True]*n,128,'n'+str(n))
    CHECKS.append('every n0..128: minimum rounds, modulo alias dedup, overlapping old-state support/reachability')
    for n,offsets in [(1,()),(2,(1,)),(3,(1,)),(4,(1,3)),(6,(1,3)),(9,(1,3)),(10,(1,3,9)),(18,(1,3,9)),(54,(1,3,9,27)),(64,(1,3,9,27))]:
        check(build([(i,0,0) for i in range(n)],[0]*n,[True]*n,128)['groups'][0]['offsets']==offsets,'fixed exact offsets n'+str(n))
    cases=[([],[],[]), ([(0,0,0)]*7,[4,9,4,9,4,9,4],[True,False,True,False,False,True,True]),
      ([(i,0,0) for i in range(10)],[0,7,0,7,0,7,3,3,3,0],[True,True,False,True,True,False,True,True,False,True]),
      ([(0,0,0)]*9,[0,1,0,1,0,1,0,1,0],[True]*9), ([(i,0,0) for i in range(8)],[8]*8,[False]*8),
      ([(i,0,0) for i in range(6)],[0]*6,[True]*6), ([(i,0,0) for i in range(2)],[0,0],[True,True])]
    for i,args in enumerate(cases):valid(build,*args,64,'special'+str(i))
    for n in [3,6,17,64,65,128]:
        centers=[(i,i%3,-i) for i in range(n)];parents=[i%3 for i in range(n)];active=[i%5!=1 for i in range(n)];permutation=list(reversed(range(n)))
        original=build(centers,parents,active,128);permuted=build([centers[i] for i in permutation],[parents[i] for i in permutation],[active[i] for i in permutation],128)
        restore=lambda x:None if x is None else permutation[x]
        restored=[tuple((p,d,permutation[own],restore(plus),restore(minus)) for p,d,own,plus,minus in rows) for rows in permuted['rounds']]
        check(restored==list(original['rounds']),'unique-coordinate metadata permutation original-ID restore n'+str(n))
    invalid=[([],[],[],True),([],[],[],-1),([(0,0,0)],[0],[],64),([],[0],[True],64), ([(0,0,0)],[-1],[True],64),
      ([(0,0,0)],[True],[True],64), ([(0,0,0)],[0.0],[True],64), ([(0,0,0)],[0],[1],64),
      ([(math.nan,0,0)],[0],[True],64), ([(0,math.inf,0)],[0],[True],64), ([(0,0)],[0],[True],64),
      ([(False,0,0)],[0],[True],64), ([(0,0,0)],[0],[True],0), ([(i,0,0) for i in range(65)],[0]*65,[True]*65,64)]
    for i,args in enumerate(invalid):
        try:build(*args)
        except (ValueError,TypeError):CHECKS.append('metadata refusal '+str(i))
        else:raise AssertionError('bad metadata accepted'+str(i))
    check(3*256*256+256==196864 and 196864-525568==-328704,'exact source-only parameter arithmetic')
    check(len(build([(i,0,0) for i in range(64)],[0]*64,[True]*64,64)['rounds'])==4,'configured K64 at most4rounds')
    return {'status':'ACTUAL_STDLIB_PRODUCTION_PLAN_AND_STATIC_INTEGRATION_CHECKS_COMPLETED','assertions':ASSERTIONS,'production_valid_oracle_calls':VALID_PLAN_CALLS,'exhaustive_n':'0..128','minimum_rounds_checked':True,'negative_private_zero_alias_rows_observed':ALIASED_MINUS,'invalid_metadata_refusals':len(invalid),'special_oracle_cases':len(cases),'unique_geometry_permutation_cases':6,'checks':CHECKS,'source_hashes':{p.name:sha(p) for p in sorted(MODEL.glob('*.py'))},'YAML_sha256':sha(yaml),'torch_imported':('torch' in sys.modules),'native':'NOT_RUN','resources':'NOT_RUN','efficacy':'UNKNOWN','scope':'Actual stdlib production-plan execution plus independent dependency-set oracle and source AST/bytes. Not torch/autograd/FP32/value/resource validation. n65..128 use explicit helper test cap128; unchanged original native cap is64.'}

def main():
    result=run();owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
    assert owner['token']=='3824d9c96f6343e09d60362b4a00495b' and owner['deadline_at']=='2026-10-25T09:06:47.370222+00:00' and datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    result['recorded_at']=datetime.now(timezone.utc).isoformat()
    with (HERE/'static_validation.json').open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':result['status'],'assertions':result['assertions'],'valid_oracle_calls':VALID_PLAN_CALLS,'invalid_metadata_refusals':result['invalid_metadata_refusals'],'sha256':sha(HERE/'static_validation.json'),'torch_imported':result['torch_imported']}))

if __name__=='__main__':main()
