"""Final bounded physical GPU0-only observation, no computation, signals or leases."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

BASE=Path(__file__).resolve().parent
PAYLOAD=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import datetime as dt,json,subprocess
def run(args):
    r=subprocess.run(args,capture_output=True,text=True,timeout=15)
    assert r.returncode==0,r.stderr
    return r.stdout.strip()
inventory=run(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
assert inventory.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=run(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
print(json.dumps(dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),hostname=socket.gethostname(),
    physical_gpu=0,inventory=inventory,contexts=contexts,compute_context_present=bool(contexts),
    context_ownership='FOREIGN_OR_UNREGISTERED_PRESERVE' if contexts else 'NO_CONTEXT_OBSERVED_NOT_A_LEASE',
    GPU1='NOT_QUERIED_RELEASED_TO_OTHERS',torch_imported=False,GPU_computation=False,signals_sent=False)))
'''
def main():
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
          'songcl@192.168.1.115','/usr/bin/python3 -B -']
    r=subprocess.run(args,input=PAYLOAD,capture_output=True,text=True,encoding='utf-8',timeout=45)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=args,
        payload_sha256=hashlib.sha256(PAYLOAD.encode()).hexdigest(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    if r.returncode==0:result['data']=json.loads(r.stdout)
    p=BASE/'gpu0_slot_final.json'
    with p.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),**result.get('data',{})),ensure_ascii=False))
    if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':main()
