"""Current immutable owner guard; importing performs no mutation."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,hashlib
ROOT=Path('D:/project/cluster_project')
EXPECTED={'token': 'e2659f91767a448ebf53623f5ac58ba7', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-31T16:07:46.006821+00:00', 'deadline_at': '2026-10-31T17:07:46.006821+00:00', 'context_sha256': '31a61b0062ba44f2b07fe30524c74da7134472efbdc4315282d9b3bdc016d10e', 'pending_sha256': 'e4942a52db3fdf281c1bc74b22eb795167b89af37061be775d59d36b0076a019'}
CHECKS={'pipeline/headless/.tick_context.json': '31a61b0062ba44f2b07fe30524c74da7134472efbdc4315282d9b3bdc016d10e', 'pipeline/headless/.tick_context_state.next.json': 'e4942a52db3fdf281c1bc74b22eb795167b89af37061be775d59d36b0076a019', 'pipeline/goal.json': '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85', 'SERVERS.yaml': '19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265', 'pipeline/closure_policy.json': '299396caa229f5cb680e12d1f0c895c1d35155d619e7dbf0a1fb6cdc3f302efc', 'pipeline/authorizations/experiment_first_20261021.json': '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8', 'pipeline/authorizations/server4_gpu1_20261030.json': '6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in EXPECTED}==EXPECTED
 mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 for n,h in CHECKS.items():assert sha(ROOT/n)==h,n
 return dict(EXPECTED)
