"""Current immutable foreground owner/resource guard, no import-side effects."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project')
EXPECTED={'token': 'f1647471ac354e1299ebae355eb1bb56', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-29T00:12:33.075001+00:00', 'deadline_at': '2026-10-29T01:12:33.075001+00:00', 'context_sha256': '6d43acd27221d8245a278694a22220beeddf3c6f2bb990052c7be9eda4a477eb', 'pending_sha256': 'eb8c0cdd6d609d87f9847bc6916d0fedcb3a2b90ccd8c842187d253b56229a26'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in EXPECTED}==EXPECTED
 mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 checks={'pipeline/headless/.tick_context.json':EXPECTED['context_sha256'],'pipeline/headless/.tick_context_state.next.json':EXPECTED['pending_sha256'],'pipeline/goal.json':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85','SERVERS.yaml':'2583ddf1a21511368e98bfaed99d1a2c5e6bd7f223e577d565279a3628352fc1','pipeline/authorizations/experiment_first_20261021.json':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8','pipeline/authorizations/server4_gpu0_only_20261026.json':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}
 for p,h in checks.items():assert sha(ROOT/p)==h,p
 return {k:o[k] for k in EXPECTED}
