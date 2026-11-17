"""Current foreground lease, authorized observation, and artifact persistence."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
os.environ.update(PROJECT_ROOT='D:/project', PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0, str(SKILL))
import foreground_tick as tick
import yaml
ROOT = Path('D:/project/cluster_project')
OUT = Path(__file__).resolve().parent
TOKEN = 'dc944b44bc41467081a86ea8ef7dbfea'
THREAD = '01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL = '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
IDS = ('hierarchy-native-batch-minimum-resolution', 'hierarchy-native-superpoint-relabeling-audit')
SSH = ['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10']

def now():
    return datetime.now(timezone.utc).isoformat()

def guard(seconds=0):
    owner = tick.load(ROOT / 'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token'] == TOKEN and owner['thread_id'] == THREAD == os.environ['CODEX_THREAD_ID']
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds() > seconds
    assert tick.digest(ROOT / 'pipeline/goal.json') == GOAL
    servers = yaml.safe_load((ROOT / 'SERVERS.yaml').read_text(encoding='utf-8'))['servers']
    cfg = servers['server-4']
    assert cfg['host'] == '192.168.1.115' and cfg['expected_hostname'] == 'dl04-MS-7E06'
    assert cfg['allowed_gpus'] == [0,1] and cfg['max_tasks_per_gpu'] == 1
    assert servers['server-3']['host'] == '192.168.1.120' and servers['server-3']['allowed_gpus'] == [1]
    return owner, servers

def evidence(path):
    path = Path(path)
    return {'path':path.relative_to(ROOT).as_posix(), 'sha256':tick.digest(path)}

def save(name, value):
    guard()
    path = OUT / name
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
    return path

def remote(server, code, timeout=100, conda=False):
    _, servers = guard()
    assert server in ('server-3','server-4')
    cfg = servers[server]
    code = 'import socket\nassert socket.gethostname()==' + repr(cfg['expected_hostname']) + '\n' + code
    command = shlex.join(['python' if conda else '/usr/bin/python3','-B','-c',code])
    if conda:
        command = shlex.join(['bash','-lc','source '+shlex.quote(cfg['conda_source'])+' && conda activate '+shlex.quote(cfg['conda_env'])+' && '+command])
    started = now()
    process = subprocess.run(['ssh',*SSH,cfg['user']+'@'+cfg['host'],command],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
    result = {'started_at':started,'finished_at':now(),'returncode':process.returncode,'stdout':process.stdout[-20000:],'stderr':process.stderr[-6000:]}
    if process.returncode == 0:
        result['data'] = json.loads(process.stdout)
    return result
