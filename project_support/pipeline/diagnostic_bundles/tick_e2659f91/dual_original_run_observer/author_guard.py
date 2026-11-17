"""Private child-safe author guard; does not invoke or impersonate root guard."""
from pathlib import Path
import ast,json,hashlib,os
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
TICK=HERE.parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def author_guard():
    values={}
    for n in ast.parse((TICK/'anchor.py').read_text(encoding='utf8')).body:
        if isinstance(n,ast.Assign):
            for x in n.targets:
                if isinstance(x,ast.Name) and x.id in ('EXPECTED','CHECKS'):values[x.id]=ast.literal_eval(n.value)
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf8'))
    mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text(encoding='utf8'))
    assert {k:owner.get(k) for k in values['EXPECTED']}==values['EXPECTED']
    assert mode['mode']=='foreground' and mode['target_thread_id']==owner['thread_id']
    child=os.environ.get('CODEX_THREAD_ID');assert child and child!=owner['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    for name,digest in values['CHECKS'].items():assert sha(ROOT/name)==digest,name
    return {'actual_child_thread_id':child,'root_owner':values['EXPECTED'],'root_guard_called':False,'root_environment_impersonated':False}
def write_new(name,content):
    author_guard();path=HERE/name;assert path.resolve().is_relative_to(HERE.resolve())
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf8',newline='\n') as f:f.write(content)
    author_guard();return path
