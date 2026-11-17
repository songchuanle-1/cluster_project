import socket
assert socket.gethostname() == 'dl04-MS-7E06'
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ROOT = Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
BASE = Path('/data/songcl/Project/Cluster_project/pipeline')
OUT = BASE / 'manual_ops' / PARAMS['operation_id']
OUT.mkdir(parents=True, exist_ok=False)
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()
def save(name, value):
    with (OUT/name).open('x') as f:
        json.dump(value, f, indent=2); f.flush(); os.fsync(f.fileno())
def proc(pid):
    p = Path('/proc')/str(pid)
    s = (p/'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, state=s[0], ppid=int(s[1]), pgid=int(s[2]), sid=int(s[3]),
        starttime=s[19], uid=p.stat().st_uid, cwd=os.readlink(p/'cwd'),
        args=[a.decode() for a in (p/'cmdline').read_bytes().split(b'\0') if a])
def same(a,b): return all(a[k]==b[k] for k in ('pid','starttime','uid','cwd','args','pgid','sid'))
def alive(row):
    try:
        q=proc(row['pid'])
        return q['starttime']==row['starttime'] and q['state'] not in ('Z','X')
    except (FileNotFoundError,ProcessLookupError): return False
def nv():
    return subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
for line in inventory.splitlines():
    ix,uid,*_=map(str.strip,line.split(',')); assert uid==PARAMS['uuids'][ix]
assert hasattr(os,'pidfd_open') and hasattr(signal,'pidfd_send_signal')
head=subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
assert head==PARAMS['head']
targets=[]; members=[]; evidence=[]
contexts=nv()
for t in PARAMS['targets']:
    row=proc(t['pid'])
    assert row['starttime']==str(t['starttime']) and row['uid']==os.getuid() and row['cwd']==str(ROOT)
    assert row['pgid']==row['sid']==row['pid'] and row['state'] not in ('Z','X')
    assert row['args']==['python','tools/train.py',t['config'],'--gpu_ids',str(t['gpu']),'--num_gpus','1']
    assert os.readlink(Path('/proc')/str(t['pid'])/'fd/1')==t['log']
    assert any(line.split(',')[0].strip()==t['uuid'] and line.split(',')[1].strip()==str(t['pid']) for line in contexts.splitlines())
    for name,want in t['hashes'].items():
        assert digest(ROOT/name)==(PARAMS['yaml_sha'] if name.endswith('.yaml') else want),name
    targets.append(row)
    logfile=Path(t['log']); text=logfile.read_text(errors='replace')
    saved=re.findall(r'save last pth to ([^\r\n]+)',text)
    checkpoints=[]
    if saved:
        last=Path(saved[-1].strip()).resolve()
        expected=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/Path(t['config']).stem
        assert last.is_relative_to(expected.resolve()) and last.name=='last.pth'
        for source in (last,last.with_name('best.pth')):
            if source.is_file():
                st=source.stat(); checkpoints.append(dict(path=str(source),bytes=st.st_size,mtime_ns=st.st_mtime_ns))
    evidence.append(dict(id=t['id'], original=row,log=t['log'],log_bytes=logfile.stat().st_size,
        checkpoint_files_before=checkpoints,latest_train=re.findall(r'Train\[(\d+)/(\d+)\]:[^\r\n]*?\|\s*(\d+)/(\d+)',text)[-1:],
        partial_current_epoch_saved=False))
for p in Path('/proc').glob('[0-9]*'):
    try:
        row=proc(int(p.name))
        if row['pgid'] in {r['pgid'] for r in targets} and row['state'] not in ('Z','X'):
            assert row['sid']==row['pgid'] and row['uid']==os.getuid() and row['cwd']==str(ROOT)
            members.append(row)
    except (FileNotFoundError,ProcessLookupError,PermissionError): pass
assert {t['pid'] for t in targets}.issubset({r['pid'] for r in members})
members.sort(key=lambda r:(r['pid'] not in {t['pid'] for t in targets},r['pid']))
handles=[]
try:
    for row in members:
        fd=os.pidfd_open(row['pid']); handles.append((row,fd)); assert same(proc(row['pid']),row)
    save('stop_intent.json',dict(recorded_at=now(),human_request=PARAMS['request'],targets=evidence,members=members,
        inventory_before=inventory,contexts_before=contexts,head=head,action='exact_pidfd_SIGTERM_only'))
    for row,fd in handles:
        try:
            assert same(proc(row['pid']),row)
            signal.pidfd_send_signal(fd,signal.SIGTERM)
        except (FileNotFoundError,ProcessLookupError): pass
    deadline=time.monotonic()+15
    while any(alive(row) for row in members) and time.monotonic()<deadline: time.sleep(.2)
    killed=[]
    for row,fd in handles:
        if alive(row):
            assert same(proc(row['pid']),row)
            signal.pidfd_send_signal(fd,signal.SIGKILL); killed.append(row['pid'])
    deadline=time.monotonic()+8
    while any(alive(row) for row in members) and time.monotonic()<deadline: time.sleep(.2)
    assert not any(alive(row) for row in members),'Stop unconfirmed; hold remains'
    deadline=time.monotonic()+20
    after=nv(); member_ids={r['pid'] for r in members}
    while any(int(x.split(',')[1]) in member_ids for x in after.splitlines()) and time.monotonic()<deadline:
        time.sleep(.5); after=nv()
    assert not any(int(x.split(',')[1]) in member_ids for x in after.splitlines())
    result=dict(observed_at=now(),hostname=socket.gethostname(),stop_confirmed=True,targets=evidence,
        exact_members=members,SIGTERM_pids=[r['pid'] for r in members],SIGKILL_pids=killed,
        original_processes_absent=True,all_original_member_cuda_contexts_absent=True,contexts_after=after,
        gpus_after=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip(),
        no_new_training_or_resume=True,remote_journal=str(OUT))
    save('stop_result.json',result)
    print(json.dumps(result),flush=True)
finally:
    for row,fd in handles: os.close(fd)
