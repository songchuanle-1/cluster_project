"""Bounded pinned GPU0-only observation of the exact authorized resumed HAP process."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
PAYLOAD=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import datetime as dt,json,os,re,subprocess,time
from pathlib import Path
p=Path('/proc')/str(PARAMS['pid'])
out=dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),hostname=socket.gethostname(),pid=PARAMS['pid'],process_exists=p.exists())
if p.exists():
    s=(p/'stat').read_text().rsplit(')',1)[1].split()
    args=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
    expected=['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1','--resume',PARAMS['resume_from']]
    cwd=os.readlink(p/'cwd')
    out.update(starttime=s[19],state=s[0],argv=args,cwd=cwd,
        exact_original_identity=(s[19]==PARAMS['starttime'] and args==expected and cwd==PARAMS['remote_code_root']))
path=Path(PARAMS['log'])
with path.open('rb') as f:f.seek(max(0,path.stat().st_size-2000000));text=f.read().decode(errors='replace')
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
out['native_progress']=[dict(epoch=int(m[1]),epochs=int(m[2]),step=int(m[3]),steps=int(m[4])) for m in matches[-2:]]
lines=text.replace('\r','\n').splitlines()
out['terminal_or_metric_lines']=[s for s in lines if any(k in s for k in ('Traceback','AttributeError','RuntimeError','Early stopping','mIOU:','save last pth','save best pth'))][-12:]
out.update(log=str(path),log_bytes=path.stat().st_size,log_age_seconds=time.time()-path.stat().st_mtime)
def run(a):
    r=subprocess.run(a,text=True,capture_output=True,timeout=15)
    assert r.returncode==0,r.stderr
    return r.stdout.strip()
inventory=run(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
assert inventory.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
out.update(gpu0_inventory=inventory,gpu0_contexts=run(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']),
    GPU1='NOT_QUERIED_RELEASED_TO_OTHERS',read_only=True,torch_imported=False,GPU_computation_started=False,signals_sent=False)
print(json.dumps(out))
'''
def observe(params):
    payload='PARAMS='+repr(params)+'\n'+PAYLOAD
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
    r=subprocess.run(args,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=45)
    out=dict(command=args,payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    if r.returncode==0:out['data']=json.loads(r.stdout)
    return out
def main():
    q=json.loads((ROOT/'pipeline/queue.json').read_text(encoding='utf-8-sig'))
    task=next(t for t in q['gpu_queues']['server-4'] if t['id']=='M207-HAP')
    assert task['status']=='running' and task['launch_verified'] is True and task['pid']==1063355
    old=json.loads((ROOT/'pipeline/manual_ops/20261022_hap_resume_151948/native_resume_progress.json').read_text(encoding='utf-8'))
    params={k:task[k] for k in ('pid','config','resume_from','log')}
    params.update(starttime=old['observations'][0]['data']['starttime'],remote_code_root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
    observations=[observe(params)];time.sleep(3);observations.append(observe(params))
    healthy=False
    if all(o['returncode']==0 for o in observations):
        a,b=[o['data'] for o in observations]
        if all(v.get('exact_original_identity') and v['native_progress'] for v in (a,b)):
            pa,pb=a['native_progress'][-1],b['native_progress'][-1]
            healthy=(pb['epoch'],pb['step'])>(pa['epoch'],pa['step']) and not any(
                any(k in s for k in ('Traceback','AttributeError','RuntimeError','Early stopping')) for s in b['terminal_or_metric_lines'])
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),observations=observations,
        exact_native_progress_increasing=healthy,experiment='M207-HAP',gpu0_unavailable_for_native_candidates=bool(healthy),
        no_new_launch=True,no_source_or_scheduler_change=True)
    path=BASE/'hap_progress_observation.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),healthy=healthy,
        latest=observations[-1].get('data',{})),ensure_ascii=False))
if __name__=='__main__':main()
