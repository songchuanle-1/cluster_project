"""Archive only exact HRC natural early-stop; preserve the already live PSBR."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, re, subprocess, sys

R = Path('D:/project/cluster_project')
D = Path(__file__).resolve().parent
TOKEN = 'b96c202c871a4a1889d47e1fdc75e16e'
REMOTE_LOG = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc_20261022_223140.log'

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p): return {'path':Path(p).relative_to(R).as_posix(),'sha256':sha(p)}
def save(p,v):
    p=Path(p); tmp=p.with_name(p.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as f:
        json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def check_owner():
    o=read(R/'pipeline/headless/.foreground.lockdir/owner.json')
    assert o['token']==TOKEN and o['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o['deadline_at'])
    assert sha(R/'pipeline/headless/.tick_context.json')==o['context_sha256']
    assert sha(R/'pipeline/headless/.tick_context_state.next.json')==o['pending_sha256']

check_owner()
observation=read(D/'hrc_terminal_psbr_live_observation.json')
assert observation['token']==TOKEN and observation['HRC_natural_earlystop_confirmed'] and observation['PSBR_exact_native_progress_increasing']
assert sha(D/'hrc_terminal_psbr_live_observation.json')=='32b5b6ae795c531138789b597e28d8b5d1e2fcec6a68325112983c53cd9b8f73'
payload="""import socket,hashlib,json
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
assert not Path('/proc/2780804').exists()
p=Path(%r);raw=p.read_bytes()
assert b'Early stopping at epoch 31: no improvement for 10 epochs (best=0.4901)' in raw[-20000:]
assert b'Traceback (most recent call last)' not in raw
print(json.dumps({'hostname':socket.gethostname(),'original_pid_absent':True,'log':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}))
""" % REMOTE_LOG
command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -']
run=subprocess.run(command,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
assert run.returncode==0,run.stderr
proof=json.loads(run.stdout)
local=R/'Checkpoints/server_4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hrc/native_earlystop_b96c202c'/Path(REMOTE_LOG).name
local.parent.mkdir(parents=True,exist_ok=True)
assert not local.exists(), 'Never overwrite an existing pulled run log'
run=subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115:'+REMOTE_LOG,str(local)],capture_output=True,text=True,encoding='utf-8',timeout=60)
assert run.returncode==0,run.stderr
assert sha(local)==proof['sha256']
text=local.read_text(encoding='utf-8',errors='replace')
assert 'Early stopping at epoch 31: no improvement for 10 epochs (best=0.4901)' in text and 'Traceback (most recent call last)' not in text
progress=re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[',text)
assert tuple(map(int,progress[-1]))==(31,50,4686,4686)
proof.update(recorded_at=datetime.now(timezone.utc).isoformat(),local_log=str(local),local_remote_sha256_match=True,last_train_progress=[31,50,4686,4686],state='done_earlystop',best_miou_reported=0.4901,best_precision='native terminal line rounded4dp',signals_sent=False,source_changes=False)
save(D/'hrc_native_earlystop_log_evidence.json',proof)
check_owner()
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import pipeline_monitor as monitor
lock=monitor.acquire_lock(str(R));assert lock is not None
original_pull=monitor.pull_log
try:
    queue=monitor.load_queue(str(R))
    task=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M208-HRC')
    assert task['status']=='running' and task['pid']==2780804 and str(task['gpu'])=='0' and task['log']==REMOTE_LOG
    assert task['code_commit']=='74fcd21df0af9a971792038ffe251af1ffea2604' and task['launch_verified'] is True
    original_task=copy.deepcopy(task)
    protected_tasks=copy.deepcopy([t for t in queue['gpu_queues']['server-4'] if t['id'] in ['M206-CGCA','M209-PSBR']])
    running_before=monitor.load_running(str(R))
    assert running_before['server-4']['0']=='M209-PSBR'
    exp_before=copy.deepcopy(monitor.load_experiment(str(R),'M208-HRC'))
    def exact_pull(project,host,user,remote_log,cfg_name,state,srv_name=''):
        assert Path(project)==R and (host,user,state,srv_name)==('192.168.1.115','songcl','done_earlystop','server-4')
        assert remote_log==REMOTE_LOG and cfg_name==Path(task['config']).stem and sha(local)==proof['sha256']
        return str(local)
    monitor.pull_log=exact_pull
    events=[]
    monitor.finalize_task(str(R),queue,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,'done_earlystop',0.4901,'31/50','0',REMOTE_LOG,events)
    archived=monitor.load_experiment(str(R),'M208-HRC')
    assert archived['status']=='done_earlystop' and archived.get('prior_runs')==exp_before.get('prior_runs')
    assert archived['code_commit']==exp_before['code_commit']
    archived['training_status']='done_earlystop';monitor.save_experiment(str(R),archived)
    assert [t for t in queue['gpu_queues']['server-4'] if t['id'] in ['M206-CGCA','M209-PSBR']]==protected_tasks
    assert monitor.load_running(str(R))==running_before
    work=read(R/'pipeline/research_work.json')
    hrc=next(c for c in work['candidates'] if c.get('experiment_id')=='M208-HRC')
    hrc.update(stage='complete',training_status='done_earlystop',finished_at=archived['finished_at'],final_best_miou=0.4901,epochs_final='31/50',next_action='Preserve this exact native natural early-stop result: best0.4901 below M95.5020 by0.0119. No automatic restart/tuning or whole-hierarchy hypothesis rejection. PSBR has now independently launched on only GPU0.')
    for name in ['blocker','blocker_kind','blocked_at','retry_after','unblock_condition']:
        hrc.pop(name,None)
    psbr=next(c for c in work['candidates'] if c.get('experiment_id')=='M209-PSBR')
    assert psbr['code_commit']=='74fcd21df0af9a971792038ffe251af1ffea2604'
    psbr.update(stage='training',training_status='running',next_action='Monitor exact canonical PSBR PID2372658/start35234267/original YAML and log141002 on only GPU0. Real native steps1/50 207->215 verified; final efficacy UNKNOWN. Preserve original receipt and GPU1/M206 pause; no active source modification.')
    for c in [hrc,psbr]:
        for path in [D/'hrc_terminal_psbr_live_observation.json',D/'hrc_native_earlystop_log_evidence.json']:
            item=ref(path)
            if item not in c['evidence']:c['evidence'].append(item)
    work['updated_at']=datetime.now(timezone.utc).isoformat();save(R/'pipeline/research_work.json',work)
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_function':'pipeline_monitor.finalize_task','exact_log_adapter':True,'events':events,'original_queue_task':original_task,'archive':ref(R/'pipeline/experiments/M208-HRC.json'),'terminal_log_evidence':ref(D/'hrc_native_earlystop_log_evidence.json'),'prior_runs_preserved':True,'PSBR_and_M206_queue_unchanged':True,'running_mapping_unchanged':True,'running_after':running_before,'signals_sent':False,'deathwatch_incremented':False,'source_changes':False,'scientific_result':'This HRC realization best0.4901 < M95.5020 by0.0119 and target.5100 by0.0199; not a whole-mechanism falsification.'}
    save(D/'hrc_terminal_archive.json',result)
    print(json.dumps({'archived_status':archived['status'],'best':archived['final_best'],'epochs':archived['epochs_final'],'evidence':ref(D/'hrc_terminal_archive.json'),'PSBR_mapping_preserved':True},ensure_ascii=False))
finally:
    monitor.pull_log=original_pull
    lock.close()
