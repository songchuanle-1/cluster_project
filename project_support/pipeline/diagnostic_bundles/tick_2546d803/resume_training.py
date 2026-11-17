"""Stage, launch once and verify the specifically authorized SAME M204 resume."""
from ops import *
import argparse,ast,copy,time
import closure
import pipeline_monitor as monitor

SERVER=monitor.load_servers(str(ROOT))['server-4']

def shell(host,user,command,timeout=120):
 assert host==SERVER['host']=='192.168.1.115' and user=='songcl'
 return transport(command,timeout)

def stage():
 auth=tick.load(AUTH);environment=tick.load(OUT/'fresh_resume_environment.json')
 assert auth['authorized'] and auth['kind']=='single_checkpoint_resume' and environment['ready_for_guarded_resume']
 assert not auth['scientific_admission'] and auth['maximum_resume_launches']==1
 ast.parse((OUT/'guarded_resume.py').read_text(encoding='utf-8'))
 manifest=tick.load(ORIGINAL/'runtime_manifest.json')
 source=tick.load(OLD/'resume_contract_cpu.json')['resume_functions'][0]
 assert source['name']=='resume'
 manifest.update(authorization_path=STAGE+'/'+AUTH.name,authorization_sha256=tick.digest(AUTH),guard_sha256=tick.digest(OUT/'guarded_resume.py'),checkpoint=auth['checkpoint'],checkpoint_sha256=auth['checkpoint_sha256'],resume_implementation_path=source['path'],resume_implementation_sha256=source['file_sha256'],resume_authorization=True,scientific_admission=False)
 save('runtime_manifest.json',manifest)
 created=ssh('from pathlib import Path\nimport json\nPath('+repr(STAGE)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
 copied=run(['scp',*SSH,str(AUTH),str(OUT/'runtime_manifest.json'),str(OUT/'guarded_resume.py'),'songcl@192.168.1.115:'+STAGE+'/'],timeout=90)
 assert copied.returncode==0,copied.stderr
 checked=ssh('from pathlib import Path\nimport json,hashlib\nstage=Path('+repr(STAGE)+')\nprint(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir() if p.is_file()}))')
 for path in (AUTH,OUT/'runtime_manifest.json',OUT/'guarded_resume.py'):assert checked[path.name]==tick.digest(path)
 save('resume_staging.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'stage':STAGE,'authorization':evidence(AUTH),'runtime_manifest':evidence(OUT/'runtime_manifest.json'),'guard':evidence(OUT/'guarded_resume.py'),'uploaded_hashes_verified':True,'same_original_code_commit':manifest['code_commit'],'model_changes':0,'config_changes':0,'git_syncs':0,'launches':0})
 advance([OUT/'resume_staging.json',OUT/'runtime_manifest.json',OUT/'guarded_resume.py',OUT/'resume_training.py'],stage='deployment',blocker=None,blocker_kind=None,retry_after=None,unblock_condition=None,next_action='Execute the already-authorized single guarded SAME M204 checkpoint resume,then verify actual restored states and increasing epoch6 steps. Scientific gates remain unchanged.')
 print(json.dumps({'staged':True,'same_code_commit':manifest['code_commit'],'model_or_config_changed':False,'new_training_launches':0}))

def launch():
 guard(300)
 manifest=tick.load(OUT/'runtime_manifest.json');auth=tick.load(AUTH)
 assert auth['authorized'] and manifest['authorization_sha256']==tick.digest(AUTH)
 mutex=monitor.acquire_lock(str(ROOT));assert mutex is not None,'Monitor lock busy;do not launch'
 try:
  queue=monitor.load_queue(str(ROOT));running=monitor.load_running(str(ROOT))
  assert not any(t.get('id')==ID for values in queue['gpu_queues'].values() for t in values)
  assert not running.get('server-4',{}).get('0')
  previous=monitor.load_experiment(str(ROOT),ID)
  assert previous['status']=='stopped_unknown' and previous['automatic_restart'] is False
  save('experiment_before_resume.json',previous)
  task={'id':ID,'candidate_id':CID,'config':manifest['config'],'server':'server-4','gpu':'0','status':'claiming','label':'CPA-R1 coarse point attention (authorized checkpoint resume)','code_commit':manifest['code_commit'],'manual_exploratory_authorization':previous['manual_exploratory_authorization'],'checkpoint_resume_authorization':evidence(AUTH),'scientific_admission':False,'launch_authorization_mode':'human_exploratory_resume_exception','automatic_restart':False,'requires_exclusive_ownership':True,'launch_verified':False,'launch_verification':'pending_progress','depends_on':[],'patience':previous['patience'],'resume_checkpoint':manifest['checkpoint'],'resume_checkpoint_sha256':manifest['checkpoint_sha256'],'note':'Same M204 interrupted by host reboot;one new explicit checkpoint-resume consent. No scientific PASS,tuning,cold restart or future automatic retry.'}
  queue['gpu_queues']['server-4'].append(task)
  monitor.save_queue(str(ROOT),queue)
  claiming=copy.deepcopy(previous);claiming.update(task)
  claiming['resume_authorization_pending_launch']=True
  monitor.save_experiment(str(ROOT),claiming)
  running.setdefault('server-4',{})['0']=ID;monitor.save_running(str(ROOT),running)
  log=manifest['root']+'/logs/train_'+Path(manifest['config']).stem+'_resume_2546d803.log'
  program=r'''import json,os,subprocess,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
root=Path(MANIFEST['root']);stage=Path(STAGE)
assert hashlib.sha256((stage/'runtime_manifest.json').read_bytes()).hexdigest()==MANIFEST_SHA
assert hashlib.sha256((stage/'guarded_resume.py').read_bytes()).hexdigest()==MANIFEST['guard_sha256']
assert hashlib.sha256((stage/'cpa_resume_M204.json').read_bytes()).hexdigest()==MANIFEST['authorization_sha256']
with (stage/'launch_claim.json').open('x') as f:json.dump({'experiment_id':'M204-CPA','single_explicit_checkpoint_resume':True,'claimed_at':datetime.now(timezone.utc).isoformat()},f)
env=os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
env['PYTHONPATH']=str(root)+':'+str(root/'framework/lib')+':'+env.get('PYTHONPATH','')
pyver='.'.join(str(v) for v in sys.version_info[:2])
env['LD_LIBRARY_PATH']=env['CONDA_PREFIX']+'/lib:'+env['CONDA_PREFIX']+'/lib/python'+pyver+'/site-packages/torch/lib:'+env.get('LD_LIBRARY_PATH','')
temp=root.parent/'pipeline/tmp';temp.mkdir(parents=True,exist_ok=True);env['TMPDIR']=str(temp)
command=[sys.executable,'-u','-B',str(stage/'guarded_resume.py'),'--manifest',str(stage/'runtime_manifest.json'),'tools/train.py',MANIFEST['config'],'--resume',MANIFEST['checkpoint'],'--gpu_ids','0','--num_gpus','1']
with open(LOG,'xb',buffering=0) as output:process=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
result={'pid':process.pid,'log':LOG,'command':command,'launched_at':datetime.now(timezone.utc).isoformat()}
with (stage/'launch_process.json').open('x') as f:json.dump(result,f)
(root/'logs'/('.pid_'+Path(MANIFEST['config']).stem)).write_text(str(process.pid))
print(json.dumps(result))
'''
  program='MANIFEST='+repr(manifest)+'\nSTAGE='+repr(STAGE)+'\nLOG='+repr(log)+'\nMANIFEST_SHA='+repr(tick.digest(OUT/'runtime_manifest.json'))+'\n'+program
  result=ssh(program,conda=True,timeout=120)
  assert isinstance(result['pid'],int) and result['log']==log
  task.update(status='running',pid=result['pid'],log=log,launched=result['launched_at'])
  monitor.save_queue(str(ROOT),queue)
  experiment=copy.deepcopy(previous)
  experiment.update(task)
  experiment.update(original_launched=previous.get('original_launched',previous['launched']),resumed_at=result['launched_at'],previous_pid=previous['pid'],process_live=None,requires_resume_authorization=False,resume_authorization_pending_launch=False,interruption_snapshot=evidence(OUT/'experiment_before_resume.json'),resume_attempt_count=previous.get('resume_attempt_count',0)+1)
  for key in ('finished_at','final_best','epochs_final'):experiment.pop(key,None)
  experiment.setdefault('history',[]).append({'ts':result['launched_at'],'action':'human_authorized_same_experiment_checkpoint_resume','checkpoint_epoch':5,'start_epoch':6,'pid':result['pid'],'gpu':'0','checkpoint_sha256':manifest['checkpoint_sha256'],'authorization':evidence(AUTH)})
  monitor.save_experiment(str(ROOT),experiment)
  save('resume_launch.json',dict(result,authorization=evidence(AUTH),launch_verified=False,scientific_admission=False))
  advance([OUT/'experiment_before_resume.json',OUT/'resume_launch.json'],next_action='The sole authorized resume process was launched;verify state-restoration receipt and increasing native epoch6 steps. Do not launch or retry again from PID existence alone.')
  print(json.dumps({'pid':result['pid'],'resumed_at':result['launched_at'],'launch_verified':False,'same_experiment':ID},ensure_ascii=True))
 finally:mutex.close()

def verify():
 guard(240)
 task=monitor.load_experiment(str(ROOT),ID)
 assert task['checkpoint_resume_authorization']==evidence(AUTH)
 before=shell(SERVER['host'],SERVER['user'],'tail -c 120000 '+shlex.quote(task['log']))
 passed=closure.verify_progress(SERVER,task,shell,wait_s=180)
 time.sleep(3)
 after=shell(SERVER['host'],SERVER['user'],'tail -c 120000 '+shlex.quote(task['log']))
 program=r'''import json,subprocess,os
from pathlib import Path
from datetime import datetime,timezone
pid=PID;proc=Path('/proc')/str(pid);stage=Path(STAGE)
parts=proc.joinpath('cmdline').read_bytes().split(b'\0') if proc.exists() else []
owned=b'tools/train.py' in parts and CONFIG.encode() in parts and CHECKPOINT.encode() in parts and b'--resume' in parts
locks=[]
if proc.exists():
 for fd in proc.joinpath('fd').iterdir():
  try:target=os.readlink(fd)
  except OSError:continue
  if target.startswith('/tmp/cluster_project_gpu0_') and target.endswith('.lock'):locks.append(target)
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
assert [x.strip() for x in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
restoration=stage/'resume_restoration.json';exitfile=stage/'native_exit.json'
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'pid':pid,'owned_resume_process_live':owned,'gpu':gpu,'contexts':contexts,'lifetime_lock_fds':sorted(locks),'resume_restoration':json.loads(restoration.read_text()) if restoration.exists() else None,'native_exit':json.loads(exitfile.read_text()) if exitfile.exists() else None}))
'''
 program='PID='+repr(task['pid'])+'\nSTAGE='+repr(STAGE)+'\nCONFIG='+repr(task['config'])+'\nCHECKPOINT='+repr(task['resume_checkpoint'])+'\n'+program
 observed=ssh(program,timeout=60)
 restoration=observed['resume_restoration']
 result={'observed_at':datetime.now(timezone.utc).isoformat(),'experiment_id':ID,'launch_verified':passed,'before_steps':closure.steps(before)[-6:],'after_steps':closure.steps(after)[-6:],'state_restore_verified':bool(restoration and restoration['optimizer_matches_saved_state'] and restoration['scheduler_matches_saved_state'] and restoration['model_layout_and_anchor_match']),'environment':observed,'traceback':'Traceback (most recent call last)' in after,'unstable_loss_skip':'Skipping backward due to unstable loss' in after,'log_tail':after[-14000:],'scientific_admission':False}
 save('resume_progress_verification.json',result)
 assert passed and result['state_restore_verified'] and observed['owned_resume_process_live'] and len(observed['lifetime_lock_fds'])==3 and not result['traceback'] and not observed['native_exit'],'Resume is not verified;preserve exact PID/log and investigate without relaunch'
 assert restoration['metadata']['epoch']==5 and restoration['planned_start_epoch']==6 and all(epoch==6 for epoch,step in result['after_steps'])
 mutex=monitor.acquire_lock(str(ROOT));assert mutex is not None
 try:
  queue=monitor.load_queue(str(ROOT));current=next(t for t in queue['gpu_queues']['server-4'] if t['id']==ID)
  current.update(launch_verified=True,launch_verification='training_progress',launch_evidence=evidence(OUT/'resume_progress_verification.json'),native_restore_verified=True)
  monitor.save_queue(str(ROOT),queue)
  experiment=monitor.load_experiment(str(ROOT),ID)
  experiment.update(launch_verified=True,launch_verification='training_progress',launch_evidence=evidence(OUT/'resume_progress_verification.json'),native_restore_verified=True,process_live=True,latest_training_observation=evidence(OUT/'resume_progress_verification.json'),observed_native_step=result['after_steps'][-1])
  experiment['history'].append({'ts':result['observed_at'],'action':'native_resume_states_and_progress_verified','steps':result['after_steps'],'saved_epoch':5,'optimizer_preserved':True,'scheduler_preserved':True})
  monitor.save_experiment(str(ROOT),experiment)
 finally:mutex.close()
 advance([OUT/'resume_progress_verification.json'],stage='training',blocker=None,blocker_kind=None,retry_after=None,unblock_condition=None,gate_result='Human-authorized same-experiment native checkpoint resume and preserved optimizer/scheduler states verified;epoch6 steps increasing. Diagnosis/semantic-control gates still unpassed,revision1 inconclusive;scientific efficacy unknown.',next_action='Monitor this SAME resumed M204-CPA native TRAIN/ScanReferVAL and original preregistered evaluation plan. Keep one-resume permission consumed,no automatic future restart,tuning,new variant or scope expansion.')
 print(json.dumps({k:v for k,v in result.items() if k not in ('log_tail','environment')}|{'pid':task['pid'],'gpu':observed['gpu'],'lifetime_lock_fds':observed['lifetime_lock_fds'],'restored_metadata':restoration['metadata'],'optimizer_state_entries':restoration['optimizer']['state_entries'],'scheduler_last_epoch':restoration['scheduler']['last_epoch']},ensure_ascii=True,indent=2))

parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['stage','launch','verify'])
phase=parser.parse_args().phase
guard(240)
{'stage':stage,'launch':launch,'verify':verify}[phase]()
