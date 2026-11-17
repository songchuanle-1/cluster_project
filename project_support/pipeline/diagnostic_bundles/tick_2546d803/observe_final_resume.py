"""One final scoped progress observation; never launch or change remote training."""
from ops import *
import pipeline_monitor as monitor
import time

guard(180)
experiment=monitor.load_experiment(str(ROOT),ID)
assert experiment['launch_verified'] and experiment['native_restore_verified']
program=r'''import json,re,subprocess,os
from pathlib import Path
from datetime import datetime,timezone
pid=PID;proc=Path('/proc')/str(pid)
parts=proc.joinpath('cmdline').read_bytes().split(b'\0') if proc.exists() else []
owned=b'tools/train.py' in parts and CONFIG.encode() in parts and b'--resume' in parts and CHECKPOINT.encode() in parts
path=Path(LOG)
with path.open('rb') as stream:
 stream.seek(0,2);size=stream.tell();stream.seek(max(0,size-90000));text=stream.read().decode('utf-8','replace')
steps=[(int(a),int(b)) for a,b in re.findall(r'Train\[(\d+)/\d+\]:[^\r\n]*?\|\s*(\d+)/\d+',text)]
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
assert [x.strip() for x in gpu.split(',')][:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
stage=Path(STAGE)
native_base=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/Path(CONFIG).stem
logs=sorted(native_base.glob('*/*.log'),key=lambda p:p.stat().st_mtime)
native=logs[-1];epoch=None;metrics=[];last_train=None
for line in native.read_text(errors='replace').splitlines():
 match=re.search(r'Epoch\s*\[(\d+)/50\]\[\s*(\d+)/(\d+)\]',line)
 if match:epoch=int(match.group(1));last_train=line.strip()
 metric=re.search(r'\bmIoU\s*:\s*([0-9.eE+-]+)',line)
 if metric:metrics.append({'epoch':epoch,'mIoU':float(metric.group(1))})
locks=[]
if proc.exists():
 for fd in proc.joinpath('fd').iterdir():
  try:target=os.readlink(fd)
  except OSError:continue
  if target.startswith('/tmp/cluster_project_gpu0_') and target.endswith('.lock'):locks.append(target)
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'pid':pid,'owned_resume_process_live':owned,'steps':steps[-8:],'gpu':gpu,'lock_fds':sorted(locks),'stdout_error_lines':[line.strip() for line in text.splitlines() if any(word in line for word in ('Traceback','RuntimeError:','CUDA out of memory','Skipping backward due to unstable loss'))][-8:],'native_log':str(native),'last_training_row':last_train,'new_validation_records':metrics,'native_exit':json.loads((stage/'native_exit.json').read_text()) if (stage/'native_exit.json').exists() else None}))
'''
manifest=tick.load(OUT/'runtime_manifest_native_serializer.json')
program='PID='+repr(experiment['pid'])+'\nCONFIG='+repr(experiment['config'])+'\nCHECKPOINT='+repr(experiment['resume_checkpoint'])+'\nLOG='+repr(experiment['log'])+'\nSTAGE='+repr(STAGE+'_native_serializer')+'\n'+program
before=ssh(program,timeout=90);save('final_resume_before.json',before)
time.sleep(3)
after=ssh(program,timeout=90);save('final_resume_after.json',after)
assert before['owned_resume_process_live'] and after['owned_resume_process_live']
assert before['steps'] and after['steps'] and after['steps'][-1][1]>before['steps'][-1][1]
assert not after['native_exit'] and not after['stdout_error_lines'] and len(after['lock_fds'])==3
mutex=monitor.acquire_lock(str(ROOT));assert mutex is not None
try:
 current=monitor.load_experiment(str(ROOT),ID)
 assert current['pid']==experiment['pid']
 current.update(latest_training_observation=evidence(OUT/'final_resume_after.json'),observed_native_step=after['steps'][-1],resume_remote_stage=STAGE+'_native_serializer',resume_runtime_manifest=evidence(OUT/'runtime_manifest_native_serializer.json'),verified_training_resume_count=1,os_resume_startup_attempts=2,pretraining_observer_failures=1)
 monitor.save_experiment(str(ROOT),current)
finally:mutex.close()
advance([OUT/'final_resume_before.json',OUT/'final_resume_after.json',OUT/'observe_final_resume.py',ROOT/'pipeline/bugfixes/bugfix_20261019-1629.md'])
pending=[c for c in tick.load(ROOT/'pipeline/research_work.json')['candidates'] if c.get('stage') not in ('training','complete','rejected','closed')]
assert len(pending)==4 and all(c['stage']=='blocked' and c['blocker_kind']=='human_authorization' for c in pending)
save('resume_outcome.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment_id':ID,'same_experiment_resumed':True,'scientific_admission':False,'scientific_state':'inconclusive','actual_verified_training_resumes':1,'os_resume_startup_attempts':2,'pretraining_observer_failures':1,'cpu_full_state_serialization_proofs':1,'model_changes':0,'config_changes':0,'new_candidates':0,'structural_revisions':0,'before_step':before['steps'][-1],'after_step':after['steps'][-1],'restored_checkpoint_epoch':5,'checkpoint_best_miou':0.43399661779403687,'new_validation_records':after['new_validation_records'],'native_log':after['native_log'],'remaining_auxiliary_human_holds':[{'id':c['id'],'retry_after':c['retry_after']} for c in pending],'current_gpu_sample_not_peak':after['gpu'],'authorization':evidence(AUTH),'state_restore_verification':evidence(OUT/'resume_progress_native_serializer.json'),'final_observation':evidence(OUT/'final_resume_after.json')})
advance([OUT/'resume_outcome.json'])
work=tick.load(ROOT/'pipeline/research_work.json')
work['design_cycle']={'recorded_at':datetime.now(timezone.utc).isoformat(),'stop_reason':'external_resource_blocked','blocker_kind':'human_authorization','actual_reason':'The specific human-requested SAME M204 checkpoint recovery is complete with native progress. Remaining four old auxiliary candidates have unchanged not-yet-due human scope holds. This is not a GPU shortage,scientific no-gain claim,global research pause or assertion that spare preparation budget is zero. No unrelated new mechanism was started in this manual resume operation.','attempted_ids':[CID],'evidence':[evidence(OUT/'resume_outcome.json'),evidence(OUT/'resume_progress_native_serializer.json'),evidence(OLD/'scope_holds_recheck.json')],'resume_condition':'Monitor the actually resumed M204;continue independently authorized primary-axis research within future tick budgets. The four parked auxiliary routes require explicit scope restoration or a separately justified mainline-required auxiliary test,not a timer or free GPU. Do not ask again for the already-executed checkpoint resume permission.','retry_after':min(c['retry_after'] for c in pending)}
guard();tick.save(ROOT/'pipeline/research_work.json',work)
decision=monitor.log_decision(str(ROOT),'manual','Human authorized the exact same M204 checkpoint resume after the confirmed server4 reboot.','Restored same M204 on server4 physicalGPU0 from epoch5 last.pth;kept AdamW/PolyLR/best/patience/fixed seed1999,batch2,workers4,total50epochs. Verified native epoch6 progress. Preserved one failed pre-loop observer and its CPU-proved native-serializer correction. No future automatic restart.','Direct human reply in owning chat;fresh strict identity/source/checkpoint/idleness/flock checks;full CPU serialized state proof and real native restoration/progress receipts. No model/config/scientific gate changes.',str(OUT/'resume_outcome.json'))
save('manual_resume_decision.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'decision_file':decision,'outcome':evidence(OUT/'resume_outcome.json')})
print(json.dumps({'observed_at':after['observed_at'],'pid':after['pid'],'before_step':before['steps'][-1],'after_step':after['steps'][-1],'new_validation_records':after['new_validation_records'],'gpu':after['gpu'],'remaining_auxiliary_holds':len(pending)},ensure_ascii=True,indent=2))
