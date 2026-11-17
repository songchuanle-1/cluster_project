"""Current-lease orchestration for the new independent MDC candidate."""
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

TOKEN = '899d59f1e49b4bfaa4daa31e7b32ddce'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
CID = 'hierarchy-coarse-conditioned-fine-channel-attention'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_658721c0'
STAGE = '/data/songcl/Project/Cluster_project/pipeline/cgca_899d59f1_baseline'
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
    manifest = copy.deepcopy(tick.load(OLD / 'native_manifest.json'))
    commit = tick.load(OUT / 'version_native.json')['code_commit']
    manifest.update(stage=STAGE, current_token=TOKEN, candidate_name=NAME+'_cgca',
        candidate_id=CID, code_commit=commit, goal_sha256=GOAL,
        config='configs/Quard/ctf_hcg_csort_cgca/'+NAME+'_cgca.yaml')
    runtime = (OLD / 'native_runtime.py').read_text(encoding='utf-8')
    runtime = runtime.replace('658721c071ae487ea47224e55d51abde', TOKEN).replace('01a04987-fdbe-7301-b2f0-f9b6ab60f74c', THREAD)
    runtime = runtime.replace("'-i', '0'", "'-i', '1'").replace("['0', 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']", "['1', 'GPU-7f82edb9-f620-8045-caea-a75232265cd1']").replace('cluster_project_gpu0_', 'cluster_project_gpu1_').replace("CUDA_VISIBLE_DEVICES='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'", "CUDA_VISIBLE_DEVICES='GPU-7f82edb9-f620-8045-caea-a75232265cd1'")
    payload = {'native_runtime.py': runtime.encode(), 'worker.py': (OUT/'worker.py').read_bytes()}
    package = ROOT/'Cluster/framework/model/Quard_model'/(NAME+'_cgca')
    for p in sorted(package.glob('*.py')):
        payload['candidate_model/'+p.name] = p.read_bytes()
    config = ROOT/'Cluster'/manifest['config']
    payload['candidate.yaml'] = config.read_bytes()
    manifest['root'] = guard()[1]['remote_code_root']
    manifest['assets']['config_path'] = manifest['root']+'/configs/Quard/ctf_hcg_csort/'+NAME+'.yaml'
    manifest['candidate_source_hashes'] = {Path(n).name: hashlib.sha256(v).hexdigest() for n,v in payload.items() if n.startswith('candidate_model/')}
    manifest['candidate_config_sha256'] = hashlib.sha256(payload['candidate.yaml']).hexdigest()
    manifest['diagnostic_files'] = {n: hashlib.sha256(v).hexdigest() for n,v in payload.items()}
    save('native_manifest.json', manifest)
    payload['native_manifest.json'] = (OUT/'native_manifest.json').read_bytes()
    save('execution_lease.json', {'token': TOKEN, 'thread_id': THREAD, 'project': 'cluster_project',
        'deadline_at': owner['deadline_at'], 'native_manifest_sha256': tick.digest(OUT/'native_manifest.json')})
    payload['execution_lease.json'] = (OUT/'execution_lease.json').read_bytes()
    advance([OUT/'native_manifest.json', OUT/'worker.py', OUT/'control.py'],
        'Run exact committed native YAML TRAIN two-step smoke and standard resource pair; training efficacy remains unknown.')
    encoded = {n: base64.b64encode(v).decode() for n,v in payload.items()}
    hashes = {n: hashlib.sha256(v).hexdigest() for n,v in payload.items()}
    code = '''
import base64,hashlib,json
from pathlib import Path
stage=Path(STAGE);stage.mkdir(parents=False,exist_ok=False)
for name,value in PAYLOAD.items():
 path=stage/name
 assert path.resolve().is_relative_to(stage.resolve())
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:f.write(base64.b64decode(value))
 assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[name]
print(json.dumps({'stage':str(stage),'files':len(PAYLOAD),'sha256':HASHES}))
'''
    result = remote('STAGE='+repr(STAGE)+'\nPAYLOAD='+repr(encoded)+'\nHASHES='+repr(hashes)+'\n'+code)
    save('staging.json', result)
    assert result['returncode'] == 0
    print(json.dumps({'staged': STAGE, 'files': len(payload)}))


def run(mode, target='candidate'):
    guard(1000)
    code = '''
import json,subprocess,sys
from pathlib import Path
stage=Path(STAGE)
command=[sys.executable,'-B',str(stage/'worker.py'),'--lease',str(stage/'execution_lease.json'),'--mode',MODE,'--target',TARGET]
p=subprocess.run(command,capture_output=True,text=True,timeout=840)
with (stage/(MODE+'_'+TARGET+'_stdout.log')).open('x') as f:f.write(p.stdout)
with (stage/(MODE+'_'+TARGET+'_stderr.log')).open('x') as f:f.write(p.stderr)
r={'returncode':p.returncode,'command':command,'stdout':p.stdout[-10000:],'stderr':p.stderr[-20000:]}
path=stage/(MODE+'_'+TARGET+'_result.json')
if path.exists():
 try:r['result']=json.loads(path.read_text())
 except Exception as e:r['raw_result']=path.read_text();r['parse_error']=str(e)
print(json.dumps(r))
'''
    result = remote('STAGE='+repr(STAGE)+'\nMODE='+repr(mode)+'\nTARGET='+repr(target)+'\n'+code, timeout=900, conda=True)
    execution = save(mode+'_'+target+'_execution.json', result)
    assert result['returncode'] == 0, 'Observer failed: reconcile; no blind replay'
    observed = result['data']
    p = save(mode+'_'+target+'_result.json', observed.get('result', {}))
    advance([execution, p], 'Review exact native smoke/resources; create receipt only if all four experiment-first gates pass.')
    print(json.dumps({'process_returncode': observed['returncode'], 'result': observed.get('result', {}),
        'error_tail': observed.get('stderr', '')[-2500:]}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['probe','stage','smoke','resources'])
    parser.add_argument('--target', choices=['champion','candidate'], default='candidate')
    args = parser.parse_args()
    if args.operation == 'probe':
        probe()
    elif args.operation == 'stage':
        stage()
    else:
        run(args.operation, args.target)


