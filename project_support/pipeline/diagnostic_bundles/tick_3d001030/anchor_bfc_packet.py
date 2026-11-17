"""Fresh GPU0-only owner guard for this heartbeat; no mutation on import."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project')
EXPECTED={'token':'3d001030cda04cddade0810e9d380a22','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T10:05:37.308291+00:00','deadline_at':'2026-10-26T11:05:37.308291+00:00','context_sha256':'58907261bcdd1c77799391926782c69573a4c401610de57381fa2571d5cae71d','pending_sha256':'bf6fc5e11ef8e1138972f47cb9bc8275838689ee8165547f194d4b0729abab0e'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:owner.get(k) for k in EXPECTED}==EXPECTED
 mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 checks={'pipeline/headless/.tick_context.json':EXPECTED['context_sha256'],'pipeline/headless/.tick_context_state.next.json':EXPECTED['pending_sha256'],'SERVERS.yaml':'2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1','pipeline/goal.json':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85','pipeline/authorizations/experiment_first_20261021.json':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8','pipeline/authorizations/server4_gpu0_only_20261026.json':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
 for rel,value in checks.items():assert sha(ROOT/rel)==value,rel
 return owner
