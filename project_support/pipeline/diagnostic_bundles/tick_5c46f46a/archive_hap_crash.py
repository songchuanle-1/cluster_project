"""Canonical, exact-log HAP crash archival plus truthful research dispositions."""
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[2]
TOKEN='5c46f46a17514a6f984ad08364f0c7cc'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import pipeline_monitor as monitor

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def ref(path):return dict(path=path.relative_to(PROJECT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def atomic(path,value):
    temporary=path.with_name(path.name+'.'+TOKEN+'.tmp')
    with temporary.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)

def main():
    assert os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
    owner=read(PROJECT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN
    lock=monitor.acquire_lock(str(PROJECT));assert lock is not None,'Project lifecycle lock busy'
    original_pull=monitor.pull_log
    try:
        proof=read(BASE/'hap_original_log_evidence.json')
        checkpoint=read(BASE/'hap_checkpoint_evidence.json')['data']
        observation=read(BASE/'hap_crash_remote_inspection.json')['data']
        assert observation['hap_pid_absent'] and checkpoint['cpu_inspection']['meta']['epoch']==18
        assert checkpoint['cpu_inspection']['cuda_initialized'] is False
        local=Path(proof['log_local']);assert hashlib.sha256(local.read_bytes()).hexdigest()==proof['sha256']==observation['log']['sha256']
        assert proof['last_train_progress']==[19,50,3665,4686]
        queue=monitor.load_queue(str(PROJECT))
        tasks=[t for t in queue['gpu_queues']['server-4'] if t.get('id')=='M207-HAP']
        assert len(tasks)==1
        task=tasks[0]
        assert task['status']=='running' and task['pid']==979955 and task['gpu']=='0'
        assert task['code_commit']=='f51823bbddf0f8095a9a5813bf1f8169e3d7edb0'
        assert task['admission_receipt']=='pipeline/admissions/M207-HAP.json' and task['launch_verified'] is True
        assert task['log']==proof['remote_log'] and 'ctf_hcg_csort_hap/' in task['config']
        before_task=copy.deepcopy(task)
        m206_before=copy.deepcopy([t for t in queue['gpu_queues']['server-4'] if t.get('id')=='M206-CGCA'])
        def exact_pull(project,host,user,remote_log,cfg_name,state,srv_name=''):
            assert Path(project)==PROJECT and (host,user,srv_name,state)==('192.168.1.115','songcl','server-4','crashed')
            assert remote_log==proof['remote_log'] and cfg_name==Path(task['config']).stem
            assert hashlib.sha256(local.read_bytes()).hexdigest()==proof['sha256']
            return str(local)
        monitor.pull_log=exact_pull
        events=[]
        # Explicit native Traceback + exact original PID absence proves a crash.
        # No deathwatch counters, broad latest-log lookup, repair or launch are invoked.
        monitor.finalize_task(str(PROJECT),queue,'server-4','192.168.1.115','songcl',task,
            Path(task['config']).stem,'crashed',checkpoint['cpu_inspection']['meta']['best_miou'],
            '19/50 interrupted; full checkpoint epoch18', '0',proof['remote_log'],events)
        assert [t for t in queue['gpu_queues']['server-4'] if t.get('id')=='M206-CGCA']==m206_before
        work_path=PROJECT/'pipeline/research_work.json';work=read(work_path)
        by_id={c['experiment_id']:c for c in work['candidates'] if c.get('experiment_id')}
        now=dt.datetime.now(dt.timezone.utc);retry=(now+dt.timedelta(hours=1)).isoformat()
        all_proofs=[ref(BASE/name) for name in ('gpu0_observation.json','hap_crash_remote_inspection.json',
            'hap_original_log_evidence.json','hap_checkpoint_evidence.json','cpu_tensor_numpy_check.json',
            'hap_source_integrity.json','dataloader_source_diagnosis.json','archive_contract_review.json')]
        hap=by_id['M207-HAP']
        hap.update(stage='blocked',resume_stage='training',training_status='crashed',failure_scope='implementation',
            blocker_kind='human_authorization',human_hold=True,resume_authorized=False,blocked_at=now.isoformat(),retry_after=retry,
            blocker='Original HAP run crashed in DataLoader Tensor-to-NumPy conversion. Full epoch18 checkpoint is preserved, root cause unresolved. Canonical cluster_resume requires explicit human authorization for this exact full-state resume; GPU0 also has live foreign/unregistered compute occupation.',
            unblock_condition='Explicit human authorization for M207-HAP exact f518/native-YAML/epoch18 full resume on server4GPU0, then fresh source/checkpoint/environment/data/UUID/idleness/exclusive-lease checks. Never use GPU1 or cold-start.',
            next_action='Prepare the exact full-state resume for review and ask once for the missing human resume grant required by cluster_resume.validate. Fresh CPU interop passed but original long-worker/input failure is not reproduced or fixed. Preserve original seed1999/epochs50/maxiters70/4workers, all negative evidence, and original checkpoint; wait for authorized idle GPU0. M206 remains manually paused.',
            resume_from=checkpoint['resume_from'],checkpoint_sha256=checkpoint['checkpoint_sha256'],
            saved_meta=checkpoint['cpu_inspection']['meta'])
        hap['evidence'].extend(x for x in all_proofs if x not in hap['evidence'])
        m206=by_id['M206-CGCA']
        m206.update(stage='blocked',resume_stage='training',blocker_kind='human_authorization',
            blocked_at=now.isoformat(),retry_after=retry,
            blocker='Direct human paused M206 and released GPU1 to others. Current queue user_paused/dispatch_hold/resume_authorized=false is unchanged.',
            unblock_condition='A later explicit human M206 resume instruction plus exact admitted source/full-checkpoint/runtime/current authorized resource validation. GPU1 idleness or HAP crash is not permission.',
            next_action='Preserve manually paused M206 and full epoch24 checkpoint. Do not resume/migrate/cold-start on any GPU without a later explicit human instruction; GPU1 remains released to others.')
        pause_ref=ref(BASE/'source_and_pause_reuse_check.json')
        if pause_ref not in m206['evidence']:m206['evidence'].append(pause_ref)
        for name in ('M208-HRC','M209-PSBR'):
            c=by_id[name]
            c.update(blocker_kind='live_external_gpu_occupation',blocked_at=now.isoformat(),retry_after=retry,
                blocker='HAP original process has crashed and is canonically archived, but physical GPU0 has fresh foreign/unregistered compute contexts. Only server4GPU0 is authorized; GPU1 belongs to others.',
                unblock_condition='Fresh authorized server4 physicalGPU0 with no foreign or unregistered compute context, correct UUID and current ownership/exclusive leases. GPU1 becoming idle never authorizes use.')
            c['next_action']=c['next_action'].replace('GPU0 only: preserve HAP until natural completion; then verify','GPU0 only: HAP crash is archived; preserve all foreign work and wait for a real GPU0 opening, then verify')
            for r in (ref(BASE/'gpu0_observation.json'),ref(BASE/'hap_crash_remote_inspection.json'),ref(BASE/'source_and_pause_reuse_check.json')):
                if r not in c['evidence']:c['evidence'].append(r)
        context=read(PROJECT/'pipeline/headless/.tick_model_view.json')
        work['tick_attempt']=dict(tick_started_at=context['generated_at'],candidate_id=by_id['M208-HRC']['id'],
            kind='resource_check',result='blocked',command='python -B pipeline/diagnostic_bundles/tick_5c46f46a/collect_hap_crash.py',
            observation='Strict pinned server4 only physicalGPU0 observation: HAP originalPID979955 absent/native DataLoader crash; GPU0 still has non-HAP compute context181902/1638MiB at04:19UTC. Native HRC/PSBR tests were not run; GPU1 not queried or used.',
            evidence=[ref(BASE/'hap_crash_remote_inspection.json')])
        work['updated_at']=now.isoformat()
        work['next_action']='HAP exact full-state resume awaits human grant and runtime/resource validation. Preserve M206 manual pause and GPU1 exclusion. HRC/PSBR unchanged prepared packages await genuine authorized GPU0 opening for native pair checks/admission.'
        atomic(work_path,work)
        after=monitor.load_experiment(str(PROJECT),'M207-HAP')
        result=dict(recorded_at=now.isoformat(),tick_token=TOKEN,state='crashed',
            canonical_function='pipeline_monitor.finalize_task',exact_log_adapter=True,events=events,
            original_queue_task=before_task,archived_experiment=after,
            running_after=monitor.load_running(str(PROJECT)),
            queue_after=monitor.load_queue(str(PROJECT)),m206_queue_unchanged=True,
            deathwatch_incremented=False,signals_sent=False,training_started=False,
            scientific_rejection=False,full_checkpoint=checkpoint['resume_from'],
            checkpoint_sha256=checkpoint['checkpoint_sha256'],evidence=all_proofs)
        target=BASE/'hap_terminal_archive.json'
        with target.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print(json.dumps(dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            archived_status=after['status'],running_after=result['running_after'],m206_queue_unchanged=True),ensure_ascii=False))
    finally:
        monitor.pull_log=original_pull
        lock.close()

if __name__=='__main__':main()
