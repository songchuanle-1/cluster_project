"""Read-only probe compatible with server3 system Python3.6."""
from ops import *
guard(90)
program=r'''import json,subprocess,fcntl
from datetime import datetime,timezone
gpu=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],universal_newlines=True,timeout=15).strip()
cells=[x.strip() for x in gpu.split(',')]
assert cells[:2]==['1','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0']
contexts=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],universal_newlines=True,timeout=15).strip()
handles=[];locks={}
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu1_'+kind+'.lock','a+b')
 try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks[kind]=True;handles.append(handle)
 except BlockingIOError:locks[kind]=False;handle.close()
for handle in reversed(handles):handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':gpu,'contexts':contexts,'locks_available':locks,'probe_locks_released':True,'idle':not contexts and int(cells[2])<1024 and int(cells[3])<10 and all(locks.values()),'cuda_tests':0}))
'''
value=remote('server-3',program,timeout=60)
result=tick.load(OUT/'authorized_slots_verified.json');result['server-3']=value
save('authorized_slots_final.json',result)
advance([OUT/'authorized_slots_final.json',OUT/'probe_server3_compatible.py'])
print(json.dumps(result,ensure_ascii=True,indent=2))
