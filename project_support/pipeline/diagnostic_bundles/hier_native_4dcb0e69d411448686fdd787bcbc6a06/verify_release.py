"""Verify only server3 physical GPU1 and release every diagnostic flock."""
from datetime import datetime, timezone
import json
import subprocess
from run import BUNDLE, TOKEN, guard, tick

guard()
payload = '''import fcntl,json,subprocess
from datetime import datetime,timezone
assert subprocess.check_output(['hostname'],text=True).strip()=='sysu311-MS-7C59'
gpu=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert gpu.split(',')[0].strip()=='1' and 'GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0' in gpu
contexts=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert not contexts,'Do not evict or change a live context.'
handles=[]
try:
 for name in ('/tmp/cluster_project_gpu1_m201_migration.lock','/tmp/cluster_project_gpu1_exclusive.lock','/tmp/cluster_project_gpu1_parameter_transport.lock'):
  handle=open(name,'a+b')
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  handles.append(handle)
finally:
 for handle in reversed(handles):handle.close()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':'sysu311-MS-7C59','physical_gpu':1,'gpu':gpu,'contexts':contexts,'flocks_acquired_released':len(handles),'new_training':False,'gpu0_used':False}))
'''
process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
    'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=payload,text=True,
    encoding='utf-8',capture_output=True,timeout=35)
guard()
path=BUNDLE/'release_verification.json'
assert not path.exists()
record={'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),'returncode':process.returncode,
    'stdout':process.stdout,'stderr':process.stderr,'source_sha256':tick.digest(BUNDLE/'verify_release.py')}
if process.returncode==0:record['result']=json.loads(process.stdout)
tick.save(path,record)
print(json.dumps(record,ensure_ascii=False))
assert process.returncode==0
