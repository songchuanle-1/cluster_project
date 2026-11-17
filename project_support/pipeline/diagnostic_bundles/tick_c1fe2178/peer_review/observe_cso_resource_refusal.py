"""Fresh read-only GPU0 refusal observation, without launch, locks, or signals."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
TICK=ROOT/'pipeline/diagnostic_bundles/tick_c1fe2178'
HERE=Path(__file__).resolve().parent
PACKET=TICK/'cso_production_prepare_v2'
DISPATCH=TICK/'cso_dispatch_execution_v2'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def value_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert sys.dont_write_bytecode and not sys.flags.optimize
assert os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
owner=read(TICK/'current_owner_binding.json')
assert len(owner)==6 and datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
frozen=read(PACKET/'FROZEN.json');assert frozen['owner']==owner
for name,digest in frozen['files'].items():assert sha(PACKET/name)==digest,name
render=read(TICK/'cso_setup_execution_v2/render_result.json')
assert render['owner']==owner and render['kind']=='PRODUCTION_PATH_INSTALLED_NO_TRAINER_LAUNCHED'
assert render['one_shot_consumed'] is False
binding=render['binding'];assert binding['source_commit']=='5413102c57b526035f3920b5e7a81f3b58ad764d'
assert binding['required_free_memory_mib']==20000 and binding['physical_gpu']==0
assert binding['expected_gpu_uuid']=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
stderr_path=DISPATCH/'cso_dispatch_ssh_00.stderr'
stderr=stderr_path.read_text(encoding='utf-8-sig')
assert 'ResourceRefused: Direct memory.free below unchanged 20000 MiB gate' in stderr
assert (DISPATCH/'cso_dispatch_ssh_00.stdout').read_bytes()==b''
absent_names=('cso_dispatch_intent.json','cso_dispatch_result.json','cso_prelaunch_actual_resources.json')
assert all(not (DISPATCH/name).exists() for name in absent_names)
dispatch_files={p.name:sha(p) for p in DISPATCH.iterdir() if p.is_file()}
queue=read(ROOT/'pipeline/queue.json')
tasks=[t for group in queue.get('gpu_queues',{}).values() for t in group]
cso=[t for t in tasks if t.get('id')=='M236-CSO'];assert len(cso)==1
assert cso[0]['status']=='waiting' and not cso[0].get('pid') and cso[0].get('launch_verified') is not True
assert cso[0]['code_commit']==binding['source_commit']
oldqueue=read(TICK/'queue.json.before')
oldtasks=[t for group in oldqueue.get('gpu_queues',{}).values() for t in group]
protected={}
for taskid in ('M206-CGCA','M227-LFT'):
 current=next(t for t in tasks if t.get('id')==taskid)
 original=next(t for t in oldtasks if t.get('id')==taskid)
 assert current==original
 protected[taskid]={'canonical_task_sha256':value_sha(current),'unchanged_from_tick_before':True,
     'status':current['status'],'dispatch_phase':current.get('dispatch_phase'),'resume_authorized':current.get('resume_authorized')}
local_paths=[ROOT/'pipeline/queue.json',ROOT/'pipeline/running.json',PACKET/'FROZEN.json',
 PACKET/'direct_memory_free_guard.py',PACKET/'dispatch_cso_once.py',TICK/'cso_setup_execution_v2/render_result.json',
 TICK/'cso_setup_execution_v2/render_actual.json',TICK/'current_owner_binding.json',TICK/'queue.json.before']
local_hashes={str(p):sha(p) for p in local_paths}
source8={p:h for p,h in read(TICK/'cso_deployment_prepare/baseline.json')['source_files_exact9'].items() if p.endswith('.py')}
expected_producer={name:frozen['files'][name] for name in ('production_controller.py','lock_core.py','entry_factory.py')}
parameters={'owner':owner,'source':binding['source_commit'],'source8':source8,
 'producer':binding['producer'],'producer_files':expected_producer,'production':binding['stage'],
 'production_files':render['files'],'marker':binding['one_shot_marker'],'locks':binding['lock_files'],
 'config':'configs/Quard/ctf_hcg_csort_cso/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cso.yaml',
 'config_hashes':['908bc08a4d78dcc2723588abb7a6e3adeb169a79e788ce74ee5afbd78c991081',binding['runtime_config_sha256']]}
program='P='+repr(parameters)+'\n'+r'''
from datetime import datetime,timezone
import hashlib,json,os,pathlib,socket,stat,subprocess
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
assert datetime.now(timezone.utc)<datetime.fromisoformat(P['owner']['deadline_at'])
root=pathlib.Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
project=pathlib.Path('/data/songcl/Project/Cluster_project')
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def run(argv):
 return subprocess.check_output(argv,env=dict(os.environ,PATH='/usr/bin:/bin',LC_ALL='C',GIT_OPTIONAL_LOCKS='0',PYTHONDONTWRITEBYTECODE='1'),text=True,timeout=15).strip()
head=run(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'rev-parse','HEAD'])
assert head==P['source']
source_hashes={name:sha(root/name) for name in P['source8']};assert source_hashes==P['source8']
producer_hashes={name:sha(pathlib.Path(P['producer'])/name) for name in P['producer_files']}
assert producer_hashes==P['producer_files']
production_hashes={name:sha(pathlib.Path(P['production'])/name) for name in P['production_files']}
assert production_hashes==P['production_files']
assert not pathlib.Path(P['marker']).exists()
config_sha=sha(root/P['config']);assert config_sha in P['config_hashes']
gpu_command=['/usr/bin/nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits']
gpu_raw=run(gpu_command);fields=[x.strip() for x in gpu_raw.split(',')]
assert len(fields)==6 and fields[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
gpu={'physical_gpu':0,'uuid':fields[1],'memory_free_mib':int(fields[2]),'memory_used_mib':int(fields[3]),'memory_total_mib':int(fields[4]),'utilization_percent':int(fields[5]),'free_queried_directly':True,'required_free_memory_mib':20000,'below_unchanged_gate':int(fields[2])<20000}
context_raw=run(['/usr/bin/nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
contexts=[]
for row in context_raw.splitlines():
 if not row.strip():continue
 values=[x.strip() for x in row.split(',')]
 assert len(values)==3 and values[0]==gpu['uuid']
 context={'gpu_uuid':values[0],'pid':int(values[1]),'used_gpu_memory_mib':int(values[2])}
 proc=pathlib.Path('/proc')/str(context['pid'])
 for label,call in [('uid',lambda:proc.stat().st_uid),('commandline_sha256',lambda:hashlib.sha256((proc/'cmdline').read_bytes()).hexdigest()),('cwd',lambda:os.readlink(proc/'cwd')),('executable',lambda:os.readlink(proc/'exe'))]:
  try:context[label]=call()
  except (OSError,RuntimeError) as error:context[label+'_error']=type(error).__name__
 contexts.append(context)
trainers=[];inventory_errors=[];same_uid_scanned=0
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 try:
  if proc.stat().st_uid!=1001:continue
  same_uid_scanned+=1
  argv=(proc/'cmdline').read_bytes().split(b'\0')
  entry=any(v in (b'tools/train.py',b'tools/test.py') or v.endswith((b'/tools/train.py',b'/tools/test.py')) for v in argv)
  if not entry:continue
  cwd=pathlib.Path(os.readlink(proc/'cwd'))
  if cwd==project or project in cwd.parents:
   trainers.append({'pid':int(proc.name),'cwd':str(cwd),'commandline_sha256':hashlib.sha256((proc/'cmdline').read_bytes()).hexdigest()})
 except (FileNotFoundError,ProcessLookupError):pass
 except (OSError,RuntimeError) as error:inventory_errors.append({'pid':int(proc.name),'error_type':type(error).__name__})
locks=[]
kernel=pathlib.Path('/proc/locks').read_text()
for item in P['locks']:
 metadata=os.lstat(item['path']);assert stat.S_ISREG(metadata.st_mode) and metadata.st_uid==1001
 assert (metadata.st_dev,metadata.st_ino)==(item['dev'],item['ino'])
 matching=[]
 for line in kernel.splitlines():
  for token in line.split():
   parts=token.split(':')
   if len(parts)==3:
    try:identity=(int(parts[0],16),int(parts[1],16),int(parts[2]))
    except ValueError:continue
    if identity==(os.major(metadata.st_dev),os.minor(metadata.st_dev),metadata.st_ino):matching.append(line)
 locks.append({'path':item['path'],'dev':metadata.st_dev,'ino':metadata.st_ino,'uid':metadata.st_uid,'kernel_lock_lines':matching})
assert run(['/usr/bin/git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(root),'rev-parse','HEAD'])==head
assert {name:sha(root/name) for name in P['source8']}==source_hashes
assert not pathlib.Path(P['marker']).exists()
print(json.dumps({'owner':P['owner'],'recorded_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'uid':os.getuid(),
 'runtime_HEAD':head,'source8_sha256':source_hashes,'runtime_config_sha256':config_sha,
 'producer':P['producer'],'producer_files_sha256':producer_hashes,'production':P['production'],'production_files_sha256':production_hashes,
 'one_shot_marker':P['marker'],'one_shot_marker_absent_before_after':True,
 'gpu':gpu,'gpu_raw_row':gpu_raw,'contexts':contexts,'context_query_raw':context_raw,
 'project_trainers_or_testers':trainers,'same_uid_scanned':same_uid_scanned,'same_uid_inventory_errors':inventory_errors,
 'no_project_trainer_proven':not trainers and not inventory_errors,'original_locks_metadata_only':locks,
 'kernel_locks_read':True,'locks_acquired':False,'signals_sent':False,'remote_writes':False,
 'GPU0_only_queried':True,'GPU1_or_other_servers_queried':False,'Torch_imported':False,'training_launched_by_observer':False}))
'''
command='/usr/bin/python3 -I -B -c '+shlex.quote(program)
argv=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','songcl@192.168.1.115',command]
run=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
assert run.returncode==0,json.dumps({'returncode':run.returncode,'stderr':run.stderr[-2500:]})
observed=json.loads(run.stdout);assert observed['owner']==owner and observed['remote_writes'] is False
for path,expected in local_hashes.items():assert sha(path)==expected,path
assert {p.name:sha(p) for p in DISPATCH.iterdir() if p.is_file()}==dispatch_files
assert all(not (DISPATCH/name).exists() for name in absent_names)
actual={'owner':owner,'recorded_at':datetime.now(timezone.utc).isoformat(),'kind':'READ_ONLY_ACTUAL_CSO_PRELAUNCH_RESOURCE_REFUSAL_RECONCILIATION',
 'certainty':'terminal','collector_thread_id':'/root/cso_sync_peer','resource_gate_required_free_mib':20000,
 'known_prelaunch_refusal':{'stderr_path':str(stderr_path),'stderr_sha256':sha(stderr_path),'reason':'Direct memory.free below unchanged 20000 MiB gate','dispatch_intent_absent':True,'dispatch_result_absent':True,'prelaunch_result_absent':True},
 'producer_FROZEN_sha256':sha(PACKET/'FROZEN.json'),'producer_controller_sha256':frozen['files']['production_controller.py'],
 'direct_free_helper_sha256':sha(PACKET/'direct_memory_free_guard.py'),'probe_path':str(Path(__file__).resolve()),'probe_sha256':sha(__file__),
 'command_sha256':hashlib.sha256(command.encode()).hexdigest(),'ssh_returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'observation':observed,
 'local_files_sha256':local_hashes,'dispatch_files_sha256':dispatch_files,
 'M236_queue':{'canonical_task_sha256':value_sha(cso[0]),'status':cso[0]['status'],'pid':cso[0].get('pid'),'launch_verified':cso[0].get('launch_verified',False),'production_ready':cso[0].get('production_ready'),'source_commit':cso[0]['code_commit']},
 'protected_paused_tasks':protected,'no_launch_in_this_attempt':True,
 'no_launch_basis':'Direct-free failure precedes local dispatch intent and canonical queue dispatch; no intent/result, current M236 has no PID, and new production one-shot marker remains absent.',
 'prior_native_resource_checks_reclassified':False,'threshold_lowered':False,'automatic_retry_or_dispatch_performed':False,'remote_writes_or_signals':False}
target=TICK/'cso_resource_refusal.actual.json'
with target.open('x',encoding='utf-8',newline='\n') as stream:json.dump(actual,stream,indent=2);stream.write('\n')
print(json.dumps({'actual':str(target),'sha256':sha(target),'probe_sha256':sha(__file__),'gpu':observed['gpu'],'contexts':[{'pid':x['pid'],'used_gpu_memory_mib':x['used_gpu_memory_mib']} for x in observed['contexts']],'no_project_trainer_proven':observed['no_project_trainer_proven'],'one_shot_marker_absent':True}))
