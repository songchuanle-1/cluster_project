"""Current owning-lease guard; cluster_project diagnostic scope only."""
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
os.environ.update(PROJECT_ROOT='D:/project',PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
import foreground_tick as tick
ROOT=Path('D:/project/cluster_project')
OUT=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689'
MODELS=ROOT/'pipeline/diagnostic_bundles/tick_4eca1157/models.json'
TOKEN='ed0d2b32aa804291bbf7f5a23828a4a6'
THREAD='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
GOAL='42a250c221648b191d2120e30cf6e7029a8d02c9dc1c0f3817a1144c2bdbafec'
CID='native-train-prefix-repeatability-audit'
STAGE='/data/songcl/Project/Cluster_project/pipeline/native_stride_ed0d2b32'
HOST='192.168.1.115'
SSH=['-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10']
def guard(seconds=0):
    owner=tick.load(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==THREAD==os.environ['CODEX_THREAD_ID']
    assert (datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()>seconds
    assert tick.digest(ROOT/'pipeline/goal.json')==GOAL
    assert tick.load(ROOT/'pipeline/execution_mode.json')=={'mode':'foreground','target_thread_id':THREAD}
    return owner
def save(name,value):
    guard()
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
def evidence(path):
    path=Path(path)
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':tick.digest(path)}
def advance(paths,candidate_id=CID,**updates):
    guard()
    work=tick.load(ROOT/'pipeline/research_work.json')
    c=next(c for c in work['candidates'] if c['id']==candidate_id)
    c.update(updates)
    known={(e['path'],e['sha256']) for e in c['evidence']}
    for path in paths:
        e=evidence(path)
        if (e['path'],e['sha256']) not in known:c['evidence'].append(e)
    guard()
    tick.save(ROOT/'pipeline/research_work.json',work)
def run(args,timeout=90):
    return subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
def ssh(program,timeout=90):
    program='import socket\nassert socket.gethostname()=="dl04-MS-7E06"\n'+program
    r=run(['ssh',*SSH,'songcl@'+HOST,shlex.join(['/usr/bin/python3','-B','-c',program])],timeout)
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)
