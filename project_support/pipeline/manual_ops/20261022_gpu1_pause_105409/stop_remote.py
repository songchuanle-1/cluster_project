import socket
assert socket.gethostname() == 'dl04-MS-7E06'
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1'
TARGET, PROTECTED = PARAMS['target'], PARAMS['protected']
assert TARGET['pid'] == 732137 and TARGET['starttime'] == '21298582'
assert PROTECTED['pid'] == 979955 and PROTECTED['starttime'] == '21613920'


def proc(pid):
    p = Path('/proc') / str(pid)
    tail = (p / 'stat').read_text().rsplit(')', 1)[1].split()
    return dict(pid=pid, state=tail[0], ppid=int(tail[1]), pgid=int(tail[2]), sid=int(tail[3]),
        starttime=tail[19], cwd=os.readlink(p / 'cwd'), uid=p.stat().st_uid,
        args=[x.decode() for x in (p / 'cmdline').read_bytes().split(b'\0') if x])


def same(row, original):
    return all(row[k] == original[k] for k in ('pid', 'starttime', 'cwd', 'uid', 'pgid', 'sid', 'args'))


assert same(proc(TARGET['pid']), TARGET) and same(proc(PROTECTED['pid']), PROTECTED)
assert TARGET['uid'] == PROTECTED['uid'] == os.getuid() and TARGET['cwd'] == PROTECTED['cwd'] == ROOT
assert TARGET['pgid'] == TARGET['sid'] == TARGET['pid'] and PROTECTED['pgid'] != TARGET['pgid']
snapshot = Path(PARAMS['snapshot'])
h = hashlib.sha256()
with snapshot.open('rb') as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
        h.update(block)
assert h.hexdigest() == PARAMS['checkpoint_sha256']
inventory = subprocess.check_output(['nvidia-smi', '-i', '1', '--query-gpu=index,uuid', '--format=csv,noheader,nounits'], text=True).strip()
assert inventory == '1, GPU-7f82edb9-f620-8045-caea-a75232265cd1'
members = []
for path in Path('/proc').glob('[0-9]*'):
    try:
        row = proc(int(path.name))
        if row['pgid'] == TARGET['pgid'] and row['state'] not in ('Z', 'X'):
            members.append(row)
    except (OSError, ValueError):
        pass
assert any(row['pid'] == TARGET['pid'] for row in members)
assert all(row['sid'] == TARGET['sid'] and row['uid'] == os.getuid() and row['cwd'] == ROOT for row in members)
assert PROTECTED['pid'] not in {row['pid'] for row in members}
members.sort(key=lambda row: (row['pid'] != TARGET['pid'], row['pid']))
handles = []
try:
    for row in members:
        fd = os.pidfd_open(row['pid'])
        handles.append((row, fd))
        assert same(proc(row['pid']), row), 'Process changed before signal; no signal sent'
    assert same(proc(PROTECTED['pid']), PROTECTED)
    journal_dir = Path('/data/songcl/Project/Cluster_project/pipeline/manual_ops') / PARAMS['operation_id']
    assert journal_dir.resolve().is_relative_to(Path('/data/songcl/Project/Cluster_project/pipeline/manual_ops').resolve())
    journal_dir.mkdir(parents=True, exist_ok=False)
    request = dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), action='exact_pidfd_SIGTERM',
        target=TARGET, protected=PROTECTED, members=members, checkpoint=PARAMS['snapshot'],
        checkpoint_sha256=PARAMS['checkpoint_sha256'])
    with (journal_dir / 'stop_request.json').open('x') as stream:
        json.dump(request, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    for row, fd in handles:
        try:
            assert same(proc(row['pid']), row), 'Original member identity changed'
            signal.pidfd_send_signal(fd, signal.SIGTERM)
        except (FileNotFoundError, ProcessLookupError):
            pass

    def alive_original(row):
        try:
            current = proc(row['pid'])
            return current['starttime'] == row['starttime'] and current['state'] not in ('Z', 'X')
        except (FileNotFoundError, ProcessLookupError):
            return False

    until = time.monotonic() + 12
    while any(alive_original(row) for row in members) and time.monotonic() < until:
        time.sleep(.2)
    killed = []
    for row, fd in handles:
        if alive_original(row):
            assert same(proc(row['pid']), row), 'Do not signal a reused or changed process'
            signal.pidfd_send_signal(fd, signal.SIGKILL)
            killed.append(row['pid'])
    until = time.monotonic() + 8
    while any(alive_original(row) for row in members) and time.monotonic() < until:
        time.sleep(.2)
    assert not any(alive_original(row) for row in members), 'Exact stop unconfirmed; retain hold'

    def contexts():
        return subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()

    # CUDA teardown can outlive process exit; reconcile it without another signal.
    until = time.monotonic() + 20
    after = contexts()
    while any(line.split(',')[1].strip() == str(TARGET['pid']) for line in after.splitlines()) and time.monotonic() < until:
        time.sleep(.5)
        after = contexts()
    assert not any(line.split(',')[1].strip() == str(TARGET['pid']) for line in after.splitlines()), 'GPU context teardown not yet confirmed'
    safe = proc(PROTECTED['pid'])
    assert same(safe, PROTECTED) and safe['state'] not in ('Z', 'X')
    assert any(line.startswith('GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c') and line.split(',')[1].strip() == str(PROTECTED['pid']) for line in after.splitlines())
    result = dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(), stop_confirmed=True,
        exact_members=members, pidfd_SIGTERM_pids=[row['pid'] for row in members], SIGKILL_pids=killed,
        original_processes_not_alive=True, target_GPU_context_absent=True,
        gpu1_empty_at_check=not any(line.startswith('GPU-7f82edb9-f620-8045-caea-a75232265cd1') for line in after.splitlines()),
        contexts_after=after, protected_pid=PROTECTED['pid'], protected_identity_unchanged=True,
        gpus_after=subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True).strip(),
        no_resume_or_new_training=True, remote_journal=str(journal_dir))
    with (journal_dir / 'stop_result.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))
finally:
    for row, fd in handles:
        os.close(fd)
