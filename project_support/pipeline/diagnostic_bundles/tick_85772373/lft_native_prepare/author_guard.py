"""Explicit root-authorized private author scope; never impersonates root guard."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys

HERE=Path(__file__).resolve().parent
CURRENT=HERE.parent
ROOT=Path('D:/project/cluster_project')
sys.path.insert(0,str(CURRENT))
import anchor

def check():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
    assert {k:owner.get(k) for k in anchor.EXPECTED}==anchor.EXPECTED
    mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text(encoding='utf-8'))
    assert mode['mode']=='foreground' and mode['target_thread_id']==anchor.EXPECTED['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(anchor.EXPECTED['deadline_at'])
    for name,h in anchor.CHECKS.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    return {'scope':'EXPLICITLY_AUTHORIZED_PRIVATE_AUTHOR_GUARD_ONLY','owner':dict(anchor.EXPECTED),
            'actual_child_thread':os.environ.get('CODEX_THREAD_ID'),'root_thread':anchor.EXPECTED['thread_id'],
            'root_guard_pass_claimed':False,'environment_modified':False}

def target(path):
    check();path=Path(path).resolve();assert path.is_relative_to(HERE.resolve())
    return path

def write_text(path,text):
    path=target(path);assert not path.exists(),path
    path.parent.mkdir(parents=True,exist_ok=True);check()
    path.write_text(text,encoding='utf-8')

def write_bytes(path,data):
    path=target(path);assert not path.exists(),path
    path.parent.mkdir(parents=True,exist_ok=True);check()
    path.write_bytes(data)

def save(path,value):
    write_text(path,json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
