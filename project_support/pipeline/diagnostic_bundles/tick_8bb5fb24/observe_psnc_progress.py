"""Read-only exact registered PSNC process and short native progress observation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,time

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
TOKEN='8bb5fb2403ab4c028ab917f23bb08cf4'

def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text())
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    queue=json.loads((ROOT/'pipeline/queue.json').read_text())
    task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M210-PSNC')
    assert task['status']=='running' and task['launch_verified'] is True and task['pid']==2502712 and str(task['gpu'])=='0'
    params={k:task[k] for k in ('pid','config','log')}
    payload='PARAMS='+repr(params)+'\n'+r'''
import socket,json,os,re,time,subprocess
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
p=Path('/proc')/str(PARAMS['pid']); s=(p/'stat').read_text().rsplit(')',1)[1].split()
args=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
expected=['python','tools/train.py',PARAMS['config'],'--gpu_ids','0','--num_gpus','1']
assert args==expected and os.readlink(p/'cwd')==root
assert os.readlink(p/'fd/1')==PARAMS['log']
path=Path(PARAMS['log'])
with path.open('rb') as f: f.seek(max(0,path.stat().st_size-600000)); text=f.read().decode(errors='replace')
trains=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text))
assert trains
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert row.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert any(line.split(',')[0].strip()==str(PARAMS['pid']) for line in contexts.splitlines())
head=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()
assert head=='43dce016c1a1713c2a5dab7061810dc2efde8954'
lines=text.replace('\r','\n').splitlines()
errors=[line for line in lines if any(k in line for k in ['Traceback','AttributeError','RuntimeError','Early stopping'])]
print(json.dumps({'pid':PARAMS['pid'],'start_ticks':s[19],'state':s[0],'argv':args,'cwd':root,'runtime_HEAD':head,
 'train_progress':[int(trains[-1][i]) for i in (1,2,3,4)],'log':str(path),'log_bytes':path.stat().st_size,
 'log_age_seconds':time.time()-path.stat().st_mtime,'gpu0':row,'gpu0_contexts':contexts,'errors':errors,
 'last_nonempty_lines':[line[-400:] for line in lines if line.strip()][-6:],
 'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS','read_only':True,'signals_sent':False}))
'''
    cmd=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
    observations=[]
    for i in range(2):
        if i:time.sleep(3)
        run=subprocess.run(cmd,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
        if run.returncode:
            fail={'returncode':run.returncode,'stderr':run.stderr,'observations':observations,'signals_sent':False,'launch_retried':False}
            (HERE/'psnc_observation_failure.json').write_text(json.dumps(fail,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            raise RuntimeError('Exact readonly observation failed; no process change or restart performed')
        observations.append({'observed_at':datetime.now(timezone.utc).isoformat(),'data':json.loads(run.stdout)})
    a,b=[o['data'] for o in observations]
    assert a['start_ticks']==b['start_ticks']=='41082267' and a['argv']==b['argv'] and not a['errors'] and not b['errors']
    increasing=(b['train_progress'][0],b['train_progress'][2])>(a['train_progress'][0],a['train_progress'][2])
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'experiment':'M210-PSNC','observations':observations,
            'same_exact_registered_process_and_native_TRAIN_growth':increasing,'start_identity_scope':'Exact original /proc start_ticks41082267 was first captured in previous7dcc observation and is unchanged across these two observations; original dispatch did not record it.',
            'no_launch_source_change_or_signal':True,'GPU1':'NOT_QUERIED_NOT_USED'}
    path=HERE/'psnc_progress_observation.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'progress':[a['train_progress'],b['train_progress']],
                      'growth':increasing,'pid':task['pid'],'start_ticks':b['start_ticks'],'runtime_HEAD':b['runtime_HEAD']},ensure_ascii=False))

if __name__=='__main__':main()
