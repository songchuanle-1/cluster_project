"""Root-only, exact one-file CTS log archival; default performs no action."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import json
import os
import shlex
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
OWNER = {
    'token': '94f8ddb8a6e049c48c8e6237f4c737e8',
    'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253',
    'generated_at': '2026-10-26T14:57:12.614254+00:00',
    'deadline_at': '2026-10-26T15:57:12.614254+00:00',
    'context_sha256': '0104947a1b56f553572b7cddc0fa2f5ab0edbee9ba33f161af61e6990c234793',
    'pending_sha256': '95a698a880ff7b5655a002531c1e3b5704e0f9c34ed4e1093f2c6ad72dba2331',
}
REMOTE_LOG = '/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts_20261026_140443.log'
HOSTNAME = 'dl04-MS-7E06'
DEST = HERE / REMOTE_LOG.rsplit('/', 1)[1]
INTENT = HERE / 'archive_intent.json'
EVIDENCE = HERE / 'archive_evidence.json'


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def guard():
    owner = json.loads((ROOT / 'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
    assert {k: owner.get(k) for k in OWNER} == OWNER, 'Current actual owner mismatch'
    assert os.environ.get('CODEX_THREAD_ID') == OWNER['thread_id'], 'Actual root thread required; never override environment'
    mode = json.loads((ROOT / 'pipeline/execution_mode.json').read_text('utf8'))
    assert mode['target_thread_id'] == OWNER['thread_id'], 'Target thread mismatch'
    assert datetime.now(timezone.utc) < datetime.fromisoformat(OWNER['deadline_at']), 'Original deadline expired'
    assert sha_bytes((ROOT / 'pipeline/headless/.tick_context.json').read_bytes()) == OWNER['context_sha256']
    assert sha_bytes((ROOT / 'pipeline/headless/.tick_context_state.next.json').read_bytes()) == OWNER['pending_sha256']


def save_new(path, value):
    with path.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


REMOTE_PROGRAM = r'''
import os,socket,stat,hashlib,json,base64
expected_host='dl04-MS-7E06'
actual_host=socket.gethostname()
assert actual_host==expected_host, 'Server identity mismatch; file not read'
path='/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1/logs/train_model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts_20261026_140443.log'
fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
with os.fdopen(fd,'rb') as stream:
    before=os.fstat(stream.fileno())
    assert stat.S_ISREG(before.st_mode), 'Exact log is not a regular file'
    data=stream.read()
    after=os.fstat(stream.fileno())
assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'Log changed during archival; do not treat partial bytes as exact'
assert len(data)==after.st_size
print(json.dumps({'hostname':actual_host,'remote_path':path,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'mtime_ns':after.st_mtime_ns,'inode':after.st_ino,'content_b64':base64.b64encode(data).decode('ascii')}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root', action='store_true')
    args = parser.parse_args()
    if not args.execute_root:
        print(json.dumps({'status': 'DRAFT_DEFAULT_NO_ACTION', 'remote_operations': 0, 'exact_remote_log': REMOTE_LOG}))
        return
    guard()
    assert not any(p.exists() for p in (INTENT, EVIDENCE, DEST)), 'Existing archival request/material: inspect existing evidence, never replay blindly'
    command = ['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=8', 'songcl@192.168.1.115', 'python3 -B -c ' + shlex.quote(REMOTE_PROGRAM)]
    save_new(INTENT, {'recorded_at': datetime.now(timezone.utc).isoformat(), 'owner': OWNER, 'hostname_required': HOSTNAME, 'remote_path': REMOTE_LOG, 'purpose': 'exact_log_bytes_only_not_checkpoint', 'command_sha256': sha_bytes(json.dumps(command).encode()), 'partial_policy': 'read_only_reconcile_no_blind_replay'})
    guard()
    completed = subprocess.run(command, capture_output=True, timeout=90)
    if completed.returncode != 0:
        save_new(HERE / 'archive_failure.json', {'recorded_at': datetime.now(timezone.utc).isoformat(), 'returncode': completed.returncode, 'stderr': completed.stderr.decode('utf8', 'replace')[-3000:], 'exact_log_archived': False, 'reason_of_training_exit': 'UNKNOWN'})
        raise RuntimeError('Exact log read failed; inspect failure and original request; no automatic retry')
    payload = json.loads(completed.stdout.decode('utf8'))
    assert payload['hostname'] == HOSTNAME and payload['remote_path'] == REMOTE_LOG
    data = base64.b64decode(payload.pop('content_b64'), validate=True)
    assert type(payload['size']) is int and len(data) == payload['size']
    assert sha_bytes(data) == payload['sha256']
    guard()
    with DEST.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    actual = DEST.read_bytes()
    assert len(actual) == payload['size'] and sha_bytes(actual) == payload['sha256']
    evidence = {'status': 'EXACT_SINGLE_LOG_ARCHIVED_SHA_SIZE_MATCH', 'recorded_at': datetime.now(timezone.utc).isoformat(), 'actual_thread_id': os.environ.get('CODEX_THREAD_ID'), 'owner': OWNER, 'remote': payload, 'local_path': str(DEST), 'local_size': len(actual), 'local_sha256': sha_bytes(actual), 'sha256_size_match': True, 'ssh_returncode': completed.returncode, 'checkpoint_read_or_copied': False, 'historical_log_enumeration': False, 'gpu_or_process_queries': False, 'shared_state_modified': False, 'training_terminal_status': 'stopped_unknown', 'reason_of_training_exit': 'UNKNOWN', 'no_normal_completion_inferred': True, 'no_restart_or_resume': True}
    save_new(EVIDENCE, evidence)
    print(json.dumps({'status': evidence['status'], 'evidence': str(EVIDENCE), 'local_path': str(DEST), 'size': len(actual), 'sha256': sha_bytes(actual), 'reason_of_training_exit': 'UNKNOWN'}))


if __name__ == '__main__':
    main()
