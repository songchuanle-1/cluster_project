"""Current immutable foreground owner/resource guard, no import-side effects."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project')
EXPECTED={'token': 'a6e82f44da954be096beeaef0a3755bc', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-30T08:07:36.868186+00:00', 'deadline_at': '2026-10-30T09:07:36.868186+00:00', 'context_sha256': '92328cba570e995a45b3f9f1f2afea593c76b3bd397f39fb70fb143a8400d723', 'pending_sha256': 'd09ab844ae1689008acf65b670499c2a2fe7ea0a4799e269df48b19739312ac2'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guard():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in EXPECTED}==EXPECTED
 mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text('utf8'));assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
 checks={'pipeline/headless/.tick_context.json':EXPECTED['context_sha256'],'pipeline/headless/.tick_context_state.next.json':EXPECTED['pending_sha256'],'pipeline/goal.json':'0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85','SERVERS.yaml':'19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265','pipeline/authorizations/experiment_first_20261021.json':'2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8','pipeline/authorizations/server4_gpu1_20261030.json':'6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2'}
 for p,h in checks.items():assert sha(ROOT/p)==h,p
 return {k:o[k] for k in EXPECTED}
