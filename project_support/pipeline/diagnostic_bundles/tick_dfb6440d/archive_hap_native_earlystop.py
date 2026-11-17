"""Archive only the exact naturally early-stopped resumed HAP run."""
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
TOKEN = 'dfb6440d1b69401da8e932239883e613'
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
REMOTE_LOG = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap_20261022_152545.log'


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
    observation = read(HERE/'hap_progress_observation.json')
    assert all(o['returncode'] == 0 and not o['data']['process_exists'] for o in observation['observations'])
    payload = """import socket,hashlib,json,os
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
assert not Path('/proc/1063355').exists()
p=Path(%r)
raw=p.read_bytes();t=raw[-20000:].decode(errors='replace')
assert 'Early stopping at epoch 31: no improvement for 10 epochs (best=0.5002)' in t
print(json.dumps({'hostname':socket.gethostname(),'pid_absent':True,'log':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'tail':t[-3000:]}))
""" % REMOTE_LOG
    command = ['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
               'songcl@192.168.1.115','/usr/bin/python3 -B -']
    remote = subprocess.run(command,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=40)
    assert remote.returncode == 0, remote.stderr
    proof = json.loads(remote.stdout)
    local = ROOT/'Checkpoints/server_4/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hap/20261022_152554'/Path(REMOTE_LOG).name
    local.parent.mkdir(parents=True, exist_ok=True)
    assert not local.exists(), 'Do not overwrite a prior pulled log'
    copied = subprocess.run(['scp','-q','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
                             'songcl@192.168.1.115:'+REMOTE_LOG,str(local)],capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert copied.returncode == 0, copied.stderr
    assert sha(local) == proof['sha256']
    text = local.read_text(encoding='utf-8',errors='replace')
    assert 'Early stopping at epoch 31: no improvement for 10 epochs (best=0.5002)' in text
    assert 'Traceback (most recent call last)' not in text
    progress = re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?(\d+)/(\d+)\s*\[', text)
    assert tuple(map(int, progress[-1])) == (31,50,4686,4686)
    proof.update(recorded_at=datetime.now(timezone.utc).isoformat(),local_log=str(local),
                 local_remote_sha256_match=True,last_train_progress=[31,50,4686,4686],
                 state='done_earlystop',best_miou_reported=0.5002,best_precision='native terminal line rounded4dp',
                 signals_sent=False,torch_imported=False,underlying_previous_crash_root_cause='UNKNOWN')
    save(HERE/'hap_native_earlystop_log_evidence.json',proof)
    sys.path.insert(0,str(SKILL)); import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT)); assert lock is not None
    original_pull = monitor.pull_log
    try:
        queue = monitor.load_queue(str(ROOT))
        task = next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M207-HAP')
        assert task['status']=='running' and task['pid']==1063355 and str(task['gpu'])=='0' and task['log']==REMOTE_LOG
        assert task['code_commit']=='f51823bbddf0f8095a9a5813bf1f8169e3d7edb0' and task['launch_verified'] is True
        before_task = copy.deepcopy(task)
        m206_before = copy.deepcopy([t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA'])
        prior_runs_before = copy.deepcopy(monitor.load_experiment(str(ROOT),'M207-HAP').get('prior_runs'))
        def exact_pull(project, host, user, remote_log, cfg_name, state, srv_name=''):
            assert Path(project)==ROOT and (host,user,state,srv_name)==('192.168.1.115','songcl','done_earlystop','server-4')
            assert remote_log==REMOTE_LOG and cfg_name==Path(task['config']).stem and sha(local)==proof['sha256']
            return str(local)
        monitor.pull_log = exact_pull
        events=[]
        monitor.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,Path(task['config']).stem,
                              'done_earlystop',0.5002,'31/50','0',REMOTE_LOG,events)
        archived = monitor.load_experiment(str(ROOT),'M207-HAP')
        assert archived['status']=='done_earlystop' and archived.get('prior_runs')==prior_runs_before
        # The canonical finalizer preserves extra fields; reconcile this auxiliary status.
        archived['training_status']='done_earlystop'
        monitor.save_experiment(str(ROOT),archived)
        assert [t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA']==m206_before
        work_path=ROOT/'pipeline/research_work.json'; work=read(work_path)
        hap=next(c for c in work['candidates'] if c.get('experiment_id')=='M207-HAP')
        hap.update(stage='complete',training_status='done_earlystop',finished_at=archived['finished_at'],
                   final_best_miou=0.5002,epochs_final='31/50',
                   next_action='Preserve both original crash/prior_run and exact resumed native early-stop archive. This realization best0.5002 did not exceed M95 .5020; no automatic restart, tuning, or whole-hierarchy hypothesis rejection. Proceed with already prepared independent HRC then PSBR using only actually idle authorizedGPU0.')
        for name in ('blocker','blocker_kind','blocked_at','retry_after','unblock_condition'):
            hap.pop(name,None)
        for path in (HERE/'hap_progress_observation.json',HERE/'hap_native_earlystop_log_evidence.json'):
            item=ref(path)
            if item not in hap['evidence']:hap['evidence'].append(item)
        hrc=next(c for c in work['candidates'] if c.get('experiment_id')=='M208-HRC')
        assert hrc['stage']=='blocked' and hrc['resume_stage']=='validation' and hrc['code_commit']=='74fcd21df0af9a971792038ffe251af1ffea2604'
        hrc['stage']='validation'
        hrc['previous_resource_block']={k:hrc.get(k) for k in ['blocker_kind','blocker','blocked_at','retry_after','unblock_condition']}
        for name in ('blocker_kind','blocker','blocked_at','retry_after','unblock_condition'):
            hrc.pop(name,None)
        hrc['next_action']='HAP exact resumed run naturally stopped/archived. Execute already anchored HRC74f four real native/resource pair checks now only after fresh actual owner/deadline/UUID/GPU0 idle/three-lock/runtime/assets guards. Do not use GPU1 or resume M206. Native statuses remain NOT_RUN until actual results.'
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        save(work_path,work)
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_function':'pipeline_monitor.finalize_task',
                'exact_log_adapter':True,'events':events,'original_queue_task':before_task,
                'archived_experiment':archived,'prior_crash_and_run_history_preserved':True,
                'm206_queue_unchanged':True,'running_after':monitor.load_running(str(ROOT)),
                'signals_sent':False,'deathwatch_incremented':False,'source_changes':False,
                'terminal_log_evidence':ref(HERE/'hap_native_earlystop_log_evidence.json'),
                'scientific_result':'This HAP realization best0.5002 < M95.5020 by0.0018 and target.5100 by0.0098; not a whole-mechanism falsification.'}
        save(HERE/'hap_terminal_archive.json',result)
        print(json.dumps({'archived_status':archived['status'],'best':archived['final_best'],'epochs':archived['epochs_final'],
                          'evidence':ref(HERE/'hap_terminal_archive.json'),'running':result['running_after']},ensure_ascii=False))
    finally:
        monitor.pull_log=original_pull
        lock.close()


if __name__=='__main__':main()
