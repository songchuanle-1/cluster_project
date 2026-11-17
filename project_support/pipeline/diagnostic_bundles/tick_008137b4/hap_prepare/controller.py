"""Owner-only fresh HAP diagnostic controller; no queue, sync or ledger mutation."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

import yaml

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
TOKEN = '008137b428f54f20a65fe71e999f13dc'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
GENERATED = '2026-10-21T16:03:27.572736+00:00'
DEADLINE = '2026-10-21T17:03:27.572736+00:00'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
COMMIT = 'f51823bbddf0f8095a9a5813bf1f8169e3d7edb0'
STAGE = '/data/songcl/Project/Cluster_project/pipeline/hap_008137b4'
GPU_UUID = 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
SSH_OPTIONS = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=10']


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard(seconds=0):
    owner = read(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == THREAD == os.environ['CODEX_THREAD_ID']
    assert owner['generated_at'] == GENERATED and owner['deadline_at'] == DEADLINE
    assert (datetime.fromisoformat(DEADLINE) - datetime.now(timezone.utc)).total_seconds() > seconds
    assert sha(ROOT / 'pipeline/goal.json') == GOAL
    assert sha(ROOT / 'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(ROOT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    preparation = read(OUT / 'preparation.json')
    assert preparation['token'] == TOKEN and preparation['deadline_at'] == DEADLINE
    assert preparation['context_sha256'] == owner['context_sha256']
    assert preparation['pending_sha256'] == owner['pending_sha256']
    for name, expected in preparation['prepared_file_hashes'].items():
        path = (OUT / name).resolve()
        assert path.is_relative_to(OUT.resolve())
        assert sha(path) == expected, name
    cfg = yaml.safe_load((ROOT / 'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    assert all(cfg.get(key) == value for key, value in preparation['server_binding'].items())
    assert cfg['host'] == '192.168.1.115' and cfg['expected_hostname'] == 'dl04-MS-7E06'
    assert cfg['allowed_gpus'] == [0, 1] and cfg['max_tasks_per_gpu'] == 1
    assert {str(k): v for k, v in cfg['expected_gpu_uuids'].items()}['0'] == GPU_UUID
    manifest = read(OUT / 'native_manifest.json')
    assert manifest['physical_gpu'] == 0 and manifest['gpu_uuid'] == GPU_UUID
    assert manifest['code_commit'] == COMMIT and manifest['stage'] == STAGE
    assert manifest['root'] == cfg['remote_code_root']
    lease = read(OUT / 'execution_lease.json')
    assert lease['token'] == TOKEN and lease['thread_id'] == THREAD
    assert lease['deadline_at'] == DEADLINE and lease['generated_at'] == GENERATED
    assert lease['native_manifest_sha256'] == sha(OUT / 'native_manifest.json')
    return owner, cfg


def save(name, value):
    guard()
    assert Path(name).name == name
    path = OUT / name
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return path


def remote(code, timeout=120, conda=False):
    _, cfg = guard(timeout + 120)
    python = shlex.join(['python' if conda else '/usr/bin/python3', '-B', '-'])
    if conda:
        python = shlex.join(['bash', '-lc', 'source ' + shlex.quote(cfg['conda_source'])
            + ' && conda activate ' + shlex.quote(cfg['conda_env']) + ' && ' + python])
    command = ['ssh', *SSH_OPTIONS, cfg['user'] + '@' + cfg['host'], python]
    prefix = "import socket\nassert socket.gethostname() == 'dl04-MS-7E06'\n"
    try:
        process = subprocess.run(command, input=prefix + code, capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired as error:
        def tail(value):
            return value.decode('utf-8', errors='replace')[-24000:] if isinstance(value, bytes) else (value or '')[-24000:]
        return dict(observed_at=now(), returncode=None, transport_timeout=True,
                    execution_uncertain=True, stdout=tail(error.stdout), stderr=tail(error.stderr))
    result = dict(observed_at=now(), returncode=process.returncode,
                  stdout=process.stdout[-30000:], stderr=process.stderr[-20000:])
    if process.returncode == 0:
        result['data'] = json.loads(process.stdout)
    return result


def probe():
    code = '''
import fcntl,json,subprocess
row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
fields=[v.strip() for v in row.split(',')]
assert fields[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
locks={}
for kind in ('training','diagnostic','exclusive'):
 handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
 try:
  fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
  locks[kind]='available'
 except BlockingIOError:locks[kind]='busy'
 finally:handle.close()
print(json.dumps({'physical_gpu':0,'inventory':row,'contexts':contexts,'locks':locks,
 'idle':not contexts and int(fields[2])<1024 and int(fields[3])<10,
 'scope':'GPU0 only; locks released after observation; acquire rechecks before CUDA'}))
'''
    result = remote(code)
    name = 'probe_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
    save(name, result)
    print(json.dumps(dict(file=name, observation=result), ensure_ascii=False))


def payload():
    manifest = read(OUT / 'native_manifest.json')
    names = list(manifest['diagnostic_files']) + ['native_manifest.json', 'execution_lease.json']
    return {name: (OUT / name).read_bytes() for name in names}


def stage():
    guard(360)
    save('stage_request.json', dict(requested_at=now(), token=TOKEN, stage=STAGE,
         manifest_sha256=sha(OUT / 'native_manifest.json'), remote_execution='file staging and CPU hashes only'))
    files = payload()
    encoded = {name: base64.b64encode(value).decode('ascii') for name, value in files.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in files.items()}
    code = '''
import base64,hashlib,json,sys
from pathlib import Path
stage=Path(STAGE)
assert stage.parent.resolve()==Path('/data/songcl/Project/Cluster_project/pipeline').resolve()
assert not stage.exists(), 'Fresh isolated stage required; inspect prior request instead of replay'
stage.mkdir(exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
sys.path.insert(0,str(stage))
from native_runtime import verify
verify()
print(json.dumps({'stage':str(stage),'files':len(PAYLOAD),'file_sha256':HASHES,
 'remote_asset_hashes_verified':True,'gpu_execution':False,'native_execution':False}))
'''
    result = remote('STAGE=' + repr(STAGE) + '\nPAYLOAD=' + repr(encoded)
        + '\nHASHES=' + repr(hashes) + '\n' + code, timeout=240)
    save('staging_execution.json', result)
    assert result['returncode'] == 0, 'Staging failed/uncertain: inspect saved evidence, never blindly replay'
    print(json.dumps(dict(stage=STAGE, staged=True, remote_asset_hashes_verified=True,
                         native_smoke_passed=False, resource_passed=False)))


def verify_assets():
    guard(360)
    code = 'import json,sys\nsys.path.insert(0,' + repr(STAGE) + ')\nfrom native_runtime import verify\nverify()\nprint(json.dumps({"asset_hashes_verified":True,"gpu_execution":False}))\n'
    result = remote(code, timeout=240)
    name = 'asset_check_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
    save(name, result)
    assert result['returncode'] == 0, 'Native assets differ/unavailable; no worker execution'
    print(json.dumps(dict(file=name, asset_hashes_verified=True, native_smoke_passed=False)))


def run(mode, target):
    guard(1020)
    assert mode in ('smoke', 'resources') and target in ('candidate', 'champion')
    staging = read(OUT / 'staging_execution.json')
    assert staging['returncode'] == 0 and staging['data']['remote_asset_hashes_verified'] is True
    request = mode + '_' + target + '_request.json'
    save(request, dict(requested_at=now(), mode=mode, target=target, token=TOKEN,
         deadline_at=DEADLINE, stage=STAGE, physical_gpu=0, gpu_uuid=GPU_UUID,
         worker_sha256=sha(OUT / 'worker_v2.py'), manifest_sha256=sha(OUT / 'native_manifest.json')))
    code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
command=[sys.executable,'-B',str(stage/'worker_v2.py'),'--lease',str(stage/'execution_lease.json'),'--mode',MODE,'--target',TARGET]
process=subprocess.run(command,capture_output=True,text=True,timeout=840)
result={'returncode':process.returncode,'command':command,'stdout':process.stdout[-24000:],'stderr':process.stderr[-24000:]}
path=stage/(MODE+'_'+TARGET+'_result.json')
if path.exists():result['result']=json.loads(path.read_text())
print(json.dumps(result,allow_nan=False))
'''
    execution = remote('STAGE=' + repr(STAGE) + '\nMODE=' + repr(mode)
        + '\nTARGET=' + repr(target) + '\n' + code, timeout=900, conda=True)
    save(mode + '_' + target + '_execution.json', execution)
    assert execution['returncode'] == 0, 'Transport failed/uncertain: reconcile exact staged request; no replay'
    observed = execution['data']
    result = observed.get('result', {})
    save(mode + '_' + target + '_result.json', result)
    print(json.dumps(dict(mode=mode, target=target, process_returncode=observed['returncode'],
        execution_completed=result.get('execution_completed', False),
        optimizer_steps=result.get('optimizer_steps'),
        observer_readout_complete=result.get('observer_readout_complete'),
        profile=result.get('profile'), error_type=result.get('error_type'), error=result.get('error'),
        scientific_admission=False), ensure_ascii=False))
    assert observed['returncode'] == 0 and result.get('execution_completed') is True, 'Native checks failed; preserve full evidence, no PASS'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['probe', 'stage', 'verify-assets', 'smoke', 'resources', 'status'])
    parser.add_argument('--target', choices=['candidate', 'champion'], default='candidate')
    args = parser.parse_args()
    if args.operation == 'probe':
        probe()
    elif args.operation == 'stage':
        stage()
    elif args.operation == 'verify-assets':
        verify_assets()
    elif args.operation in ('smoke', 'resources'):
        run(args.operation, args.target)
    else:
        guard()
        print(json.dumps(dict(token=TOKEN, deadline_at=DEADLINE, stage=STAGE,
            manifest_sha256=sha(OUT / 'native_manifest.json'),
            result_files=[p.name for p in sorted(OUT.glob('*_result.json'))],
            execution_requests=[p.name for p in sorted(OUT.glob('*_request.json'))]), ensure_ascii=False))


if __name__ == '__main__':
    main()
