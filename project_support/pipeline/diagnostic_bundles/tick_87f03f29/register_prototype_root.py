"""Register one actually prepared and reviewed source-only prototype."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
PREP = HERE / 'new_candidate_prepare'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-root', action='store_true')
    parser.add_argument('--candidate-id')
    parser.add_argument('--experiment-id')
    parser.add_argument('--preparation-sha256')
    parser.add_argument('--review')
    parser.add_argument('--review-sha256')
    args = parser.parse_args()
    if not args.execute_root:
        print('DEFAULT_NO_REGISTRATION')
        return
    guard()
    cid, exp = args.candidate_id, args.experiment_id
    assert isinstance(cid, str) and cid.startswith('hierarchy-') and exp.startswith('M225-')
    assert sha(PREP / 'preparation.json') == args.preparation_sha256
    prep = u.read(PREP / 'preparation.json')
    assert prep['candidate_id'] == cid and prep['experiment_id'] == exp
    assert (prep['source_file_count'], prep['model_file_count']) == (9, 8)
    assert all(prep[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit'))
    assert prep['base_reference_commit'] == u.SOURCE
    assert all(prep[k] == 'NOT_RUN' for k in ('native', 'resources', 'Torch_FP32_autograd'))
    for n, h in prep['prepared_file_hashes'].items():
        p = (PREP / n).resolve()
        assert p.is_relative_to(PREP.resolve()) and sha(p) == h, n
    for n, h in prep['source_files'].items():
        assert sha(PREP / 'staged_repository' / n) == h, n
    peer = (HERE / args.review).resolve()
    assert peer.is_relative_to(HERE.resolve()) and sha(peer) == args.review_sha256
    review = u.read(peer)
    assert review['candidate_id'] == cid and review['code_commit'] is None
    assert review['material_concerns'] == [] and u.ref(PREP / 'preparation.json') in review['anchors'].values()
    static = u.read(PREP / 'static_validation.json')
    assert static['status'] == 'PASS_SOFTWARE_ONLY_NOT_NATIVE' and static['check_count'] >= 1 and static['Torch'] is False
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        baseline = u.read(HERE / 'protected_assets_before.json')
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 150 and cid not in old
        assert not any(c.get('experiment_id') == exp for c in work['candidates'])
        assert not any((ROOT / 'pipeline' / area / (exp + '.json')).exists() for area in ('experiments', 'admissions'))
        c = copy.deepcopy(u.read(PREP / 'candidate_record.json'))
        assert c['id'] == cid and c['experiment_id'] == exp and c['stage'] == 'implementation'
        now = datetime.now(timezone.utc).isoformat()
        c.update(created_at=now, created_tick=EXPECTED['generated_at'],
                 source_preparation=u.ref(PREP / 'preparation.json'), source_independent_review=u.ref(peer),
                 source_status='FROZEN_UNVERSIONED_SOFTWARE_CHECKED_PROTOTYPE', native_status='NOT_RUN', resource_status='NOT_RUN',
                 native_execution_code_commit=None, queued=False, required_server='server-4', required_physical_gpu=0)
        c['next_action'] = ('Preserve original AOC training and existing FCB/SFC order. Save these unchanged nine prototype source bytes '
                            'on the actual then-compatible source parent and prepare the original matched natural TRAIN2/resources tools. '
                            'Only truly idle authorized physicalGPU0/fresh owner/original deadline/assets/three locks allow native work. '
                            'No GPU1, sibling/cumulative fast-forward, old recovery or assumed native/efficacy PASS.')
        c['carryover_scope'] = ('Only source-level production plan/forward software and integration checks. Actual Git version, '
                                'native tools, Torch/FP32/autograd, resources and training remain outstanding; efficacy/novelty UNKNOWN.')
        for ref in (u.ref(PREP / 'preparation.json'), u.ref(peer), u.ref(PREP / 'static_validation.json')):
            if ref not in c['evidence']:
                c['evidence'].append(ref)
        work['candidates'].append(c)
        work.update(updated_at=now, last_event_tick=EXPECTED['generated_at'],
                    next_action='Preserve original AOC/GPU0. Existing FCB is first for native checks; SFC is conditional on real FCB parent promotion. One new unversioned source prototype awaits actual compatible version/native checks; GPU1 forbidden.')
        work['tick_attempt'] = {'tick_started_at': EXPECTED['generated_at'], 'candidate_id': cid,
            'kind': 'implementation_test', 'result': 'passed', 'command': prep['static_check_command'],
            'observation': 'Actual bounded production-plan/forward carrier and original integration software checks, independently reviewed. No Torch/autograd/native TRAIN/resource execution.',
            'evidence': [u.ref(PREP / 'static_validation.json')]}
        assert len(work['candidates']) == 151 and all(u.digest(c) == old[c['id']] for c in work['candidates'] if c['id'] != cid)
        u.save(HERE / 'new_variant_registration_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'new_candidate_id': cid, 'source_preparation': u.ref(PREP / 'preparation.json'), 'independent_review': u.ref(peer),
            'scope': 'One source-only prototype; NULL actual commits. No Git/native/lifecycle/queue/receipt or launch.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        u.save(HERE / 'new_variant_registration_result.json', {'owner': EXPECTED,
            'status': 'ONE_SOURCE_PROTOTYPE_REGISTERED_NATIVE_NOT_RUN', 'candidate_id': cid, 'experiment_id': exp,
            'candidate_count': 151, 'new_candidates': 1, 'model_revisions': 0, 'code_commit': None, 'source_commit': None,
            'source_parent_commit': None, 'other150_candidates_unchanged': True,
            'all28_lifecycle_and28_user_paths_and_index_preserved': True,
            'source_preparation': u.ref(PREP / 'preparation.json'), 'independent_review': u.ref(peer)})
        print({'status': 'One source-only prototype registered; native/resources NOT_RUN', 'candidate_id': cid})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
