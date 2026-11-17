"""Actual-child private writer guard. Never invokes or claims the root guard."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
EXPECTED={'token': '265517f1c8984940a6925367924f062f', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-04T15:32:34.093174+00:00', 'deadline_at': '2026-11-04T16:32:34.093174+00:00', 'context_sha256': '2fb717f78660eeaa567660d1efa0937d3e27b4322a564d60b50b4971de1f58cf', 'pending_sha256': '92e42ef9d828bbc2440ed6e2297a673a4fce7b1b03bae8b342aa77871395f5c9'}
CHECKS={'pipeline/goal.json': '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85', 'SERVERS.yaml': 'f046762ec6e87321a70d2595cf35e52fa6e57b3f4aa585ab1fedbf624ae7ef6c', 'pipeline/execution_mode.json': '9eee762e94931ad0788895edd5b80641919069583d5d4e96681260300f85fa51', 'pipeline/closure_policy.json': '299396caa229f5cb680e12d1f0c895c1d35155d619e7dbf0a1fb6cdc3f302efc', 'pipeline/authorizations/experiment_first_20261021.json': '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8', 'pipeline/headless/.tick_context.json': '2fb717f78660eeaa567660d1efa0937d3e27b4322a564d60b50b4971de1f58cf', 'pipeline/headless/.tick_context_state.next.json': '92e42ef9d828bbc2440ed6e2297a673a4fce7b1b03bae8b342aa77871395f5c9'}
CHILD='01a15a3d-3c65-78b3-9ac7-57d0423dcc6e'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def author_guard():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf-8-sig'))
    assert {k:owner.get(k) for k in EXPECTED}==EXPECTED, 'root owner changed'
    mode=json.loads((ROOT/'pipeline/execution_mode.json').read_text(encoding='utf-8-sig'))
    assert mode=={'mode':'foreground','target_thread_id':EXPECTED['thread_id']}
    assert os.environ.get('CODEX_THREAD_ID')==CHILD and CHILD!=EXPECTED['thread_id']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED['deadline_at'])
    for name,digest in CHECKS.items():
        assert sha(ROOT/name)==digest, name
    anchor=HERE.parent/'anchor.py'
    if anchor.exists():
        values={}
        for node in ast.parse(anchor.read_text(encoding='utf-8-sig')).body:
            if isinstance(node,ast.Assign):
                for target in node.targets:
                    if isinstance(target,ast.Name) and target.id in ('EXPECTED','CHECKS'):
                        values[target.id]=ast.literal_eval(node.value)
        assert values.get('EXPECTED') and values.get('CHECKS')
        assert {k:owner.get(k) for k in values['EXPECTED']}==values['EXPECTED']
        for name,digest in values['CHECKS'].items():
            assert sha(ROOT/name)==digest, name
    return {'actual_child_thread_id':CHILD,'root_thread_id':EXPECTED['thread_id'],
            'root_owner_token':EXPECTED['token'],'root_guard_pass_claimed':False,
            'root_guard_called':False,'root_environment_impersonated':False,
            'root_anchor_present':anchor.exists(),'checked_at':datetime.now(timezone.utc).isoformat()}
def write_bytes(path,content):
    author_guard()
    path=Path(path).resolve()
    assert path.is_relative_to(HERE.resolve()) and path!=HERE.resolve()
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)
    author_guard()
    return path
def write_text(path,content):
    return write_bytes(path,content.encode('utf-8'))
def write_json(path,data):
    return write_text(path,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
