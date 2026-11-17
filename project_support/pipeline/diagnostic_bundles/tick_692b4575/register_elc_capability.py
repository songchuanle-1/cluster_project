"""Register an existing conditional source and tooling, without native execution."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, os, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'elc_native_prepare'
OP = HERE / 'elc_operational_prepare'
PREP = ROOT / 'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
CID = 'hierarchy-undirected-edge-state-line-graph-composition'
EXP = 'M225-ELC'
COMMIT = '18e64b8d95ed0ba5c1053ead114c0f91a4b0c324'
PARENT = 'c9be548699cd66bf68badff9ae6198a03eafa142'


def verify(path):
    value = u.read(path)
    for n, h in value['prepared_file_hashes'].items():
        p = (path.parent / n).resolve()
        assert p.is_relative_to(path.parent.resolve()) and sha(p) == h, n
    return value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--native-sha256')
    ap.add_argument('--operational-sha256')
    ap.add_argument('--review-sha256')
    ap.add_argument('--source-review-sha256')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_REGISTRATION')
        return
    guard()
    assert sha(PREP / 'preparation.json') == 'c77746ae35e4f3bfbc1c58e62aff629798946bb91dd0befbd08f247ca5dd7dd8'
    proto = verify(PREP / 'preparation.json')
    assert all(proto[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit'))
    version = HERE / 'elc_version_prepare/isolated_source_version.json'
    assert sha(version) == 'c1950ac3eb158ad5aaf4c5a034f6de39125da360fc66e22bae81d0d3295196b1'
    v = u.read(version)
    assert v['code_commit'] == COMMIT and v['parent_commit'] == PARENT
    assert v['diff_exact9A'] is True and v['frozen_source_files'] == proto['source_files']
    source_peer = HERE / 'elc_actual_source_version_independent_review.json'
    assert sha(source_peer) == a.source_review_sha256
    assert u.read(source_peer)['material_concerns'] == []
    assert sha(NATIVE / 'preparation.json') == a.native_sha256
    assert sha(OP / 'preparation.json') == a.operational_sha256
    n = verify(NATIVE / 'preparation.json')
    op = verify(OP / 'preparation.json')
    assert n['source_commit'] == op['code_commit'] == COMMIT
    assert n['source_parent_commit'] == n['runtime_expected_commit'] == PARENT
    assert op['source_parent_commit'] == op['expected_runtime_code_commit'] == PARENT
    assert n['source_files'] == proto['source_files']
    assert n['draft_execution_disabled'] is False and op['draft_execution_disabled'] is False
    peer = HERE / 'elc_native_operational_preparation_independent_review.json'
    assert sha(peer) == a.review_sha256
    review = u.read(peer)
    assert review['candidate_id'] == CID and review['code_commit'] == COMMIT
    assert review['material_concerns'] == []
    assert all(r in review['anchors'].values() for r in (u.ref(NATIVE / 'preparation.json'), u.ref(OP / 'preparation.json')))
    manifest = u.read(NATIVE / 'manifest_template.json')
    assert all(manifest[k] is None for k in ('current_token', 'stage', 'tick_generated_at', 'deadline_at', 'physical_gpu', 'gpu_uuid', 'allowed_gpus', 'context_sha256', 'pending_sha256', 'runtime_code_commit'))
    release = u.read(OP / 'release_template.json')
    assert release['code_commit'] == COMMIT and release['candidate_id'] == CID
    assert release['native_preparation_sha256'] == sha(NATIVE / 'preparation.json')
    assert release['source_hashes'] == {k: sha(OP / k) for k in ('adapter.py', 'remote_ops.py')}
    assert not any(p.exists() for p in (OP / 'adapter_release.json', HERE / 'elc_execution', HERE / 'elc_registration_intent.json', HERE / 'elc_registration_result.json'))
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        b = u.read(HERE / 'protected_assets_before.json')
        u.primary_protection(b)
        u.lifecycle_protection(b)
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 151
        c = next(c for c in work['candidates'] if c['id'] == CID)
        assert c['experiment_id'] == EXP and c['stage'] == 'implementation' and c['code_commit'] is None
        assert not any((ROOT / 'pipeline' / area / (EXP + '.json')).exists() for area in ('admissions', 'experiments'))
        now = datetime.now(timezone.utc).isoformat()
        release_ref = {'path': (OP / 'adapter_release.json').relative_to(ROOT).as_posix(), 'sha256': sha(OP / 'release_template.json')}
        c.update(stage='validation', code_commit=COMMIT, source_commit=COMMIT,
                 source_parent_commit=PARENT, future_version_parent=PARENT,
                 source_version=u.ref(version), actual_source_version_independent_review=u.ref(source_peer),
                 source_status='ISOLATED_SOURCE_AND_STATIC_TOOLS_CONDITIONAL_ON_TESTED_PARENT_PROMOTION',
                 native_status='NOT_RUN_PARENT_NOT_PROMOTED', resource_status='NOT_RUN_GPU0_OCCUPIED',
                 native_execution_code_commit=None, queued=False, required_server='server-4', required_physical_gpu=0)
        c['worker_preparation'] = {
            'status': 'STATIC_REVIEWED_CONDITIONAL_CAPABILITY_NATIVE_NOT_RUN',
            'preparation': u.ref(NATIVE / 'preparation.json'), 'worker': u.ref(NATIVE / 'worker.py'),
            'runtime': u.ref(NATIVE / 'native_runtime.py'), 'manifest_template': u.ref(NATIVE / 'manifest_template.json'),
            'source_commit': COMMIT, 'source_parent_commit': PARENT, 'runtime_expected_commit': PARENT,
            'independent_review': u.ref(peer), 'native_backward_executed': False,
            'resource_profile_executed': False, 'active_native_manifest_or_execution_lease_created': False}
        c['execution_adapter'] = {
            'status': 'STATIC_REVIEWED_PARENT_PROMOTION_FENCED_NATIVE_NOT_RUN',
            'preparation': u.ref(OP / 'preparation.json'), 'release': release_ref,
            'independent_review': u.ref(peer), 'active_binding_manifest_lease_created': False, 'transport_executed': False}
        c['current_version_compatibility'] = {
            'current_source_commit': COMMIT, 'current_parent_commit': PARENT, 'runtime_expected_commit': PARENT,
            'current_primary_and_runtime': u.SOURCE, 'status': 'CONDITIONAL_PARENT_NOT_PROMOTED',
            'parent_source_version': u.ref(ROOT / 'pipeline/diagnostic_bundles/tick_928313fd/sfc_version_prepare/isolated_source_version.json'),
            'scope': ('Current main/runtime0314 remain. Mutation requires genuine M224-SFC/c9 technical receipt, actual primary c9 and remote runtime c9 before transport or active state, then fresh authorized idle GPU0/all three locks/original deadline. '
                      'No SFC training completion or efficacy gate. If SFC is not promoted or main changes, preserve this conditional source and save/test an actually compatible unchanged-nine version; no blind cumulative27A or sibling ff.')}
        c['carryover_scope'] = ('Existing ELC now has actual isolated source and conditional static native tools. Originalc777 NULL/reference0314 stay frozen; native TRAIN/resources/admission outstanding.')
        c['next_action'] = ('Preserve original AOC GPU0 training and existing FCB/SFC order. FCB runs original native checks only after genuinely idle GPU0. ELC may run original paired natural TRAIN2/resources only after genuine M224-SFC technical admission and actual local main/remote runtime c9 promotion, with fresh owner/original deadline/assets/all three locks and idle GPU0. '
                            'If parent/main differs, preserve originals and save/test an actually compatible unchanged-nine version. No GPU1, old recovery, blind0314-to-18e cumulative27A or sibling ff.')
        for r in (u.ref(version), u.ref(source_peer), u.ref(NATIVE / 'preparation.json'), u.ref(OP / 'preparation.json'), u.ref(peer), release_ref, n['static_validation']):
            if r not in c['evidence']:
                c['evidence'].append(r)
        work['updated_at'] = now
        work['last_event_tick'] = EXPECTED['generated_at']
        work['next_action'] = c['next_action']
        work['tick_attempt'] = {
            'tick_started_at': EXPECTED['generated_at'], 'candidate_id': CID,
            'kind': 'implementation_test', 'result': 'passed', 'command': n['static_check_command'],
            'observation': 'Actual bounded software checks of ELC observer transparency, missing active-manifest early refusal, dynamic common schema and conditional version guards. No Torch/native/autograd/resources; current main/runtime0314 have not promoted SFCc9.',
            'evidence': [n['static_validation']]}
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] != CID)
        u.save(HERE / 'elc_registration_intent.json', {
            'owner': EXPECTED, 'research_work_before_sha256': before, 'candidate_id': CID,
            'source_version': u.ref(version), 'native_preparation': u.ref(NATIVE / 'preparation.json'),
            'operational_preparation': u.ref(OP / 'preparation.json'), 'independent_review': u.ref(peer),
            'release': release_ref, 'scope': 'Existing candidate only, exact unchanged9 source; no model revision, new candidate, native, primary/runtime, lifecycle, queue or launch mutation.'})
        guard()
        assert sha(path) == before
        with (OP / 'adapter_release.json').open('xb') as f:
            f.write((OP / 'release_template.json').read_bytes())
            f.flush()
            os.fsync(f.fileno())
        assert sha(OP / 'adapter_release.json') == release_ref['sha256']
        u.atomic(path, work)
        u.primary_protection(b)
        u.lifecycle_protection(b)
        u.save(HERE / 'elc_registration_result.json', {
            'owner': EXPECTED, 'status': 'EXISTING_ELC_CONDITIONAL_CAPABILITY_REGISTERED_NATIVE_NOT_RUN',
            'candidate_id': CID, 'experiment_id': EXP, 'code_commit': COMMIT, 'parent_commit': PARENT,
            'primary_runtime': u.SOURCE, 'candidate_count': 151, 'new_candidates': 0, 'model_revisions': 0,
            'source_versions': 1, 'other150_candidates_unchanged': True,
            'all28_lifecycle_and28_user_paths_and_index_preserved': True,
            'release': release_ref, 'native_preparation': u.ref(NATIVE / 'preparation.json'),
            'operational_preparation': u.ref(OP / 'preparation.json'), 'independent_review': u.ref(peer)})
        print('Existing ELC conditional source and tooling registered; actual parent not promoted; native NOT_RUN.')
    finally:
        lock.close()


if __name__ == '__main__':
    main()
