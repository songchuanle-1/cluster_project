"""Reconcile asynchronous CUDA teardown, validate resume contract, and ready the queue."""
import copy
import importlib.util
import json
import msvcrt
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('manual_pause', HERE / 'pause_m206.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SKILL = Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0, str(SKILL))
import closure
import cluster_resume
import pipeline_monitor as pm


def strict_ssh(host, user, command):
    assert host == '192.168.1.115' and user == 'songcl'
    result = subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',
        '-o','ConnectTimeout=10',user+'@'+host,command],capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=150)
    assert result.returncode == 0, result.stderr[-3000:]
    return result.stdout.strip()


def main():
    m.guard()
    lock = (m.ROOT / '.pipeline.lock').open('a+b')
    lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    try:
        m.guard()
        reconciliation = m.load(HERE/'stop_reconciliation.json')
        data = reconciliation['data']
        assert reconciliation['returncode']==0
        assert data['pids']['3873690']['exists'] is False
        assert data['pids']['3842306']['exists'] is True
        assert 'ctf_hcg_csort_mdc.yaml' in data['pids']['3842306']['args']
        assert not any('GPU-7f82edb9-f620-8045-caea-a75232265cd1' in line
            for line in data['contexts'].splitlines())
        stop_path=HERE/'stop_confirmation_reconciled.json'
        m.save(stop_path,{'observed_at':m.now(),'stop_confirmed':True,'target_pid':3873690,
            'target_process_absent':True,'target_gpu1_context_absent':True,'gpu1_released':True,
            'protected_m205_pid':3842306,'protected_starttime':data['pids']['3842306']['starttime'],
            'protected_continues':True,'reconciliation':m.evidence(HERE/'stop_reconciliation.json'),
            'earlier_stop_attempt':m.evidence(HERE/'exact_stop_confirmation.json'),
            'earlier_observer_failure':'Only final NVML-context assertion failed after exact group termination; CUDA teardown subsequently cleared. No repeat kill.'},exclusive=True)
        queue=m.load(m.ROOT/'pipeline/queue.json')
        task=next(x for x in queue['gpu_queues']['server-4'] if x['id']=='M206-CGCA')
        assert task['status']=='waiting' and task['dispatch_phase']=='pause_stop_pending'
        assert task['gpu']=='0' and task['resume_from']==m.SNAPSHOT
        original_queue=m.load(HERE/'before_pipeline__queue.json')
        original_m205=next(x for x in original_queue['gpu_queues']['server-4'] if x['id']=='M205-MDC')
        assert next(x for x in queue['gpu_queues']['server-4'] if x['id']=='M205-MDC')==original_m205
        original_proof=m.load(m.ROOT/task['resume_checkpoint_evidence']['path'])
        final_proof=copy.deepcopy(original_proof)
        final_proof.update(lineage={'id':'M206-CGCA','config':m.CONFIG,'code_commit':m.COMMIT,
            'source_checkpoint':m.ORIGINAL,'original_pid':3873690,'original_gpu':'1',
            'original_log':task['paused_run']['log'],'original_run_timestamp':'20261021_051530',
            'original_queue_record':m.evidence(HERE/'before_pipeline__queue.json'),
            'native_checkpoint_capture':m.evidence(HERE/'checkpoint_capture.json')},
            runtime_binary_snapshot=m.evidence(HERE/'runtime_binary_readonly_snapshot.json'),
            stop_confirmation=m.evidence(stop_path))
        proof_path=HERE/'checkpoint_evidence_final.json'
        m.save(proof_path,final_proof,exclusive=True)
        task['resume_checkpoint_evidence']=m.evidence(proof_path)
        task['paused_run']['stop_confirmation']=m.evidence(stop_path)
        task['paused_at']=m.now()
        task['dispatch_phase']='resume_waiting'
        # This stays in place until all local admission and actual remote source checks pass.
        task['dispatch_hold']='Resume contract validation in progress; never cold-start.'
        server=pm.load_servers(str(m.ROOT))['server-4']
        assert server['allowed_gpus']==[0] and server['name']=='server-4'
        assert pm.load_servers(str(m.ROOT))['server-3']['allowed_gpus']==[]
        assert pm.load_servers(str(m.ROOT))['server-3']['dispatch_enabled'] is False
        closure.admission(m.ROOT,task)
        contract=cluster_resume.validate(m.ROOT,server,task,'0')
        cluster_resume.verify_source(m.ROOT,m.ROOT/'Cluster',server,task,'0',strict_ssh)
        # Actual checkpoint SHA was independently re-read after the CPU inspection.
        runtime=m.load(HERE/'runtime_binary_readonly_snapshot.json')['data']
        assert runtime['checkpoint_unchanged_sha256']==contract['checkpoint_sha256']
        assert any(v['sha256']=='c86f516858d480e2583a437deb598279bc626e74975a060b17d75bf03f630033'
            for v in runtime['files'].values())
        task.pop('dispatch_hold',None)
        task.pop('admission_error',None)
        task.update(launch_verified=False,launch_verification='paused_pending_resume',
            resume_validated_at=m.now(),resume_validation='full_checkpoint_and_exact_admitted_remote_source')
        task['note']='User paused GPU1. SAME experiment resumes full checkpoint on server4 GPU0 after it is free; optimizer/scheduler/epoch/best/patience preserved, no cold start.'
        m.save(m.ROOT/'pipeline/queue.json',queue)
        running=m.load(m.ROOT/'pipeline/running.json')
        assert running['server-4']['0']=='M205-MDC'
        assert running['server-4'].get('1')=='M206-CGCA'
        del running['server-4']['1']
        m.save(m.ROOT/'pipeline/running.json',running)
        exp_path=m.ROOT/'pipeline/experiments/M206-CGCA.json'
        exp=m.load(exp_path)
        exp.update(status='waiting',server='server-4',gpu='0',paused_run=task['paused_run'],
            resume_from=task['resume_from'],resume_authorization=task['resume_authorization'],
            resume_checkpoint_evidence=task['resume_checkpoint_evidence'],
            launch_verified=False,launch_verification='paused_pending_resume')
        for key in ('pid','log','launched'):exp.pop(key,None)
        meta=final_proof['cpu_inspection']['meta']
        exp.setdefault('history',[]).append({'ts':m.now(),'action':'user_paused_and_queued_full_resume',
            'from_gpu':'1','to_gpu':'0','checkpoint':task['resume_from'],
            'checkpoint_sha256':contract['checkpoint_sha256'],'meta':meta,
            'stop_confirmation':m.evidence(stop_path)})
        m.save(exp_path,exp)
        work=m.load(m.ROOT/'pipeline/research_work.json')
        cgca=next(x for x in work['candidates'] if x['id']==m.CID)
        assert cgca['stage']=='training'
        cgca.update(training_status='paused_waiting_resume',
            next_action='User paused M206 GPU1; same admitted source/full epoch8 checkpoint queued to server4 GPU0. Wait for M205/actual GPU0 vacancy, then verified native --resume starts epoch9 with optimizer/scheduler/best/patience. No cold start.')
        for file in (m.ROOT/task['resume_authorization']['path'],proof_path,stop_path):
            ev=m.evidence(file)
            if ev not in cgca['evidence']:cgca['evidence'].append(ev)
        hap=next(x for x in work['candidates'] if x['id']=='hierarchy-affine-coarse-to-fine-prolongation')
        hap.update(required_server='server-4',required_gpu='0',native_status='pending_resource',
            blocker='Latest direct user scope is server4 GPU0 ONLY. M205 occupies GPU0 and M206 same-experiment full-checkpoint resume is queued first. GPU1 is released but unauthorized for new project work.',
            next_action='Respect GPU0-only scope. Prioritize existing queued M206 full resume; HAP native checks wait for an actual authorized GPU0 slot and fresh current lease/stage with reviewed worker_v2. Do not use server4GPU1/server3GPU1.',
            unblock_condition='Fresh live server4 GPU0 idle, no other CUDA contexts and required ownership locks; existing waiting M206 resume takes precedence. GPU1 availability or old dual-card grant does not unblock HAP.')
        m.save(m.ROOT/'pipeline/research_work.json',work)
        tests={'new_resume_tests':16,'root_command':'python -B -m unittest test_cluster_resume',
            'root_result':'PASS 16 tests','agent_full_regression':'PASS 132 tests, no GPU or launch',
            'independent_review':'Partial-proof cold-start gap found and fixed; requested detects any of three resume intent fields.',
            'implementation_files':[{'path':str(SKILL/name),'sha256':m.digest(SKILL/name)}
                for name in ('cluster_resume.py','closure.py','pipeline_monitor.py','test_cluster_resume.py')]}
        validation_path=HERE/'resume_queue_validation.json'
        m.save(validation_path,{'validated_at':m.now(),'contract':contract,'tests':tests,
            'original_admission_passed':True,'actual_admitted_remote_source_verified':True,
            'current_local_HEAD_different_but_original_remote_source_preserved':True,
            'no_sync_or_cold_launch':True,'queue_status':'waiting','queue_gpu':'0','dispatch_hold':False,
            'same_experiment':'M206-CGCA','resume_start_epoch':meta['epoch']+1,
            'model_optimizer_scheduler_best_patience_preserved':True,
            'resource_scope':{'server-4':[0],'server-3':[],'server-6':[]},
            'stop_confirmation':m.evidence(stop_path),'checkpoint_evidence':m.evidence(proof_path)},exclusive=True)
        print(json.dumps({'status':'RESUME_QUEUED_READY_GPU0','checkpoint_epoch':meta['epoch'],
            'resume_start_epoch':meta['epoch']+1,'best_miou':meta['best_miou'],
            'gpu0_m205_preserved':True,'gpu1_released':True,'ready_waiting_resume':True,
            'validation':m.evidence(validation_path)},ensure_ascii=False),flush=True)
    finally:
        lock.close()


if __name__=='__main__':main()
