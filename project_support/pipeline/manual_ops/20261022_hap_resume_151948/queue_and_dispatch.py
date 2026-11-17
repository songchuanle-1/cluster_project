"""Authorize the exact existing HAP run's full resume and invoke canonical dispatch once."""
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
sys.path.insert(0,str(SKILL))
import closure
import cluster_resume
import pipeline_monitor as monitor

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def save(p,value,exclusive=False):
    if exclusive:
        with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
        return
    tmp=p.with_name(p.name+'.hap_resume_151948.tmp')
    with tmp.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)

CALLS=[]
def strict_ssh(host,user,command,timeout=8):
    assert (host,user)==('192.168.1.115','songcl')
    # Canonical dispatch only needs the one authorized GPU's row.
    inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
    if command==inventory:command=command.replace('nvidia-smi ','nvidia-smi -i 0 ',1)
    launch='proc=subprocess.Popen(' in command and 'tools/train.py' in command
    if launch:
        # Additional read-only idleness/UUID check immediately before the unchanged native launcher.
        guard="import socket,subprocess;assert socket.gethostname()=='dl04-MS-7E06';r=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',');assert r[0].strip()=='0' and r[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' and int(r[2])<1024 and int(r[3])<10;assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()"
        command='/usr/bin/python3 -B -c '+shlex.quote(guard)+' && '+command
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,command]
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(timeout,150))
    CALLS.append(dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=args,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,launch_request=launch))
    save(BASE/'transport_calls.json',CALLS)
    if r.returncode:raise RuntimeError('Pinned SSH command failed; preserve launch uncertainty: '+r.stderr[-1500:])
    return r.stdout.strip()

def main():
    assert os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert not (ROOT/'pipeline/headless/.foreground.lockdir').exists()
    assert not (ROOT/'pipeline/headless/.tick_context_state.next.json').exists()
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    original_ssh=monitor.ssh
    try:
        operation=read(BASE/'operation.json');grant_ref=operation['authorization']
        grant=read(ROOT/grant_ref['path']);assert ref(ROOT/grant_ref['path'])==grant_ref
        assert grant['source']=='human' and grant['human_request']=='授权 HAP 在 GPU0 续训'
        assert grant['authorization_granted'] is True and grant['gpu']=='0'
        runtime=read(BASE/'fresh_runtime_checkpoint_verification.json')
        assert runtime['returncode']==0 and runtime['data']['three_flocks_acquired']
        assert runtime['data']['checkpoint_sha256']==grant['checkpoint_sha256']
        assert read(BASE/'hap_source_integrity.json')['passed'] is True
        server=monitor.load_servers(str(ROOT))['server-4']
        assert server['allowed_gpus']==[0] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled']
        assert server['remote_code_root']==grant['remote_code_root']
        proof={k:grant[k] for k in ('schema_version','purpose','id','config','code_commit','server','gpu','remote_code_root','resume_from','checkpoint_sha256')}
        proof.update(cpu_inspection=runtime['data']['cpu_inspection'],observed_at=runtime['data']['observed_at'],
            evidence=[ref(BASE/'fresh_runtime_checkpoint_verification.json')],partial_current_epoch_saved=False)
        proof_path=BASE/'checkpoint_evidence.json';save(proof_path,proof,exclusive=True)
        queue=monitor.load_queue(str(ROOT));before=copy.deepcopy(queue)
        assert not any(t.get('id')=='M207-HAP' for group in queue['gpu_queues'].values() for t in group)
        assert not any(t.get('status') in ('running','claiming') for t in queue['gpu_queues']['server-4'])
        m206_before=copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA'))
        assert m206_before['resume_authorized'] is False and m206_before['dispatch_hold']
        archive_path=ROOT/'pipeline/diagnostic_bundles/tick_5c46f46a/hap_terminal_archive.json'
        archive=read(archive_path);old_exp=monitor.load_experiment(str(ROOT),'M207-HAP')
        assert old_exp==archive['archived_experiment'] and old_exp['status']=='crashed'
        save(BASE/'prior_crashed_experiment.json',old_exp,exclusive=True)
        task=copy.deepcopy(archive['original_queue_task'])
        for k in ('pid','log','launched','claimed_gpu','dispatch_hold','admission_error'):task.pop(k,None)
        task.update(status='waiting',gpu='0',server='server-4',dispatch_phase='resume_waiting',
            launch_verified=False,launch_verification='waiting_full_resume',training_status='waiting_resume',
            resume_from=grant['resume_from'],resume_authorization=grant_ref,resume_checkpoint_evidence=ref(proof_path),
            resume_authorized=True,requires_exclusive_ownership=True,
            note='Same M207-HAP/f518/native YAML full epoch18 state; native epoch19 resume, no cold start. GPU0 only; M206/GPU1 remain paused/released.')
        work=read(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c.get('experiment_id')=='M207-HAP')
        candidate.update(stage='deployment',resume_stage='training',human_hold=False,resume_authorized=True,
            training_status='waiting_resume',required_gpu='0',required_server='server-4',
            resume_authorization=grant_ref,resume_checkpoint_evidence=ref(proof_path),
            next_action='Human exact HAP full resume authorized. Reuse original f518 receipt/native YAML; wait for real GPU0 vacancy and revalidated source/checkpoint/runtime, then canonical --resume from saved epoch18, verify native epoch19 increasing steps. Never use GPU1 or resume M206.')
        for k in ('blocker','blocker_kind','blocked_at','retry_after','unblock_condition'):candidate.pop(k,None)
        candidate['pending_human_resume_question'].update(status='AUTHORIZED',authorization=grant_ref,received_at=dt.datetime.now(dt.timezone.utc).isoformat())
        for ev in (grant_ref,ref(proof_path),ref(BASE/'human_request.json'),ref(BASE/'hap_source_integrity.json'),ref(BASE/'fresh_runtime_checkpoint_verification.json')):
            if ev not in candidate['evidence']:candidate['evidence'].append(ev)
        save(ROOT/'pipeline/research_work.json',work)
        # Admission is unchanged scientific/version evidence; new proof only grants this full resume.
        closure.admission(ROOT,task)
        cluster_resume.validate(ROOT,server,task,'0')
        cluster_resume.verify_source(ROOT,ROOT/'Cluster',server,task,'0',strict_ssh)
        queue['gpu_queues']['server-4'].append(task)
        closure.validate_foreground_dispatch_budget(ROOT,queue,task)
        monitor.save_queue(str(ROOT),queue)
        exp=copy.deepcopy(old_exp)
        exp.setdefault('prior_runs',[]).append(dict(state='crashed',archived_experiment=ref(BASE/'prior_crashed_experiment.json'),terminal_archive=ref(archive_path),archive_id=old_exp['archive_id']))
        for k in ('pid','log','launched','finished_at','final_best','log_local','epochs_final','archive_id'):exp.pop(k,None)
        exp.update(status='waiting',gpu='0',server='server-4',launch_verified=False,launch_verification='waiting_full_resume',
            resume_from=task['resume_from'],resume_authorization=grant_ref,resume_checkpoint_evidence=ref(proof_path),training_status='waiting_resume')
        exp.setdefault('history',[]).append(dict(ts=dt.datetime.now(dt.timezone.utc).isoformat(),action='human_authorized_full_resume_queued',
            from_checkpoint_epoch=18,resume_start_epoch=19,authorization=grant_ref,checkpoint=ref(proof_path),prior_archive=ref(archive_path)))
        monitor.save_experiment(str(ROOT),exp)
        decision=monitor.log_decision(str(ROOT),'manual','Human authorizes exact HAP GPU0 full resume','Queue same HAP epoch18 full-state resume on GPU0',
            '人类明确回复授权 HAP 在 GPU0 续训；固定原f518/YAML/epoch18全状态，fresh CPU/源/原生数据资产核通过。仅GPU0且空闲复核后canonical派发；GPU1继续给别人/M206保持暂停。不改参数/源/环境，不冷启动；底因未知不称修复。',
            'grant='+grant_ref['path']+'; operation='+str(BASE.relative_to(ROOT)))
        events=[];monitor.ssh=strict_ssh
        # Existing canonical queue dispatcher; no full monitor, sync, legacy launcher, signal or retry.
        monitor._process_queue(queue,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,
            max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=server['remote_code_root'],current_tasks=0)
        after=monitor.load_queue(str(ROOT));current=next(t for t in after['gpu_queues']['server-4'] if t['id']=='M207-HAP')
        assert next(t for t in after['gpu_queues']['server-4'] if t['id']=='M206-CGCA')==m206_before
        work=read(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c.get('experiment_id')=='M207-HAP')
        verified=current.get('status')=='running' and current.get('launch_verified') is True
        candidate.update(stage='training' if verified else 'deployment',training_status='running' if verified else current['status'],
            next_action=('Native full resume has verified increasing progress. Monitor exact new HAP process/log on GPU0 under original fixed protocol; preserve old crash/full-state and unknown DataLoader root cause. GPU1 remains released and M206 user-paused.' if verified else
                'Authorized full resume is queued or launch is unresolved; preserve exact current PID/log/dispatch state. Wait for authorized idle GPU0 or reconcile original launch, never blind replay. M206 stays paused; GPU1 remains released.'))
        save(ROOT/'pipeline/research_work.json',work)
        result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),canonical_dispatch_invoked=True,
            task_after=current,events=events,running_after=monitor.load_running(str(ROOT)),
            m206_queue_unchanged=True,verified_native_progress=verified,authorization=grant_ref,
            checkpoint_evidence=ref(proof_path),manual_decision=ref(Path(decision)),
            source_synced=False,model_yaml_environment_changed=False,cold_start=False,
            GPU1='NOT_QUERIED_RELEASED_TO_OTHERS',signals_sent=False,training_process_retried=False)
        save(BASE/'dispatch_result.json',result,exclusive=True)
        print(json.dumps(dict(status=current['status'],launch_verified=current.get('launch_verified'),pid=current.get('pid'),
            log=current.get('log'),dispatch_hold=current.get('dispatch_hold'),m206_queue_unchanged=True),ensure_ascii=False))
    finally:
        monitor.ssh=original_ssh
        lock.close()
if __name__=='__main__':main()
