"""Record current original PES progress, without training or lifecycle control."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
PES = 'hierarchy-palindromic-euler-state-composition'
AOC = 'hierarchy-ancestral-order-commutator-composition'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_STATE_CHANGE')
        return
    guard()
    obs = HERE / 'pes_progress_observer/pes_training_progress_observation.json'
    peer = HERE / 'current_pes_wait_independent_review.json'
    assert sha(obs) == '8c6a492bd656c1b409dd8831c7846177702144db3ba4286382a5a15c7f0e6c61'
    assert sha(peer) == '2fcf6d34c583d67887b0b1c779e8b4c11e46e1cdd1ee1ffd7e8d5c2fa6f3372f'
    ob = u.read(obs)
    assert ob['owner'] == EXPECTED and ob['returncode'] == 0
    assert ob['observation']['runtime_commit'] == u.SOURCE
    assert u.read(peer)['material_concerns'] == []
    samples = ob['observation']['samples']
    assert samples[0]['last_native_step'] == [3, 4020]
    assert samples[-1]['last_native_step'] == [3, 4025]
    assert ob['precise_native_validation']['values'] == [0.2965591251850128, 0.3763071894645691]
    assert ob['precise_native_validation']['best'] == 0.3763071894645691
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
        p = next(c for c in work['candidates'] if c['id'] == PES)
        c = next(c for c in work['candidates'] if c['id'] == AOC)
        assert p['stage'] == 'training' and p['code_commit'] == u.SOURCE
        assert c['stage'] == 'blocked' and c['blocker_kind'] == 'exclusive_gpu_slot'
        now = datetime.now(timezone.utc).isoformat()
        p['current_live_observation'] = {
            'recorded_at': now, 'evidence': u.ref(obs), 'independent_review': u.ref(peer),
            'original_pid': 2265073, 'original_start_ticks': 88396735,
            'native_step_before': [3, 4020], 'native_step_after': [3, 4025],
            'precise_native_validation': copy.deepcopy(ob['precise_native_validation']),
            'scope': 'Only exact original process/log/source and observed native step growth. Two completed validation lines in incomplete training, no final efficacy or new launch claim.'}
        c['current_resource_check'] = {
            'recorded_at': ob['observed_at'], 'result': 'Original_PES_compute_PID_and_GPU0_context_confirmed_busy',
            'evidence': u.ref(obs),
            'scope': 'Dated original process/source context observation only. Canonical current-owner occupation proof follows before finish; no native or resource-profile PASS.'}
        for candidate in (p, c):
            for ref in (u.ref(obs), u.ref(peer)):
                if ref not in candidate['evidence']:
                    candidate['evidence'].append(ref)
        work['updated_at'] = now
        work['last_event_tick'] = EXPECTED['generated_at']
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] not in (PES, AOC))
        u.save(HERE / 'current_progress_record_intent.json', {
            'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [PES, AOC], 'observation': u.ref(obs), 'independent_review': u.ref(peer),
            'scope': 'Record current original training and existing resource wait; no source, lifecycle, native, queue or launch control.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        u.primary_protection(b)
        u.lifecycle_protection(b)
        u.save(HERE / 'current_progress_record_result.json', {
            'owner': EXPECTED, 'status': 'ORIGINAL_PES_PROGRESS_RECORDED', 'candidate_count': 149,
            'other147_candidates_unchanged': True,
            'all26_lifecycle_and28_user_paths_and_index_preserved': True,
            'research_work_sha256': sha(path)})
        print('Original PES TRAIN3 growth and two partial validation values recorded; no training control.')
    finally:
        lock.close()


if __name__ == '__main__':
    main()
