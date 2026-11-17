"""Preserve a proved pre-loop observer failure before completing the same resume."""
from ops import *
import pipeline_monitor as monitor

guard(240)
proof=tick.load(OUT/'native_serialization_cpu_proof.json')
failure=tick.load(OUT/'resume_progress_verification.json')
manifest=tick.load(OUT/'runtime_manifest.json')
assert proof['all_native_saved_tensors_equal'] and not proof['optimizer_tensor_mismatches'] and proof['scheduler_equal']
assert not proof['cuda_initialized'] and proof['native_optimizer_steps']==0
assert not failure['before_steps'] and not failure['after_steps']
exit_record=failure['environment']['native_exit']
assert exit_record['error']=='Model state restore mismatch' and exit_record['resume_observed'] is False
auth=tick.load(AUTH)
assert auth['authorized'] and auth['kind']=='single_checkpoint_resume' and not auth['automatic_retry_or_restart']
program=r'''import json,hashlib,re,subprocess,fcntl
from pathlib import Path
from datetime import datetime,timezone
root=Path(MANIFEST['root'])
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
assert sha(MANIFEST['checkpoint'])==MANIFEST['checkpoint_sha256']
stage=Path(STAGE);exit_record=json.loads((stage/'native_exit.json').read_text())
assert exit_record['error']=='Model state restore mismatch' and exit_record['resume_observed'] is False
text=Path(LOG).read_text(errors='replace')
assert not re.search(r'Train\[\d+/|Epoch\s*\[',text),'Native training already ran;no pre-training correction permitted'
matches=[]
for path in Path('/proc').glob('[0-9]*/cmdline'):
 try:parts=path.read_bytes().split(b'\0')
 except OSError:continue
 if b'tools/train.py' in parts and MANIFEST['config'].encode() in parts:matches.append(int(path.parent.name))
assert not matches,'Do not relaunch an existing candidate process'
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
cells=[v.strip() for v in gpu.split(',')]
assert cells[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
handles=[];locks={}
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;handles.append(handle)
 except BlockingIOError:locks[kind]=False;handle.close()
for handle in reversed(handles):handle.close()
ready=not contexts and int(cells[2])<1024 and int(cells[3])<10 and all(locks.values())
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'prior_startup_failed_before_any_train_loop':True,'prior_new_training_steps':0,'prior_checkpoint_writes':0,'checkpoint_sha256':MANIFEST['checkpoint_sha256'],'exact_config_process_ids':matches,'gpu':gpu,'contexts':contexts,'exclusive_locks_available':locks,'probe_locks_released':True,'ready_for_guarded_resume':ready,'original_failure':exit_record}))
'''
experiment=monitor.load_experiment(str(ROOT),ID)
program='MANIFEST='+repr(manifest)+'\nSTAGE='+repr(STAGE)+'\nLOG='+repr(experiment['log'])+'\n'+program
environment=ssh(program,timeout=120)
save('fresh_environment_after_cpu_proof.json',environment)
assert environment['ready_for_guarded_resume'],'Actual resource block;do not start'
save('pretraining_correction_decision.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'authorization':evidence(AUTH),'new_human_authorization':False,'authorization_unchanged':True,'human_requested_operation':'Resume SAME M204 from immutable epoch5 checkpoint;one actual resumed training run,not a new experiment.','classification':'Completion of the still-unfulfilled direct human resume operation after correcting our own observer before the first training step. This is not restart of training that had begun,not a scientific implementation revision,and not permission for future automatic restarts.','failed_os_startups':1,'actual_resumed_training_runs_so_far':0,'corrective_pretraining_startups_bounded_to':1,'change':'Use gorilla.solver.checkpoint.get_state_dict for observation,the exact same serializer used by native checkpoint saving;do not omit tensors or weaken numerical equality.','cpu_proof':evidence(OUT/'native_serialization_cpu_proof.json'),'failed_startup':evidence(OUT/'resume_progress_verification.json'),'fresh_resources':evidence(OUT/'fresh_environment_after_cpu_proof.json'),'model_changes':0,'config_changes':0,'scientific_gate_changes':0,'no_blind_retry':True,'no_automatic_post_training_restart':True})
mutex=monitor.acquire_lock(str(ROOT));assert mutex is not None
try:
 guard(180)
 experiment=monitor.load_experiment(str(ROOT),ID)
 assert experiment['pid']==1002720 and not experiment['launch_verified'] and experiment['resume_attempt_count']==1
 queue=monitor.load_queue(str(ROOT));running=monitor.load_running(str(ROOT))
 assert running['server-4']['0']==ID
 save('failed_startup_lifecycle.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment':experiment,'native_failure':failure['environment']['native_exit'],'native_training_steps':0,'native_resume_restoration_receipt_absent':True,'cpu_proof':evidence(OUT/'native_serialization_cpu_proof.json')})
 experiment.update(status='stopped_unknown',process_live=False,launch_verified=False,launch_verification='startup_observer_failed_before_training',requires_resume_authorization=False,pretraining_observer_failure=evidence(OUT/'failed_startup_lifecycle.json'),corrective_pretraining_operation=evidence(OUT/'pretraining_correction_decision.json'))
 experiment.setdefault('history',[]).append({'ts':datetime.now(timezone.utc).isoformat(),'action':'pretraining_observer_false_mismatch_proved_on_cpu','pid':1002720,'native_training_steps':0,'native_serializer_tensor_equality':True,'model_or_scientific_revision':False,'failure_evidence':evidence(OUT/'resume_progress_verification.json')})
 monitor.save_experiment(str(ROOT),experiment)
 queue['gpu_queues']['server-4']=[task for task in queue['gpu_queues']['server-4'] if task.get('id')!=ID]
 monitor.save_queue(str(ROOT),queue)
 del running['server-4']['0']
 if not running['server-4']:del running['server-4']
 monitor.save_running(str(ROOT),running)
finally:mutex.close()
advance([OUT/'failed_startup_lifecycle.json',OUT/'pretraining_correction_decision.json',OUT/'fresh_environment_after_cpu_proof.json',OUT/'reconcile_pretraining_guard.py'],next_action='Complete the same already-authorized checkpoint resume using the CPU-proved native serializer observer. Exactly one bounded corrective pre-training startup;preserve failed attempt,no later automatic training restart or model/config change.')
print(json.dumps({'pretraining_failure_preserved':True,'model_optimizer_scheduler_cpu_equality':True,'exact_active_processes':environment['exact_config_process_ids'],'gpu':environment['gpu'],'failed_native_training_steps':0,'same_human_authorized_operation_pending':True},ensure_ascii=True,indent=2))
