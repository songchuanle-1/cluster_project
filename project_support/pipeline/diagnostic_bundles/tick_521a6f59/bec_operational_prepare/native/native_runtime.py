"""Reusable BEC diagnostic runtime; fresh current-owner manifest/lease required.

No torch import or CUDA setup occurs before the two idle observations and locks.
The preparation bundle deliberately does not include native_manifest.json/lease.
"""
import re
DRAFT_EXECUTION_DISABLED = False

def require_promoted_version():
    if DRAFT_EXECUTION_DISABLED or not isinstance(SOURCE_PARENT_COMMIT,str) or re.fullmatch(r'[0-9a-f]{40}', SOURCE_PARENT_COMMIT) is None or not isinstance(CANDIDATE_COMMIT, str) or re.fullmatch(r'[0-9a-f]{40}', CANDIDATE_COMMIT) is None or not isinstance(SOURCE_PREPARATION_SHA256,str) or re.fullmatch(r'[0-9a-f]{64}', SOURCE_PREPARATION_SHA256) is None:
        raise RuntimeError('BEC native preparation is execution-disabled; a fresh reviewed operational bundle and lease are required')

# Reject an unversioned bundle before manifest access, NVML, locks or torch.
CANDIDATE_COMMIT = '9b6782f44ca7f2c8ac35baea01dfd070314b5701'
SOURCE_PARENT_COMMIT = '48fc302c3c02ffef0b241be3593c386b6b65a72e'
SOURCE_PREPARATION_SHA256 = '2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
RUNTIME_EXPECTED_COMMIT = '48fc302c3c02ffef0b241be3593c386b6b65a72e'
require_promoted_version()


import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
    TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='1')
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import re
import signal
import socket
import subprocess

STAGE = Path(__file__).resolve().parent
MANIFEST = json.loads((STAGE / 'native_manifest.json').read_text())
ASSETS = MANIFEST['assets']
ROOT = Path(MANIFEST['root'])
NAME = MANIFEST['name']
HANDLES = []
GPU_UUIDS = {0: 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',
            1: 'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
BASE_NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
assert MANIFEST['schema_version'] == 2
assert MANIFEST['project'] == 'cluster_project' and MANIFEST['server_id'] == 'server-4'
assert MANIFEST['candidate_id'] == 'hierarchy-cross-level-bipartite-edge-composition'
assert MANIFEST['code_commit'] == CANDIDATE_COMMIT
assert MANIFEST['runtime_code_commit'] == RUNTIME_EXPECTED_COMMIT
assert MANIFEST['experiment_id'] == 'M215-BEC'
assert MANIFEST['config'] == 'configs/Quard/ctf_hcg_csort_bec/' + BASE_NAME + '_bec.yaml'
assert NAME == BASE_NAME and MANIFEST['candidate_name'] == BASE_NAME + '_bec'
assert MANIFEST['goal_sha256'] == GOAL
assert MANIFEST['source_preparation_sha256'] == SOURCE_PREPARATION_SHA256
assert ROOT == Path('/data/songcl/Project/Cluster_project/Cluster_experiment_first_899d59f1')
assert Path(MANIFEST['stage']).resolve() == STAGE.resolve()
assert STAGE.parent == Path('/data/songcl/Project/Cluster_project/pipeline')
assert re.fullmatch(r'[0-9a-f]{32}', MANIFEST['current_token'])
assert STAGE.name == 'bec_' + MANIFEST['current_token'][:8] + '_gpu' + str(MANIFEST['physical_gpu'])
PHYSICAL_GPU = MANIFEST['physical_gpu']
assert type(PHYSICAL_GPU) is int and PHYSICAL_GPU in GPU_UUIDS
assert MANIFEST['gpu_uuid'] == GPU_UUIDS[PHYSICAL_GPU]
assert MANIFEST['allowed_gpus'] and all(type(g) is int and g in GPU_UUIDS for g in MANIFEST['allowed_gpus'])
assert len(set(MANIFEST['allowed_gpus'])) == len(MANIFEST['allowed_gpus'])
assert PHYSICAL_GPU in MANIFEST['allowed_gpus']
assert MANIFEST['tolerance'] == 1e-6


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_source_version():
    require_promoted_version()
    version_path = STAGE / 'source_version_binding.json'
    assert sha(version_path) == MANIFEST['source_version_binding_sha256']
    version = json.loads(version_path.read_text())
    assert version['code_commit'] == MANIFEST['source_version_commit'] == CANDIDATE_COMMIT
    assert version['candidate_id'] == MANIFEST['candidate_id']
    assert version['candidate_source_hashes'] == MANIFEST['candidate_source_hashes']
    assert version['candidate_config_sha256'] == MANIFEST['candidate_config_sha256']
    assert version['original_source_preparation_sha256'] == MANIFEST['source_preparation_sha256']
    assert len(version['source_files']) == 9 and version['parent_commit'] == SOURCE_PARENT_COMMIT


def verify():
    verify_source_version()
    for name, expected in ASSETS['source_hashes'].items():
        assert sha(ROOT / 'framework/model/Quard_model' / NAME / name) == expected, name
    for name, expected in MANIFEST['candidate_source_hashes'].items():
        assert sha(STAGE / 'candidate_model' / name) == expected, name
    assert len(MANIFEST['candidate_source_hashes']) == 8
    assert sha(STAGE / 'candidate.yaml') == MANIFEST['candidate_config_sha256']
    for name in ('config', 'checkpoint', 'annotation'):
        path = ASSETS['config_path'] if name == 'config' else ASSETS['annotation_path'] if name == 'annotation' else ASSETS['checkpoint']
        assert sha(path) == ASSETS[name + '_sha256'], name
    assert sha(ROOT / 'framework/dataset/scannetv2.py') == ASSETS['dataset_source_sha256']
    assert sha(ASSETS['pretrain']) == ASSETS['pretrain_sha256']
    assert sha(ROOT / 'tools/train.py') == ASSETS['native_train_source_sha256']
    runtime_commit = MANIFEST['runtime_code_commit']
    assert re.fullmatch(r'[0-9a-f]{40}', runtime_commit)
    actual_commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True, timeout=10).strip()
    assert actual_commit == runtime_commit, 'Runtime checkout changed; no sync/reset/checkout is performed by this worker'
    required = {'native_runtime.py', 'worker.py', 'candidate.yaml'} | {
        'candidate_model/' + name for name in MANIFEST['candidate_source_hashes']}
    assert required <= set(MANIFEST['diagnostic_files'])
    for name, expected in MANIFEST['diagnostic_files'].items():
        path = (STAGE / name).resolve()
        assert path.is_relative_to(STAGE.resolve()) and sha(path) == expected, name


def observe(require_idle=False):
    assert socket.gethostname() == 'dl04-MS-7E06'
    gpu = str(PHYSICAL_GPU)
    row = subprocess.check_output(['nvidia-smi', '-i', gpu,
        '--query-gpu=index,uuid,memory.used,utilization.gpu', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
    fields = [part.strip() for part in row.split(',')]
    assert fields[:2] == [gpu, GPU_UUIDS[PHYSICAL_GPU]]
    contexts = subprocess.check_output(['nvidia-smi', '-i', gpu,
        '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
    foreign = [line for line in contexts.splitlines() if int(line.split(',')[0]) != os.getpid()]
    assert not foreign, 'Occupied authorized GPU; no sharing or eviction'
    if require_idle:
        assert not contexts and int(fields[2]) < 1024 and int(fields[3]) < 10
    return {'observed_at': datetime.now(timezone.utc).isoformat(), 'gpu': row, 'contexts': contexts}


def acquire(lease_path):
    assert not HANDLES
    lease = json.loads(Path(lease_path).read_text())
    assert lease['project'] == 'cluster_project' and lease['thread_id'] == THREAD
    assert lease['native_manifest_sha256'] == sha(STAGE / 'native_manifest.json')
    assert lease['token'] == MANIFEST['current_token']
    assert lease['generated_at'] == MANIFEST['tick_generated_at']
    assert lease['deadline_at'] == MANIFEST['deadline_at']
    assert lease['server_id'] == 'server-4' and lease['physical_gpu'] == PHYSICAL_GPU
    assert lease['gpu_uuid'] == GPU_UUIDS[PHYSICAL_GPU]
    assert lease['allowed_gpus'] == MANIFEST['allowed_gpus']
    assert lease['goal_sha256'] == GOAL
    for field in ('context_sha256', 'pending_sha256'):
        assert re.fullmatch(r'[0-9a-f]{64}', lease[field]) and lease[field] == MANIFEST[field]
    generated = datetime.fromisoformat(lease['generated_at'])
    deadline = datetime.fromisoformat(lease['deadline_at'])
    now = datetime.now(timezone.utc)
    assert generated <= now < deadline and 0 < (deadline-generated).total_seconds() <= 3600
    remaining = (deadline-now).total_seconds()
    assert 300 < remaining <= 3600, 'Require a fresh current-owner lease with sufficient deadline'
    before = observe(True)
    try:
        for kind in ('training', 'diagnostic', 'exclusive'):
            handle = open('/tmp/cluster_project_gpu' + str(PHYSICAL_GPU) + '_' + kind + '.lock', 'a+b')
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BaseException:
                handle.close()
                raise
            HANDLES.append(handle)
        observe(True)
        verify()
        os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES=GPU_UUIDS[PHYSICAL_GPU])
        signal.alarm(min(600, int(remaining)-150))
        return before
    except BaseException:
        release()
        raise


def release():
    for handle in reversed(HANDLES):
        handle.close()
    HANDLES.clear()


def fingerprint(torch, value):
    h = hashlib.sha256()
    def feed(item):
        if torch.is_tensor(item):
            item = item.detach().cpu().contiguous()
            h.update(str((str(item.dtype), tuple(item.shape))).encode())
            h.update(item.numpy().tobytes())
        elif isinstance(item, dict):
            for key in sorted(item):
                h.update(str(key).encode()); feed(item[key])
        elif isinstance(item, (tuple, list)):
            for part in item:
                feed(part)
        else:
            h.update(repr(item).encode())
    feed(value)
    return h.hexdigest()


def save(name, value):
    assert Path(name).name == name
    value['observed_at'] = datetime.now(timezone.utc).isoformat()
    with (STAGE / name).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
