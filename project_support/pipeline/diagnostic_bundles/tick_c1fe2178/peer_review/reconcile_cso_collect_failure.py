"""One read-only key-only SSH observation of the retained failed CSO producer."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
TICK = ROOT / 'pipeline/diagnostic_bundles/tick_c1fe2178'
HERE = Path(__file__).resolve().parent
OLD = TICK / 'cso_production_prepare'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
assert sys.dont_write_bytecode and not sys.flags.optimize
assert os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'
owner = read(TICK / 'current_owner_binding.json')
assert len(owner) == 6
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
failure_path = TICK / 'cso_setup_execution/collect_actual.json'
failure = read(failure_path)
stage_path = TICK / 'cso_setup_execution/stage_actual.json'
stage = read(stage_path)
assert failure['owner'] == stage['owner'] == owner
assert failure['action'] == 'collect' and failure['certainty'] == 'terminal'
assert failure['ssh_returncode'] == 0 and failure['training_launch_or_GPU_use'] is False
observation = failure['observation']
assert json.loads(failure['stdout']) == observation
assert observation['certainty'] == 'terminal' and observation['returncode'] == 1
assert observation['pid'] == 385504 and observation['result'] is None
assert observation['remote_result_sha256'] is None
assert 'line 137' in observation['stderr'] and 'digest(original)' in observation['stderr']
frozen = read(OLD / 'FROZEN.json')
assert frozen['owner'] == owner
for name, expected in frozen['files'].items(): assert sha(OLD / name) == expected, name
source8 = {p:h for p,h in read(TICK / 'cso_deployment_prepare/baseline.json')['source_files_exact9'].items() if p.endswith('.py')}
assert len(source8) == 8
producer = '/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prepare_c1fe2178'
production = '/data/songcl/Project/Cluster_project/pipeline/runtime/cso_path_prod_c1fe2178'
assert observation['stage'] == producer
staged = stage['observation']['files']
assert set(staged) == {'production_controller.py', 'lock_core.py', 'entry_factory.py'}
assert all(staged[n] == frozen['files'][n] for n in staged)
readset = {str(p):sha(p) for p in (failure_path, stage_path, OLD / 'FROZEN.json', TICK / 'cso_setup_execution/collect_intent.json', TICK / 'cso_setup_execution/collect_request.json')}
program = 'OWNER=' + repr(owner) + '\nEXPECTED_SOURCE8=' + repr(source8) + '\nEXPECTED_STAGED=' + repr(staged) + '\n' + r'''
from datetime import datetime,timezone
import hashlib,json,os,pathlib,socket,stat,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert datetime.now(timezone.utc)<datetime.fromisoformat(OWNER['deadline_at'])
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
project=pathlib.Path('/data/songcl/Project/Cluster_project')
producer=project/'pipeline/runtime/cso_path_prepare_c1fe2178'
production=project/'pipeline/runtime/cso_path_prod_c1fe2178'
commit='5413102c57b526035f3920b5e7a81f3b58ad764d'
config='configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def data(path):
 s=os.lstat(path);assert stat.S_ISREG(s.st_mode) and s.st_uid==1001 and not stat.S_ISLNK(s.st_mode)
 return pathlib.Path(path).read_bytes()
environment=dict(os.environ,GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='')
def git(*args,text=False):
 return subprocess.check_output(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),*args],env=environment,text=text,timeout=30)
assert git('rev-parse','HEAD',text=True).strip()==commit
pid_path=pathlib.Path('/proc/385504')
assert not pid_path.exists(),'Old collect PID still present; do not replay'
trainers=[];controllers=[];unreadable=[]
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  if proc.stat().st_uid!=1001:continue
  args=[v.decode('utf-8','replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v]
  if str(producer/'production_controller.py') in args:controllers.append({'pid':int(proc.name),'argv':args[:5]})
  is_entry=any(v in ('tools/train.py','tools/test.py') or v.endswith('/tools/train.py') or v.endswith('/tools/test.py') for v in args)
  if is_entry:
   cwd=(proc/'cwd').resolve()
   if cwd==project or project in cwd.parents:trainers.append({'pid':int(proc.name),'cwd':str(cwd),'entry':[v for v in args if v.endswith(('tools/train.py','tools/test.py'))]})
 except FileNotFoundError:pass
 except (PermissionError,OSError,RuntimeError) as error:unreadable.append({'pid':int(proc.name),'error_type':type(error).__name__})
assert not trainers and not controllers
assert not unreadable,'Same-UID process inventory incomplete'
assert producer.is_dir() and producer.resolve()==producer
staged={name:sha(data(producer/name)) for name in EXPECTED_STAGED}
assert staged==EXPECTED_STAGED
request=data(producer/'collect_request.json')
assert sha(request)=='91772ffa0a4389d9f9217ba1b2606b75d03b3ac8af62dd32b02340c801b2990e'
assert json.loads(request)['owner']==OWNER
assert not production.exists(),'Old production path exists; preserve and reconcile'
absence={name:not (producer/name).exists() for name in ('actual_observation.json','production_render_result.json','render_request.json')}
assert all(absence.values())
source_hashes={name:sha(data(root/name)) for name in EXPECTED_SOURCE8}
assert source_hashes==EXPECTED_SOURCE8
raw=git('show',commit+':'+config)
text=git('show',commit+':'+config,text=True).encode('utf-8')
actual=data(root/config)
assert len(raw)==2791 and sha(raw)=='908bc08a4d78dcc2723588abb7a6e3adeb169a79e788ce74ee5afbd78c991081'
assert actual==raw
assert text==raw.replace(b'\r\n',b'\n') and sha(text)!=sha(raw)
assert git('rev-parse','HEAD',text=True).strip()==commit
assert not pid_path.exists()
print(json.dumps({'owner':OWNER,'recorded_at':datetime.now(timezone.utc).isoformat(),
 'hostname':socket.gethostname(),'uid':os.getuid(),'old_collect_pid':385504,'old_collect_pid_absent':True,
 'old_controller_processes':controllers,'project_trainers_or_testers':trainers,'same_uid_inventory_errors':unreadable,
 'producer':str(producer),'staged_files_sha256':staged,'collect_request_sha256':sha(request),
 'producer_result_and_render_absence':absence,'old_production_path':str(production),'old_production_path_absent':True,
 'old_one_shot_marker_absent':not (production/'train-consumed.json').exists(),
 'runtime_HEAD':commit,'source8_sha256':source_hashes,
 'yaml':{'git_raw_bytes':len(raw),'git_raw_sha256':sha(raw),'git_raw_CRLF_count':raw.count(b'\r\n'),
  'git_text_utf8_bytes':len(text),'git_text_utf8_sha256':sha(text),
  'runtime_bytes':len(actual),'runtime_sha256':sha(actual),'raw_equals_runtime':actual==raw,
  'text_equals_CRLF_to_LF':text==raw.replace(b'\r\n',b'\n')},
 'read_only':True,'signals_sent':False,'Torch_imported':False,'GPU_queries_or_compute':False,'training_launched':False}))
'''
command = '/usr/bin/python3 -I -B -c ' + shlex.quote(program)
argv = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
    '-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','songcl@192.168.1.115', command]
run = subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
assert run.returncode == 0, json.dumps({'returncode':run.returncode,'stderr':run.stderr[-2000:]})
remote = json.loads(run.stdout)
assert remote['owner'] == owner and remote['old_collect_pid_absent'] is True
assert remote['read_only'] is True and remote['GPU_queries_or_compute'] is False
for path, expected in readset.items(): assert sha(path) == expected, path
actual = {'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'kind':'READ_ONLY_FAILED_COLLECT_RECONCILIATION_NOT_REPLAY',
    'certainty':'terminal','passed':True,'reviewer_thread_id':'/root/cso_sync_peer',
    'failed_collect':{'path':str(failure_path),'sha256':sha(failure_path),'certainty':'terminal','ssh_returncode':0,'controller_returncode':1,'pid':385504,'result':None},
    'old_producer':producer,'old_producer_FROZEN_sha256':sha(OLD/'FROZEN.json'),
    'command_sha256':hashlib.sha256(command.encode()).hexdigest(),'ssh_returncode':run.returncode,
    'stdout':run.stdout,'stderr':run.stderr,'observation':remote,
    'conclusion':'Known terminal producer digest failure: text-mode Git normalized CRLF YAML; raw committed YAML and runtime YAML agree. Old PID exited, old production/render artifacts absent; preserve old evidence and use separately reviewed new producer rather than replay.',
    'remote_writes_signals_GPU_queries_Torch_launch':False,'old_producer_or_intents_modified':False,
    'frozen_local_readset_sha256':readset}
target=HERE/'cso_collect_failure_reconcile.actual.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(actual,stream,indent=2);stream.write('\n')
review={'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),
    'reviewer_thread_id':'/root/cso_sync_peer','passed':True,'material_concerns':[],
    'kind':'INDEPENDENT_FAILED_COLLECT_RECONCILIATION_REVIEW_NOT_PRODUCTION_PASS',
    'actual_path':str(target),'actual_sha256':sha(target),'failed_collect_sha256':sha(failure_path),
    'old_producer':producer,'old_producer_FROZEN_sha256':sha(OLD/'FROZEN.json'),
    'known_terminal_failed_collect':True,'old_pid_exited_no_project_trainer_no_production_marker':True,
    'runtime_HEAD541_source8_and_raw_YAML_unchanged':True,'CRLF_text_mode_hash_failure_demonstrated':True,
    'new_producer_and_review_required_before_stage':True,'production_or_training_success':False,
    'remote_read_only':True,'signals_GPU_queries_Torch_launch':False}
review_path=HERE/'cso_collect_failure_reconcile_independent_review.json'
with review_path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(review,stream,indent=2);stream.write('\n')
print(json.dumps({'actual':str(target),'actual_sha256':sha(target),'review':str(review_path),'review_sha256':sha(review_path),'yaml':remote['yaml'],'known_terminal':True,'old_pid_absent':True,'old_production_absent':True}))
