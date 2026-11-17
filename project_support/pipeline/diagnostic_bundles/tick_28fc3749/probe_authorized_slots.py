"""Read only the two authorized physical GPU slots;never dispatch or evict."""
from ops import *

guard(90)
program=r'''import json,subprocess,fcntl,os
from pathlib import Path
from datetime import datetime,timezone
gpu=subprocess.check_output(['nvidia-smi','-i',str(GPU),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
cells=[cell.strip() for cell in gpu.split(',')]
assert cells[:2]==[str(GPU),UUID]
contexts=subprocess.check_output(['nvidia-smi','-i',str(GPU),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
locks={};handles=[]
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu'+str(GPU)+'_'+kind+'.lock','a+b')
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;handles.append(handle)
 except BlockingIOError:locks[kind]=False;handle.close()
for handle in reversed(handles):handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':contexts,'locks_available':locks,'probe_locks_released':True,'idle':not contexts and int(cells[2])<1024 and int(cells[3])<10 and all(locks.values()),'cuda_tests':0}))
'''
result={}
for server,gpu in (('server-4',0),('server-3',1)):
 try:
  result[server]=remote(server,'GPU='+str(gpu)+'\nUUID='+repr(SERVERS[server]['expected_gpu_uuid'])+'\n'+program,timeout=60)
 except Exception as error:result[server]={'observed_at':datetime.now(timezone.utc).isoformat(),'status':'probe_failed','error':str(error),'idle':None}
save('authorized_slots.json',result)
advance([OUT/'authorized_slots.json',OUT/'probe_authorized_slots.py'])
print(json.dumps(result,ensure_ascii=True,indent=2))
