"""Record the actual AOC launch and newly satisfied FCB parent dependency."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse, copy, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
AOC = 'hierarchy-ancestral-order-commutator-composition'
FCB = 'hierarchy-fine-coarse-complete-bipartite-composition'
SOURCE = '0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--peer-sha256')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_RECORD_MUTATION')
        return
    guard()
    b = u.read(HERE / 'post_pes_terminal_baseline.json')
    ff = u.read(HERE / 'aoc_root_ff_result.json')
    assert ff['HEAD'] == SOURCE and ff['only_nine_tested_additions'] is True
    paths = ff['source_paths']
    assert len(paths) == 9
    repo = ROOT / 'Cluster'
    index = Path(u.git(repo, 'rev-parse', '--git-path', 'index').decode().strip())
    index = index if index.is_absolute() else repo / index
    index_hash = sha(index)
    def protect():
        guard()
        assert u.git(repo, 'rev-parse', 'HEAD').decode().strip() == SOURCE
        assert u.git(repo, 'status', '--porcelain=v1', '--untracked-files=all', '-z').hex() == b['status_hex']
        assert not u.git(repo, 'diff', '--cached', '--name-only', '-z') and sha(index) == index_hash
        assert all(sha(repo / n) == h for n, h in b['files'].items())
        assert all(sha(repo / n) == h for n, h in paths.items())
    protect()
    assert sha(ROOT / 'pipeline/admissions/M222-AOC.json') == 'bf4426ca1b9251ed850de7d8a13f643a26de14ef59a1329c345140d4436a1778'
    assert sha(ROOT / 'pipeline/admissions/M221-PES.json') == '6fcee3f5bbfb865b9902ff04e0b019c464f8911c600906de07577608a930f2b1'
    peer = HERE / 'aoc_launch_independent_review.json'
    assert sha(peer) == a.peer_sha256 and u.read(peer)['material_concerns'] == []
    progress = HERE / 'aoc_progress_observer/aoc_training_progress_observation.json'
    assert sha(progress) == '5106a25d114181f9271e25002de47e49805539ebed40bbfe65227d24a76a06ea'
    ob = u.read(progress)
    assert ob['owner'] == EXPECTED and ob['returncode'] == 0 and ob['observation']['runtime_commit'] == SOURCE
    samples = ob['observation']['samples']
    assert samples[0]['last_native_step'] == [1, 156] and samples[-1]['last_native_step'] == [1, 165]
    assert all(ob['precise_native_validation'][k] is None for k in ('values', 'best', 'no_improve'))
    local = HERE / 'fcb_parent_ready_local_observation.json'
    assert sha(local) == 'bf6a071dfd312ffe66349423ea6f9ac639500175e1f36f03275089e64e9ebf1d'
    assert u.read(local)['status'] == 'ACTUAL_PARENT_PROMOTION_LOCAL_GUARD_PASSED_NOT_GPU_IDLE'
    assert u.read(local)['transport_calls'] == 0
    assert u.read(HERE / 'pes_finalize_result.json')['state'] == 'crashed'
    names = list(dict.fromkeys([*b['protected_ledgers'], 'admissions/M222-AOC.json', 'experiments/M222-AOC.json']))
    ledgers = {n: sha(ROOT / 'pipeline' / n) for n in names}
    assert len(ledgers) == 28
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        protect()
        assert all(sha(ROOT / 'pipeline' / n) == h for n, h in ledgers.items())
        path = ROOT / 'pipeline/research_work.json'
        before = sha(path)
        work = u.read(path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 149
        c = next(x for x in work['candidates'] if x['id'] == AOC)
        f = next(x for x in work['candidates'] if x['id'] == FCB)
        assert c['stage'] == 'training' and c['code_commit'] == SOURCE
        assert f['stage'] == 'validation' and f['code_commit'] == 'd4d062ef075abfe7cde93d4b4347ce146572762f'
        q = mon.load_queue(str(ROOT))
        tasks = [t for rows in q['gpu_queues'].values() for t in rows]
        live = next(t for t in tasks if t.get('id') == 'M222-AOC')
        paused = next(t for t in tasks if t.get('id') == 'M206-CGCA')
        assert live['status'] == 'running' and live['pid'] == 3437349 and live['launch_verification'] == 'training_progress'
        assert paused['status'] == 'waiting' and paused['dispatch_hold'] and paused.get('pid') is None
        assert mon.load_running(str(ROOT))['server-4']['0'] == 'M222-AOC'
        now = datetime.now(timezone.utc)
        c['current_live_observation'] = {
            'recorded_at': now.isoformat(), 'evidence': u.ref(progress), 'independent_review': u.ref(peer),
            'original_pid': 3437349, 'original_start_ticks': 90046755,
            'native_step_before': [1, 156], 'native_step_after': [1, 165],
            'precise_native_validation': copy.deepcopy(ob['precise_native_validation']),
            'scope': 'Actual original new AOC formal native progress, not a PID-only launch claim. No validation printed; technical admission is not efficacy or PES root-cause repair.'}
        c['source_status'] = 'EXACT_TESTED_AOC_PRESENT_PRIMARY_AND_VERIFIED_REMOTE_RUNTIME'
        c['next_action'] = 'Monitor exact original AOC3437349/start90046755/log/source0314 on server4 GPU0 through natural completion. Real native progress is verified; do not replay stale dispatch_phase. GPU1 remains forbidden and PES is canonically archived as crashed without automatic recovery.'
        for ref in (u.ref(progress), u.ref(peer), u.ref(HERE / 'aoc_original_process_identity.json')):
            if ref not in c['evidence']:
                c['evidence'].append(ref)
        f.setdefault('version_compatibility_history', []).append(copy.deepcopy(f.get('current_version_compatibility')))
        f['current_version_compatibility'] = {
            'recorded_at': now.isoformat(), 'current_source_commit': f['code_commit'], 'current_parent_commit': SOURCE,
            'runtime_expected_commit': SOURCE, 'current_primary_and_runtime': SOURCE,
            'status': 'ACTUAL_AOC_PARENT_PROMOTED_LOCAL_GUARD_PASSED_GPU0_OCCUPIED_BY_AOC',
            'AOC_technical_receipt': u.ref(ROOT / 'pipeline/admissions/M222-AOC.json'), 'local_parent_guard': u.ref(local),
            'physical_occupation_scope': u.ref(progress),
            'scope': 'Only actual source-parent/technical-receipt readiness changed. FCB native/resources remain NOT_RUN; no GPU0 idle or FCB source-promotion claim. Fresh compatible-source checks still required if main changes.'}
        f.update(stage='blocked', blocker_kind='exclusive_gpu_slot', blocked_from_stage='validation', resume_stage='validation',
                 required_server='server-4', required_physical_gpu=0, blocked_at=now.isoformat(),
                 retry_after=(now + timedelta(hours=1)).isoformat(),
                 blocker='Sole authorized GPU0 is occupied by the original admitted AOC3437349. FCB source parent0314 is now genuinely promoted; native TRAIN/resources remain NOT_RUN.',
                 unblock_condition='Original AOC naturally frees GPU0; then fresh actual UUID/occupation/source0314/assets/three-lock/owner-original-deadline checks permit original FCB d4d062 native execution. No GPU1, eviction, old recovery or sibling ff.',
                 native_status='NOT_RUN_GPU0_OCCUPIED_BY_ORIGINAL_AOC', resource_status='NOT_RUN_GPU0_OCCUPIED_BY_ORIGINAL_AOC')
        f['source_status'] = 'ISOLATED_FCB_SOURCE_VALID_PARENT_PROMOTED_NATIVE_NOT_RUN'
        f['next_action'] = 'Actual AOC0314 parent and genuine technical receipt are ready; wait for original AOC GPU0 task to end naturally as a physical resource condition. Then execute original FCB d4d062 paired natural TRAIN2/resources under fresh owner/original deadline, current compatible source/runtime/UUID/assets/idle/three locks. No FCB admission before actual passes.'
        for ref in (u.ref(local), u.ref(progress), u.ref(peer)):
            if ref not in f['evidence']:
                f['evidence'].append(ref)
        work['updated_at'] = now.isoformat()
        work['last_event_tick'] = EXPECTED['generated_at']
        work['next_action'] = c['next_action']
        smoke = u.read(HERE / 'aoc_native_smoke.json')
        work['tick_attempt'] = {'tick_started_at': EXPECTED['generated_at'], 'candidate_id': AOC, 'kind': 'native_smoke', 'result': 'passed',
            'command': smoke['command'], 'observation': 'Actual original matched natural TRAIN2/backward/whole-cell updates and paired resources independently reviewed. One actual AOC admission/dispatch and strict formal native progress verified; efficacy UNKNOWN.', 'evidence': [u.ref(HERE / 'aoc_native_smoke.json')]}
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] not in (AOC, FCB))
        u.save(HERE / 'aoc_launch_fcb_wait_record_intent.json', {'owner': EXPECTED, 'research_work_before_sha256': before,
            'changed_candidate_ids': [AOC, FCB], 'new_original_progress': u.ref(progress), 'launch_review': u.ref(peer),
            'FCB_parent_ready': u.ref(local), 'scope': 'Actual AOC progress and actual FCB parent readiness/resource disposition only; no new native/source/queue/launch action.'})
        guard()
        assert sha(path) == before
        u.atomic(path, work)
        protect()
        assert all(sha(ROOT / 'pipeline' / n) == h for n, h in ledgers.items())
        post = dict(b)
        post.update(owner=EXPECTED, recorded_at=now.isoformat(), head=SOURCE, index_sha256=index_hash,
                    protected_ledgers=ledgers, candidate_digests={x['id']: u.digest(x) for x in work['candidates']},
                    current_candidate_source_paths=paths, exact_tested_nine_source_paths=paths,
                    research_work_sha256=sha(path), native_progress=u.ref(progress), source_ff=u.ref(HERE / 'aoc_root_ff_result.json'))
        u.save(HERE / 'post_aoc_launch_baseline.json', post)
        u.save(HERE / 'aoc_launch_fcb_wait_record_result.json', {'owner': EXPECTED,
            'status': 'ACTUAL_AOC_TRAINING_AND_FCB_PARENT_READY_GPU0_WAIT_RECORDED', 'candidate_count': 149,
            'other147_candidates_unchanged': True, 'protected28_lifecycle_and28_user_paths_and_index_preserved': True,
            'post_launch_baseline': u.ref(HERE / 'post_aoc_launch_baseline.json')})
        print({'status': 'AOC genuine launch and FCB actual parent readiness saved', 'baseline': u.ref(HERE / 'post_aoc_launch_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
