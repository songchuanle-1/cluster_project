"""GPU1 port AST, controlled runtime stubs and local disabled-refusal checks."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import ast
import copy
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_41eb62fa/bcr_operational_prepare/native'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
source=(HERE/'native_runtime.py').read_text(encoding='utf-8')
old=(ORIGIN/'native_runtime.py').read_text(encoding='utf-8')
runtime=ast.parse(source); previous=ast.parse(old)
checks={}
changes=[('DRAFT_EXECUTION_DISABLED = False','DRAFT_EXECUTION_DISABLED = True'),
         ("STAGE.name == 'bcr_'","STAGE.name == 'bcr_gpu1_'"),
         ('PHYSICAL_GPU == 0','PHYSICAL_GPU == 1')]
expected=old
for before,after in changes:
    assert expected.count(before)==1
    expected=expected.replace(before,after)
checks['runtime_exactly_three_listed_literal_changes']=source==expected
funcs=lambda t:{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
checks['all_runtime_function_AST_including_all_safety_guards_unchanged']=funcs(runtime)==funcs(previous)
checks['worker_complete_bytes_unchanged']=sha(HERE/'worker.py')==sha(ORIGIN/'worker.py')=='a3b10169a9edee14b7943626934abbe46662e366268dcd4919320c86aefd6538'
checks['logical_cuda_zero_preserved_for_only_visible_physical_UUID1']='torch.cuda.set_per_process_memory_fraction(0.75, 0)' in (HERE/'worker.py').read_text(encoding='utf-8') and 'model = network(**cfg.model).cuda()' in (HERE/'worker.py').read_text(encoding='utf-8')
for name in ('worker.py','native_runtime.py'):
    compile((HERE/name).read_text(encoding='utf-8'),str(HERE/name),'exec')
checks['both_actual_sources_compile_without_import']=True
t=read(HERE/'manifest_template.json');original_template=read(ORIGIN/'manifest_template.json')
checks['model9_and_source_version_binding_original_bytes_unchanged']=all(sha(HERE/name)==sha(ORIGIN/name) for name in original_template['diagnostic_files'] if name not in ('native_runtime.py','worker.py'))
checks['template_execution_fields_null_no_active_files']=all(t[name] is None for name in ('current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit')) and not any((HERE/name).exists() for name in ('native_manifest.json','execution_lease.json','execution_binding.json'))
checks['template_GPU1_static_scope_and_same_scientific_identity']=t['draft_execution_disabled'] is True and t['native_port_scope']['selected_physical_gpu']==1 and t['native_port_scope']['logical_cuda_device']==0 and all(t[name]==original_template[name] for name in ('candidate_id','experiment_id','code_commit','goal_sha256','config','tolerance','candidate_source_hashes','candidate_config_sha256','assets','source_version_binding_sha256','source_parent_commit'))

# Execute the actual original runtime functions against only explicit in-memory stubs.
commands=[];opened=[];flocks=[];alarms=[];verified=[]
gpu_uuid='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
gpu0_uuid='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
state={'foreign':False,'fail_lock':False}
def output(argv,**kwargs):
    assert argv[:3]==['nvidia-smi','-i','1'],'GPU0 or unconstrained inventory requested'
    commands.append(list(argv))
    if '--query-gpu=index,uuid,memory.used,utilization.gpu' in argv:
        return '1, '+gpu_uuid+', 41, 0\n'
    assert '--query-compute-apps=pid,used_memory' in argv
    return '99999, 100\n' if state['foreign'] else ''
class Handle:
    def __init__(self,name):self.name=name;self.closed=False
    def close(self):self.closed=True
def open_stub(name,mode):
    assert mode=='a+b' and name.startswith('/tmp/cluster_project_gpu1_')
    handle=Handle(name);opened.append(handle);return handle
def flock(handle,flags):
    flocks.append((handle.name,flags))
    if state['fail_lock'] and handle.name.endswith('_diagnostic.lock') and flags==3:
        raise BlockingIOError('Controlled foreign-held GPU1 diagnostic lock')
now=datetime.now(timezone.utc)
manifest={'current_token':'1'*32,'tick_generated_at':(now-timedelta(seconds=1)).isoformat(),
          'deadline_at':(now+timedelta(seconds=600)).isoformat(),'allowed_gpus':[0,1],
          'context_sha256':'a'*64,'pending_sha256':'b'*64}
lease={'project':'cluster_project','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
       'native_manifest_sha256':'c'*64,'token':manifest['current_token'],
       'generated_at':manifest['tick_generated_at'],'deadline_at':manifest['deadline_at'],
       'server_id':'server-4','physical_gpu':1,'gpu_uuid':gpu_uuid,'allowed_gpus':[0,1],
       'goal_sha256':t['goal_sha256'],'context_sha256':'a'*64,'pending_sha256':'b'*64}
class VirtualPath:
    def __init__(self,value):self.value=str(value)
    def __truediv__(self,value):return VirtualPath(self.value+'/'+value)
    def read_text(self):assert self.value=='virtual-lease';return json.dumps(lease)
env={'socket':SimpleNamespace(gethostname=lambda:'dl04-MS-7E06'),
     'subprocess':SimpleNamespace(check_output=output),
     'os':SimpleNamespace(getpid=lambda:12345,environ={}),
     'datetime':datetime,'timezone':timezone,'json':json,'re':__import__('re'),
     'Path':VirtualPath,'STAGE':VirtualPath('/virtual-stage'),
     'sha':lambda p:'c'*64,'verify':lambda:verified.append(True),
     'PHYSICAL_GPU':1,'GPU_UUIDS':{0:gpu0_uuid,1:gpu_uuid},'GOAL':t['goal_sha256'],
     'THREAD':lease['thread_id'],'MANIFEST':manifest,'HANDLES':[],
     'open':open_stub,'fcntl':SimpleNamespace(LOCK_EX=1,LOCK_NB=2,LOCK_UN=8,flock=flock),
     'signal':SimpleNamespace(alarm=lambda seconds:alarms.append(seconds))}
for name in ('observe','release','acquire'):
    node=next(n for n in runtime.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),name,'exec'),env)
env['acquire']('virtual-lease')
assert len(commands)==4 and len(opened)==3 and len(env['HANDLES'])==3
assert env['os'].environ['CUDA_VISIBLE_DEVICES']==gpu_uuid
assert {x.name for x in opened}=={'/tmp/cluster_project_gpu1_'+kind+'.lock' for kind in ('training','diagnostic','exclusive')}
env['release']();assert env['HANDLES']==[] and all(x.closed for x in opened)
checks['actual_acquire_functions_stub_select_only_GPU1_two_idle_three_locks_UUID1_CUDA']=True
commands.clear();lease['physical_gpu']=0
try:env['acquire']('virtual-lease')
except AssertionError:pass
else:raise AssertionError('GPU0 lease was accepted')
assert not commands and not env['HANDLES'];lease['physical_gpu']=1
checks['actual_lease_wrong_physical_GPU0_refused_before_inventory']=True
state['foreign']=True;commands.clear()
try:env['observe'](True)
except AssertionError:pass
else:raise AssertionError('Foreign GPU1 context accepted')
assert all(cmd[2]=='1' for cmd in commands);state['foreign']=False
checks['actual_observe_foreign_GPU1_context_refused_without_querying_GPU0']=True
state['fail_lock']=True;opened.clear();commands.clear()
try:env['acquire']('virtual-lease')
except BlockingIOError:pass
else:raise AssertionError('Foreign diagnostic lock accepted')
assert not env['HANDLES'] and len(opened)==2 and all(x.closed for x in opened)
checks['actual_partial_acquire_releases_only_own_GPU1_handles']=True

refusals=[]
probe="""import json,runpy,sys
sys.path.insert(0,str(__import__('pathlib').Path(sys.argv[1]).parent))
try:runpy.run_path(sys.argv[1],run_name='__main__')
except RuntimeError as e:
 assert 'BCR native preparation is execution-disabled' in str(e)
 assert 'torch' not in sys.modules and 'fcntl' not in sys.modules
 print(json.dumps({'own_disabled_error':str(e),'torch_imported':False,'fcntl_imported':False}))
else:raise AssertionError('Disabled native entry did not refuse')
"""
for name in ('native_runtime.py','worker.py'):
    done=subprocess.run([sys.executable,'-B','-c',probe,str(HERE/name)],capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert done.returncode==0,(name,done.stdout,done.stderr)
    refusals.append({'entry':name,'returncode':done.returncode,'observation':json.loads(done.stdout)})
checks['two_real_local_disabled_entry_refusals_before_manifest_fcntl_torch']=True
assert all(checks.values()),checks
result={'schema_version':1,'status':'GPU1_PORT_AST_CONTROLLED_STUB_AND_DISABLED_ENTRY_CHECKED_NATIVE_NOT_RUN',
        'checks':checks,'logical_check_count':len(checks),'entry_refusals':refusals,
        'source_hashes':{n:sha(HERE/n) for n in ('worker.py','native_runtime.py')},
        'native':'NOT_RUN','resources':'NOT_RUN','SSH_or_GPU_queries':'NOT_RUN',
        'grant_created_or_hardware_idleness_proved':False,
        'scope':'Exact copied bytes/AST; actual extracted observe/acquire/release functions against explicit in-memory subprocess/files/lease/lock stubs; two real local stdlib disabled-entry refusals. No torch, real NVML/lock/GPU/SSH or native execution. No fake fixture is a usable grant/binding/lease.',
        'material_concerns':[]}
with (HERE/'static_validation.json').open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
print(json.dumps({'path':str(HERE/'static_validation.json'),'sha256':sha(HERE/'static_validation.json'),'logical_checks':len(checks)}))
