"""Current immutable owner guard; importing performs no mutation."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,hashlib
ROOT=Path('D:/project/cluster_project')
EXPECTED={'token': '2c5dccfbdc4840a790faa7a0c4003f0e', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-31T20:04:05.705401+00:00', 'deadline_at': '2026-10-31T21:04:05.705401+00:00', 'context_sha256': 'd43c97b9f544322962c3db10e0f8b5aa3f594848be8fbcdedf8c1210cbd94339', 'pending_sha256': 'ddd85feb4572d476259abc418d8129072f9d28d41a4cba2fdafb2fd7115be5b5'}
CHECKS={'pipeline/headless/.tick_context.json': 'd43c97b9f544322962c3db10e0f8b5aa3f594848be8fbcdedf8c1210cbd94339', 'pipeline/headless/.tick_context_state.next.json': 'ddd85feb4572d476259abc418d8129072f9d28d41a4cba2fdafb2fd7115be5b5', 'pipeline/goal.json': '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85', 'SERVERS.yaml': '19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265', 'pipeline/closure_policy.json': '299396caa229f5cb680e12d1f0c895c1d35155d619e7dbf0a1fb6cdc3f302efc', 'pipeline/authorizations/experiment_first_20261021.json': '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8', 'pipeline/authorizations/server4_gpu1_20261030.json': '6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in EXPECTED}==EXPECTED
 mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 for n,h in CHECKS.items():assert sha(ROOT/n)==h,n
 return dict(EXPECTED)
