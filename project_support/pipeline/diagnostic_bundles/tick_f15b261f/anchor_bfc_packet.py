"""Readonly current foreground owner guard. No model or GPU operation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='f15b261f91d845788f9187e85e699762'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def guard():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    expected={'token':TOKEN,'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
        'generated_at':'2026-10-26T02:10:42.571429+00:00','deadline_at':'2026-10-26T03:10:42.571429+00:00',
        'context_sha256':'f4b9ce27ba27cd3e609a0301028b1b3bf4133a4967ae8e607fd76fd006ee6de0',
        'pending_sha256':'30f54a572a22fed635cafb12581bd8f71f36113f90859e8bd1d0d23e7c209846'}
    assert {k:owner.get(k) for k in expected}==expected
    mode=read(ROOT/'pipeline/execution_mode.json')
    assert mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==expected['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(expected['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==expected['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==expected['pending_sha256']
    assert sha(ROOT/'pipeline/goal.json')=='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
    assert sha(ROOT/'SERVERS.yaml')=='d5277972e80b6fe184a3e07f0fff34f7e1e7950b558d60905416ced302b206a2'
    assert sha(ROOT/'pipeline/authorizations/experiment_first_20261021.json')=='2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8'
    assert sha(ROOT/'pipeline/authorizations/server4_gpu1_20261025.json')=='90f8820a60ef4d4e277904815b025658f7b8b457b0711a4d0ef5f7395fdd23f8'
    return owner
if __name__=='__main__':raise SystemExit('READONLY_OWNER_GUARD_ONLY')
