"""Offline regressions for archived dependencies and interrupted dispatch."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import closure
import pipeline_monitor as monitor
import render_tick_report
import tick_efficiency


class QueueReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'pipeline/experiments').mkdir(parents=True)
        self.task = dict(id='child', config='configs/child.yaml', status='claiming')
        self.queue = {'gpu_queues': {'test-server': [self.task]}}
        self.server = dict(host='unused', user='unused', remote_code_root='/code',
                           max_tasks_per_gpu=1)
        self.silence = contextlib.redirect_stdout(io.StringIO())
        self.silence.__enter__()
        self.addCleanup(self.silence.__exit__, None, None, None)

    def record(self, state):
        monitor.save_experiment(str(self.root), dict(id='parent', status=state))

    def states(self, queue=None):
        return monitor.dependency_states(str(self.root), queue or {}, {'parent'})

    def reconcile(self, procs=None, read_only=False):
        monitor.reconcile_claims(str(self.root), self.queue, 'test-server', self.server,
                                 {} if procs is None else procs, {'0'}, read_only)

    def test_archived_success_dispatches_child(self):
        parent = dict(id='parent', config='configs/parent.yaml', status='running', gpu='0')
        self.task.update(status='waiting', depends_on=['parent'])
        self.queue['gpu_queues']['test-server'].insert(0, parent)
        monitor.finalize_task(str(self.root), self.queue, 'test-server', 'unused', 'unused',
                              parent, 'parent', 'done_complete', .5, '10/10', '0', '', [])
        self.assertEqual(self.states()['parent'], 'done_complete')
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(monitor, 'ssh', return_value='0, 0, 0, 80000'))
            stack.enter_context(patch.object(monitor, 'load_active_gpu_reservations', return_value={}))
            stack.enter_context(patch.object(closure, 'enabled', return_value=False))
            stack.enter_context(patch.object(monitor, 'check_code_sync', return_value=True))
            launch = stack.enter_context(patch.object(monitor, 'launch_training'))
            stack.enter_context(patch.object(monitor, 'verify_launched', return_value=True))
            stack.enter_context(patch.object(monitor, 'log_decision'))
            monitor._process_queue(self.queue, 'test-server', 'unused', 'unused',
                                   str(self.root), set(), {'0'}, [])
        launch.assert_called_once()
        self.assertEqual(self.task['status'], 'running')

    def test_failed_or_unknown_dependency_never_dispatches(self):
        for state in ('crashed', 'stopped_unknown', 'unknown'):
            self.record(state)
            self.task.update(status='waiting', depends_on=['parent'])
            with patch.object(monitor, 'ssh', return_value='0, 0, 0, 80000'), \
                    patch.object(monitor, 'launch_training') as launch:
                monitor._process_queue(self.queue, 'test-server', 'unused', 'unused',
                                       str(self.root), set(), {'0'}, [])
            launch.assert_not_called()

    def test_live_retry_overrides_archived_success(self):
        self.record('done_complete')
        queue = {'gpu_queues': {'other': [dict(id='parent', status='running')]}}
        self.assertEqual(self.states(queue)['parent'], 'running')

    def test_conflicting_live_ids_fail_closed(self):
        queue = {'gpu_queues': {'a': [dict(id='parent', status='done_complete')],
                                'b': [dict(id='parent', status='running')]}}
        self.assertEqual(self.states(queue)['parent'], 'unknown')

    def test_legacy_csv_fallback_uses_latest_status(self):
        (self.root / 'pipeline/experiments.csv').write_text(
            'id,state\nparent,done_complete\nparent,crashed\n', encoding='utf-8')
        self.assertEqual(self.states()['parent'], 'crashed')
        self.record('done_earlystop')
        self.assertEqual(self.states()['parent'], 'done_earlystop')

    def test_invalid_record_does_not_fall_back_to_old_success(self):
        (self.root / 'pipeline/experiments.csv').write_text(
            'id,state\nparent,done_complete\n', encoding='utf-8')
        (self.root / 'pipeline/experiments/parent.json').write_text('{')
        self.assertEqual(self.states()['parent'], 'unknown')

    def test_orphan_legacy_claim_is_explicitly_held(self):
        self.reconcile()
        self.reconcile()
        self.assertEqual(self.task['status'], 'claiming')
        self.assertTrue(self.task['dispatch_hold'].startswith('Interrupted claim;'))

    def test_durable_prelaunch_phase_can_requeue_without_launching(self):
        self.task['dispatch_phase'] = 'syncing'
        with patch.object(monitor, 'launch_training') as launch:
            self.reconcile()
        launch.assert_not_called()
        self.assertEqual(self.task['status'], 'waiting')
        self.assertNotIn('dispatch_hold', self.task)

    def test_launch_requested_phase_never_blindly_requeues(self):
        self.task['dispatch_phase'] = 'launch_requested'
        self.reconcile()
        self.assertEqual(self.task['status'], 'claiming')
        self.assertIn('dispatch_hold', self.task)

    def test_missing_process_observation_never_recovers(self):
        self.task['dispatch_phase'] = 'syncing'
        before = copy.deepcopy(self.queue)
        monitor.reconcile_claims(str(self.root), self.queue, 'test-server', self.server,
                                 None, {'0'})
        self.assertEqual(self.queue, before)

    def test_read_only_never_changes_queue_or_ledgers(self):
        for phase in ('syncing', 'launch_requested'):
            self.task['dispatch_phase'] = phase
            before = copy.deepcopy(self.queue)
            with patch.object(monitor, 'save_queue') as save:
                self.reconcile(read_only=True)
            self.assertEqual(self.queue, before)
            save.assert_not_called()

    def test_exact_live_claim_recovers_all_ledgers_once(self):
        self.task.update(pid=12, gpu='0', log='/logs/current',
                         launch_verification='pending_progress',
                         dispatch_hold='Launch uncertain; response lost')
        procs = {'configs/child.yaml': ('12', 'configs/child.yaml', '0', None, 'train')}
        with patch.object(closure, 'verify_progress', return_value=True):
            self.reconcile(procs)
            self.reconcile(procs)
        self.assertEqual(self.task['status'], 'running')
        self.assertTrue(self.task['launch_verified'])
        self.assertNotIn('dispatch_hold', self.task)
        exp = monitor.load_experiment(str(self.root), 'child')
        self.assertEqual(len(exp['history']), 1)
        self.assertEqual(monitor.load_running(str(self.root))['test-server']['0'], 'child')

    def test_wrong_pid_gpu_or_manual_hold_cannot_be_adopted(self):
        for pid, gpu, hold in ((13, '0', ''), (12, '1', ''), (12, '0', 'User paused')):
            self.task.update(status='claiming', pid=12, gpu='0', log='/logs/current',
                             dispatch_hold=hold)
            procs = {'configs/child.yaml': (str(pid), 'configs/child.yaml', gpu, None, 'train')}
            with patch.object(closure, 'verify_progress', return_value=True):
                self.reconcile(procs)
            self.assertEqual(self.task['status'], 'claiming')

    def test_pid_without_progress_is_not_success(self):
        self.task.update(pid=12, gpu='0', log='/logs/current')
        procs = {'configs/child.yaml': ('12', 'configs/child.yaml', '0', None, 'train')}
        with patch.object(closure, 'verify_progress', return_value=False):
            self.reconcile(procs)
        self.assertNotEqual(self.task['status'], 'running')
        self.assertNotIn('launch_verified', self.task)

    def test_actual_failure_markers_and_task_binding(self):
        output = ('--- test-server (example) ---\n'
                  '  [进程观测不可用] retry\n'
                  '  [准入阻止] A: Goal changed\n'
                  '  [认领待核验] [B] verify\n'
                  '  [依赖阻止] [C] A=unknown\n'
                  '  >>> 队列推送: [D] on test-server gpu0\n'
                  '  >>> 推送失败 (retry 1)\n')
        issues = tick_efficiency.monitor_issues(output)
        self.assertEqual([i['reason'] for i in issues],
                         ['process_unknown', 'admission_blocked', 'claim_uncertain',
                          'dependency_blocked', 'launch_failed'])
        self.assertEqual([i['task'] for i in issues], [None, 'A', 'B', 'C', 'D'])
        report = render_tick_report.render({'mode': 'event', 'preflight': {
            'operational_issues': issues}})
        self.assertNotIn('未知执行故障', report)

    def test_integrity_failure_has_specific_reason(self):
        issues = tick_efficiency.monitor_issues('[同步阻止] Source integrity mismatch')
        self.assertEqual(issues[0]['reason'], 'source_integrity')

    def dispatch(self, sync=True, launch=None, progress=True, observed=True):
        self.snapshots = []
        self.task.update(status='waiting', code_commit='a' * 40)
        save = monitor.save_queue
        def journal(project, queue):
            self.snapshots.append(copy.deepcopy(queue))
            save(project, queue)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(monitor, 'ssh', return_value='0, 0, 0, 80000'))
            stack.enter_context(patch.object(monitor, 'load_active_gpu_reservations', return_value={}))
            stack.enter_context(patch.object(monitor, 'load_servers', return_value={'test-server': self.server}))
            stack.enter_context(patch.object(monitor, 'find_local_code_dir', return_value=str(self.root)))
            stack.enter_context(patch.object(monitor, 'save_queue', side_effect=journal))
            stack.enter_context(patch.object(monitor, 'log_decision'))
            stack.enter_context(patch.object(monitor, 'verify_launched', return_value=observed))
            stack.enter_context(patch.object(closure, 'enabled', return_value=True))
            stack.enter_context(patch.object(closure, 'admission'))
            stack.enter_context(patch.object(closure, 'git', return_value='a' * 40))
            stack.enter_context(patch.object(closure, 'safe_sync', **(
                {'side_effect': sync} if isinstance(sync, BaseException) or callable(sync)
                else {'return_value': sync})))
            starter = stack.enter_context(patch.object(closure, 'safe_launch', **(
                {'side_effect': launch} if isinstance(launch, BaseException) or callable(launch)
                else {'return_value': launch or dict(pid=12, log='/logs/current')})))
            stack.enter_context(patch.object(closure, 'verify_progress', **(
                {'side_effect': progress} if isinstance(progress, BaseException) or callable(progress)
                else {'return_value': progress})))
            monitor._process_queue(self.queue, 'test-server', 'unused', 'unused',
                                   str(self.root), set(), {'0'}, [])
            return starter.call_count

    def test_sync_interruption_has_durable_prelaunch_phase(self):
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch(sync=KeyboardInterrupt())
        self.assertEqual(monitor.load_queue(str(self.root))['gpu_queues']['test-server'][0]
                         ['dispatch_phase'], 'syncing')
        self.reconcile()
        self.assertEqual(self.task['status'], 'waiting')

    def test_launch_request_is_journaled_before_call(self):
        def launch(*args):
            last = self.snapshots[-1]['gpu_queues']['test-server'][0]
            self.assertEqual(last['dispatch_phase'], 'launch_requested')
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch(launch=launch)
        self.reconcile()
        self.assertEqual(self.task['status'], 'claiming')
        self.assertIn('dispatch_hold', self.task)

    def test_pid_is_persisted_before_progress_probe(self):
        def progress(*args):
            last = self.snapshots[-1]['gpu_queues']['test-server'][0]
            self.assertEqual((last['pid'], last['log']), (12, '/logs/current'))
            self.assertEqual(last['launch_verification'], 'pending_progress')
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.dispatch(progress=progress)
        self.assertEqual(self.task['dispatch_phase'], 'progress_pending')

    def test_lost_launch_reply_is_held_not_blindly_retried(self):
        self.assertEqual(self.dispatch(launch=ValueError('reply lost'), observed=False), 1)
        self.assertIn('dispatch_hold', self.task)
        with patch.object(closure, 'safe_launch') as launch:
            monitor._process_queue(self.queue, 'test-server', 'unused', 'unused',
                                   str(self.root), set(), {'0'}, [])
        launch.assert_not_called()

    def test_missing_progress_is_held_even_if_process_probe_fails(self):
        self.dispatch(progress=False, observed=False)
        self.assertEqual(self.task['launch_verification'], 'pending_progress')
        self.assertIn('dispatch_hold', self.task)

    def test_failed_sync_preserves_any_gpu_preference(self):
        self.task['gpu'] = None
        self.assertEqual(self.dispatch(sync=False), 0)
        self.assertEqual(self.task['status'], 'waiting')
        self.assertIsNone(self.task['gpu'])

    def test_read_only_verified_progress_does_not_write_ledgers(self):
        self.task.update(pid=12, gpu='0', log='/logs/current')
        before = copy.deepcopy(self.queue)
        procs = {'configs/child.yaml': ('12', 'configs/child.yaml', '0', None, 'train')}
        with patch.object(closure, 'verify_progress', return_value=True), \
                patch.object(monitor, 'save_queue') as save:
            self.reconcile(procs, read_only=True)
        save.assert_not_called()
        self.assertEqual(self.queue, before)
        self.assertFalse((self.root / 'pipeline/experiments/child.json').exists())


if __name__ == '__main__':
    unittest.main()
