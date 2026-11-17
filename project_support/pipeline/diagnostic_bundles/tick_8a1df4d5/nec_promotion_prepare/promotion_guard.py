"""Exact root-only current-owner guard for disabled promotion drafts; no import actions."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project');TICK=Path(__file__).resolve().parent.parent
EXPECTED=json.loads((TICK/'owner_binding.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 p=ROOT/'pipeline';o=json.loads((p/'headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8'))
 assert {k:o.get(k) for k in EXPECTED}==EXPECTED
 assert os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 assert sha(p/'headless/.tick_context.json')==EXPECTED['context_sha256'] and sha(p/'headless/.tick_context_state.next.json')==EXPECTED['pending_sha256']
 assert json.loads((p/'execution_mode.json').read_text(encoding='utf-8'))==dict(mode='foreground',target_thread_id=EXPECTED['thread_id'])
 return o
