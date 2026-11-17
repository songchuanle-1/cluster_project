"""Small ELC observer/schema checks only; no model/runtime import, Torch or remote calls."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
CHECKS=[]
def check(name,value):
    if not value:raise AssertionError(name)
    CHECKS.append(name)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(p):return ast.parse(p.read_text(encoding='utf-8'))
def function(t,name):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
def dump(n):return ast.dump(n,include_attributes=False)
def extract(nodes,scope):exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes),type_ignores=[])),'actual_ELC_observer_AST','exec'),scope)

def main():
    wt=tree(HERE/'worker.py');rt=tree(HERE/'native_runtime.py');oldwt=tree(ORIGIN/'worker.py');oldrt=tree(ORIGIN/'native_runtime.py')
    for p in HERE.rglob('*.py'):compile(p.read_bytes(),str(p),'exec')
    check('all private Python source compiles without importing entries',True)
    check('complete original resources function AST unchanged',dump(function(wt,'resources'))==dump(function(oldwt,'resources')))
    old_functions={n.name:n for n in oldrt.body if isinstance(n,ast.FunctionDef)}
    new_functions={n.name:n for n in rt.body if isinstance(n,ast.FunctionDef)}
    check('nine original runtime function names preserved',new_functions.keys()==old_functions.keys() and len(new_functions)==9)
    for name,n in new_functions.items():
        expected=dump(old_functions[name]).replace('SFC native preparation','ELC native preparation')
        check('original runtime '+name+' body preserved except diagnostic identity',dump(n)==expected)
    manifest=json.loads((HERE/'manifest_template.json').read_text(encoding='utf-8'))
    binding=json.loads((HERE/'source_version_binding.json').read_text(encoding='utf-8'))
    check('formal source18e/parent-runtimec9 separated from current0314',binding['code_commit']=='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324' and binding['parent_commit']==binding['runtime_expected_commit']=='c9be548699cd66bf68badff9ae6198a03eafa142' and manifest['base_reference_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33')
    active=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
    check('ten active template fields remain NULL and no active artifacts',all(manifest[k] is None for k in active) and not any((HERE/n).exists() for n in ('native_manifest.json','lease.json','adapter_release.json')))
    check('all twelve diagnostic hashes actual',len(manifest['diagnostic_files'])==12 and all(sha(HERE/n)==h for n,h in manifest['diagnostic_files'].items()))
    check('exact unchanged candidate source8/YAML and frozen source9 maps',len(binding['source_files'])==9 and all(sha(HERE/'candidate_model'/n)==h for n,h in binding['candidate_source_hashes'].items()) and sha(HERE/'candidate.yaml')==binding['candidate_config_sha256']=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
    for key in ('source_preparation','native_protocol','isolated_source_version','isolated_source_version_independent_review','independent_source_review'):
        ref=binding[key];assert sha(ROOT/ref['path'])==ref['sha256'],key
    check('real source/protocol/proof/actual sourcepeer refs match',True)
    helper=tree(HERE/'candidate_model/edge_line_graph.py');scope={'copy':copy}
    extract([function(helper,'build_edge_line_graph_plan'),function(helper,'build_edge_rounds'),function(wt,'elc_plan_observation'),function(wt,'elc_rounds_observation'),function(wt,'elc_coverage_preflight')],scope)
    members=[([],[],[]),([0],[0],[0]),([1,3,4],[0,2,1,0,2],[1,0,1])]
    plans=[scope['build_edge_line_graph_plan'](*values,[6,4,3]) for values in members]
    check('actual producer plans accepted by new observer on empty/D1/D3 metadata',all(scope['elc_plan_observation'](p,m)==p for p,m in zip(plans,members)))
    rounds=scope['build_edge_rounds'](plans)
    check('actual producer rounds/edge-denominators accepted without forced D3 gate',scope['elc_rounds_observation'](plans,rounds) and [len(r['receivers']) for r in rounds]==[7,5,5])
    check('all-empty coverage is INCONCLUSIVE before watches, singleton path is legal',not scope['elc_coverage_preflight']([members[0]])['true_supported_core_possible'] and scope['elc_coverage_preflight']([members[0],members[1]])['true_supported_core_possible'])
    wrong=copy.deepcopy(rounds);wrong[0]['counts'][0]+=1
    try:scope['elc_rounds_observation'](plans,wrong)
    except AssertionError:pass
    else:raise AssertionError('wrong mean denominator accepted')
    check('wrong producer mean-denominator metadata rejected',True)
    smoke=function(wt,'smoke');nested={n.name:n for n in ast.walk(smoke) if isinstance(n,ast.FunctionDef)}
    class Op:
        def __init__(self,shape,tag):self.shape=shape;self.tag=tag;self.requires_grad=False
    class Index:
        def __init__(self,values):self.values=values
        def detach(self):return self
        def cpu(self):return self
        def tolist(self):return self.values
    counts={'mean':0,'incident':0,'select':0,'copy':0}
    state={};att=SimpleNamespace(edge_line_graph=SimpleNamespace(channels=2))
    def original_select(tensor,dim,index,*a,**kw):counts['select']+=1;return Op((len(index.values),2),'actual_select_'+str(counts['select']))
    def original_copy(tensor,dim,index,source,*a,**kw):counts['copy']+=1;return Op(tensor.shape,'actual_copy_'+str(counts['copy']))
    ns={'state':state,'att':att,'summary':lambda x:{'finite':True,'shape':list(x.shape)},'fingerprint':lambda torch,x:x.tag,
        'torch':None,'copy':copy,'lite_watch':lambda *a:None,'original_select':original_select,'original_copy':original_copy}
    extract([nested[n] for n in ('observed_select','observed_mean','observed_incident','observed_copy')],ns)
    plan=plans[1];round_plan=scope['build_edge_rounds']([plan])[0];old=Op((2,2),'old E state')
    record={'primitive_calls':[],'mean_calls':[],'incident_mean_calls':[],'round_calls':[]}
    context={'record':record,'current_state_ref':old,'rounds':[round_plan],'round_index':0,'phase':'own','mean_count':0,
        'plans_ref':[plan],'node_count':3,'incident_count':0,'state_write_count':0,'pending_round':{},'GELU_ref':Op((2,2),'actual GELU')}
    state['elc_context']=context
    def original_mean(tensor,r):
        counts['mean']+=1
        for bucket in r['endpoint_buckets']:ns['observed_select'](tensor,0,Index(bucket['edges']))
        return mean_output
    mean_output=Op((2,2),'actual mean return');ns['original_mean']=original_mean
    own=ns['observed_select'](old,0,Index(round_plan['receivers']))
    actual=ns['observed_mean'](old,round_plan)
    check('actual adjacent-mean callback calls original once and returns same object',counts['mean']==1 and actual is mean_output and context['mean_ref'] is mean_output and context['phase']=='cell')
    context['phase']='mean_ready';before=counts.copy()
    try:ns['observed_mean'](Op((2,2),'wrong state'),round_plan)
    except AssertionError:pass
    else:raise AssertionError('stale state accepted')
    check('stale OLDstate refused before original mean',counts==before)
    context['phase']='state_write'
    copied=ns['observed_copy'](old,0,Index(round_plan['receivers']),context['GELU_ref'])
    check('one actual functional replacement returns original object and becomes new state',counts['copy']==1 and copied is context['current_state_ref'] and context['phase']=='incident_ready')
    incident_output=Op((3,2),'actual incident mean return')
    def original_incident(tensor,ps):
        counts['incident']+=1;sources=[];offset=0
        for p in ps:
            for incident in p['incident']:sources.extend(offset+e for e in incident)
            offset+=len(p['edges'])
        ns['observed_select'](tensor,0,Index(sources));return incident_output
    ns['original_incident']=original_incident
    got=ns['observed_incident'](copied,context['plans_ref'])
    check('actual incident-mean callback once and same return passed to final readout',counts['incident']==1 and got is incident_output and context['node_state_ref'] is got and context['phase']=='final_scatter')
    # Execute only the actual installation/finally AST, with opaque owners and an injected train error.
    class Owner:
        inherited=lambda self:None
    owner=Owner();original=object();replacement=object();owner.method=original;owner.inherited=replacement
    removed=[];flushed=[];closed=[]
    hook=SimpleNamespace(remove=lambda:removed.append(True));writer=SimpleNamespace(flush=lambda:flushed.append(True),close=lambda:closed.append(True))
    def fail(*a):raise RuntimeError('injected software train sentinel')
    cleanup={'installations':[(owner,'method',replacement)],'global_replacements':[(owner,'method',original)],'replacements':[(owner,'inherited')],
        'hooks':[hook],'state':{'elc_context':object()},'writer':writer,'train':SimpleNamespace(train=fail),
        'model':None,'TwoNativeBatches':lambda x:x,'loader':None,'optimizer':None,'scheduler':None,'cfg':None,'logger':None,'torch':None}
    try_node=next(n for n in smoke.body if isinstance(n,ast.Try))
    try:extract([try_node],cleanup)
    except RuntimeError as e:assert str(e)=='injected software train sentinel'
    check('actual finally restores global methods and inherited overrides on failure',owner.method is original and 'inherited' not in vars(owner) and removed==[True])
    check('actual finally clears active context and closes writer on failure',cleanup['state']=={} and flushed==closed==[True])
    # Actual version-guard AST, without imports/entry/file/NVML/Torch operations.
    names={'DRAFT_EXECUTION_DISABLED','CANDIDATE_COMMIT','SOURCE_PARENT_COMMIT','SOURCE_PREPARATION_SHA256','RUNTIME_EXPECTED_COMMIT'}
    def prefix(t):return [n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='require_promoted_version' or isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id in names for v in n.targets)]
    wip={'re':re};extract(prefix(tree(HERE/'unversioned_disabled_wip/native_runtime.py')),wip)
    try:wip['require_promoted_version']()
    except RuntimeError:pass
    else:raise AssertionError('disabled/unversioned runtime accepted')
    check('preserved WIP True/None guard rejects before manifest/imports',wip['DRAFT_EXECUTION_DISABLED'] is True and wip['CANDIDATE_COMMIT'] is None)
    formal={'re':re};extract(prefix(rt),formal);formal['require_promoted_version']()
    check('formal False declares actual compatible version, not a current lease',formal['DRAFT_EXECUTION_DISABLED'] is False and formal['CANDIDATE_COMMIT']==binding['code_commit'] and formal['SOURCE_PARENT_COMMIT']==binding['parent_commit'])
    reads=[]
    class Absent:
        def __truediv__(self,name):assert name=='native_manifest.json';return self
        def read_text(self):reads.append('native_manifest.json');raise FileNotFoundError('No fresh active manifest')
    manifest_assignment=next(n for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='MANIFEST' for v in n.targets))
    try:extract([manifest_assignment],{'json':json,'STAGE':Absent()})
    except FileNotFoundError:pass
    else:raise AssertionError('missing active manifest accepted')
    check('actual active-manifest assignment refuses absence without Torch/NVML/process imports',reads==['native_manifest.json'])
    worker_text=(HERE/'worker.py').read_text(encoding='utf-8')
    check('dynamic common names/shapes/count/hash retains original LN',all(s in worker_text for s in ("'names':list(common)","'shapes':{n:list(p.shape)","'tensor_count':len(common)","'sha256':fingerprint(torch,common)","'dec.cluster_att.edge_line_graph.'")))
    check('wholecore gradient/update gates and four descriptive columns only',all(s in worker_text for s in ('whole_edge_line_graph_weight_gradient','whole_edge_line_graph_weight_updated','whole_edge_line_graph_module_updated','other_edge_mean_columns','individual maps/weights/rows/bias may be zero')) and 'abs_max' not in ast.get_source_segment(worker_text,nested['parameter_blocks']))
    check('original native train invocation preserved exactly',dump(next(n for n in ast.walk(smoke) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='train' and n.func.attr=='train'))==dump(next(n for n in ast.walk(function(oldwt,'smoke')) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='train' and n.func.attr=='train')))
    out={'status':'PASS_SOFTWARE_PREPARATION_ONLY_NOT_NATIVE','check_count':len(CHECKS),'checks':CHECKS,'Torch':False,'native':'NOT_RUN','resources':'NOT_RUN',
        'scope':'Small AST/hash/metadata and actual observer callbacks with opaque operator return objects; original-call count/identity, stale-state rejection and injected-failure finally only. No full producer/model/Linear/GELU/FP32/autograd/native execution, old27/151 suite or remote operations.',
        'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),'manifest_template_sha256':sha(HERE/'manifest_template.json'),'source_version_binding_sha256':sha(HERE/'source_version_binding.json')}
    (HERE/'static_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':out['status'],'check_count':len(CHECKS),'Torch':False}))

if __name__=='__main__':
    try:main()
    except Exception as e:
        p=HERE/'static_validation_failed.json'
        if p.exists():raise RuntimeError('Preserve prior failed software result; use a new version') from e
        p.write_text(json.dumps({'status':'FAILED_SOFTWARE_PREPARATION_CHECK','checks_before_failure':CHECKS,'error':type(e).__name__+': '+str(e),'Torch':False},indent=2)+'\n',encoding='utf-8');raise
