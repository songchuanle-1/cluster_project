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

TOKEN = '3e3adfa365e1475f87ea8d8bb0f6eb71'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
CID = 'hierarchy-affine-coarse-to-fine-prolongation'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_658721c0'
STAGE = '/data/songcl/Project/Cluster_project/pipeline/hap_3e3adfa3'
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


