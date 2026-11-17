from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,os
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;ROOT=Path('D:/project/cluster_project');sys.path.insert(0,str(CURRENT));import anchor
def check():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in anchor.EXPECTED}==anchor.EXPECTED
 m=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert m['mode']=='foreground' and m['target_thread_id']==anchor.EXPECTED['thread_id'];assert datetime.now(timezone.utc)<datetime.fromisoformat(anchor.EXPECTED['deadline_at'])
 for n,h in anchor.CHECKS.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
 return {'owner':anchor.EXPECTED,'actual_child_thread':os.environ.get('CODEX_THREAD_ID'),'root_guard_pass_claimed':False,'environment_modified':False}
def save(name,value):
 check();p=(HERE/name).resolve();assert p.is_relative_to(HERE) and not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value,encoding='utf8')
