"""Record disabled AOC tooling and its corrected static interface only."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
CID = 'hierarchy-ancestral-order-commutator-composition'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--review-sha256')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_RECORD_MUTATION')
        return
    guard()
    original = HERE / 'aoc_promotion_prepare/preparation.json'
    original_peer = HERE / 'aoc_promotion_static_independent_review.json'
    prep_path = HERE / 'aoc_promotion_prepare_r1/preparation.json'
    peer = HERE / 'aoc_promotion_r1_static_independent_review.json'
    assert sha(original) == 'd3a34fccfedc91a770f7ade2e10c139f60ab17f30d5d550f9443e055d854e816'
    assert sha(original_peer) == 'd66a9ef104fea6d282aec48894b930293166525fb4ef30a50b852976b758cb7d'
    assert sha(prep_path) == '38abf859f7ba669238f45a46c7cee654020be05b690caa60b5b0ad240d49522c'
    assert sha(peer) == a.review_sha256
    prep = u.read(prep_path)
    review = u.read(peer)
    assert prep['candidate_id'] == review['candidate_id'] == CID
    assert review['material_concerns'] == []
    assert prep['code_commit'] == '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'
    assert prep['source_parent_commit'] == u.SOURCE
    assert prep['draft_execution_disabled'] is True
    assert all(prep[k] is None for k in ('actual_independent_review', 'actual_four_result_review', 'actual_raw_results'))
    assert prep['model_or_implementation_revision_created'] is False
    assert prep['supersedes_preparation'] == u.ref(original)
    for n, h in prep['prepared_file_hashes'].items():
        p = (prep_path.parent / n).resolve()
        assert p.is_relative_to(prep_path.parent.resolve()) and sha(p) == h, n
    for ref in (prep['source_bindings'], prep['evidence_bindings'], prep['static_validation']):
        assert sha(ROOT / ref['path']) == ref['sha256']
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
        c = next(c for c in work['candidates'] if c['id'] == CID)
        assert c['stage'] == 'blocked' and c['blocker_kind'] == 'exclusive_gpu_slot'
        assert c['code_commit'] == prep['code_commit']
        original_revision = c.get('implementation_revisions', 0)
        c['promotion_preparation'] = {
            'recorded_at': datetime.now(timezone.utc).isoformat(),
            'preparation': u.ref(prep_path), 'static_independent_review': u.ref(peer),
            'superseded_preparation': u.ref(original),
            'superseded_static_interface_failure_review': u.ref(original_peer),
            'scope': ('Disabled five-helper preparation only; original static schema '
                      'typo retained and corrected in a sibling package. No model '
                      'revision, native/resource pass, admission or active execution.')}
        for r in (u.ref(original), u.ref(original_peer), u.ref(prep_path), u.ref(peer)):
            if r not in c['evidence']:
                c['evidence'].append(r)
        assert c.get('implementation_revisions', 0) == original_revision
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] != CID)
        work['updated_at'] = datetime.now(timezone.utc).isoformat()
        u.save(HERE / 'aoc_promotion_record_intent.json', {
            'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [CID], 'preparation': u.ref(prep_path),
            'static_review': u.ref(peer), 'scope': 'Static preparation reference only; preserve the current actual GPU0 resource wait.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        u.primary_protection(baseline)
        u.lifecycle_protection(baseline)
        u.save(HERE / 'aoc_promotion_record_result.json', {
            'owner': EXPECTED, 'status': 'DISABLED_AOC_PROMOTION_PREPARATION_RECORDED_NATIVE_NOT_RUN',
            'candidate_count': len(work['candidates']), 'model_revisions': 0,
            'native_arms': 0, 'admissions': 0, 'launches': 0,
            'preparation': u.ref(prep_path), 'static_independent_review': u.ref(peer),
            'all_other_candidates_and26_ledgers_and28_user_paths_and_index_preserved': True})
        print('Corrected disabled AOC preparation recorded; actual GPU0 wait and native NOT_RUN preserved.')
    finally:
        lock.close()


if __name__ == '__main__':
    main()
