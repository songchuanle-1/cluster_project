"""Preserve failed nvidia-smi evidence;unknown hardware is not idle/busy."""
from ops import *
guard(120)
save('initial_slot_probe_failure.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'script':evidence(OUT/'probe_current_slots.py'),'status':'FAILEDbeforeJSONsave','server':'server-3','stage':'nvidia-smi-i1query-gpu','returncode':255,'exception':'subprocess.CalledProcessError','server4_partial_result_saved':False,'interpretation':'Server3SSHhostnameverified but NVMLqueryfailed;currentGPU1occupationunknown,NOTidle/NOTprovenbusy. NoCUDAworkattempted.'})
program=r'''import json,subprocess,fcntl,os,re
from pathlib import Path
from datetime import datetime,timezone
def run(args):
 value=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
 return {'returncode':value.returncode,'stdout':value.stdout[-3000:],'stderr':value.stderr[-3000:]}
inventory=run(['nvidia-smi','-L'])
gpu=run(['nvidia-smi','-i',str(GPU),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
contexts=run(['nvidia-smi','-i',str(GPU),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
locks={};held=[];idle=None
if gpu['returncode']==0 and contexts['returncode']==0:
 fields=[s.strip() for s in gpu['stdout'].strip().split(',')];assert fields[:2]==[str(GPU),UUID]
 for kind in ('training','diagnostic','exclusive'):
  handle=open('/tmp/cluster_project_gpu'+str(GPU)+'_'+kind+'.lock','a+b')
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;held.append(handle)
  except BlockingIOError:locks[kind]=False;handle.close()
 for handle in reversed(held):handle.close()
 idle=not contexts['stdout'].strip() and int(fields[2])<1024 and int(fields[3])<10 and all(locks.values())
result={'observed_at':datetime.now(timezone.utc).isoformat(),'gpu_query':gpu,'compute_contexts':contexts,'inventory':inventory,'locks_available':locks,'idle':idle,'probe_locks_released':True,'cuda_tests':0,'status':'verified' if idle is not None else 'nvml_query_failed_occupation_unknown'}
if GPU==0:
 path=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
 text=path.read_text(encoding='utf-8',errors='replace')
 steps=re.findall(r'Train\[(\d+)/50\].*?\|\s*(\d+)/4686',text)
 metrics=[s for s in text.splitlines() if s.startswith('mIOU:')][-4:]
 result['M204']={'alive':Path('/proc/1085297').exists(),'pid':1085297,'latest_native_steps':steps[-8:],'recent_VAL':metrics,'recent_traceback':'Traceback' in text[-50000:],'log_bytes':path.stat().st_size}
print(json.dumps(result))
'''
records={}
for server,gpu in (('server-4',0),('server-3',1)):
 records[server]=remote(server,'GPU='+str(gpu)+'\nUUID='+repr(SERVERS[server]['expected_gpu_uuid'])+'\n'+program,timeout=90)
save('authorized_slots_and_fault.json',records)
advance([OUT/'initial_slot_probe_failure.json',OUT/'inspect_slot_failure.py',OUT/'authorized_slots_and_fault.json'])
print(json.dumps(records,ensure_ascii=True,indent=2))
