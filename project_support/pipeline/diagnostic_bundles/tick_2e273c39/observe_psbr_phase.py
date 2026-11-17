"""Additional exact PSBR native-progress observation after canonical dispatch."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import subprocess
import time

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]

def main():
    task=next(t for t in json.loads((ROOT/'pipeline/queue.json').read_text(encoding='utf-8'))['gpu_queues']['server-4'] if t['id']=='M209-PSBR')
    assert task['status']=='running' and task['launch_verified'] is True and task['pid']==2372658 and str(task['gpu'])=='0'
    params={k:task[k] for k in ('pid','config','log')}
    payload='PARAMS='+repr(params)+'\n'+r'''
import socket,json,os,re,time,subprocess
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
p=Path('/proc')/str(PARAMS['pid']);s=(p/'stat').read_text().rsplit(')',1)[1].split()
assert s[19]=='35234267', 'original PSBR starttime changed'
args=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
expected=['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1']
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
cwd=os.readlink(p/'cwd');assert args==expected and cwd==root
path=Path(PARAMS['log'])
with path.open('rb') as f:f.seek(max(0,path.stat().st_size-600000));text=f.read().decode(errors='replace')
matches=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
assert matches
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()
assert head=='74fcd21df0af9a971792038ffe251af1ffea2604'
lines=text.replace('\r','\n').splitlines()
errors=[line for line in lines if any(k in line for k in ['Traceback','AttributeError','RuntimeError','Early stopping'])]
print(json.dumps({'pid':PARAMS['pid'],'starttime':s[19],'state':s[0],'argv':args,'cwd':cwd,'runtime_HEAD':head,
 'progress':[int(matches[-1][i]) for i in (1,2,3,4)],'log':str(path),'log_bytes':path.stat().st_size,
 'log_age_seconds':time.time()-path.stat().st_mtime,'gpu0':row,'gpu0_contexts':contexts,'errors':errors,
 'last_nonempty_lines':[line[-400:] for line in lines if line.strip()][-6:], 'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS','read_only':True,'signals_sent':False}))
'''
    command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
    observations=[]
    for i in range(2):
        if i:time.sleep(3)
        run=subprocess.run(command,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
        assert run.returncode==0,run.stderr
        observations.append({'observed_at':datetime.now(timezone.utc).isoformat(),'returncode':run.returncode,'data':json.loads(run.stdout)})
    a,b=[o['data'] for o in observations]
    assert a['starttime']==b['starttime'] and a['argv']==b['argv'] and not a['errors'] and not b['errors']
    progress_increasing=(b['progress'][0],b['progress'][2])>(a['progress'][0],a['progress'][2])
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment':'M209-PSBR','observations':observations,
            'exact_original_process_and_native_progress_increasing':progress_increasing,'formal_training_not_smoke':True,
            'no_new_launch_or_source_modification':True,'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS'}
    path=HERE/'psbr_phase_observation.json'
    with path.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'native_progress':[a['progress'],b['progress']],'pid':task['pid'],'starttime':b['starttime'],'runtime_HEAD':b['runtime_HEAD']},ensure_ascii=False))

if __name__=='__main__':main()
