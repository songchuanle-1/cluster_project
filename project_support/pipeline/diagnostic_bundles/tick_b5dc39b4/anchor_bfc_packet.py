"""Readonly current foreground owner guard. No model or GPU operation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
TOKEN='b5dc39b4780a44c6855520bc22692b65'
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def guard():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    expected={'token':TOKEN,'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
        'generated_at':'2026-10-25T22:11:14.827798+00:00','deadline_at':'2026-10-25T23:11:14.827798+00:00',
        'context_sha256':'7082c7c328d7e20f4ca107f32cd4df7929ffff12427ff0883774f2ec2f217f98',
        'pending_sha256':'63ff0e9d20d0877f4a3b4d8a790e1881fac5db412656a9fc83e755eb104f18cf'}
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
