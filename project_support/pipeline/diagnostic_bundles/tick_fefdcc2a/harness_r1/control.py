"""Current-lease orchestration for the existing independent PCE candidate."""
import argparse
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0, str(SKILL))
import foreground_tick as tick
import yaml

TOKEN = 'fefdcc2a82294674927257b9c68f7b47'
THREAD = '01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
CID = 'hierarchy-cross-leaf-physical-contact-exchange'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_658721c0'
STAGE = '/data/songcl/Project/Cluster_project/pipeline/pce_fefdcc2a'
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
SSH = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10']


def now():
    return datetime.now(timezone.utc).isoformat()


def guard(seconds=0):
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == THREAD == os.environ['CODEX_THREAD_ID']
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > seconds
    assert tick.digest(ROOT / 'pipeline/goal.json') == GOAL
    assert tick.digest(ROOT / 'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert tick.digest(ROOT / 'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    cfg = yaml.safe_load((ROOT / 'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
    assert cfg['host'] == '192.168.1.115' and cfg['expected_hostname'] == 'dl04-MS-7E06'
    assert cfg['allowed_gpus'] == [0, 1] and cfg['max_tasks_per_gpu'] == 1
    return owner, cfg


def evidence(path):
    path = Path(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': tick.digest(path)}


def save(name, data):
    guard()
    path = OUT / name
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
    return path


def advance(paths, action):
    guard()
    work = tick.load(ROOT / 'pipeline/research_work.json')
    candidate = next(item for item in work['candidates'] if item['id'] == CID)
    existing = {(item['path'], item['sha256']) for item in candidate['evidence']}
    for path in paths:
        item = evidence(path)
        if (item['path'], item['sha256']) not in existing:
            candidate['evidence'].append(item)
    candidate['next_action'] = action
    candidate['scientific_admission'] = False
    tick.save(ROOT / 'pipeline/research_work.json', work)


def remote(code, timeout=120, conda=False):
    _, cfg = guard(max(120, min(timeout + 90, 1200)))
    command = shlex.join(['python' if conda else '/usr/bin/python3', '-B', '-'])
    if conda:
        command = shlex.join(['bash', '-lc', 'source ' + shlex.quote(cfg['conda_source'])
            + ' && conda activate ' + shlex.quote(cfg['conda_env']) + ' && ' + command])
    result = subprocess.run(['ssh', *SSH, cfg['user'] + '@' + cfg['host'], command],
        input="import socket\nassert socket.gethostname() == 'dl04-MS-7E06'\n" + code,
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    data = {'observed_at': now(), 'returncode': result.returncode,
        'stdout': result.stdout[-24000:], 'stderr': result.stderr[-14000:]}
    if result.returncode == 0:
        data['data'] = json.loads(result.stdout)
    return data


def probe():
    code = '''
import fcntl,json,subprocess
from datetime import datetime,timezone
r={'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpus':[]}
for gpu in (0,1):
 row=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 expected={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}[gpu]
 fields=[v.strip() for v in row.split(',')]
 assert fields[:2]==[str(gpu),expected]
 contexts=subprocess.check_output(['nvidia-smi','-i',str(gpu),'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
 locks={}
 for kind in ('training','diagnostic','exclusive'):
  handle=open('/tmp/cluster_project_gpu'+str(gpu)+'_'+kind+'.lock','a+b')
  try:
   fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
   locks[kind]='available'
  except BlockingIOError:locks[kind]='busy'
  finally:handle.close()
 r['gpus'].append({'index':gpu,'inventory':row,'contexts':contexts,'locks':locks,'idle':not contexts and int(fields[2])<1024 and int(fields[3])<10})
print(json.dumps(r))
'''
    result = remote(code)
    path = save('initial_resources.json', result)
    print(json.dumps({'evidence': evidence(path), 'observation': result}, ensure_ascii=False))


def stage():
    owner, _ = guard(1200)
    protocol = save('preregistration.json', {
        'preregistered_at': now(), 'token': TOKEN, 'candidate_id': CID,
        'implementation': 'Exact existing independent PCE package; no model edits or new implementation revision.',
        'resources': {'targets': ['champion', 'candidate'], 'processes': 'fresh isolated process per target',
            'input': 'same first native VAL expression, original deterministic nonaugmented loader',
            'batch_size': 1, 'warmup': 20, 'repeat': 100, 'statistics': ['median_ms', 'p90_ms'],
            'counter': "Original fvcore FlopCountAnalysis(model,(sample,'predict')); unchanged historical handlers",
            'memory': 'matched full predict allocated/reserved peak; full optimizer peak unknown',
            'threshold': 'Default total counted FLOPs<=10G; original memory/Pareto constraint unchanged',
            'accuracy': 'No validation accuracy evaluation or selection; resource sample only'},
        'controls': {'input': 'Same two fixed TRAIN scenes/eight expressions as prior native capture',
            'source': 'Actual native loss then original full hierarchy-bank/encoder recomputation, NOT frozen-bank replacement.',
            'repeat': 'Three exact encoder recomputations with unchanged inputs/memberships/dtype',
            'permutation': 'Reverse valid SP rows, inverse-map contact edges and first-level membership rows; recompute all banks/full encoder and restore rows.',
            'negative': 'Delete all contacts, compare original verified parent gather with fresh full bank recomputation.',
            'tolerance': 1e-6,
            'limits': 'Not whole-model SP renumbering/FPS-equivariance. Preserve failed controls; no threshold/precision/operator waiver.',
            'decision': 'No admission from frozen-bank controls or efficacy from untrained readouts.'},
        'seed': 1999, 'epochs': 50, 'max_iters': 70, 'new_training': 0, 'optimizer_steps': 0, 'production_changes': False})
    manifest = copy.deepcopy(tick.load(OLD / 'native_manifest.json'))
    manifest.update(stage=STAGE, current_token=TOKEN, resource_protocol=evidence(protocol))
    runtime = (OLD / 'native_runtime.py').read_text(encoding='utf-8')
    assert runtime.count('658721c071ae487ea47224e55d51abde') == 1
    payload = {'native_runtime.py': runtime.replace('658721c071ae487ea47224e55d51abde', TOKEN).encode('utf-8'),
        'worker.py': (OUT / 'worker.py').read_bytes()}
    package = ROOT / 'Cluster/framework/model/Quard_model' / (NAME + '_pce')
    for path in sorted(package.glob('*.py')):
        payload['candidate_model/' + path.name] = path.read_bytes()
    config = ROOT / 'Cluster/configs/Quard/ctf_hcg_csort_pce' / (NAME + '_pce.yaml')
    payload['candidate.yaml'] = config.read_bytes()
    manifest['candidate_source_hashes'] = {Path(name).name: hashlib.sha256(value).hexdigest()
        for name, value in payload.items() if name.startswith('candidate_model/')}
    manifest['diagnostic_files'] = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    save('native_manifest.json', manifest)
    payload['native_manifest.json'] = (OUT / 'native_manifest.json').read_bytes()
    save('execution_lease.json', {'token': TOKEN, 'thread_id': THREAD, 'project': 'cluster_project',
        'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(OUT / 'native_manifest.json')})
    payload['execution_lease.json'] = (OUT / 'execution_lease.json').read_bytes()
    advance([protocol, OUT / 'native_manifest.json', OUT / 'worker.py', OUT / 'control.py'],
        'Execute same-standard full-model resource pair and actual full-source hierarchy/encoder controls under current lease; no training before original gates pass.')
    encoded = {name: base64.b64encode(value).decode('ascii') for name, value in payload.items()}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in payload.items()}
    code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE)
stage.mkdir(parents=False,exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as stream:stream.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'stage':str(stage),'files':len(PAYLOAD),'sha256':HASHES}))
'''
    observed = remote('STAGE=' + repr(STAGE) + '\nPAYLOAD=' + repr(encoded) + '\nHASHES=' + repr(hashes) + '\n' + code)
    save('staging.json', observed)
    assert observed['returncode'] == 0
    print(json.dumps({'staged': STAGE, 'files': len(payload), 'scientific_admission': False}))


def run(mode, target):
    guard(1100 if mode == 'resources' else 700)
    label = mode + '_' + target
    code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
p=subprocess.run([sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json'),'--mode',MODE,'--target',TARGET],capture_output=True,text=True,timeout=TIMEOUT)
r={'returncode':p.returncode,'stdout':p.stdout[-10000:],'stderr':p.stderr[-14000:]}
path=stage/(MODE+'_'+TARGET+'_result.json')
if path.exists():r['result']=json.loads(path.read_text())
print(json.dumps(r))
'''
    limit = 900 if mode == 'resources' else 600
    observed = remote('STAGE=' + repr(STAGE) + '\nMODE=' + repr(mode) + '\nTARGET=' + repr(target)
        + '\nTIMEOUT=' + str(limit) + '\n' + code, timeout=limit + 45, conda=True)
    observation = save(label + '_execution.json', observed)
    assert observed['returncode'] == 0, 'Observer failed; reconcile, never blindly replay.'
    result = observed['data'].get('result', {})
    path = save(label + '_result.json', result)
    advance([observation, path], 'Inspect preserved full-model resources and full-source controls; failed/unresolved gates are not admission; no new GPU authorization needed.')
    keys = ('execution_completed', 'target', 'mode', 'error_type', 'error', 'profile', 'median_ms',
        'p90_ms', 'peak_allocated_bytes', 'controls', 'all_full_source_controls_passed',
        'native_loss_forwards', 'native_criterion_backwards', 'gradient_tensor_count')
    print(json.dumps({'returncode': observed['data']['returncode'], 'result': {key: result.get(key) for key in keys}}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('probe', 'stage', 'resources', 'controls'))
    parser.add_argument('--target', choices=('champion', 'candidate'), default='candidate')
    args = parser.parse_args()
    if args.operation == 'probe':
        probe()
    elif args.operation == 'stage':
        stage()
    else:
        run(args.operation, args.target)
