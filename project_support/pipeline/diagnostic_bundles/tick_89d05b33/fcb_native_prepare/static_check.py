"""Necessary FCB producer/observer schema and entry refusal checks; no model execution."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,copy,hashlib,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_2ef53d6b/aoc_native_prepare'
SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_f8d84d12/new_candidate_prepare'
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
worker=(HERE/'worker.py').read_text(encoding='utf-8');wt=ast.parse(worker)
runtime=(HERE/'native_runtime.py').read_text(encoding='utf-8');rt=ast.parse(runtime)
for name in ('worker.py','native_runtime.py'):compile((HERE/name).read_text(encoding='utf-8'),name,'exec')
check('both_core_sources_compile_without_import',True)
def functions(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
old_worker=functions((ORIGIN/'worker.py').read_text(encoding='utf-8'));new_worker=functions(worker)
check('complete_original_resource_function_AST',old_worker['resources']==new_worker['resources'])
old_rt=functions((ORIGIN/'native_runtime.py').read_text(encoding='utf-8'));new_rt=functions(runtime)
check('eight_runtime_guard_functions_exact',all(new_rt[n]==value for n,value in old_rt.items() if n!='require_promoted_version'))
check('version_predicate_only_FCB_diagnostic_label',new_rt['require_promoted_version'].replace('FCB','AOC')==old_rt['require_promoted_version'])
check('original_setup_numerical_AST_and_common_shapes_preserved',old_worker['setup'].replace('AOC','FCB').replace('ancestral_commutator','fine_coarse_bipartite')==new_worker['setup'] and "'shapes':{n:list(p.shape)" in worker)
check('wholecore_gate_and_four_columns_descriptive','whole_fine_coarse_bipartite_weight_gradient' in worker and 'whole_fine_coarse_bipartite_weight_updated' in worker and 'whole_fine_coarse_bipartite_module_updated' in worker and 'Four map-input-column blocks descriptive; zeros legal' in worker)
check('no_old_diamond_or_Euler_schema','actual_cell_calls' not in worker and 'actual_total_events' not in worker and 'ancestral_commutator' not in worker)
template=json.loads((HERE/'manifest_template.json').read_text(encoding='utf-8'));binding=json.loads((HERE/'source_version_binding.json').read_text(encoding='utf-8'))
check('actual_source_parent_runtime_conditional',binding['code_commit']=='d4d062ef075abfe7cde93d4b4347ce146572762f' and binding['parent_commit']==binding['runtime_expected_commit']=='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33' and 'Currentmain/runtimePES9c' in binding['scope'])
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
check('formalFalse_ten_fields_NULL',template['draft_execution_disabled'] is False and all(template[key] is None for key in active))
for name,expected in template['diagnostic_files'].items():check('diagnostic_hash_'+name,sha(HERE/name)==expected)
source=json.loads((SOURCE/'preparation.json').read_text(encoding='utf-8'))
check('original_NULL_source_and_original_YAML',all(source[k] is None for k in ('code_commit','source_commit','source_parent_commit')) and sha(HERE/'candidate.yaml')=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a')
guard=next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=='require_promoted_version')
for label,change in [('disabled',{'DRAFT_EXECUTION_DISABLED':True}),('missingcode',{'CANDIDATE_COMMIT':None}),('badparent',{'SOURCE_PARENT_COMMIT':'bad'}),('missinghash',{'SOURCE_PREPARATION_SHA256':None})]:
    env={'re':re,'DRAFT_EXECUTION_DISABLED':False,'CANDIDATE_COMMIT':binding['code_commit'],'SOURCE_PARENT_COMMIT':binding['parent_commit'],'SOURCE_PREPARATION_SHA256':binding['original_source_preparation_sha256']};env.update(change)
    exec(compile(ast.Module(body=[guard],type_ignores=[]),'actual_version_guard','exec'),env)
    try:env['require_promoted_version']()
    except RuntimeError:check('version_guard_refusal_'+label,True)
    else:check('version_guard_refusal_'+label,False)
class MissingPath:
    def __init__(self,value):self.value=str(value)
    def resolve(self):return self
    @property
    def parent(self):return self
    def __truediv__(self,value):return MissingPath(self.value+'/'+value)
    def read_text(self):reads.append(self.value);raise FileNotFoundError('No active native manifest')
reads=[];imports=[]
def inert_import(name,globals=None,locals=None,fromlist=(),level=0):
    imports.append(name)
    if name=='re':return re
    if name=='json':return json
    if name=='hashlib':return hashlib
    if name=='datetime':return SimpleNamespace(datetime=datetime,timezone=timezone)
    if name=='pathlib':return SimpleNamespace(Path=MissingPath)
    if name=='os':return SimpleNamespace(environ={})
    if name in ('fcntl','signal','socket','subprocess'):return SimpleNamespace()
    raise AssertionError('Unexpected import before missing manifest: '+name)
prefix=[]
for n in rt.body:
    prefix.append(n)
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MANIFEST' for t in n.targets):break
env={'__file__':'private/fcb/native_runtime.py','__builtins__':{**vars(__import__('builtins')),'__import__':inert_import}}
try:exec(compile(ast.fix_missing_locations(ast.Module(body=prefix,type_ignores=[])),'actual_prefix_until_manifest','exec'),env)
except FileNotFoundError:refused=True
else:refused=False
check('missing_active_manifest_refuses_before_Torch_or_runtime_calls',refused and len(reads)==1 and reads[0].endswith('native_manifest.json') and 'torch' not in imports)
# Actual pure metadata producer and new observer schema only, not model-forward control.
model_tree=ast.parse((HERE/'candidate_model/fine_coarse_bipartite.py').read_text(encoding='utf-8'))
producer=[n for n in model_tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_original_ids','build_fine_coarse_plan')]
schema=[n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name in ('fcb_plan_observation','fcb_coverage_preflight')]
env={'copy':copy};exec(compile(ast.Module(body=producer+schema,type_ignores=[]),'actual_metadata_producer_schema','exec'),env)
members=([0,2,4,4],[2,0,2,1,3],[1,0,2,1]);plan=env['build_fine_coarse_plan'](*members,[7,5,4]);record=env['fcb_plan_observation'](plan,members)
check('actual_plan_producer_matches_observer_schema',record['pair_count']==6 and record['observed_nonancestor_pairs']==3 and record['fine_pair_counts']==[2,2,2])
check('empty_preflight_inconclusive_and_single_root_legal',not env['fcb_coverage_preflight']([([],[],[])])['true_fine_coarse_pair_possible'] and env['fcb_coverage_preflight']([([],[],[]),([0],[0],[0])])['total_true_pairs']==1)
# Execute only the new transparent mean callback against opaque objects, no arithmetic.
smoke=next(n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name=='smoke')
mean_callback=next(n for n in ast.walk(smoke) if isinstance(n,ast.FunctionDef) and n.name=='observed_mean')
class Opaque:
    def __init__(self,label):self.label=label
    def detach(self):return self
    def clone(self):return Opaque(self.label)
def mean_environment():
    q=Opaque('actual_q');context={'record':{'mean_calls':[]},'mean_count':0,'phase':'fine_mean','q_ref':q,'mean_outputs':[],'mean_snapshots':[],
        'pair_fine':[0,0,1,1],'pair_coarse':[0,1,0,1],'fine_counts':[2,2],'coarse_counts':[2,2],'fine_parents':[0,0],'middle_counts':[2]}
    calls=[]
    def original_mean(*args):out=Opaque('actual_mean_'+str(len(calls)));calls.append((args,out));return out
    ns={'state':{'fcb_context':context},'summary':lambda obj:{'finite':True},'fingerprint':lambda torch,obj:obj.label,
        'torch':None,'lite_watch':lambda *args:None,'original_mean':original_mean}
    exec(compile(ast.Module(body=[mean_callback],type_ignores=[]),'actual_mean_callback_only','exec'),ns)
    return q,context,calls,ns['observed_mean']
q,context,calls,callback=mean_environment();outputs=[]
for positions,counts in [(context['pair_fine'],context['fine_counts']),(context['pair_coarse'],context['coarse_counts']),(context['fine_parents'],context['middle_counts'])]:
    messages=q if len(outputs)<2 else outputs[0]
    outputs.append(callback(messages,positions,counts))
check('three_actual_mean_calls_once_original_returns',len(calls)==3 and all(out is original[1] for out,original in zip(outputs,calls)))
check('sameq_both_marginals_actualfine_delta_third',calls[0][0][0] is calls[1][0][0] is q and calls[2][0][0] is outputs[0] and context['phase']=='middle_map')
q,context,calls,callback=mean_environment()
try:callback(q,[999],context['fine_counts'])
except AssertionError:rejected=True
else:rejected=False
check('wrong_mean_group_rejected_before_original_call',rejected and not calls)
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':binding['candidate_id'],'code_commit':binding['code_commit'],
    'check_count':len(checks),'checks':checks,'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),
    'manifest_template_sha256':sha(HERE/'manifest_template.json'),'source_version_binding_sha256':sha(HERE/'source_version_binding.json'),
    'Torch':False,'actual_model_or_production_forward_executed':False,'old_suites_executed':False,'native':'NOT_RUN','resources':'NOT_RUN',
    'scope':'Compile/hash/AST, actual metadata producer-to-observer schema, opaque transparent mean callback, extracted version guard/missingmanifest prefix with inert imports only. No model software-control suite, Torch, numerical GELU/autograd or entry execution.'}
(HERE/'static_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'check_count':len(checks),'report':str(HERE/'static_validation.json')}))
