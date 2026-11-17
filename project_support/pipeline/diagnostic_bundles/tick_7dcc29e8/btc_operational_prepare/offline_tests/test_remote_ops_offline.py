"""Offline remote orchestration tests; all process/NVML calls are mocked.

Disposable fixture directories hold simulated requests/results only. No native
runtime/model, SSH, CUDA, /tmp lock or production lease is opened by these tests.
"""
import copy
from datetime import datetime,timedelta,timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock,patch

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('review_remote_ops',OUT.parent/'remote_ops.py')
remote=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'fcntl':MagicMock()}):spec.loader.exec_module(remote)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')


class RemoteOperationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='.remote_fixture_',dir=OUT)
        self.addCleanup(temp.cleanup)
        self.assertTrue(Path(temp.name).resolve().is_relative_to(OUT.resolve()))
        self.parent=Path(temp.name)/'pipeline';self.parent.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(remote,'PARENT',self.parent).start()
        self.token='a'*32;self.stage=self.parent/('btc_'+self.token[:8]);self.stage.mkdir()
        now=datetime.now(timezone.utc)
        self.binding={'project':'cluster_project','candidate_id':remote.CANDIDATE,'code_commit':remote.COMMIT,
            'owner':{'token':self.token,'generated_at':(now-timedelta(minutes=2)).isoformat(),
                     'deadline_at':(now+timedelta(minutes=50)).isoformat()},
            'stage':str(self.stage),'physical_gpu':0,'gpu_uuid':remote.GPU_UUIDS[0],
            'native_manifest_sha256':'b'*64,'execution_lease_sha256':'c'*64,'runtime_code_commit':'d'*40}
        self.request={'project':'cluster_project','candidate_id':remote.CANDIDATE,'code_commit':remote.COMMIT,
            'stage':str(self.stage),'token':self.token,'request_id':'e'*32,'operation':'run','physical_gpu':0,
            'gpu_uuid':remote.GPU_UUIDS[0],'native_manifest_sha256':'b'*64,'mode':'smoke','target':'candidate'}
        self.command=['/mock/env/bin/python','-B',str(self.stage/'worker.py'),'--lease',str(self.stage/'execution_lease.json'),
            '--mode','smoke','--target','candidate']
        self.info={'pid':123,'start_ticks':'777','argv':self.command,'state':'S'}
        self.result={'candidate_id':remote.CANDIDATE,'code_commit':remote.COMMIT,'goal_sha256':remote.GOAL,
            'mode':'smoke','target':'candidate','model_package':'framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_btc',
            'execution_completed':True}

    def artifacts(self):
        write(self.stage/'smoke_candidate_request.json',self.request)
        write(self.stage/'smoke_candidate_started.json',{'identity':remote.identity(self.binding,self.request),
            'mode':'smoke','target':'candidate','pid':123,'process_identity':self.info,'command':self.command})
        write(self.stage/'smoke_candidate_completed.json',{'identity':remote.identity(self.binding,self.request),
            'command':self.command,'returncode':0,'result':self.result})
        write(self.stage/'smoke_candidate_result.json',self.result)

    def reconcile(self):
        with patch.object(remote,'exact_workers',return_value=[self.info]),patch.object(remote,'process_info',return_value=self.info),\
             patch.object(remote.subprocess,'check_output',side_effect=['0, '+remote.GPU_UUIDS[0], '123, 45']),\
             patch.object(remote,'write',side_effect=AssertionError('Readonly reconcile wrote a file')),\
             patch.object(remote,'require_fresh',side_effect=AssertionError('Readonly reconcile renewed/validated old lease')),\
             patch.object(remote.subprocess,'Popen',side_effect=AssertionError('Readonly reconcile started process')):
            return remote.reconcile_operation({'binding':self.binding,'request_id':self.request['request_id']})

    def test_readonly_expired_binding_keeps_exact_pid_and_result_identity(self):
        self.binding['owner']['generated_at']='2020-01-01T00:00:00+00:00'
        self.binding['owner']['deadline_at']='2020-01-01T01:00:00+00:00'
        self.artifacts();found=self.reconcile();item=found['requests'][0]
        for field in ['identity_matches','started_identity_matches','started_command_matches','original_pid_still_same',
                      'completed_identity_matches','completed_command_matches','completed_result_identity_matches','result_identity_matches']:
            self.assertTrue(item[field],field)
        self.assertTrue(found['read_only']);self.assertTrue(found['gpu_identity_matches'])

    def test_foreign_command_never_counts_as_original_pid(self):
        self.command[2]='/foreign/worker.py';self.artifacts()
        item=self.reconcile()['requests'][0]
        self.assertFalse(item['started_command_matches']);self.assertFalse(item['original_pid_still_same'])

    def test_pid_reuse_never_counts_as_original(self):
        self.artifacts();self.info=copy.deepcopy(self.info);self.info['start_ticks']='999'
        self.assertFalse(self.reconcile()['requests'][0]['original_pid_still_same'])

    def test_wrong_result_commit_and_mode_are_reported_false(self):
        self.result['code_commit']='f'*40;self.result['mode']='resources';self.artifacts()
        item=self.reconcile()['requests'][0]
        self.assertFalse(item['result_identity_matches']);self.assertFalse(item['completed_result_identity_matches'])

    def test_filename_request_target_mismatch_is_reported_false(self):
        self.request['target']='champion';self.artifacts()
        self.assertFalse(self.reconcile()['requests'][0]['identity_matches'])

    def test_malformed_request_is_explicit_unknown(self):
        write(self.stage/'smoke_candidate_request.json',{'request_id':self.request['request_id']})
        item=self.reconcile()['requests'][0]
        self.assertFalse(item['identity_matches']);self.assertIn('read_error',item)

    def test_expired_mutation_never_starts_a_process(self):
        self.binding['owner']['generated_at']='2020-01-01T00:00:00+00:00'
        self.binding['owner']['deadline_at']='2020-01-01T01:00:00+00:00'
        write(self.stage/'stage_completed.json',{'verified':True})
        with patch.object(remote.subprocess,'Popen') as popen:
            with self.assertRaises(RuntimeError):remote.run_operation({'binding':self.binding,'request':self.request})
            popen.assert_not_called()
        self.assertFalse((self.stage/'smoke_candidate_request.json').exists())

    def test_existing_remote_request_is_never_replayed(self):
        self.artifacts();write(self.stage/'stage_completed.json',{'verified':True})
        with patch.object(remote,'require_idle'),patch.object(remote,'native_verify'),patch.object(remote.subprocess,'Popen') as popen:
            with self.assertRaises(RuntimeError):remote.run_operation({'binding':self.binding,'request':self.request})
            popen.assert_not_called()

    def test_wait_timeout_neither_kills_nor_restarts_worker(self):
        write(self.stage/'stage_completed.json',{'verified':True})
        fake=MagicMock();fake.pid=123;fake.wait.side_effect=remote.subprocess.TimeoutExpired('fixture',660)
        with patch.object(remote,'require_idle'),patch.object(remote,'native_verify'),\
             patch.object(remote,'process_info',return_value=self.info),patch.object(remote,'exact_workers',return_value=[]),\
             patch.object(remote.subprocess,'Popen',return_value=fake) as popen:
            result=remote.run_operation({'binding':self.binding,'request':self.request})
        self.assertEqual(result['certainty'],'uncertain');self.assertEqual(result['pid'],123)
        self.assertEqual(popen.call_count,1);fake.kill.assert_not_called();fake.terminate.assert_not_called()
        self.assertTrue((self.stage/'smoke_candidate_started.json').exists())
        self.assertFalse((self.stage/'smoke_candidate_completed.json').exists())

    def test_wrong_gpu_and_stage_refused_before_remote_action(self):
        wrong=copy.deepcopy(self.binding);wrong['gpu_uuid']=remote.GPU_UUIDS[1]
        with self.assertRaises(RuntimeError):remote.binding_stage(wrong)
        wrong=copy.deepcopy(self.binding);wrong['stage']=str(self.parent/'other_project')
        with self.assertRaises(RuntimeError):remote.binding_stage(wrong)

    def test_gpu1_binding_and_probe_refuse_before_inventory_or_process_action(self):
        wrong=copy.deepcopy(self.binding);wrong['physical_gpu']=1;wrong['gpu_uuid']=remote.GPU_UUIDS[1]
        with patch.object(remote.subprocess,'check_output',side_effect=AssertionError('No GPU1 inventory')) as query,\
             patch.object(remote.subprocess,'Popen',side_effect=AssertionError('No native process')) as popen:
            with self.assertRaises(RuntimeError):remote.binding_stage(wrong)
            with self.assertRaises(RuntimeError):remote.probe(1)
            query.assert_not_called();popen.assert_not_called()


if __name__=='__main__':unittest.main()
