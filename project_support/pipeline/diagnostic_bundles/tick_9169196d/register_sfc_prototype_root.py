"""Root-only registration of one source prototype; no native or resource pass."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
PREP = HERE / 'new_candidate_prepare'
CID = 'hierarchy-synchronous-full-neighbor-composition'
EXP = 'M224-SFC'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--preparation-sha256')
    ap.add_argument('--review-sha256')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_REGISTRATION')
        return
    guard()
    assert sha(PREP / 'preparation.json') == a.preparation_sha256
    prep = u.read(PREP / 'preparation.json')
    assert prep['candidate_id'] == CID and prep['experiment_id'] == EXP
    assert (prep['source_file_count'], prep['model_file_count']) == (9, 8)
    assert all(prep[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit'))
    assert prep['base_reference_commit'] == u.SOURCE
    assert all(prep[k] == 'NOT_RUN' for k in ('native', 'resources', 'Torch_FP32_autograd'))
    for n, h in prep['prepared_file_hashes'].items():
        p = (PREP / n).resolve()
        assert p.is_relative_to(PREP.resolve()) and sha(p) == h, n
    for n, h in prep['source_files'].items():
        assert sha(PREP / 'staged_repository' / n) == h, n
    peer = HERE / 'sfc_source_independent_review.json'
    assert sha(peer) == a.review_sha256
    review = u.read(peer)
    assert review['candidate_id'] == CID and review['code_commit'] is None
    assert review['material_concerns'] == []
    assert u.ref(PREP / 'preparation.json') in review['anchors'].values()
    static = u.read(PREP / 'static_validation.json')
    assert static['status'] == 'PASS_SOFTWARE_ONLY_NOT_NATIVE'
    assert static['check_count'] >= 1 and static['Torch'] is False
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
        w = u.read(path)
        old = {c['id']: u.digest(c) for c in w['candidates']}
        assert len(old) == 149 and CID not in old
        assert not any(c.get('experiment_id') == EXP for c in w['candidates'])
        assert not (ROOT / 'pipeline/experiments' / (EXP + '.json')).exists()
        assert not (ROOT / 'pipeline/admissions' / (EXP + '.json')).exists()
        c = copy.deepcopy(u.read(PREP / 'candidate_record.json'))
        assert c['id'] == CID and c['stage'] == 'implementation'
        now = datetime.now(timezone.utc).isoformat()
        c.update(created_at=now, created_tick=EXPECTED['generated_at'],
                 source_preparation=u.ref(PREP / 'preparation.json'),
                 source_independent_review=u.ref(peer),
                 source_status='FROZEN_UNVERSIONED_SOFTWARE_CHECKED_PROTOTYPE',
                 native_status='NOT_RUN', resource_status='NOT_RUN',
                 native_execution_code_commit=None, queued=False,
                 required_server='server-4', required_physical_gpu=0)
        c['next_action'] = ('Preserve original AOC training and advance the existing FCB first. '
                            'Bind these exact nine unchanged prototype bytes to the actual '
                            'then-current compatible source parent and freeze native tools; '
                            'only on truly idle authorized GPU0 execute original matched '
                            'natural TRAIN2 and resources under fresh owner/original deadline. '
                            'No GPU1, sibling fast-forward, historical recovery or native PASS.')
        c['carryover_scope'] = ('Actual production-forward software results only. '
                                'Actual Git version, native tooling, Torch/autograd and GPU '
                                'tests remain outstanding; efficacy and novelty UNKNOWN.')
        for r in (u.ref(PREP / 'preparation.json'), u.ref(peer)):
            if r not in c['evidence']:
                c['evidence'].append(r)
        w['candidates'].append(c)
        w['updated_at'] = now
        w['last_event_tick'] = EXPECTED['generated_at']
        w['next_action'] = ('Preserve original AOC on GPU0; next native-capable reserve '
                            'is FCB. SFC is one unversioned software-checked source '
                            'implementation; GPU1 remains forbidden.')
        w['tick_attempt'] = {
            'tick_started_at': EXPECTED['generated_at'], 'candidate_id': CID,
            'kind': 'implementation_test', 'result': 'passed',
            'command': prep['static_check_command'],
            'observation': ('Actual production plan/forward AST carrier and original '
                            'integration software checks passed, independently reviewed. '
                            'Torch/autograd/native TRAIN/resources NOT_RUN.'),
            'evidence': [u.ref(PREP / 'static_validation.json')]}
        assert len(w['candidates']) == 150
        assert all(u.digest(x) == old[x['id']] for x in w['candidates'] if x['id'] != CID)
        u.save(HERE / 'sfc_registration_intent.json', {
            'owner': EXPECTED, 'research_work_before_sha256': before,
            'new_candidate_id': CID, 'source_preparation': u.ref(PREP / 'preparation.json'),
            'independent_review': u.ref(peer),
            'scope': 'One source-only candidate. Actual source/code/parent NULL; no Git, native, lifecycle, queue, receipt or launch mutation.'})
        guard()
        assert sha(path) == before
        u.atomic(path, w)
        u.primary_protection(b)
        u.lifecycle_protection(b)
        u.save(HERE / 'sfc_registration_result.json', {
            'owner': EXPECTED, 'status': 'ONE_SFC_SOURCE_PROTOTYPE_REGISTERED_NATIVE_NOT_RUN',
            'candidate_id': CID, 'experiment_id': EXP, 'candidate_count': 150,
            'new_candidates': 1, 'model_revisions': 0,
            'code_commit': None, 'source_commit': None, 'source_parent_commit': None,
            'other149_candidates_unchanged': True,
            'all28_lifecycle_and28_user_paths_and_index_preserved': True,
            'source_preparation': u.ref(PREP / 'preparation.json'),
            'independent_review': u.ref(peer)})
        print('One SFC source prototype registered; native/resources not run.')
    finally:
        lock.close()


if __name__ == '__main__':
    main()
