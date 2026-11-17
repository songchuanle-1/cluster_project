"""Due evidence check,not repetition of completed CPU/scientific studies."""
from tick_ops import *
guard(180)
program=r'''import json,subprocess,fcntl,re,os
from pathlib import Path
from datetime import datetime,timezone
def capture(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
 return {'returncode':p.returncode,'stdout':p.stdout[-2500:],'stderr':p.stderr[-2500:]}
gpu=capture(['nvidia-smi','-i',str(GPU),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
contexts=capture(['nvidia-smi','-i',str(GPU),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
locks={};held=[];idle=None
if gpu['returncode']==0 and contexts['returncode']==0:
 fields=[s.strip() for s in gpu['stdout'].strip().split(',')]
 assert fields[:2]==[str(GPU),UUID],'UnexpectedphysicalGPUidentity;noCUDAallowed'
 for kind in ('training','diagnostic','exclusive'):
  handle=open('/tmp/cluster_project_gpu'+str(GPU)+'_'+kind+'.lock','a+b')
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;held.append(handle)
  except BlockingIOError:locks[kind]=False;handle.close()
 for handle in reversed(held):handle.close()
 idle=not contexts['stdout'].strip() and int(fields[2])<1024 and int(fields[3])<10 and all(locks.values())
result={'observed_at':datetime.now(timezone.utc).isoformat(),'physical_gpu':GPU,'expected_uuid':UUID,'gpu_query':gpu,'compute_contexts':contexts,'locks_available':locks,'idle':idle,'probe_locks_released':True,'cuda_executions':0,'status':'verified' if idle is not None else 'device_query_failed_current_occupation_unknown'}
if GPU==0:
 path=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
 with path.open('rb') as stream:
  stream.seek(max(0,path.stat().st_size-65536));tail=stream.read().decode('utf-8',errors='replace')
 steps=re.findall(r'Train\[(\d+)/50\].*?\|\s*(\d+)/4686',tail)
 distinct=[]
 for step in steps:
  if not distinct or distinct[-1]!=step:distinct.append(step)
 result['M204']={'pid':1085297,'process_exists':Path('/proc/1085297').exists(),'latest_distinct_native_steps':distinct[-6:],'recent_traceback':'Traceback' in tail,'log_modified_at':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),'observed_tail_window_bytes':65536,'log_size':path.stat().st_size}
print(json.dumps(result))
'''
records={}
for server,gpu in (('server-4',0),('server-3',1)):
 result=remote(server,'GPU='+str(gpu)+'\nUUID='+repr(SERVERS[server]['expected_gpu_uuid'])+'\n'+program)
 save('slot_'+server+'.json',result);records[server]=result
save('authorized_slots_current.json',records)
bundles=[]
for cid,folder in zip(PRIMARY,('tick_28fc3749','tick_87d50f0c')):
 path=ROOT/'pipeline/diagnostic_bundles'/folder/'native_manifest.json'
 m=tick.load(path);checks={name:tick.digest(path.parent/name)==sha for name,sha in m['diagnostic_files'].items()}
 protocol=ROOT/m['protocol']['path'];assert tick.digest(protocol)==m['protocol']['sha256']
 assert m['candidate_id']==cid and m['tolerance']==1e-6 and all(checks.values())
 bundles.append({'candidate_id':cid,'manifest':evidence(path),'protocol':evidence(protocol),'runner_hash_checks':checks,'local_frozen_files_unchanged':True,'native_gpu_task_run':False,'scientific_passes':0})
save('frozen_bundle_integrity.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'bundles':bundles,'interpretation':'Readiness/sourceidentityonly;no rerun of priorCPU/numericalfixtures,nonnative taskPASSornewmechanism.'})
goal=tick.load(ROOT/'pipeline/goal.json');assert goal['research_mainline']['primary_axis']=='hierarchical_attention_point_feature_update'
work=tick.load(ROOT/'pipeline/research_work.json')
scope=[]
for cid in AUX:
 c=next(c for c in work['candidates'] if c['id']==cid)
 assert c['stage']=='blocked' and c['blocker_kind']=='human_authorization'
 scope.append({'id':cid,'old_retry_after':c['retry_after'],'scope_hold':c['blocker'],'unblock_condition':c['unblock_condition'],'old_gates':c.get('gates'),'next_action':c['next_action']})
save('scope_recheck.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'goal_sha256':GOAL,'current_primary':goal['research_mainline'],'auxiliary_candidates':scope,'new_scope_authorization_in_this_turn':False,'CPA_resume_permission_already_executed':True,'scientific_retest_or_rejection':False,'decision':'Keepall4originalauxiliaryscopeholds;duetimersarenotpriorityrestoration/permission.NoM201recovery,noredundantCPAresumeapprovalrequest.'})
print(json.dumps({'resources':records,'bundle_count':len(bundles),'scope_holds_rechecked':len(scope),'native_gpu_executions':0,'new_training':0},ensure_ascii=True,indent=2))
