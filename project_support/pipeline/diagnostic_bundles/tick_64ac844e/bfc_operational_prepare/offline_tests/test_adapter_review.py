"""Independent mocked orchestration review; no SSH, torch or native execution.

All simulated leases/results are inside disposable fixture directories here.
The frozen preparation is read-only. The historical orchestration fixtures use
a release stub; dedicated real-gate fixtures create their static catalog and
external anchors only inside the disposable temporary project.
"""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import adapter as module

OUT = Path(__file__).resolve().parent
SOURCE_ORIGIN = OUT.parent
REAL_ROOT = Path('D:/project/cluster_project')
KEYS = ('project', 'candidate_id', 'code_commit', 'stage', 'token', 'request_id',
        'operation', 'physical_gpu', 'gpu_uuid', 'native_manifest_sha256')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.request_history = []
        self.busy = False
        self.lock_busy = False
        self.timeout = False
        self.wrong_stage = False

    def call(self, operation, payload, server, *, timeout, conda=False):
        self.calls.append(operation)
        if operation == 'probe':
            gpu = payload['physical_gpu']
            return dict(server_id='server-4', hostname='dl04-MS-7E06',
                root=module.REMOTE_ROOT, physical_gpu=gpu,
                gpu_uuid=module.GPU_UUIDS[gpu], runtime_code_commit='a'*40,
                idle=not self.busy, contexts='123, 100' if self.busy else '',
                memory_used_mib=100 if self.busy else 0, utilization_percent=0,
                locks={k:'busy' if self.lock_busy else 'available'
                       for k in ('training','diagnostic','exclusive')})
        binding = payload['binding']
        if operation == 'reconcile':
            return dict(stage='wrong' if self.wrong_stage else binding['stage'],
                native_manifest_sha256=binding['native_manifest_sha256'],
                requests=[], certainty='unknown', request_id=payload.get('request_id'))
        request = payload['request']
        self.request_history.append(copy.deepcopy(request))
        if operation == 'run' and self.timeout:
            raise module.Uncertain('unit-test transport timeout; not a remote command')
        identity = {k:request[k] for k in KEYS}
        package = 'framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
        if request.get('target') == 'candidate': package += '_bfc'
        return dict(identity=identity, certainty='terminal', verified=True,
            returncode=0, result=dict(execution_completed=True,
                candidate_id=module.CANDIDATE, code_commit=module.COMMIT,
                goal_sha256=module.GOAL, model_package=package,
                mode=request.get('mode'), target=request.get('target')))


class FixtureAdapter(module.Adapter):
    def _release_details(self):
        return {'unit_test_release_stub': True}


class AdapterReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='f_', dir=OUT)
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name).resolve()
        self.assertTrue(base.is_relative_to(OUT))
        self.root = base/'cluster_project'
        self.origin = base/'adapter_release_fixture'
        write(self.origin/'adapter_release.json', {'unit_fixture':True})
        self.now = datetime(2026, 10, 22, 0, 0, tzinfo=timezone.utc)
        self.token = '1'*32
        goal = self.root/'pipeline/goal.json'
        goal.parent.mkdir(parents=True)
        goal.write_bytes((REAL_ROOT/'pipeline/goal.json').read_bytes())
        policy = json.loads((REAL_ROOT/'pipeline/closure_policy.json').read_text(encoding='utf-8'))
        self.authorization = policy['experiment_first']['authorization']
        auth = self.root/self.authorization['path']
        auth.parent.mkdir(parents=True, exist_ok=True)
        auth.write_bytes((REAL_ROOT/self.authorization['path']).read_bytes())
        write(self.root/'pipeline/closure_policy.json', policy)
        self.server = yaml.safe_load((REAL_ROOT/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']
        self.server = copy.deepcopy(self.server)
        self.server['allowed_gpus'] = [0, 1]
        self.server['dispatch_enabled'] = True
        self.save_server()
        template = module.read(module.FROZEN/'manifest_template.json')
        self.candidate = dict(id=module.CANDIDATE, experiment_id='M213-BFC',
            code_commit=module.COMMIT, goal_sha256=module.GOAL,
            authorization=self.authorization, config=template['config'], stage='validation')
        write(self.root/'pipeline/research_work.json', {'candidates':[self.candidate]})
        write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[]}})
        write(self.root/'pipeline/running.json', {'server-4':{}})
        write(self.root/'pipeline/execution_mode.json', {'mode':'foreground','target_thread_id':module.THREAD})
        self.rotate_owner()
        self.transport = FakeTransport()
        self.execution = self.root/'pipeline/diagnostic_bundles'/('tick_'+self.token[:8])/'bfc_execution'
        self.adapter = FixtureAdapter(root=self.root, frozen=module.FROZEN,
            transport=self.transport, env={'CODEX_THREAD_ID':module.THREAD},
            clock=lambda:self.now, execution_dir=self.execution, origin=self.origin)

    def save_server(self):
        (self.root/'SERVERS.yaml').write_text(yaml.safe_dump({'servers':{'server-4':self.server}}), encoding='utf-8')

    def rotate_owner(self, remaining=3600, token=None):
        token = token or self.token
        generated = self.now - timedelta(seconds=3600-remaining)
        deadline = self.now + timedelta(seconds=remaining)
        context = {'project':'cluster_project', 'generated_at':generated.isoformat(),
            'deadline_at':deadline.isoformat(), 'experiment_first':{
                'enabled':True, 'authorization':self.authorization},
            'queue':{'servers':[{'name':'server-4',
                'allowed_gpus':self.server['allowed_gpus'], 'max_tasks_per_gpu':1}]}}
        context_path = self.root/'pipeline/headless/.tick_context.json'
        pending = self.root/'pipeline/headless/.tick_context_state.next.json'
        write(context_path, context); write(pending, {'unit_fixture':token})
        owner = dict(token=token, thread_id=module.THREAD, generated_at=generated.isoformat(),
            deadline_at=deadline.isoformat(), context_sha256=module.sha(context_path),
            pending_sha256=module.sha(pending))
        write(self.root/'pipeline/headless/.foreground.lockdir/owner.json', owner)

    def assert_no_lease(self):
        self.assertFalse((self.execution/'execution_lease.json').exists())
        self.assertFalse((self.execution/'native_manifest.json').exists())

    def real_release_adapter(self):
        origin = self.root/'pipeline/diagnostic_bundles'/('tick_'+self.token[:8])/'reviewed_package'
        origin.mkdir(parents=True)
        for name in ('adapter.py', 'remote_ops.py', 'release_template.json'):
            (origin/name).write_bytes((SOURCE_ORIGIN/name).read_bytes())
        template = module.read(origin/'release_template.json')
        write(origin/'adapter_release.json', template)
        prepared = dict(candidate_id=module.CANDIDATE, code_commit=module.COMMIT,
            prepared_file_hashes={name:module.sha(origin/name)
                for name in ('adapter.py', 'remote_ops.py', 'release_template.json')})
        write(origin/'preparation.json', prepared)
        self.candidate['execution_adapter'] = {
            key:dict(path=(origin/name).relative_to(self.root).as_posix(), sha256=module.sha(origin/name))
            for key,name in (('preparation','preparation.json'), ('release','adapter_release.json'))}
        write(self.root/'pipeline/research_work.json', {'candidates':[self.candidate]})
        adapter = module.Adapter(root=self.root, frozen=module.FROZEN,
            transport=self.transport, env={'CODEX_THREAD_ID':module.THREAD},
            clock=lambda:self.now, execution_dir=self.execution, origin=origin)
        return adapter, origin

    def test_GPU0_BTC_running_and_M206_user_pause_do_not_block_selected_GPU1(self):
        tasks=[{'id':'M211-BTC','status':'running','gpu':'0'},
               {'id':'M206-CGCA','status':'waiting','gpu':'1','resume_authorized':False,'dispatch_hold':'User paused M206; no resume grant'}]
        write(self.root/'pipeline/running.json',{'server-4':{'0':['M211-BTC']}})
        write(self.root/'pipeline/queue.json',{'gpu_queues':{'server-4':tasks}})
        original=copy.deepcopy(tasks)
        binding=self.adapter.prepare(1)
        self.assertEqual(binding['physical_gpu'],1)
        self.assertEqual(binding['gpu_uuid'],module.GPU_UUIDS[1])
        self.assertEqual(module.read(self.root/'pipeline/queue.json')['gpu_queues']['server-4'],original)
        self.assertEqual(self.transport.calls,['probe'])

    def test_registered_running_GPU1_refuses_before_transport_and_lease(self):
        write(self.root/'pipeline/running.json',{'server-4':{'1':['already-running']}})
        with self.assertRaises(module.Refused):self.adapter.prepare(1)
        self.assertEqual(self.transport.calls,[])
        self.assert_no_lease()

    def test_invalid_gpu2_refused_even_when_capability_allowlist_contains_both_cards(self):
        self.assertEqual(self.server['allowed_gpus'], [0, 1])
        with self.assertRaises(module.Refused): self.adapter.prepare(2)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_wrong_ssh_user_guard_refuses_before_transport(self):
        self.server['user'] = 'another-account'; self.save_server()
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_direct_transport_wrong_account_or_host_refuses_before_subprocess(self):
        for change in ({'user':'another-account'}, {'host':'192.168.1.116'}):
            with self.subTest(change=change):
                server = dict(self.server, **change)
                with patch.object(module.subprocess,'run',side_effect=AssertionError('SSH must not be invoked')) as run:
                    with self.assertRaises(module.Refused):
                        module.SSHTransport(SOURCE_ORIGIN).call('probe', {'physical_gpu':0}, server, timeout=1)
                    run.assert_not_called()

    def test_real_release_missing_refuses_without_transport_or_lease(self):
        adapter, origin = self.real_release_adapter()
        (origin/'adapter_release.json').unlink()
        with self.assertRaises(module.Refused): adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_real_release_wrong_external_preparation_anchor_refuses(self):
        adapter, origin = self.real_release_adapter()
        self.candidate['execution_adapter']['preparation']['sha256'] = '0'*64
        write(self.root/'pipeline/research_work.json', {'candidates':[self.candidate]})
        with self.assertRaises(module.Refused): adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_real_release_wrong_external_release_anchor_refuses(self):
        adapter, origin = self.real_release_adapter()
        self.candidate['execution_adapter']['release']['sha256'] = '0'*64
        write(self.root/'pipeline/research_work.json', {'candidates':[self.candidate]})
        with self.assertRaises(module.Refused): adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_real_release_template_mismatch_refuses_even_with_matching_release_anchor(self):
        adapter, origin = self.real_release_adapter()
        release = module.read(origin/'adapter_release.json'); release['code_commit'] = 'f'*40
        write(origin/'adapter_release.json', release)
        self.candidate['execution_adapter']['release']['sha256'] = module.sha(origin/'adapter_release.json')
        write(self.root/'pipeline/research_work.json', {'candidates':[self.candidate]})
        with self.assertRaises(module.Refused): adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_real_release_complete_temp_external_anchors_verify_without_transport(self):
        adapter, origin = self.real_release_adapter()
        self.assertEqual(adapter._release_details(), module.read(origin/'release_template.json'))
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_guard_identity_and_hash_mismatches_refuse_before_transport(self):
        self.adapter.guard()
        self.adapter.env['CODEX_THREAD_ID'] = 'other-thread'
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.adapter.env['CODEX_THREAD_ID'] = module.THREAD
        (self.root/'pipeline/headless/.tick_context.json').write_text('{}')
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_busy_and_lock_busy_never_create_manifest_or_lease(self):
        for field in ('busy', 'lock_busy'):
            with self.subTest(field=field):
                setattr(self.transport, field, True)
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
                setattr(self.transport, field, False)

    def test_deadline_and_disallowed_gpu_fail_before_probe_or_lease(self):
        self.rotate_owner(remaining=350)
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.rotate_owner()
        self.server['allowed_gpus'] = [0]; self.save_server()
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])
        self.assert_no_lease()

    def test_deadline_exhausted_during_probe_does_not_create_lease(self):
        original = self.transport.call
        def elapsed_probe(*args, **kwargs):
            result = original(*args, **kwargs)
            self.now += timedelta(seconds=3300)
            return result
        self.transport.call = elapsed_probe
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assertEqual(self.transport.calls, ['probe'])
        self.assert_no_lease()

    def test_registered_task_gpu_strings_and_integers_are_same_card(self):
        for gpu in ('1', 1):
            with self.subTest(gpu=gpu):
                write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
                    {'id':'already-reserved','status':'claiming','gpu':gpu}]}})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        self.assertEqual(self.transport.calls, [])

    def test_unknown_active_assignment_is_not_treated_as_idle(self):
        for value in (None, True, 2, '2', 'unknown', '00'):
            with self.subTest(value=value):
                write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
                    {'id':'unknown-assignment','status':'claiming','gpu':value}]}})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
            {'id':'missing-assignment','status':'claiming'}]}})
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])

    def test_ordinary_waiting_and_nonlaunch_dependency_holds_do_not_reserve_card(self):
        write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
            {'id':'ordinary-fifo','status':'waiting'},
            {'id':'dependency-wait','status':'waiting','gpu':'0',
             'dispatch_hold':'Dependency is not complete'},
            {'id':'nonlaunch-hold','status':'waiting','dispatch_hold':'Human review pending'}]}})
        binding = self.adapter.prepare(1)
        self.assertEqual(binding['physical_gpu'], 1)
        self.assertEqual(self.transport.calls, ['probe'])

    def test_waiting_pending_progress_with_unknown_assignment_refuses(self):
        for task in (
            {'id':'unknown-launched-card','status':'waiting','launch_verification':'pending_progress','gpu':None},
            {'id':'missing-launched-card','status':'waiting','launch_verification':'pending_progress'}):
            with self.subTest(task=task):
                write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[task]}})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        self.assertEqual(self.transport.calls, [])

    def test_waiting_pending_progress_string_and_integer_same_card_refuse(self):
        for gpu in ('1', 1):
            with self.subTest(gpu=gpu):
                write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
                    {'id':'unverified-launch','status':'waiting','gpu':gpu,
                     'launch_verification':'pending_progress'}]}})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        self.assertEqual(self.transport.calls, [])

    def test_canonical_launch_uncertain_hold_prefixes_reserve_unknown_card(self):
        for prefix in ('Interrupted claim;', 'Launch uncertain;', 'Process observed'):
            with self.subTest(prefix=prefix):
                write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
                    {'id':'uncertain-launch','status':'waiting','gpu':None,
                     'dispatch_hold':prefix+' exact request needs reconciliation'}]}})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        self.assertEqual(self.transport.calls, [])

    def test_active_assignment_outside_current_whitelist_refuses(self):
        self.server['allowed_gpus'] = [1]; self.save_server(); self.rotate_owner()
        for value in (0, '0'):
            with self.subTest(value=value):
                write(self.root/'pipeline/queue.json', {'gpu_queues':{'server-4':[
                    {'id':'not-authorized-card','status':'claiming','gpu':value}]}})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        self.assertEqual(self.transport.calls, [])

    def test_candidate_holds_and_disabled_dispatch_refuse_before_probe(self):
        for key in ('human_hold','scope_hold','numerical_hold','paused'):
            with self.subTest(key=key):
                write(self.root/'pipeline/research_work.json', {'candidates':[
                    dict(self.candidate, **{key:True})]})
                with self.assertRaises(module.Refused): self.adapter.prepare(1)
                self.assert_no_lease()
        write(self.root/'pipeline/research_work.json', {'candidates':[self.candidate]})
        self.server['dispatch_enabled'] = False; self.save_server()
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assertEqual(self.transport.calls, [])

    def test_snapshot_whitelist_and_top_level_policy_disabled_refuse(self):
        self.server['allowed_gpus'] = [1]; self.save_server()
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assert_no_lease()
        self.server['allowed_gpus'] = [0, 1]; self.save_server()
        policy_path = self.root/'pipeline/closure_policy.json'
        policy = module.read(policy_path); policy['enabled'] = False
        write(policy_path, policy)
        with self.assertRaises(module.Refused): self.adapter.prepare(1)
        self.assert_no_lease()
        self.assertEqual(self.transport.calls, [])

    def test_idle_gpu1_fixture_binds_exact_uuid_and_immutable_frozen_reference(self):
        binding = self.adapter.prepare(1)
        manifest = module.read(self.execution/'native_manifest.json')
        lease = module.read(self.execution/'execution_lease.json')
        self.assertEqual(binding['physical_gpu'], 1)
        self.assertEqual(manifest['gpu_uuid'], module.GPU_UUIDS[1])
        self.assertEqual(lease['native_manifest_sha256'], module.sha(self.execution/'native_manifest.json'))
        self.assertEqual(binding['frozen_preparation_sha256'], module.PREPARATION_SHA)
        self.assertEqual(binding['owner']['token'], self.token)

    def test_old_binding_readonly_status_but_no_mutating_stage_after_owner_change(self):
        self.adapter.prepare(1)
        lease_before = (self.execution/'execution_lease.json').read_bytes()
        self.rotate_owner(token='2'*32)
        status = self.adapter.status(remote=True)
        self.assertFalse(status['binding_is_current'])
        with self.assertRaises(module.Refused): self.adapter.stage()
        self.assertEqual((self.execution/'execution_lease.json').read_bytes(), lease_before)
        self.assertNotIn('stage', self.transport.calls)

    def test_existing_stage_request_is_reconciled_and_never_replayed(self):
        self.adapter.prepare(1)
        write(self.execution/'stage_request.json', {'request_id':'prior-attempt'})
        self.transport.calls.clear()
        with self.assertRaises(module.ReplayRefused): self.adapter.stage()
        self.assertEqual(self.transport.calls, ['reconcile'])

    def test_uncertain_run_keeps_request_and_only_reconciles_on_retry(self):
        self.adapter.prepare(1); self.adapter.stage()
        self.transport.timeout = True
        with self.assertRaises(module.Uncertain): self.adapter.run('smoke','champion')
        self.assertTrue((self.execution/'smoke_champion_request.json').exists())
        self.transport.calls.clear()
        with self.assertRaises(module.ReplayRefused): self.adapter.run('smoke','champion')
        self.assertEqual(self.transport.calls, ['reconcile'])

    def test_prepare_stage_pair_runs_each_mock_request_once(self):
        self.adapter.prepare(1); self.adapter.stage()
        results = self.adapter.pair()
        requests = [r for r in self.transport.request_history if r['operation']=='run']
        self.assertEqual([(r['mode'],r['target']) for r in requests], list(module.PAIRS))
        self.assertEqual(len({r['request_id'] for r in requests}), 4)
        self.assertEqual(len(results), 4)
        self.assertTrue(all(r['returncode']==0 for r in results))
        self.assertEqual(self.transport.calls.count('stage'), 1)
        self.assertEqual(self.transport.calls.count('run'), 4)

    def test_reconcile_rejects_foreign_stage(self):
        self.adapter.prepare(1); self.transport.wrong_stage = True
        with self.assertRaises(module.Refused): self.adapter.reconcile()

    def test_binding_cannot_trim_owner_context_fields(self):
        self.adapter.prepare(1)
        path = self.execution/'execution_binding.json'; binding = module.read(path)
        del binding['owner']['context_sha256']; write(path, binding)
        with self.assertRaises(module.Refused): self.adapter.stage()

    def test_self_consistent_hash_rewrite_cannot_change_manifest_identity(self):
        self.adapter.prepare(1)
        path = self.execution/'execution_binding.json'; binding = module.read(path)
        manifest_path = self.execution/'native_manifest.json'
        manifest = module.read(manifest_path); manifest['physical_gpu'] = 0
        write(manifest_path, manifest)
        binding['native_manifest_sha256'] = module.sha(manifest_path)
        lease_path = self.execution/'execution_lease.json'; lease = module.read(lease_path)
        lease['native_manifest_sha256'] = binding['native_manifest_sha256']
        write(lease_path, lease); binding['execution_lease_sha256'] = module.sha(lease_path)
        write(path, binding)
        with self.assertRaises(module.Refused): self.adapter.stage()
        self.assertNotIn('stage', self.transport.calls)


    def test_selected_gpu0_success_binds_exact_stage_uuid_manifest_and_lease(self):
        binding=self.adapter.prepare(0)
        manifest=module.read(self.execution/'native_manifest.json');lease=module.read(self.execution/'execution_lease.json')
        self.assertEqual(binding['stage'],module.REMOTE_PARENT+'/bfc_'+self.token[:8]+'_gpu0')
        for value in [binding,manifest,lease]:
            self.assertEqual(value['physical_gpu'],0);self.assertEqual(value['gpu_uuid'],module.GPU_UUIDS[0])
        self.assertEqual(self.transport.calls,['probe'])

    def test_selected_gpu1_stage_and_uuid_are_bound(self):
        binding=self.adapter.prepare(1)
        manifest=module.read(self.execution/'native_manifest.json');lease=module.read(self.execution/'execution_lease.json')
        self.assertEqual(binding['stage'],module.REMOTE_PARENT+'/bfc_'+self.token[:8]+'_gpu1')
        for value in [binding,manifest,lease]:
            self.assertEqual(value['physical_gpu'],1);self.assertEqual(value['gpu_uuid'],module.GPU_UUIDS[1])

    def test_both_registered_cards_refuse_before_any_probe_or_execution_files(self):
        write(self.root/'pipeline/running.json',{'server-4':{'0':'M211-BTC','1':'M212-BCR'}})
        for gpu in [0,1]:
            with self.subTest(gpu=gpu),self.assertRaises(module.Refused):self.adapter.prepare(gpu)
        self.assertEqual(self.transport.calls,[]);self.assert_no_lease();self.assertFalse(self.execution.exists())

    def test_selected_registered_gpu0_refuses_while_other_card_is_available(self):
        write(self.root/'pipeline/running.json',{'server-4':{'0':'M211-BTC'}})
        with self.assertRaises(module.Refused):self.adapter.prepare(0)
        self.assertEqual(self.transport.calls,[]);self.assert_no_lease()

    def test_same_fresh_execution_cannot_switch_to_other_card(self):
        self.adapter.prepare(0)
        before={n:(self.execution/n).read_bytes() for n in ['execution_binding.json','native_manifest.json','execution_lease.json']}
        self.transport.calls.clear()
        with self.assertRaises(module.Refused):self.adapter.prepare(1)
        self.assertEqual(self.transport.calls,[])
        self.assertEqual(before,{n:(self.execution/n).read_bytes() for n in before})

    def test_future_single_card_whitelist_rejects_other_card_before_probe(self):
        for allowed,selected in [([0],1),([1],0)]:
            with self.subTest(allowed=allowed):
                self.server['allowed_gpus']=allowed;self.save_server();self.rotate_owner()
                for method in [self.adapter.prepare,self.adapter.probe]:
                    with self.assertRaises(module.Refused):method(selected)
                self.assert_no_lease()
        self.assertEqual(self.transport.calls,[])

    def test_explicit_api_invalid_selected_types_refuse_before_transport(self):
        for value in [None,False,True,'0','1',2,-1,'unknown']:
            for method in [self.adapter.prepare,self.adapter.probe]:
                with self.subTest(value=value,method=method.__name__),self.assertRaises(module.Refused):method(value)
        self.assertEqual(self.transport.calls,[]);self.assert_no_lease()


if __name__ == '__main__':
    unittest.main()
