"""External GPU occupation must be real, current, complete and scope-bound."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import closure


class ExternalOccupationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.headless=self.root/'pipeline/headless'
        (self.headless/'.foreground.lockdir').mkdir(parents=True)
        self.now=datetime.now(timezone.utc)
        self.token='a'*32
        self.config=dict(servers={'server-2':dict(host='192.0.2.2',user='test',
            role='gpu_server',expected_hostname='test-node',allowed_gpus=[0],max_tasks_per_gpu=1)})
        self.server=dict(name='server-2',allowed_gpus=[0],max_tasks_per_gpu=1)
        self.context=dict(project=self.root.name,generated_at=(self.now-timedelta(seconds=20)).isoformat(),
            deadline_at=(self.now+timedelta(hours=1)).isoformat(),mode='event',
            queue=dict(servers=[self.server],active_tasks=[]))
        self.queue=dict(gpu_queues={'server-2':[]})
        self.proof=dict(schema_version=1,kind='exclusive_gpu_occupation',complete=True,read_only=True,
            project=self.root.name,token=self.token,snapshot_generated_at=self.context['generated_at'],
            observed_at=self.now.isoformat(),candidate_ids=['probe'],
            scope=dict(server='server-2',host='192.0.2.2',user='test',allowed_gpus=[0],max_tasks_per_gpu=1),
            queries=dict(hostname=dict(rc=0,stdout='test-node\n'),
                gpu=dict(rc=0,stdout='0, GPU-0000, 90, 22000, 24576\n'),
                compute=dict(rc=0,stdout='GPU-0000, 12345\n')))
        self.candidate=dict(id='probe',stage='blocked',blocker='Foreign compute occupies GPU0',
            blocker_kind='exclusive_gpu_slot',required_server='server-2',
            retry_after=(self.now+timedelta(hours=1)).isoformat(),unblock_condition='Fresh exclusive idle slot',
            next_action='Run native probe after real idleness',evidence=[])
        self.bind_scope()

    def bind_scope(self):
        cfg=self.root/'SERVERS.yaml'
        cfg.write_text(json.dumps(self.config),encoding='utf-8')
        snapshot=self.headless/'.tick_context.json'
        snapshot.write_text(json.dumps(self.context),encoding='utf-8')
        owner=dict(token=self.token,generated_at=self.context['generated_at'],
            context_sha256=closure.digest(snapshot),deadline_at=self.context['deadline_at'])
        (self.headless/'.foreground.lockdir/owner.json').write_text(json.dumps(owner))
        self.proof['snapshot_sha256']=owner['context_sha256']
        self.proof['servers_sha256']=closure.digest(cfg)
        self.proof['snapshot_generated_at']=self.context['generated_at']

    def save(self):
        log=self.root/'queries.json'
        log.write_text(json.dumps(self.proof['queries']),encoding='utf-8')
        self.proof['raw_log']=dict(path='queries.json',sha256=closure.digest(log))
        path=self.root/'occupation.json'
        path.write_text(json.dumps(self.proof),encoding='utf-8')
        ref=dict(path='occupation.json',sha256=closure.digest(path))
        self.candidate['occupation_evidence']=ref
        self.candidate['evidence']=[ref,self.proof['raw_log']]

    def validate(self):
        self.save()
        closure.validate_work(self.root,self.context,[self.candidate],self.queue)

    def reject(self):
        with self.assertRaises(ValueError):self.validate()

    def test_fresh_foreign_compute_allows_empty_project_queue(self):
        self.validate()

    def test_idle_gpu_cannot_be_disguised_by_summary(self):
        self.proof['queries']['gpu']['stdout']='0, GPU-0000, 0, 98, 24576\n'
        self.proof['queries']['compute']['stdout']=''
        self.proof['idle_authorized_gpus']=[]
        self.reject()

    def test_foreign_pid_blocks_even_when_utilization_and_memory_are_low(self):
        self.proof['queries']['gpu']['stdout']='0, GPU-0000, 0, 98, 24576\n'
        self.validate()

    def test_high_graphics_memory_without_compute_pid_is_busy(self):
        self.proof['queries']['compute']['stdout']=''
        self.validate()

    def test_busy_unapproved_device_does_not_hide_allowed_idle_device(self):
        self.proof['queries']['gpu']['stdout']='0, GPU-0000, 0, 98, 24576\n1, GPU-1111, 99, 22000, 24576\n'
        self.proof['queries']['compute']['stdout']='GPU-1111, 12345\n'
        self.reject()

    def test_any_allowed_idle_device_rejects_block(self):
        self.config['servers']['server-2']['allowed_gpus']=[0,1]
        self.server['allowed_gpus']=[0,1]
        self.proof['scope']['allowed_gpus']=[0,1]
        self.proof['queries']['gpu']['stdout']+='1, GPU-1111, 0, 98, 24576\n'
        self.bind_scope()
        self.reject()

    def test_missing_authorized_device_is_unknown_not_busy(self):
        self.proof['queries']['gpu']['stdout']='1, GPU-1111, 90, 22000, 24576\n'
        self.reject()

    def test_query_failure_is_not_resource_block(self):
        for query in ('hostname','gpu','compute'):
            with self.subTest(query=query):
                old=self.proof['queries'][query]['rc']
                self.proof['queries'][query]['rc']=1
                self.reject()
                self.proof['queries'][query]['rc']=old

    def test_malformed_unknown_and_duplicate_gpu_fields_are_rejected(self):
        for row in ['0, GPU-0000, N/A, 22000, 24576\n',
                    '0, GPU-0000, nan, 22000, 24576\n',
                    '0, GPU-0000, 0, -1, 24576\n',
                    '0, GPU-0000, 90, 22000, 24576\n0, GPU-1111, 90, 22000, 24576\n']:
            with self.subTest(row=row):
                self.proof['queries']['gpu']['stdout']=row
                self.reject()

    def test_bad_compute_pid_is_rejected(self):
        self.proof['queries']['compute']['stdout']='GPU-0000, N/A\n'
        self.reject()

    def test_wrong_host_hostname_whitelist_or_candidate_is_rejected(self):
        original=copy.deepcopy(self.proof)
        for change in ('host','hostname','allowed','candidate','candidate_string'):
            self.proof=copy.deepcopy(original)
            if change=='host':self.proof['scope']['host']='192.0.2.99'
            elif change=='hostname':self.proof['queries']['hostname']['stdout']='other-node'
            elif change=='allowed':self.proof['scope']['allowed_gpus']=[1]
            elif change=='candidate':self.proof['candidate_ids']=['other']
            else:self.proof['candidate_ids']='probe'
            with self.subTest(change=change):self.reject()

    def test_previous_token_and_wrong_snapshot_are_rejected(self):
        original=copy.deepcopy(self.proof)
        for key,value in [('token','b'*32),('snapshot_sha256','0'*64),
                          ('snapshot_generated_at',(self.now-timedelta(days=1)).isoformat())]:
            self.proof=copy.deepcopy(original)
            self.proof[key]=value
            with self.subTest(key=key):self.reject()

    def test_stale_future_and_pre_snapshot_observations_are_rejected(self):
        self.context['generated_at']=(self.now-timedelta(minutes=20)).isoformat()
        self.bind_scope()
        for seconds in (-600,30,-1300):
            self.proof['observed_at']=(self.now+timedelta(seconds=seconds)).isoformat()
            with self.subTest(seconds=seconds):self.reject()

    def test_changed_server_configuration_requires_new_observation(self):
        self.save()
        (self.root/'SERVERS.yaml').write_text('{}')
        with self.assertRaises(ValueError):
            closure.validate_work(self.root,self.context,[self.candidate],self.queue)

    def test_evidence_must_be_hash_valid_and_bound_to_candidate(self):
        self.save()
        (self.root/'occupation.json').write_text('{}')
        with self.assertRaises(ValueError):
            closure.validate_work(self.root,self.context,[self.candidate],self.queue)
        self.save()
        self.candidate['evidence']=[]
        with self.assertRaises(ValueError):
            closure.validate_work(self.root,self.context,[self.candidate],self.queue)

    def test_fake_reserved_gpu_summary_cannot_hide_idle_gpu(self):
        self.proof['queries']['gpu']['stdout']='0, GPU-0000, 0, 98, 24576\n'
        self.proof['queries']['compute']['stdout']=''
        self.proof['reserved_gpu_ids']=[0]
        self.reject()

    def test_raw_query_tampering_is_rejected(self):
        self.save()
        (self.root/'queries.json').write_text('{}')
        with self.assertRaises(ValueError):
            closure.validate_work(self.root,self.context,[self.candidate],self.queue)

    def test_collector_preserves_user_pause_and_queue_bytes(self):
        import gpu_occupation
        import pipeline_monitor
        self.context['experiment_first']={'enabled':True}
        self.bind_scope()
        pending=self.headless/'.tick_context_state.next.json'
        pending.write_text('{}')
        owner_path=self.headless/'.foreground.lockdir/owner.json'
        owner=json.loads(owner_path.read_text())
        owner.update(thread_id='test-thread',pending_sha256=closure.digest(pending))
        owner_path.write_text(json.dumps(owner))
        paused=dict(id='paused',stage='blocked',required_server='server-2',
            blocker_kind='human_authorization',next_action='Await explicit user instruction',evidence=[])
        work_path=self.root/'pipeline/research_work.json'
        work_path.write_text(json.dumps(dict(candidates=[self.candidate,paused])))
        queue_path=self.root/'pipeline/queue.json'
        queue_path.write_text(json.dumps(self.queue))
        original_queue=queue_path.read_bytes()
        original_work=work_path.read_bytes()
        with patch.dict('os.environ',{'CODEX_THREAD_ID':'test-thread'}), \
                patch.object(pipeline_monitor,'ssh',return_value=json.dumps(self.proof['queries'])), \
                patch.object(pipeline_monitor,'acquire_lock',return_value=Mock()):
            result=gpu_occupation.collect(self.root,self.token,'server-2')
        updated=json.loads(work_path.read_text())
        self.assertEqual(result['state']['idle_gpu_ids'],[])
        self.assertEqual(updated['candidates'][1],paused)
        self.assertEqual(queue_path.read_bytes(),original_queue)

        work_path.write_bytes(original_work)
        failed=copy.deepcopy(self.proof['queries'])
        failed['compute']['rc']=1
        with patch.dict('os.environ',{'CODEX_THREAD_ID':'test-thread'}), \
                patch.object(pipeline_monitor,'ssh',return_value=json.dumps(failed)), \
                patch.object(pipeline_monitor,'acquire_lock',return_value=Mock()), \
                self.assertRaises(ValueError):
            gpu_occupation.collect(self.root,self.token,'server-2',label='query_failed')
        self.assertEqual(work_path.read_bytes(),original_work)
        self.assertEqual(queue_path.read_bytes(),original_queue)
        self.assertEqual(updated['tick_attempt']['result'],'blocked')
        closure.validate_work(self.root,self.context,updated['candidates'][:1],self.queue)
        queries=copy.deepcopy(self.proof['queries'])
        queries['gpu']['stdout']='0, GPU-0000, 0, 98, 24576\n'
        queries['compute']['stdout']=''
        with patch.dict('os.environ',{'CODEX_THREAD_ID':'test-thread'}), \
                patch.object(pipeline_monitor,'ssh',return_value=json.dumps(queries)), \
                patch.object(pipeline_monitor,'acquire_lock',return_value=Mock()):
            idle=gpu_occupation.collect(self.root,self.token,'server-2',label='now_idle')
        after_idle=json.loads(work_path.read_text())
        self.assertEqual(idle['state']['idle_gpu_ids'],[0])
        self.assertEqual(after_idle['candidates'][0]['stage'],'validation')
        self.assertNotIn('blocker_kind',after_idle['candidates'][0])
        self.assertEqual(after_idle['candidates'][1],paused)
        self.assertEqual(queue_path.read_bytes(),original_queue)

    def test_real_current_queue_claim_keeps_its_slot(self):
        self.proof['queries']['gpu']['stdout']='0, GPU-0000, 0, 98, 24576\n'
        self.proof['queries']['compute']['stdout']=''
        self.queue['gpu_queues']['server-2']=[dict(id='other',status='claiming',gpu=0)]
        self.validate()


if __name__=='__main__':unittest.main()
