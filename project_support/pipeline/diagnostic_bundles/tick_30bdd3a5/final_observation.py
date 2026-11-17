"""Verify diagnostic GPU1 released while original GPU0 M204 keeps progressing."""
from gpu1_ops import *
guard(120)
program=r'''import json,subprocess,fcntl,re
from datetime import datetime,timezone
from pathlib import Path
cards={}
for gpu in (0,1):
 row=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 contexts=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
 fields=[x.strip() for x in row.split(',')]
 assert fields[:2]==[str(gpu),'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' if gpu==0 else 'GPU-7f82edb9-f620-8045-caea-a75232265cd1']
 locks={};held=[]
 for kind in ('training','diagnostic','exclusive'):
  handle=open('/tmp/cluster_project_gpu'+str(gpu)+'_'+kind+'.lock','a+b')
  try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;held.append(handle)
  except BlockingIOError:locks[kind]=False;handle.close()
 for handle in reversed(held):handle.close()
 cards[str(gpu)]={'gpu':row,'contexts':contexts,'locks_available':locks}
assert not cards['1']['contexts'] and all(cards['1']['locks_available'].values()),'GPU1cleanupnotverified'
assert '1085297' in cards['0']['contexts'] and not any(cards['0']['locks_available'].values())
path=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cpa_r1_resume_2546d803_native_serializer.log')
with path.open('rb') as stream:
 stream.seek(max(0,path.stat().st_size-65536));tail=stream.read().decode('utf-8',errors='replace')
steps=re.findall(r'Train\[(\d+)/50\].*?\|\s*(\d+)/4686',tail);distinct=[]
for step in steps:
 if not distinct or distinct[-1]!=step:distinct.append(step)
assert len(distinct)>=2
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'cards':cards,'GPU1_context_and_all_locks_released':True,'M204_pid':1085297,'M204_native_steps':distinct[-6:],'M204_log_modified_at':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),'M204_recent_traceback':'Traceback' in tail,'production_training_restarted_or_migrated':False,'new_training':0}))
'''
result=remote(program,conda=True);save('final_gpu_and_training_observation.json',result)
print(json.dumps(result,ensure_ascii=True,indent=2))
