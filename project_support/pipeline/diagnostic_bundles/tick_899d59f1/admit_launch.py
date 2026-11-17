"""Guarded existing safe synchronization, admission queue and native dispatch."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import control as c

os.environ['PROJECT_ROOT'] = 'D:/project'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
os.environ['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10'
sys.path.insert(0, str(c.SKILL))
import pipeline_monitor as pm
import closure

R = c.ROOT
CODE = R/'Cluster'
SERVER = 'server-4'
EID = 'M205-MDC'
CONFIG = 'configs/Quard/ctf_hcg_csort_mdc/'+c.NAME+'_mdc.yaml'
RECEIPT = 'pipeline/admissions/M205-MDC.json'


def task():
    c.guard()
    version = c.tick.load(c.OUT/'version_native.json')
    assert closure.git(CODE, 'rev-parse', 'HEAD') == version['code_commit']
    t = dict(id=EID, label='M205-MDC middle directional convolution', config=CONFIG,
        status='waiting', code_commit=version['code_commit'], admission_receipt=RECEIPT,
        candidate_id=c.CID, requires_exclusive_ownership=True)
    receipt = closure.admission(R, t)
    assert receipt['profile'] == 'experiment_first' and receipt['candidate_id'] == c.CID
    return t


def checked_ssh(host, user, command, timeout=120):
    _, cfg = c.guard()
    assert (host, user) == (cfg['host'], cfg['user'])
    result = subprocess.run(['ssh', *c.SSH, user+'@'+host, command], capture_output=True,
        text=True, encoding='utf-8', errors='replace', timeout=timeout, check=True)
    return result.stdout.strip()


def server():
    c.guard()
    srv = pm.load_servers(str(R))[SERVER]
    assert checked_ssh(srv['host'], srv['user'], 'hostname') == 'dl04-MS-7E06'
    return srv


def sync():
    c.guard(300)
    t = task()
    srv = server()
    assert closure.safe_sync(R, CODE, srv, checked_ssh)
    c.save('sync.json', dict(code_commit=t['code_commit'], server=SERVER,
        observed_at=c.now(), safe_sync_passed=True))


def enqueue():
    c.guard(120)
    t = task()
    synced = c.tick.load(c.OUT/'sync.json')
    assert synced['safe_sync_passed'] is True and synced['code_commit'] == t['code_commit']
    lock = pm.acquire_lock(str(R))
    if lock is None:
        raise RuntimeError('SKIPPED_BUSY: queue lock held')
    try:
        c.guard()
        q = pm.load_queue(str(R))
        found = [(s, x) for s, rows in q['gpu_queues'].items() for x in rows if x.get('id') == EID]
        if found:
            assert len(found) == 1
            s, x = found[0]
            assert s == SERVER and all(x.get(k) == t[k] for k in ('config','code_commit','admission_receipt'))
            print(json.dumps({'already_queued': True, 'task': x}))
            return
        assert pm.load_experiment(str(R), EID) is None, 'Existing registry: reconcile, no duplicate'
        proposed = copy.deepcopy(q)
        proposed['gpu_queues'].setdefault(SERVER, []).append(t)
        closure.validate_foreground_dispatch_budget(R, proposed, t)
        c.guard()
        pm.save_queue(str(R), proposed)
    finally:
        lock.close()
    c.save('enqueue.json', dict(observed_at=c.now(), server=SERVER, task=t,
        queue_path='pipeline/queue.json', queue_sha256=c.tick.digest(R/'pipeline/queue.json')))


def monitor():
    c.guard(300)
    task()
    server()
    rc = pm.main(['cluster_project', '--server', SERVER])
    c.save('monitor.json', dict(observed_at=c.now(), returncode=rc))
    assert rc == 0, 'Monitor busy/failed: reconcile, no blind relaunch'


def observe():
    c.guard(120)
    task()
    server()
    rc = pm.main(['cluster_project', '--server', SERVER, '--read-only'])
    q = pm.load_queue(str(R))
    rows = [x for values in q['gpu_queues'].values() for x in values if x.get('id') == EID]
    assert len(rows) == 1
    stamp = c.datetime.now(c.timezone.utc).strftime('%H%M%S%f')
    c.save('observe_'+stamp+'.json', dict(observed_at=c.now(), returncode=rc, task=rows[0],
        native_launch_verified=rows[0].get('launch_verified') is True))
    assert rc == 0




def move():
    c.guard(300)
    t=task()
    synced=c.tick.load(c.OUT/'sync.json')
    assert synced['safe_sync_passed'] and synced['code_commit']==t['code_commit']
    lock=pm.acquire_lock(str(R))
    if lock is None:raise RuntimeError('SKIPPED_BUSY')
    try:
        q=pm.load_queue(str(R))
        found=[(s,i,x) for s,rows in q['gpu_queues'].items() for i,x in enumerate(rows) if x.get('id')==EID]
        assert len(found)==1
        source,index,entry=found[0]
        assert source=='server-3' and entry['status']=='waiting'
        assert not any(entry.get(k) for k in ('pid','launch_phase','launch_state','launch_log','claim_token','launch_hold'))
        assert pm.load_experiment(str(R),EID) is None
        assert all(entry[k]==t[k] for k in ('config','code_commit','admission_receipt'))
        before=copy.deepcopy(q)
        del q['gpu_queues'][source][index]
        q['gpu_queues'].setdefault(SERVER,[]).append(entry)
        c.guard()
        pm.save_queue(str(R),q)
    finally:lock.close()
    c.save('queue_placement.json',dict(observed_at=c.now(),experiment_id=EID,
        old_server=source,new_server=SERVER,waiting_only=True,no_source_process_or_claim=True,
        old_queue_sha256=__import__('hashlib').sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        queue_sha256=c.tick.digest(R/'pipeline/queue.json')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['sync','move','monitor','observe'])
    globals()[parser.parse_args().operation]()
