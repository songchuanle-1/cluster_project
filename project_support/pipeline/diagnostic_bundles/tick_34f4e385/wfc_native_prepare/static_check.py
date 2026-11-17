"""Bounded new WFC worker metadata/transparent-wrapper software checks only."""
from pathlib import Path
import ast, hashlib, json, copy, itertools, re
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
BASE=ROOT/'pipeline/diagnostic_bundles/tick_692b4575/elc_native_prepare'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)});assert condition,name
def funcs(path):
    return {n.name:n for n in ast.walk(ast.parse(path.read_text(encoding='utf-8'))) if isinstance(n,ast.FunctionDef)}
def dump(node):return ast.dump(node,include_attributes=False)
worker=funcs(HERE/'worker.py');oldworker=funcs(BASE/'worker.py')
runtime=funcs(HERE/'native_runtime.py');oldruntime=funcs(BASE/'native_runtime.py')
check('resources_full_original_AST',dump(worker['resources'])==dump(oldworker['resources']))
check('json_safe_and_main_original_control',dump(worker['json_safe'])==dump(oldworker['json_safe']))
for name in oldruntime:
    if name!='require_promoted_version':check('runtime_exact_body:'+name,dump(runtime[name])==dump(oldruntime[name]))
for name in ('worker.py','native_runtime.py','assemble_packet.py'):
    compile((HERE/name).read_text(encoding='utf-8'),str(HERE/name),'exec');check('compile:'+name,True)
manifest=json.loads((HERE/'manifest_template.json').read_text(encoding='utf-8'))
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
check('ten_active_NULL_no_execution_assets',all(manifest[k] is None for k in active) and not any((HERE/n).exists() for n in ('native_manifest.json','lease.json','adapter_release.json')))
check('real94_parent18e_DRAFTTrue',manifest['code_commit']=='94c4fe61b38f46f321a7ee84236fea70ade04d9b' and manifest['runtime_expected_commit']=='18e64b8d95ed0ba5c1053ead114c0f91a4b0c324' and manifest['draft_execution_disabled'] is True)
check('all_diagnostic_bytes',all(sha(HERE/n)==h for n,h in manifest['diagnostic_files'].items()))
setup=ast.unparse(worker['setup'])
check('dynamic_common_names_shapes_count_hash',all(s in setup for s in ("'names'","'shapes'","'tensor_count'","'parameter_count'","'sha256'",'dec.cluster_att.wedge_factor.','cluster_ffn.0.','cluster_ffn.1.','cluster_ffn.2.')))
smoke=ast.unparse(worker['smoke'])
check('whole_core_only_not_columns_positive',"whole_wedge_factor_weight_gradient" in smoke and "Whole wedge_factor aggregate original-loss weight gradient" in smoke and "assert info is None or info['finite']" in smoke)
check('no_old_ELC_or_dynamic_round_gate',not any(s in smoke for s in ('edge_line_graph','actual_rounds','actual_initialize_calls','actual_incident_mean_calls','line_diameter')))
check('finally_restore_global_wrappers_and_hooks',all(s in smoke for s in ('reversed(global_replacements)','setattr(owner, name, original)','hook.remove()','state.clear()')))
namespace={'copy':copy,'itertools':itertools}
exec(compile(ast.Module(body=[worker['wfc_plan_observation'],worker['wfc_coverage_preflight']],type_ignores=[]),'<actual-WFC-metadata>','exec'),namespace)
plan={'fine_ids':[2],'middle_ids':[1],'coarse_ids':[0],'node_keys':[(0,2),(1,1),(2,0)],'neighbors':[[1],[0,2],[1]],'edges':[(0,1),(1,2)],'wedges':[(0,1,2)],'incidence':[[0],[0],[0]],'factor_count':1,'point_count':2}
members=([2,2],[0,0,1],[0,0])
check('actual_single_path_plan_original_ids',namespace['wfc_plan_observation'](plan,members)==plan)
check('empty_before_watch_inconclusive',not namespace['wfc_coverage_preflight']([([],[],[])])['true_supported_core_possible'])
check('mixed_natural_empty_and_supported_legal',namespace['wfc_coverage_preflight']([([],[],[]),members])['true_supported_core_possible'])
bad=copy.deepcopy(plan);bad['wedges']=[(0,1,1)]
try:namespace['wfc_plan_observation'](bad,members)
except AssertionError:check('malformed_wedge_metadata_refused',True)
else:raise AssertionError('bad wedge accepted')
for name in ('observed_stack','observed_cat','observed_select','observed_add','observed_copy'):
    calls=[];returned=object()
    def original(*args,**kwargs):calls.append((args,kwargs));return returned
    original_name={'observed_stack':'original_stack','observed_cat':'original_cat','observed_select':'original_select','observed_add':'original_add','observed_copy':'original_copy'}[name]
    scope={'state':{},original_name:original}
    exec(compile(ast.Module(body=[worker[name]],type_ignores=[]),'<actual-inactive-wrapper>','exec'),scope)
    arguments=([],) if name in ('observed_stack','observed_cat') else ((object(),0,object()) if name=='observed_select' else (object(),0,object(),object()))
    check('actual_inactive_transparent_once:'+name,scope[name](*arguments) is returned and len(calls)==1)
class Opaque:
    shape=(3,256)
factors=Opaque();output=Opaque();plans=object();calls=[]
context={'phase':'mean_ready','factors_ref':factors,'plans_ref':plans,'mean_calls':0,'rows':[1,2,3],
    'incidence_sources':[0,0,0],'incidence_receivers':[0,1,2],'counts':[1,1,1],'record':{'mean_calls':[]}}
def original_mean(f,p):
    assert f is factors and p is plans;calls.append(1);context['mean_add_calls']=1;return output
class Core:channels=256
class Att:wedge_factor=Core()
scope={'state':{'wfc_context':context},'original_mean':original_mean,'att':Att(),
    'fingerprint':lambda t,v:str(id(v)),'torch':None,'summary':lambda v:{'finite':True,'shape':list(v.shape)},'lite_watch':lambda v,r:None}
exec(compile(ast.Module(body=[worker['observed_mean']],type_ignores=[]),'<actual-mean-wrapper>','exec'),scope)
check('actual_mean_original_once_exact_return',scope['observed_mean'](factors,plans) is output and calls==[1] and context['mean_calls']==1 and context['phase']=='final_scatter')
try:scope['observed_mean'](Opaque(),plans)
except AssertionError:check('actual_mean_wrong_reference_refused_before_original',calls==[1])
else:raise AssertionError('wrong factors accepted')
guard_scope={'re':re,'DRAFT_EXECUTION_DISABLED':True,'CANDIDATE_COMMIT':manifest['code_commit'],
    'SOURCE_PARENT_COMMIT':manifest['source_parent_commit'],'SOURCE_PREPARATION_SHA256':manifest['source_preparation_sha256']}
exec(compile(ast.Module(body=[runtime['require_promoted_version']],type_ignores=[]),'<actual-version-guard>','exec'),guard_scope)
try:guard_scope['require_promoted_version']()
except RuntimeError:check('actual_DRAFT_guard_before_manifest_Torch',True)
else:raise AssertionError('draft passed')
out=HERE/'static_validation.json';assert not out.exists()
result={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','check_count':len(checks),'checks':checks,'Torch':False,
    'native':'NOT_RUN','resources':'NOT_RUN','scope':'New metadata/AST/compile, inactive wrappers and opaque actual-mean control only; no full worker/model/Tensor/autograd/old source suite.',
    'command':'python -B pipeline/diagnostic_bundles/tick_34f4e385/wfc_native_prepare/static_check.py'}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'check_count':len(checks),'sha256':sha(out)}))
