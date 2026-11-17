"""Publish reviewed same-source HRC execution metadata; never touch remote jobs."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN = '37695e94da4a485c8979d474d3f33b39'
THREAD = '01a159c5-29ab-7a22-ba7f-e79174757253'
OLD = '9e543af623acd7fa9bd4a3f81ce79c932e98774a'
NEW = '74fcd21df0af9a971792038ffe251af1ffea2604'
CID = 'hierarchy-bottom-up-refined-token-composition'
NATIVE = HERE/'hrc_native_prepare_head74f'
ADAPTER = HERE/'hrc_execution_adapter_head74f'
ANCHORS = {
    'hrc_native_prepare_head74f/preparation.json': '87ef65ab7ac065688879bc0587a26ef1704d001a8190086ba55b2d005f6ae8e1',
    'hrc_execution_adapter_head74f/preparation.json': 'f2ed5b65c0d673ec1ef38ed67fc52905aac9e6a1c1cdfd8b0145ac0978e8395a',
    'hrc_execution_adapter_head74f/adapter_release.json': '7aa68337a4aa653e4bc55d0fff2c4e0a1fa84ac3fda7d968732ddd1bf93c1b23',
    'hrc_native_prepare_head74f/worker.py': '37782c1ae1ea9cb2f7bb77d59c7b8aff926438fbac827106f94d8c8fa396ef01',
    'hrc_native_prepare_head74f/native_runtime.py': 'cd71a8be1a91988931ee147aadd86a4f9d0e10f23f938c49df2ecbdfc46f3943',
    'hrc_native_prepare_head74f/manifest_template.json': '41ed6ca1e60b61eaaa0a379c930e457eb7b09d5d9abaebc59143867864346bec',
    'hrc_execution_adapter_head74f/adapter.py': 'e061cb634d167dc71c641908113522e47995bcae532dde29c936153dbf9f1eda',
    'hrc_execution_adapter_head74f/remote_ops.py': '78e5035e55b4e580912049d729d2888b7f5b4604231fa7d054cdf1ce0db62c6b',
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}


def write(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.37695e94.tmp')
    assert not tmp.exists()
    with tmp.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def verify_owner():
    owner = read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    mode = read(ROOT/'pipeline/execution_mode.json')
    assert owner['token'] == TOKEN
    assert owner['thread_id'] == mode['target_thread_id'] == os.environ.get('CODEX_THREAD_ID') == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json') == owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json') == owner['pending_sha256']
    return owner


def main():
    # Review hash is supplied by root only after reading the independent verdict.
    review_path = HERE/'hrc_forward_binding_independent_review.json'
    assert len(sys.argv) == 2 and sha(review_path) == sys.argv[1]
    assert review_path.is_file()
    review = read(review_path)
    assert review['status'] == 'INDEPENDENT_FORWARD_BINDING_STATIC_AND_OFFLINE_PASS_NATIVE_NOT_RUN'
    assert review['blocking_findings'] == []
    assert review['independent_static_checks']['all_pass'] is True
    assert review['offline_validation']['independent_fresh_run']['count'] == 31
    assert review['offline_validation']['independent_fresh_run']['passed'] is True
    assert sha(HERE/'hrc_forward_independent_fixture_run.json') == 'b09164d26610330c9f81644fb425c77d548811499908fde5b8deb5a1847bbf21'
    for rel, expected in ANCHORS.items():
        assert sha(HERE/rel) == expected, rel
    for folder in (NATIVE, ADAPTER):
        prep = read(folder/'preparation.json')
        assert prep['source_commit'] == NEW and prep['candidate_id'] == CID
        for name, expected in prep['prepared_file_hashes'].items():
            assert sha(folder/name) == expected, name
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT/'Cluster', text=True).strip() == NEW
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT/'Cluster', text=True).strip()
    owner = verify_owner()
    sys.path.insert(0, str(SKILL))
    import pipeline_monitor as monitor
    lock = monitor.acquire_lock(str(ROOT))
    assert lock is not None, 'Canonical project lock is busy'
    try:
        verify_owner()
        work_path = ROOT/'pipeline/research_work.json'
        work = read(work_path)
        candidates = work['candidates']
        candidate = next(c for c in candidates if c['id'] == CID)
        before = copy.deepcopy(candidate)
        assert candidate['code_commit'] == OLD
        assert not candidate.get('revision_history') and not candidate.get('implementation_revision_sha256')
        assert candidate['stage'] == 'blocked' and candidate['resume_stage'] == 'validation'
        assert candidate['blocker_kind'] == 'exclusive_gpu_slot'
        assert candidate['scientific_admission'] is False
        assert candidate['native_status'].startswith('NOT_RUN') and candidate['resource_status'].startswith('NOT_RUN')
        protected = {name: sha(ROOT/'pipeline'/name) for name in ('queue.json', 'running.json', 'experiments/M207-HAP.json', 'experiments/M206-CGCA.json')}
        other_before = {c['id']: copy.deepcopy(c) for c in candidates if c['id'] != CID}
        now = datetime.now(timezone.utc).isoformat()
        history = candidate.setdefault('version_binding_history', [])
        assert not history, 'Forward binding was already activated; no replay'
        history.append({
            'recorded_at': now, 'kind': 'same_source_forward_binding',
            'from_code_commit': OLD, 'to_code_commit': NEW,
            'original_worker_preparation': copy.deepcopy(candidate['worker_preparation']),
            'original_execution_adapter': copy.deepcopy(candidate['execution_adapter']),
            'lineage': ref(HERE/'hrc_commit_lineage.json'),
            'dispatch_binding_audit': ref(HERE/'hrc_dispatch_binding_audit.json'),
            'independent_forward_review': ref(review_path),
            'model_revision': False, 'old_raw_results_relabelled': False,
            'reason': 'Canonical fresh dispatch requires current local HEAD. Only nine PSBR additions separate commits; all HRC source/YAML/worker bytes unchanged. New real native evidence still required.'
        })
        candidate['code_commit'] = NEW
        candidate['worker_preparation'] = {
            'status': 'PREPARED_UNEXECUTED',
            'preparation': ref(NATIVE/'preparation.json'), 'worker': ref(NATIVE/'worker.py'),
            'runtime': ref(NATIVE/'native_runtime.py'), 'manifest_template': ref(NATIVE/'manifest_template.json'),
            'root_static_validation': ref(NATIVE/'static_validation.json'),
            'independent_review': ref(review_path),
            'active_native_manifest_or_execution_lease_created': False,
            'native_backward_executed': False, 'resource_profile_executed': False,
        }
        candidate['execution_adapter'] = {
            'status': 'PREPARED_UNEXECUTED',
            'preparation': ref(ADAPTER/'preparation.json'), 'release': ref(ADAPTER/'adapter_release.json'),
            'adapter': ref(ADAPTER/'adapter.py'), 'remote_ops': ref(ADAPTER/'remote_ops.py'),
            'README': ref(ADAPTER/'README.md'),
            'preparer_offline_tests': ref(ADAPTER/'offline_validation.json'),
            'independent_tests': ref(HERE/'hrc_forward_independent_fixture_run.json'),
            'root_review': ref(review_path), 'external_anchor_required': True,
            'standard_result_formatter_implemented': False, 'native_execution_tested': False,
            'remote_adapter_execution_tested': False, 'active_binding_manifest_lease_created': False,
            'provenance': 'Root verified exact independently reviewed new74f external anchors. Original9e binding retained in version_binding_history/evidence. New actual native/resources/pairing NOT_RUN; future fresh owner/deadline/idle GPU0 required.'
        }
        evidence_paths = [
            HERE/'hrc_commit_lineage.json', HERE/'hrc_dispatch_binding_audit.json', review_path,
            HERE/'hrc_forward_independent_fixture_run.json',
            NATIVE/'preparation.json', NATIVE/'static_validation.json', NATIVE/'manifest_template.json',
            NATIVE/'native_runtime.py', NATIVE/'worker.py', ADAPTER/'preparation.json',
            ADAPTER/'adapter_release.json', ADAPTER/'adapter.py', ADAPTER/'remote_ops.py',
            ADAPTER/'offline_validation.json', ADAPTER/'port_validation.json',
        ]
        for path in evidence_paths:
            item = ref(path)
            if item not in candidate['evidence']:
                candidate['evidence'].append(item)
        candidate['next_action'] = (
            'Current74f same-source binding is prepared and externally anchored; no native PASS or admission. '
            'Wait for HAP natural completion and real authorized physicalGPU0 idle/UUID/exclusive locks; GPU1 remains released and M206 paused. '
            'Before invocation verify candidate exact new preparation/release/source anchors and fresh actual owner/context/pending/goal/current whitelist/original deadline. '
            'Create a new execution binding/manifest/lease/isolated stage only on available GPU0, then obtain four real M95/HRC TRAIN2 and original-resource results. '
            'Reconcile uncertain exact request/PID/startticks/argv/result without replay/kill/lease renewal. '
            'Audit real losses/backward/FFN/mean/dependency controls, both TRAIN input/init fingerprints and original profiler/unsupported/memory scopes; '
            'produce actual canonical native_smoke/resource summaries and closure.admission receipt bound74f before canonical queue/dispatch; '
            'fresh dispatch must still see localHEAD74f and safe source/assets/remote fast-forward only after the live HAP checkout is no longer in use. Efficacy UNKNOWN.'
        )
        m206 = next(c for c in candidates if c.get('experiment_id') == 'M206-CGCA')
        assert m206.get('human_hold') is True and m206.get('resume_authorized') is False
        boundary = ref(HERE/'continuation_boundary_check.json')
        if boundary not in m206['evidence']:
            m206['evidence'].append(boundary)
        m206['last_authorization_boundary_checked_at'] = now
        m206['retry_after'] = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
        assert {k:v for k,v in m206.items() if k not in ('evidence', 'last_authorization_boundary_checked_at', 'retry_after')} == {k:v for k,v in other_before[m206['id']].items() if k not in ('evidence', 'last_authorization_boundary_checked_at', 'retry_after')}
        for c in candidates:
            if c['id'] not in (CID, m206['id']):
                assert c == other_before[c['id']]
        work['updated_at'] = now
        work['next_action'] = 'Monitor original-protocol resumed HAP on GPU0. M206 remains human-paused and GPU1 excluded. New independently reviewed HRC74f execution metadata now matches local HEAD; real native/resource checks remain blocked by HAP. Prefer HRC then PSBR on a genuine idle GPU0 after exact current guards; preserve all old holds/budgets/bans.'
        assert {name: sha(ROOT/'pipeline'/name) for name in protected} == protected
        write(HERE/'hrc_candidate_before_forward_binding.json', before)
        write(work_path, work)
        result = {
            'recorded_at': now, 'owner_token': TOKEN, 'candidate_id': CID,
            'from_code_commit': OLD, 'to_code_commit': NEW,
            'external_anchors_verified': ANCHORS, 'independent_review': ref(review_path),
            'same_source_not_model_revision': True, 'old_binding_preserved': True,
            'old_evidence_refs_preserved': all(x in candidate['evidence'] for x in before['evidence']),
            'HAP_M206_queue_running_experiment_bytes_unchanged': {name: sha(ROOT/'pipeline'/name) == expected for name, expected in protected.items()},
            'M206_only_evidence_retry_updated_no_new_resume_authorization': True,
            'PSBR_and_other_non_M206_candidates_unchanged': True,
            'native_smoke': 'NOT_RUN', 'resources': 'NOT_RUN', 'actual_pairing': 'NOT_RUN',
            'admission_receipt_or_queue_created': False, 'SSH_GPU_sync_source_changes': False,
        }
        assert all(result['HAP_M206_queue_running_experiment_bytes_unchanged'].values())
        write(HERE/'hrc_forward_binding_activation.json', result)
        print(json.dumps({'activated': True, 'candidate_id': CID, 'code_commit': NEW, 'evidence': ref(HERE/'hrc_forward_binding_activation.json')}, ensure_ascii=False))
    finally:
        lock.close()


if __name__ == '__main__':
    main()
