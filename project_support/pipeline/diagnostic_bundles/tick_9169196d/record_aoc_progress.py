"""Record exact original AOC progress without training or lifecycle control."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_STATE_CHANGE')
        return
    guard()
    obs = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    peer = HERE / 'current_aoc_wait_independent_review.json'
    assert sha(obs) == '3ea3c2e366e7b3cf4e0f99a101319011dde4fe0528afef077118bce5f558a43a'
    assert sha(peer) == '3f3f9efb327136a925ac6c7e58dcf6323569e23a21edf1970be5f9b9656dfde6'
    ob = u.read(obs)
    assert ob['owner'] == EXPECTED and ob['returncode'] == 0 and ob['observation']['runtime_commit'] == u.SOURCE
    assert u.read(peer)['material_concerns'] == []
    samples = ob['observation']['samples']
    assert samples[0]['last_native_step'] == [4, 2889] and samples[-1]['last_native_step'] == [4, 2897]
    assert ob['precise_native_validation']['best'] == 0.41503071784973145
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        b = u.read(HERE / 'protected_assets_before.json')
        guard()
        u.primary_protection(b)
        u.lifecycle_protection(b)
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 149
        c = next(c for c in work['candidates'] if c['id'] == AOC)
        f = next(c for c in work['candidates'] if c['id'] == FCB)
        assert c['stage'] == 'training' and c['code_commit'] == u.SOURCE
        assert f['stage'] == 'blocked' and f['blocker_kind'] == 'exclusive_gpu_slot'
        now = datetime.now(timezone.utc).isoformat()
        c['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(obs), 'independent_review': u.ref(peer),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': [4, 2889], 'native_step_after': [4, 2897],
            'precise_native_validation': copy.deepcopy(ob['precise_native_validation']),
            'scope': 'Actual original native progress and three completed validation lines in incomplete training. No new launch, final efficacy or old crash root-cause claim.'}
        f['current_resource_check'] = {
            'recorded_at': ob['observed_at'], 'result': 'Original_AOC_compute_PID_and_GPU0_context_confirmed_busy',
            'evidence': u.ref(obs), 'scope': 'Dated current original process/source/context observation only; canonical current-owner physical occupation proof follows before finish. FCB TRAIN/resources NOT_RUN.'}
        for candidate in (c, f):
            for ref in (u.ref(obs), u.ref(peer)):
                if ref not in candidate['evidence']:
                    candidate['evidence'].append(ref)
        work['updated_at'] = now
        work['last_event_tick'] = EXPECTED['generated_at']
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] not in (AOC, FCB))
        u.save(HERE / 'current_progress_record_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB], 'observation': u.ref(obs), 'independent_review': u.ref(peer),
            'scope': 'Current original training and existing resource wait only; no source, lifecycle, native, queue or launch control.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        u.primary_protection(b)
        u.lifecycle_protection(b)
        u.save(HERE / 'current_progress_record_result.json', {'owner': EXPECTED, 'status': 'ORIGINAL_AOC_PROGRESS_RECORDED',
            'candidate_count': 149, 'other147_candidates_unchanged': True,
            'all28_lifecycle_and28_user_paths_and_index_preserved': True, 'research_work_sha256': sha(path)})
        print('Original AOC TRAIN4 growth and partial validation recorded; no training control.')
    finally:
        lock.close()


if __name__ == '__main__':
    main()
