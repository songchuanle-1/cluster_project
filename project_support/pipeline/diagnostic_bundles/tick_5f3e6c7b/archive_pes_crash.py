"""One canonical archive of the exact original abnormal PES termination."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, hashlib, os, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE = Path(__file__).resolve().parent
EXP = 'M221-PES'
CID = 'hierarchy-palindromic-euler-state-composition'
STATE = 'crashed'
BEST = 0.4211066663265228


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--execute-root', action='store_true')
    ap.add_argument('--peer-sha256')
    a = ap.parse_args()
    if not a.execute_root:
        print('DEFAULT_NO_ARCHIVE')
        return
    guard()
    b = u.read(HERE / 'protected_assets_before.json')
    u.primary_protection(b)
    u.lifecycle_protection(b)
    observation = HERE / 'pes_end_and_slot_observation.json'
    assert sha(observation) == 'dbd4717dd46c4274106118b6b97a8e12fa2a4715bf7d6bde48274cb2ffc15195'
    ob = u.read(observation)
    raw = ob['observation']
    assert ob['owner'] == EXPECTED and raw['original_pid_absent'] is True
    assert raw['last_TRAIN_progress'] == [5, 529] and raw['explicit_early_stop'] is False
    assert 'ValueError: too many values to unpack (expected 0)' in raw['exception_trace']
    assert len(ob['precise_native_validation']['values']) == 4 and ob['precise_native_validation']['best'] == BEST
    meta = u.read(HERE / 'pes_exact_terminal_archive/exact_log_evidence.json')
    log = ROOT / meta['local']['path']
    assert sha(log) == meta['remote']['sha256'] == meta['local']['sha256'] == '358d479d5122c895434dda14c8afdbc921e3e7cb6d8f38030f62b5d314c81e0c'
    assert meta['remote']['original_pid_absent_before_after'] and meta['remote']['same_config_processes'] == []
    assert sha(ROOT / 'pipeline/admissions/M221-PES.json') == '6fcee3f5bbfb865b9902ff04e0b019c464f8911c600906de07577608a930f2b1'
    peer = HERE / 'pes_terminal_independent_review.json'
    assert sha(peer) == a.peer_sha256
    review = u.read(peer)
    assert review['status'] == STATE and review['review_status'] == 'ACTUAL_ORIGINAL_PES_ABNORMAL_TERMINAL_INDEPENDENTLY_VERIFIED'
    assert review['failure_scope'] == 'inconclusive' and review['cause'] == 'UNKNOWN'
    assert len(review['material_concerns']) == 1 and review['material_concerns'][0]['kind'] == 'original_native_training_runtime_crash'
    assert u.ref(observation) in review['anchors'].values() and u.ref(log) in review['anchors'].values()
    assert not any((HERE / n).exists() for n in ('pes_finalize_intent.json', 'pes_finalize_result.json', 'post_pes_terminal_baseline.json'))
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock = mon.acquire_lock(str(ROOT))
    assert lock is not None
    try:
        guard()
        u.primary_protection(b)
        u.lifecycle_protection(b)
        queue = mon.load_queue(str(ROOT))
        task = next(t for rows in queue['gpu_queues'].values() for t in rows if t.get('id') == EXP)
        assert task['status'] == 'running' and task['pid'] == 2265073 and task['code_commit'] == u.SOURCE
        assert str(task['gpu']) == '0' and task['launch_verified'] is True
        before_queue = copy.deepcopy(queue)
        ledgers = {n: sha(ROOT / 'pipeline' / n) for n in b['protected_ledgers']}
        work_path = ROOT / 'pipeline/research_work.json'
        work = u.read(work_path)
        old = {c['id']: u.digest(c) for c in work['candidates']}
        assert len(old) == 149
        c = next(x for x in work['candidates'] if x['id'] == CID)
        assert c['stage'] == 'training' and c['code_commit'] == u.SOURCE
        journal = ROOT / 'pipeline/archive_pending' / (hashlib.sha256(EXP.encode()).hexdigest() + '.json')
        assert not journal.exists()
        u.save(HERE / 'pes_finalize_intent.json', {
            'owner': EXPECTED, 'recorded_at': datetime.now(timezone.utc).isoformat(),
            'task': task, 'exact_log': meta['local'], 'observation': u.ref(observation),
            'independent_review': u.ref(peer), 'protected_ledgers_before': ledgers,
            'candidate_digests_before': old,
            'scope': 'One canonical original crash archive. Preserve technical receipt, source and launch evidence; no signal, source patch, restart, resume or new training.'})
        original_pull = mon.pull_log
        def exact_pull(project_dir, host, user, remote_log, cfg_name, state, srv_name=''):
            assert Path(project_dir).resolve() == ROOT.resolve()
            assert (host, user, remote_log, cfg_name, state, srv_name) == ('192.168.1.115', 'songcl', task['log'], Path(task['config']).stem, STATE, 'server-4')
            assert sha(log) == meta['local']['sha256']
            return str(log)
        mon.pull_log = exact_pull
        events = []
        try:
            mon.finalize_task(str(ROOT), queue, 'server-4', '192.168.1.115', 'songcl', task,
                              Path(task['config']).stem, STATE, BEST, '5/50', '0', task['log'], events)
        finally:
            mon.pull_log = original_pull
        exp = mon.load_experiment(str(ROOT), EXP)
        assert exp['status'] == STATE and exp['code_commit'] == u.SOURCE
        assert exp['final_best'] == '0.4211' and exp['epochs_final'] == '5/50' and exp['log_local'] == str(log)
        if exp.get('training_status') != STATE:
            exp['training_status'] = STATE
            mon.save_experiment(str(ROOT), exp)
        now = datetime.now(timezone.utc).isoformat()
        c.setdefault('admission_status_history', []).append({'recorded_at': now, 'admission_status': c.get('admission_status')})
        c.update(stage='complete', training_status=STATE, admission_status='ADMITTED_TRAINING_CRASH_ARCHIVED',
                 failure_scope='inconclusive', queued=False, finished_at=exp['finished_at'],
                 partial_best_miou=BEST, epochs_final='5/50', terminal_archive_id=exp['archive_id'],
                 completion_outcome='incomplete_training_native_parameter_enumeration_ValueError_cause_unknown',
                 next_action='Preserve exact PES source9c, technical gates/receipt, original launch and complete crash log. Parameter enumeration ValueError cause remains UNKNOWN; incomplete training is not a final efficacy or hypothesis rejection. Any recovery requires a concrete full-checkpoint/runtime/source/resource plan and its required authorization; no automatic resume or cold restart. Advance independent AOC on fresh authorized GPU0 checks.')
        c['terminal_assessment'] = {
            'recorded_at': now, 'state': STATE, 'last_native_epoch': 5, 'last_native_step': 529, 'steps_per_epoch': 4686,
            'completed_validation_count': 4, 'native_validation_values': ob['precise_native_validation']['values'],
            'partial_best': BEST, 'no_improve': 0, 'explicit_native_early_stop': False,
            'exception': 'ValueError: too many values to unpack (expected 0)',
            'exception_site': 'native clip_grad_norm_(model.parameters()) -> named_parameters/_named_members',
            'root_cause': 'UNKNOWN', 'failure_scope': 'inconclusive',
            'scope': 'Original native training stopped abnormally. No source/runtime cause, GPU fault, mechanism falsification or final efficacy inferred from the stack location.'}
        for ref in (u.ref(observation), u.ref(HERE / 'pes_exact_terminal_archive/exact_log_evidence.json'), u.ref(log), u.ref(peer), u.ref(HERE / 'pes_progress_observer/pes_training_progress_observation.json')):
            if ref not in c['evidence']:
                c['evidence'].append(ref)
        work['updated_at'] = now
        work['last_terminal_event'] = {'recorded_at': now, 'experiment_id': EXP, 'status': STATE, 'archive_id': exp['archive_id']}
        assert all(u.digest(x) == old[x['id']] for x in work['candidates'] if x['id'] != CID)
        u.atomic(work_path, work)
        current_queue = mon.load_queue(str(ROOT))
        expected_queue = copy.deepcopy(before_queue)
        for rows in expected_queue['gpu_queues'].values():
            rows[:] = [t for t in rows if t.get('id') != EXP]
        assert current_queue == expected_queue and not journal.exists()
        changed = {'queue.json', 'running.json', 'experiments.csv', 'experiments/M221-PES.json'}
        assert all(sha(ROOT / 'pipeline' / n) == h for n, h in ledgers.items() if n not in changed)
        u.primary_protection(b)
        post = dict(b)
        post.update(owner=EXPECTED, recorded_at=now,
                    protected_ledgers={n: sha(ROOT / 'pipeline' / n) for n in ledgers},
                    candidate_digests={x['id']: u.digest(x) for x in work['candidates']},
                    research_work_sha256=sha(work_path), original_PES_terminal=u.ref(observation),
                    lifecycle_change_scope=sorted(changed))
        u.save(HERE / 'post_pes_terminal_baseline.json', post)
        u.save(HERE / 'pes_finalize_result.json', {
            'owner': EXPECTED, 'recorded_at': now, 'status': 'CANONICAL_ORIGINAL_CRASH_AND_RESEARCH_TERMINAL_RECORDED',
            'experiment_id': EXP, 'archive_id': exp['archive_id'], 'state': STATE, 'printed_partial_best': '0.4211',
            'exact_logger_partial_best': BEST, 'epochs': '5/50', 'last_native_step': 529,
            'exact_full_log': meta['local'], 'events': events, 'post_terminal_baseline': u.ref(HERE / 'post_pes_terminal_baseline.json'),
            'no_signals_restart_patch_or_new_training': True, 'other148_candidates_and_other_lifecycle_preserved': True})
        print({'state': STATE, 'archive_id': exp['archive_id'], 'baseline': u.ref(HERE / 'post_pes_terminal_baseline.json')})
    finally:
        lock.close()


if __name__ == '__main__':
    main()
