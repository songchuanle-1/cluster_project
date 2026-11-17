"""Read-only authorized physical-GPU identities and fresh occupation,never evict."""
from ops import *
guard(120)
program=r'''import json,subprocess,fcntl,os
from datetime import datetime,timezone
gpu=subprocess.check_output(['nvidia-smi','-i',str(GPU),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=15).strip()
fields=[s.strip() for s in gpu.split(',')];assert fields[:2]==[str(GPU),UUID]
contexts=subprocess.check_output(['nvidia-smi','-i',str(GPU),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=15).strip()
locks={};held=[]
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu'+str(GPU)+'_'+kind+'.lock','a+b')
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;held.append(handle)
 except BlockingIOError:locks[kind]=False;handle.close()
for handle in reversed(held):handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':contexts,'locks_available':locks,'idle':not contexts and int(fields[2])<1024 and int(fields[3])<10 and all(locks.values()),'probe_locks_released':True,'cuda_tests':0}))
'''
records={}
for server,gpu in (('server-4',0),('server-3',1)):
 records[server]=remote(server,'GPU='+str(gpu)+'\nUUID='+repr(SERVERS[server]['expected_gpu_uuid'])+'\n'+program,timeout=60)
save('authorized_slots_current.json',records)
advance([OUT/'probe_current_slots.py',OUT/'authorized_slots_current.json'])
print(json.dumps(records,ensure_ascii=True,indent=2))
