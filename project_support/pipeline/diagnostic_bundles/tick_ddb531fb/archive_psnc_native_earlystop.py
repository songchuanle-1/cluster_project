"""Archive only the exact naturally early-stopped original PSNC run."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOKEN = 'ddb531fb89824389b3b2e2df5779a5ef'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
REMOTE_LOG = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc_20261024_062442.log'


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path): return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': sha(path)}
def save(path, value):
    path = Path(path); tmp = path.with_name(path.name+'.'+TOKEN+'.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)


def main():
    owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == os.environ['CODEX_THREAD_ID'] == '01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    observation = read(HERE/'psnc_terminal_idle_observation.json')
    assert all(o['data']['original_pid_absent'] and not o['data']['errors'] and not o['data']['gpu0_contexts'] for o in observation['observations'])
    payload = """import socket,hashlib,json,os
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
assert not Path('/proc/2502712').exists()
p=Path(%r)
raw=p.read_bytes();t=raw[-20000:].decode(errors='replace')
assert 'Early stopping at epoch 31: no improvement for 10 epochs (best=0.5001)' in t
print(json.dumps({'hostname':socket.gethostname(),'pid_absent':True,'log':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'tail':t[-3000:]}))
""" % REMOTE_LOG
    command = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
               'songcl@192.168.1.115','/usr/bin/python3 -B -']
    remote = subprocess.run(command,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
    assert remote.returncode == 0, remote.stderr
    proof = json.loads(remote.stdout)
    local = ROOT/'Checkpoints/server_4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psnc/native_earlystop_ddb531fb'/Path(REMOTE_LOG).name
    local.parent.mkdir(parents=True, exist_ok=True)
    assert not local.exists(), 'Do not overwrite a prior pulled log'
    copied = subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
                             'songcl@192.168.1.115:'+REMOTE_LOG,str(local)],capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert copied.returncode == 0, copied.stderr
    assert sha(local) == proof['sha256']
    text = local.read_text(encoding='utf-8',errors='replace')
    assert 'Early stopping at epoch 31: no improvement for 10 epochs (best=0.5001)' in text
    assert 'Traceback (most recent call last)' not in text
    progress = re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[', text)
    assert tuple(map(int, progress[-1])) == (31,50,4686,4686)
    proof.update(recorded_at=datetime.now(timezone.utc).isoformat(),local_log=str(local),
                 local_remote_sha256_match=True,last_train_progress=[31,50,4686,4686],
                 state='done_earlystop',best_miou_reported=0.5001,best_precision='native terminal line rounded4dp',
                 signals_sent=False,torch_imported=False,historical_crash_root_cause='NOT_APPLICABLE_TO_THIS_RUN')
    save(HERE/'psnc_native_earlystop_log_evidence.json',proof)
    sys.path.insert(0,str(SKILL)); import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT)); assert lock is not None
    original_pull = monitor.pull_log
    try:
        queue = monitor.load_queue(str(ROOT))
        task = next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M210-PSNC')
        assert task['status']=='running' and task['pid']==2502712 and str(task['gpu'])=='0' and task['log']==REMOTE_LOG
        assert task['code_commit']=='43dce016c1a1713c2a5dab7061810dc2efde8954' and task['launch_verified'] is True
        before_task = copy.deepcopy(task)
        m206_before = copy.deepcopy([t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA'])
        prior_runs_before = copy.deepcopy(monitor.load_experiment(str(ROOT),'M210-PSNC').get('prior_runs'))
        def exact_pull(project, host, user, remote_log, cfg_name, state, srv_name=''):
            assert Path(project)==ROOT and (host,user,state,srv_name)==('192.168.1.115','songcl','done_earlystop','server-4')
            assert remote_log==REMOTE_LOG and cfg_name==Path(task['config']).stem and sha(local)==proof['sha256']
            return str(local)
        monitor.pull_log = exact_pull
        events=[]
        monitor.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,
                              'done_earlystop',0.5001,'31/50','0',REMOTE_LOG,events)
        archived = monitor.load_experiment(str(ROOT),'M210-PSNC')
        assert archived['status']=='done_earlystop' and archived.get('prior_runs')==prior_runs_before
        # The canonical finalizer preserves extra fields; reconcile this auxiliary status.
        archived['training_status']='done_earlystop'
        monitor.save_experiment(str(ROOT),archived)
        assert [t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA']==m206_before
        work_path=ROOT/'pipeline/research_work.json'; work=read(work_path)
        psnc=next(c for c in work['candidates'] if c.get('experiment_id')=='M210-PSNC')
        psnc.update(stage='complete',training_status='done_earlystop',finished_at=archived['finished_at'],
                   final_best_miou=0.5001,epochs_final='31/50',
                   next_action='Preserve exact original native early-stop archive and admission/source history. This realization best0.5001 did not exceed M95 .5020; no automatic restart, tuning, or whole-hierarchy hypothesis rejection. Proceed with already prepared independent BTC using only actually idle authorizedGPU0.')
        for name in ('blocker','blocker_kind','blocked_at','retry_after','unblock_condition'):
            psnc.pop(name,None)
        for path in (HERE/'psnc_terminal_idle_observation.json',HERE/'psnc_native_earlystop_log_evidence.json'):
            item=ref(path)
            if item not in psnc['evidence']:psnc['evidence'].append(item)
        btc=next(c for c in work['candidates'] if c.get('experiment_id')=='M211-BTC')
        assert btc['stage']=='blocked' and btc['resume_stage']=='validation' and btc['code_commit']=='00e2b18c6b8d568a64edb496e6979d766440883c' and btc['native_execution_code_commit'] is None
        btc['stage']='validation'
        btc['previous_resource_block']={k:btc.get(k) for k in ['blocker_kind','blocker','blocked_at','retry_after','unblock_condition']}
        for name in ('blocker_kind','blocker','blocked_at','retry_after','unblock_condition'):
            btc.pop(name,None)
        btc['next_action']='PSNC exact original run naturally stopped31/best.5001 and is now canonically archived. Reuse existing reviewed BTC43 operational adapter/static release with fresh actual owner/deadline/UUID/GPU0 idle/three-lock/runtime/assets guards for real original-YAML M95/candidate TRAIN2 and resource pair now. No GPU1/M206 or old binding replay. Native remains NOT_RUN until actual results.'
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        save(work_path,work)
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_function':'pipeline_monitor.finalize_task',
                'exact_log_adapter':True,'events':events,'original_queue_task':before_task,
                'archived_experiment':archived,'prior_run_and_admission_history_preserved':True,
                'm206_queue_unchanged':True,'running_after':monitor.load_running(str(ROOT)),
                'signals_sent':False,'deathwatch_incremented':False,'source_changes':False,
                'terminal_log_evidence':ref(HERE/'psnc_native_earlystop_log_evidence.json'),
                'scientific_result':'This PSNC realization best0.5001 < M95.5020 by0.0019 and target.5100 by0.0099; not a whole-mechanism falsification.'}
        save(HERE/'psnc_terminal_archive.json',result)
        print(json.dumps({'archived_status':archived['status'],'best':archived['final_best'],'epochs':archived['epochs_final'],
                          'evidence':ref(HERE/'psnc_terminal_archive.json'),'running':result['running_after']},ensure_ascii=False))
    finally:
        monitor.pull_log=original_pull
        lock.close()


if __name__=='__main__':main()
