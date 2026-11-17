"""Minimal SFC native schema/once-transparency/early-refusal checks, no model controls."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import ast,copy,hashlib,json,re
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_89d05b33/fcb_native_prepare'
checks=[]
def check(name,value):
    assert value,name
    checks.append({'name':name,'passed':True})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
worker=(HERE/'worker.py').read_text(encoding='utf-8');wt=ast.parse(worker)
runtime=(HERE/'native_runtime.py').read_text(encoding='utf-8');rt=ast.parse(runtime)
for name in ('worker.py','native_runtime.py'):compile((HERE/name).read_text(encoding='utf-8'),name,'exec')
check('core_compile_without_import',True)
def funcs(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
old=funcs((ORIGIN/'worker.py').read_text(encoding='utf-8'));new=funcs(worker)
check('full_original_resource_AST',old['resources']==new['resources'])
oldrt=funcs((ORIGIN/'native_runtime.py').read_text(encoding='utf-8'));newrt=funcs(runtime)
check('eight_original_runtime_guard_bodies',all(newrt[n]==body for n,body in oldrt.items() if n!='require_promoted_version'))
check('version_guard_only_diagnostic_label',newrt['require_promoted_version'].replace('SFC','FCB')==oldrt['require_promoted_version'])
check('setup_original_numerics_and_dynamic_common_shapes',old['setup'].replace('FCB','SFC').replace('fine_coarse_bipartite','synchronous_forest')==new['setup'] and "'shapes':{n:list(p.shape)" in worker)
check('single_wholecore_gradient_update_only','whole_synchronous_forest_weight_gradient' in worker and 'whole_synchronous_forest_weight_updated' in worker and 'Two cell-input-column blocks descriptive; zeros legal' in worker and 'actual_pair_map_calls' not in worker)
smoke=next(n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name=='smoke')
train_try=next(n for n in ast.walk(smoke) if isinstance(n,ast.Try) and any(isinstance(v,ast.For) and isinstance(v.iter,ast.Name) and v.iter.id=='installations' for v in n.body))
check('global_wrappers_install_inside_try_restore_in_finally',bool(train_try.finalbody) and any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='setattr' for f in train_try.finalbody for n in ast.walk(f)))
template=json.loads((HERE/'manifest_template.json').read_text());binding=json.loads((HERE/'source_version_binding.json').read_text())
check('real_c9be_parent_runtime_d4_conditional',binding['code_commit']=='c9be548699cd66bf68badff9ae6198a03eafa142' and binding['parent_commit']==binding['runtime_expected_commit']=='d4d062ef075abfe7cde93d4b4347ce146572762f' and 'Currentmain/runtimeAOC0314' in binding['scope'])
active=('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')
check('formalFalse_all_ten_active_NULL',template['draft_execution_disabled'] is False and all(template[key] is None for key in active))
for name,want in template['diagnostic_files'].items():check('diagnostic_hash_'+name,sha(HERE/name)==want)
guard=next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=='require_promoted_version')
for label,change in [('DRAFT',{'DRAFT_EXECUTION_DISABLED':True}),('missingcode',{'CANDIDATE_COMMIT':None}),('badparent',{'SOURCE_PARENT_COMMIT':'bad'}),('missinghash',{'SOURCE_PREPARATION_SHA256':None})]:
    env={'re':re,'DRAFT_EXECUTION_DISABLED':False,'CANDIDATE_COMMIT':binding['code_commit'],'SOURCE_PARENT_COMMIT':binding['parent_commit'],'SOURCE_PREPARATION_SHA256':binding['original_source_preparation_sha256']};env.update(change)
    exec(compile(ast.Module(body=[guard],type_ignores=[]),'actual_guard_predicate','exec'),env)
    try:env['require_promoted_version']()
    except RuntimeError:refused=True
    else:refused=False
    check('actual_version_guard_refuses_'+label,refused)
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
    raise AssertionError('Unexpected import before manifest: '+name)
prefix=[]
for n in rt.body:
    prefix.append(n)
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MANIFEST' for t in n.targets):break
env={'__file__':'private/sfc/native_runtime.py','__builtins__':{**vars(__import__('builtins')),'__import__':inert_import}}
try:exec(compile(ast.fix_missing_locations(ast.Module(body=prefix,type_ignores=[])),'actual_missingmanifest_prefix','exec'),env)
except FileNotFoundError:refused=True
else:refused=False
check('missing_manifest_before_Torch_or_runtime_operations',refused and len(reads)==1 and reads[0].endswith('native_manifest.json') and 'torch' not in imports)
# One small actual pure metadata producer/schema: mixedD2/D4, no model/forward.
mt=ast.parse((HERE/'candidate_model/synchronous_forest.py').read_text(encoding='utf-8'))
producer=[n for n in mt.body if isinstance(n,ast.FunctionDef) and n.name in ('build_synchronous_forest_plan','build_synchronous_rounds')]
helpers=[n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name in ('sfc_plan_observation','sfc_rounds_observation','sfc_coverage_preflight')]
env={'copy':copy};exec(compile(ast.Module(body=producer+helpers,type_ignores=[]),'actual_metadata_schema','exec'),env)
members=([0,1,2,3,4],[0,0,1,2,2],[0,1,1]);plan=env['build_synchronous_forest_plan'](*members,[7,5,4])
record=env['sfc_plan_observation'](plan,members);rounds=env['build_synchronous_rounds']([plan])
check('actual_plan_round_schema_D2_D4_no_fake_updates',env['sfc_rounds_observation']([plan],rounds) and [len(r['receivers']) for r in rounds]==[10,10,6,6] and [c['diameter'] for c in record['components']]==[2,4])
check('empty_inconclusive_singleton_not_extra_gate',not env['sfc_coverage_preflight']([([],[],[])])['true_supported_core_possible'] and env['sfc_coverage_preflight']([([0],[0],[0])])['total_true_paths']==1)
# One opaque state-transition/return-object witness for actual primitive/mean wrappers.
names=('observed_stack','observed_select','observed_mean','observed_copy')
callbacks=[n for n in ast.walk(smoke) if isinstance(n,ast.FunctionDef) and n.name in names]
class Opaque:
    def __init__(self,tag,values=None):self.tag,self.values=tag,values
    def detach(self):return self
    def cpu(self):return self
    def tolist(self):return list(self.values)
    def __eq__(self,other):return SimpleNamespace(all=lambda:self.tag=='zero' and other==0)
class Grid:
    def __init__(self,row):self.row=row
    def __getitem__(self,key):return self.row
counts={'stack':0,'select':0,'copy':0,'mean':0};returned=[]
oldstate=Opaque('old_state');newstate=Opaque('new_state');meanvalue=Opaque('actual_mean');gelu=Opaque('actual_GELU')
ownindex=Opaque('receiver_ids',[0,1,2]);sourceindex=Opaque('source_ids',[1,0,2,1])
rows=[Opaque('fine'),Opaque('middle'),Opaque('coarse')]
stage={'receivers':[0,1,2],'sources':[1,0,2,1],'source_receivers':[0,1,1,2],'counts':[1,2,1]}
context={'phase':'initial_stack','initial_stack_calls':0,'original_rows':[(0,0,0),(0,1,0),(0,2,0)],'normalized':[Grid(row) for row in rows],
    'rounds':[stage,stage],'round_index':0,'mean_count':0,'state_write_count':0,'record':{'primitive_calls':[],'round_calls':[],'mean_calls':[]},'positions':[[0],[1],[2]],'destinations':[[0],[0],[0]]}
state={'sfc_context':context}
def original_stack(values,*args,**kw):counts['stack']+=1;returned.append(oldstate);return oldstate
def original_select(tensor,dim,index,*args,**kw):counts['select']+=1;out=Opaque('actual_select_'+str(counts['select']));returned.append(out);return out
def original_copy(tensor,dim,index,source,*args,**kw):counts['copy']+=1;returned.append(newstate);return newstate
wrapper_env={'state':state,'original_stack':original_stack,'original_select':original_select,'original_copy':original_copy,
    'fingerprint':lambda torch,obj:obj.tag,'summary':lambda obj:{'finite':True},'lite_watch':lambda *args:None,'torch':None}
exec(compile(ast.Module(body=callbacks,type_ignores=[]),'actual_transparent_callbacks_only','exec'),wrapper_env)
stackout=wrapper_env['observed_stack'](rows,dim=0);context['phase']='own'
own=wrapper_env['observed_select'](oldstate,0,ownindex)
def original_mean(tensor,plan):
    counts['mean']+=1;wrapper_env['observed_select'](tensor,0,sourceindex);return meanvalue
wrapper_env['original_mean']=original_mean
meanout=wrapper_env['observed_mean'](oldstate,stage)
context.update(phase='state_write',GELU_ref=gelu,pending_round={})
copyout=wrapper_env['observed_copy'](oldstate,0,ownindex,gelu)
check('actual_once_mean_stack_gather_copy_return_objects',counts=={'stack':1,'select':2,'copy':1,'mean':1} and stackout is oldstate and meanout is meanvalue and copyout is newstate and context['current_state_ref'] is newstate and context['phase']=='own')
before=counts['select']
try:wrapper_env['observed_select'](oldstate,0,ownindex)
except AssertionError:rejected=True
else:rejected=False
check('stale_OLDstate_rejected_before_original_gather',rejected and counts['select']==before)
state.pop('sfc_context');outside=wrapper_env['observed_copy'](oldstate,0,ownindex,gelu)
check('outside_active_context_original_once_return',outside is newstate and counts['copy']==2)
report={'status':'PASS_SOFTWARE_ONLY_NOT_NATIVE','recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':binding['candidate_id'],'code_commit':binding['code_commit'],
    'check_count':len(checks),'checks':checks,'worker_sha256':sha(HERE/'worker.py'),'runtime_sha256':sha(HERE/'native_runtime.py'),
    'manifest_template_sha256':sha(HERE/'manifest_template.json'),'source_version_binding_sha256':sha(HERE/'source_version_binding.json'),
    'Torch':False,'actual_model_or_production_forward_executed':False,'old_suites_executed':False,'native':'NOT_RUN','resources':'NOT_RUN',
    'scope':'Compile/hash/AST, one metadata producer-schema, one opaque actual stack/gather/mean/indexcopy callback transition and stale-source refusal, extracted guard and inert missingmanifest prefix. No numerical model/forward/control suite or native entry.'}
(HERE/'static_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'check_count':len(checks),'report':str(HERE/'static_validation.json')}))
