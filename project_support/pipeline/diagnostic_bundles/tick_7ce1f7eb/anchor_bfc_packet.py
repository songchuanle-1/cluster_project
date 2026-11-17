"""Fresh GPU0-only owner guard for this heartbeat; no mutation on import."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project')
EXPECTED={'token':'7ce1f7eb75114a98a169f9ff9b6bbb06','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-27T02:11:32.801863+00:00','deadline_at':'2026-10-27T03:11:32.801863+00:00','context_sha256':'3e9dda94bf30483254f5824d4d99a3f4d5e89d25969eb60a9f518fe7f5ec24d2','pending_sha256':'866dc61a74fc0d58d0b7e3cd5f26e0ef88cebb1a132bf31d0038cbcaec8b10cd'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:owner.get(k) for k in EXPECTED}==EXPECTED
 mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 checks={'pipeline/headless/.tick_context.json':EXPECTED['context_sha256'],'pipeline/headless/.tick_context_state.next.json':EXPECTED['pending_sha256'],'SERVERS.yaml':'2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1','pipeline/goal.json':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85','pipeline/authorizations/experiment_first_20261021.json':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8','pipeline/authorizations/server4_gpu0_only_20261026.json':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
 for rel,value in checks.items():assert sha(ROOT/rel)==value,rel
 return owner
