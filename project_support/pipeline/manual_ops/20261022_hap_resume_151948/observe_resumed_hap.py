"""Read-only identity, native resume metadata and increasing progress verification."""
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
import datetime as dt,os,json,re,subprocess
from pathlib import Path
p=Path('/proc')/str(PARAMS['pid'])
assert p.exists(),'Original resumed PID absent; reconcile, never relaunch'
s=(p/'stat').read_text().rsplit(')',1)[1].split()
args=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
expected=['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1','--resume',PARAMS['resume_from']]
assert args==expected,args
cwd=os.readlink(p/'cwd');assert cwd==PARAMS['remote_code_root']
path=Path(PARAMS['log']);assert path.is_file()
with path.open('rb') as f:f.seek(max(0,path.stat().st_size-120000));text=f.read().decode(errors='replace')
with path.open('rb') as f:head=f.read(2000000).decode(errors='replace')
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
progress=[dict(epoch=int(m[1]),epochs=int(m[2]),step=int(m[3]),steps=int(m[4])) for m in matches[-2:]]
resume_lines=[line for line in head.replace('\r','\n').splitlines() if 'resume start_epoch:' in line or 'Resume from ' in line]
assert not any(v in text for v in ['Traceback (most recent call last):','CUDA out of memory','AttributeError:'])
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps(dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),pid=PARAMS['pid'],starttime=s[19],state=s[0],
    argv=args,cwd=cwd,original_pid_identity=True,log=str(path),log_age_seconds=__import__('time').time()-path.stat().st_mtime,
    native_progress=progress,resume_lines=resume_lines,gpu0_contexts=contexts,
    GPU1='NOT_QUERIED_RELEASED_TO_OTHERS',read_only=True,signals_sent=False)))
'''
def observe(task):
    params={k:task[k] for k in ('pid','config','resume_from','log')}
    params['remote_code_root']='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
    payload='PARAMS='+repr(params)+'\n'+PAYLOAD
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
          'songcl@192.168.1.115','/usr/bin/python3 -B -']
    r=subprocess.run(args,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=35)
    out=dict(command=args,payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    if r.returncode==0:out['data']=json.loads(r.stdout)
    return out
def main():
    queue=json.loads((ROOT/'pipeline/queue.json').read_text(encoding='utf-8-sig'))
    task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M207-HAP')
    assert task['status']=='running' and task['launch_verified'] is True
    observations=[observe(task)];time.sleep(3);observations.append(observe(task))
    assert all(o['returncode']==0 for o in observations),observations
    a,b=[o['data'] for o in observations]
    assert a['starttime']==b['starttime']
    assert a['native_progress'] and b['native_progress']
    pa,pb=a['native_progress'][-1],b['native_progress'][-1]
    assert pa['epoch']==pb['epoch']==19 and pb['step']>pa['step']
    assert any('resume start_epoch:19,best_miou:0.4975287616252899,epochs_no_improve:0' in s for s in a['resume_lines']+b['resume_lines'])
    assert any(f", {task['pid']}," in s for s in b['gpu0_contexts'].splitlines())
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),observations=observations,
        native_resume_metadata_verified=True,exact_original_checkpoint_argv_verified=True,
        physical_gpu0_context_verified=True,progress_increased=True,from_step=pa,to_step=pb,
        m206_resume_authorized=False,GPU1='NOT_QUERIED_RELEASED_TO_OTHERS')
    path=BASE/'native_resume_progress.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pid=task['pid'],epoch=19,step_from=pa['step'],step_to=pb['step']),ensure_ascii=False))
if __name__=='__main__':main()
