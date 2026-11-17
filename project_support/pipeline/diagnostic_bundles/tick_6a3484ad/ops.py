"""Guarded orchestration for this continuing foreground tick only."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

os.environ.update(PROJECT_ROOT='D:/project', PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick

ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'pipeline/diagnostic_bundles/tick_0d3bdd38'
TOKEN = '6a3484ad478847ebb8200eee80781f84'
THREAD = '01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL = '42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
CID = 'fle-native-nonself-target-mixing-audit'
STAGE = '/data/songcl/Project/Cluster_project/pipeline/fle_qf_attribution_6a3484ad'
HOSTS = {'192.168.1.115': 'dl04-MS-7E06', '192.168.1.120': 'sysu311-MS-7C59'}

def guard(seconds=0):
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == THREAD == os.environ['CODEX_THREAD_ID']
    assert (datetime.fromisoformat(owner['deadline_at']) - datetime.now(timezone.utc)).total_seconds() > seconds
    assert tick.digest(ROOT / 'pipeline/goal.json') == GOAL
    assert tick.load(ROOT / 'pipeline/execution_mode.json') == {'mode': 'foreground', 'target_thread_id': THREAD}
    return owner

def save(name, value):
    guard()
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)

def evidence(path):
    return {'path': Path(path).relative_to(ROOT).as_posix(), 'sha256': tick.digest(path)}

def run(args, timeout=90):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)

def ssh(program, host='192.168.1.115', timeout=90):
    assert host in HOSTS
    program = 'import socket\nassert socket.gethostname()==' + repr(HOSTS[host]) + '\n' + program
    response = run(['ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=10',
                    'songcl@' + host, shlex.join(['/usr/bin/python3', '-B', '-c', program])], timeout)
    assert response.returncode == 0, response.stderr
    return json.loads(response.stdout)

def add(candidate, paths):
    known = {(item['path'], item['sha256']) for item in candidate['evidence']}
    for path in paths:
        item = evidence(path)
        if (item['path'], item['sha256']) not in known:
            candidate['evidence'].append(item)
            known.add((item['path'], item['sha256']))
