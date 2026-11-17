"""Read only the original HRC terminal log and the exact canonical PSBR launch."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess, time

R = Path('D:/project/cluster_project')
D = Path(__file__).resolve().parent
TOKEN = 'b96c202c871a4a1889d47e1fdc75e16e'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def check_owner():
    o = read(R/'pipeline/headless/.foreground.lockdir/owner.json')
    assert o['token'] == TOKEN
    assert o['thread_id'] == os.environ['CODEX_THREAD_ID'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(o['deadline_at'])
    for file, key in [('.tick_context.json', 'context_sha256'), ('.tick_context_state.next.json', 'pending_sha256')]:
        assert hashlib.sha256((R/'pipeline/headless'/file).read_bytes()).hexdigest() == o[key]

check_owner()
q = read(R/'pipeline/queue.json')['gpu_queues']['server-4']
h, p = [next(t for t in q if t['id'] == key) for key in ['M208-HRC', 'M209-PSBR']]
assert h['pid'] == 2780804 and p['pid'] == 2372658
assert p['status'] == 'running' and p['launch_verified'] is True and str(p['gpu']) == '0'
assert p['code_commit'] == h['code_commit'] == '74fcd21df0af9a971792038ffe251af1ffea2604'
params = {key: {k: task[k] for k in ['pid', 'config', 'log']} for key, task in [('hrc', h), ('psbr', p)]}
payload = 'PARAMS=' + repr(params) + '\n' + r'''
import socket,json,os,re,subprocess,time
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
root='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
assert subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip()=='74fcd21df0af9a971792038ffe251af1ffea2604'
def tail(key):
 t=PARAMS[key]; path=Path(t['log'])
 with path.open('rb') as f:
  f.seek(max(0,path.stat().st_size-600000)); s=f.read().decode(errors='replace')
 rows=list(re.finditer(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',s))
 lines=s.replace('\r','\n').splitlines()
 return {'progress':None if not rows else [int(rows[-1][i]) for i in (1,2,3,4)],'terminal':[l for l in lines if 'Early stopping' in l],
  'errors':[l for l in lines if any(k in l for k in ['Traceback','RuntimeError','AttributeError'])],
  'log_bytes':path.stat().st_size,'log_age_seconds':time.time()-path.stat().st_mtime}
hp=Path('/proc')/str(PARAMS['hrc']['pid']); assert not hp.exists(), 'HRC process requires identity reconciliation'
h=tail('hrc'); assert h['terminal']==['Early stopping at epoch 31: no improvement for 10 epochs (best=0.4901)'] and not h['errors']
pp=Path('/proc')/str(PARAMS['psbr']['pid']); st=(pp/'stat').read_text().rsplit(')',1)[1].split()
args=[v.decode() for v in (pp/'cmdline').read_bytes().split(b'\0') if v]
assert args==['python','tools/train.py',PARAMS['psbr']['config'],'--gpu_ids','0','--num_gpus','1'] and os.readlink(pp/'cwd')==root
p=tail('psbr'); assert p['progress'] and not p['errors'] and not p['terminal']
gpu=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
assert any(l.split(',')[0].strip()==str(PARAMS['psbr']['pid']) for l in contexts.splitlines())
print(json.dumps({'HRC':{'original_pid_absent':True,**h},'PSBR':{'pid':PARAMS['psbr']['pid'],'starttime':st[19],'state':st[0],'argv':args,'cwd':root,**p},'runtime_HEAD':'74fcd21df0af9a971792038ffe251af1ffea2604','gpu0':gpu,'gpu0_contexts':contexts,'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS','read_only':True,'signals_sent':False}))
'''
observations = []
for i in range(2):
    if i:
        time.sleep(3)
    check_owner()
    run = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'], input=payload, capture_output=True, text=True, encoding='utf-8', timeout=40)
    assert run.returncode == 0, run.stderr
    observations.append({'observed_at':datetime.now(timezone.utc).isoformat(),'data':json.loads(run.stdout)})
a,b = [o['data']['PSBR'] for o in observations]
assert a['starttime']==b['starttime'] and a['argv']==b['argv']
assert (b['progress'][0],b['progress'][2]) > (a['progress'][0],a['progress'][2])
result = {'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'observations':observations,'PSBR_exact_native_progress_increasing':True,'HRC_natural_earlystop_confirmed':True,'new_launch_by_this_observer':False,'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS'}
path = D/'hrc_terminal_psbr_live_observation.json'
with path.open('x',encoding='utf-8') as stream:
    json.dump(result,stream,ensure_ascii=False,indent=2); stream.write('\n')
print(json.dumps({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'PSBR_native_progress':[a['progress'],b['progress']],'PSBR_starttime':b['starttime'],'HRC':'natural_earlystop_epoch31_best0.4901_no_improve10'},ensure_ascii=False))
