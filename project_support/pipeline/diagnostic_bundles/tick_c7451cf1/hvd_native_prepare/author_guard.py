"""Actual-child private writer guard. Never invokes or claims the root guard."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
EXPECTED={'token': 'c7451cf19cec4fc5aa23d2984eb0a249', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-11-04T17:11:17.373995+00:00', 'deadline_at': '2026-11-04T18:11:17.373995+00:00', 'context_sha256': 'f0c58a6071231640baaeec3cda1f21eb851f1d79c77be602dc04ba1feb638afb', 'pending_sha256': '4a4437aee29ce2e814c170b89a07511e56552a8a9d71fec57aed927898f50de5'}
CHECKS={'pipeline/goal.json': '0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85', 'SERVERS.yaml': 'f046762ec6e87321a70d2595cf35e52fa6e57b3f4aa585ab1fedbf624ae7ef6c', 'pipeline/execution_mode.json': '9eee762e94931ad0788895edd5b80641919069583d5d4e96681260300f85fa51', 'pipeline/closure_policy.json': '299396caa229f5cb680e12d1f0c895c1d35155d619e7dbf0a1fb6cdc3f302efc', 'pipeline/authorizations/experiment_first_20261021.json': '2e892959dc60e66367401b1f0d01609ccfef0fbe331f8a9b265bb03e35053ce8', 'pipeline/authorizations/server4_gpu0_overlay_20261104.json': '783ffc27d48872940c2e15adcb85f6bb5f9b94492a8abd88694799f483d20e88', 'pipeline/headless/.tick_context.json': 'f0c58a6071231640baaeec3cda1f21eb851f1d79c77be602dc04ba1feb638afb', 'pipeline/headless/.tick_context_state.next.json': '4a4437aee29ce2e814c170b89a07511e56552a8a9d71fec57aed927898f50de5', 'pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native/worker.py': '5bdaa5532dd9b794b8e215caac81e1bef1e3ba1c2b654f7dd68fe33106c60348', 'pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native/native_runtime.py': '20fdf514a2928ddf72ee29f97a1eb714517f781336bff204ef24943bc7557ea6', 'pipeline/diagnostic_bundles/tick_265517f1/mic_gpu0_overlay_prepare/native/manifest_template.json': '2ce9532e9861b9f7bb23b0106987caa04a8cd956606c8a0e61993f37c315e345', 'pipeline/diagnostic_bundles/tick_265517f1/hvd_version_prepare/isolated_source_version.json': 'fd2d1a2338f865e0647d6e5983107fa790d8846b34e20c3f50f0d9e24354ef96', 'pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/source_manifest.json': '2b57b60a778fc3eb7fa9799dd46cafa8c5ef482871d4e1fcfb0105edecec0411', 'pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/FROZEN.json': '931a2b02b51dbf43a89efbd6128f42e2672c8fe86314bfa387edc54a0aff4112', 'pipeline/diagnostic_bundles/tick_265517f1/new_candidate_prepare/native_protocol.md': 'afa18d714089d39d82e0d56a016f80cc21592a8b8a7c4f792d753dc981fee5dd'}
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
