"""Disabled root template: one canonical selected-card dispatch, never on import."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import copy
import json
import os
import shlex
import subprocess
import sys
import yaml
import promotion_common as common

ROOT=common.ROOT
HERE=common.TICK
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN=common.TOKEN
COMMIT=common.TESTED
EXP=common.EXP
CALLS=[]
SELECTED_GPU=None


def read(path):return common.read(path)
def sha(path):return common.sha(path)
def ref(path):return common.ref(Path(path))
def owner_guard():return common.owner_guard()


def save(path,value):
    common.execution_enabled(True);owner_guard()
    path=Path(path);temporary=path.with_name(path.name+'.'+TOKEN+'.tmp')
    with temporary.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def strict_ssh(host,user,command,timeout=8):
    common.execution_enabled(True);owner_guard()
    common.require((host,user)==('192.168.1.115','songcl'),'Wrong pinned server account')
    common.require(type(SELECTED_GPU) is int and SELECTED_GPU in common.UUIDS,'Selected actual binding must precede transport')
    gpu=str(SELECTED_GPU);uuid=common.UUIDS[SELECTED_GPU]
    inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
    if command==inventory:
        command=command.replace('nvidia-smi ','nvidia-smi -i '+gpu+' ',1)
    elif 'nvidia-smi' in command:
        raise RuntimeError('Unexpected canonical GPU query shape; refuse instead of querying a nonselected card')
    launch='proc=subprocess.Popen(' in command and 'tools/train.py' in command
    if 'Popen' in command and 'tools/train.py' in command:
        common.require(launch,'Unrecognized launch text; no unlocked fallback')
    guard="import socket;assert socket.gethostname()=='dl04-MS-7E06'"
    if launch:
        common.require(not any(item['canonical_native_launch_request'] for item in CALLS),'No second native launch or blind retry in this one-shot dispatch')
        guard="""import socket,subprocess,fcntl,os,sys
assert socket.gethostname()=='dl04-MS-7E06'
gpu=GPU_INDEX
uuid=GPU_UUID
handles=[]
try:
 for kind in ('training','diagnostic','exclusive'):
  f=open('/tmp/cluster_project_gpu'+gpu+'_'+kind+'.lock','a+b'); handles.append(f); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 row=subprocess.check_output(['nvidia-smi','-i',gpu,'--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')
 assert row[0].strip()==gpu and row[1].strip()==uuid and int(row[2])<1024 and int(row[3])<10
 assert not subprocess.check_output(['nvidia-smi','-i',gpu,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
 env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
 result=subprocess.run(['/bin/bash','-lc',COMMAND],env=env,capture_output=True,text=True,timeout=120)
 sys.stdout.write(result.stdout);sys.stderr.write(result.stderr)
 if result.returncode:raise SystemExit(result.returncode)
finally:
 for handle in handles:handle.close()
""".replace('GPU_INDEX',repr(gpu)).replace('GPU_UUID',repr(uuid)).replace('COMMAND',repr(command))
    checked='export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(guard)
    if not launch:checked+=' && '+command
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,checked]
    run=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(timeout,150))
    CALLS.append({'recorded_at':datetime.now(timezone.utc).isoformat(),'command':args,'returncode':run.returncode,
        'stdout':run.stdout,'stderr':run.stderr,'canonical_native_launch_request':launch,'physical_gpu':SELECTED_GPU,'gpu_uuid':uuid})
    save(HERE/'bfc_dispatch_transport_calls.json',CALLS)
    if run.returncode:raise RuntimeError('Pinned SSH failed; preserve original uncertainty and never blindly retry: '+run.stderr[-1500:])
    return run.stdout.strip()


def main():
    global SELECTED_GPU
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    if not args.execute_root:
        print('DRAFT_DISABLED: canonical dispatcher and transport were not invoked');return
    common.execution_enabled(args.execute_root);owner_guard()
    manifest,raw_hashes,review_refs=common.reviewed_four_raw()
    SELECTED_GPU=manifest['physical_gpu']
    common.require(type(SELECTED_GPU) is int and SELECTED_GPU in common.UUIDS,'Wrong actual selected GPU')
    common.protected();expected_sources=common.source_paths(manifest)
    common.require(all(sha(ROOT/'Cluster'/p)==h for p,h in expected_sources.items()),'Primary differs from actual tested BFC bytes')
    sys.path.insert(0,str(SKILL))
    import pipeline_monitor as monitor
    import closure
    common.require(not any((HERE/n).exists() for n in ('bfc_dispatch_request.json','bfc_dispatch_result.json','bfc_dispatch_transport_calls.json')),'Existing dispatch intent/transport/result requires read-only reconciliation; no replay')
    lock=monitor.acquire_lock(str(ROOT));common.require(lock is not None,'Canonical pipeline lock busy')
    original_ssh=monitor.ssh;original_git_ssh=os.environ.get('GIT_SSH_COMMAND')
    try:
        server=monitor.load_servers(str(ROOT))['server-4']
        raw_server=yaml.safe_load((ROOT/'SERVERS.yaml').read_text('utf-8'))['servers']['server-4']
        raw_uuids={str(key):value for key,value in raw_server['expected_gpu_uuids'].items()}
        common.require(raw_uuids=={str(key):value for key,value in common.UUIDS.items()},'SHA-bound raw GPU UUID map differs')
        common.require(server['host']=='192.168.1.115' and server['expected_hostname']=='dl04-MS-7E06' and server['allowed_gpus']==[0,1] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True,'Current approved server resource registry changed')
        common.require(str(raw_uuids.get(str(SELECTED_GPU)))==common.UUIDS[SELECTED_GPU],'Selected GPU UUID changed')
        queue=monitor.load_queue(str(ROOT));tasks=queue['gpu_queues']['server-4']
        lifecycle_before=common.protected_lifecycle(queue)
        target=[t for t in tasks if t.get('id')==EXP];common.require(len(target)==1,'Exactly one actual admitted target required')
        task=target[0]
        common.require(task['status']=='waiting' and task['code_commit']==COMMIT and common.physical_gpu(task['gpu'])==SELECTED_GPU and task.get('pid') is None and 'resume_from' not in task and not task.get('dispatch_hold'),'Wrong/held/nonfresh selected binding task')
        common.require(task.get('dispatch_phase') not in ('launch_requested','progress_pending') and task.get('launch_verification')!='pending_progress' and task.get('launch_verified') is not True,'Uncertain prior launch; reconcile instead of retry')
        common.require([t['id'] for t in tasks if t['status']=='waiting' and not t.get('dispatch_hold')]==[EXP],'Canonical FIFO has other ready work; do not bypass or dispatch another task')
        active=[t for t in tasks if t['status'] in ('running','claiming')]
        common.require(0<=len(active)<=2 and all(t['id'] in ('M211-BTC','M212-BCR') and t['status']=='running' for t in active),'Unknown or uncertain active task must be reconciled first')
        common.require(all(common.physical_gpu(t['gpu'])!=SELECTED_GPU for t in active),'Selected card remains registered busy; archive only genuine terminal work first')
        registered=common.running_assignments()
        common.require(not any(server=='server-4' and gpu==SELECTED_GPU for server,gpu,eid in registered),'Selected running mapping remains; no overwrite')
        common.require(all(eid in ('M211-BTC','M212-BCR') for server,gpu,eid in registered),'Unknown/new registered task requires reconciliation first')
        busy={str(common.physical_gpu(t['gpu'])) for t in active}
        closure.admission(ROOT,task);closure.validate_foreground_dispatch_budget(ROOT,queue,task)
        common.require(closure.git(ROOT/'Cluster','rev-parse','HEAD')==COMMIT,'Primary is not actual tested48fc')
        monitor.ssh=strict_ssh
        os.environ['GIT_SSH_COMMAND']='ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8'
        events=[];owner_guard();common.reviewed_four_raw();common.protected()
        intent={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':common.EXPECTED_OWNER,'id':EXP,'code_commit':COMMIT,
            'operation':'one_canonical_FIFO_selected_card_dispatch','execution_state':'NOT_YET_OBSERVED','physical_gpu':SELECTED_GPU,
            'gpu_uuid':common.UUIDS[SELECTED_GPU],'actual_raw_hashes':raw_hashes,'actual_review_refs':review_refs,'current_active_tasks':len(active)}
        with (HERE/'bfc_dispatch_request.json').open('x',encoding='utf-8') as stream:json.dump(intent,stream,ensure_ascii=False,indent=2);stream.write('\n')
        # One original canonical call; only the actually selected card is allowed.
        monitor._process_queue(queue,'server-4',server['host'],server['user'],str(ROOT),busy,{str(SELECTED_GPU)},events,
            max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=server['remote_code_root'],current_tasks=len(active),max_tasks_total=2)
        after=monitor.load_queue(str(ROOT));final=next(t for t in after['gpu_queues']['server-4'] if t['id']==EXP)
        common.require(common.physical_gpu(final['gpu'])==SELECTED_GPU,'Canonical target moved off its actual selected binding')
        target_mappings=[item for item in common.running_assignments() if item[2]==EXP]
        common.require(not target_mappings or target_mappings==[('server-4',SELECTED_GPU,EXP)],'Target reserved on a nonselected card')
        common.require(common.protected_lifecycle(after)==lifecycle_before,'Protected BTC/BCR/M206 queue/experiment/receipt or other running mapping changed')
        owner_guard();common.protected()
        common.require(all(sha(ROOT/'Cluster'/p)==h for p,h in expected_sources.items()),'Actual tested BFC primary source changed')
        verified=final.get('status')=='running' and final.get('launch_verified') is True
        work=read(ROOT/'pipeline/research_work.json');candidate=next(c for c in work['candidates'] if c['id']==common.CID)
        candidate['stage']='training' if verified else 'deployment';candidate['training_status']='running' if verified else final['status']
        candidate['next_action']=('Monitor only exact BFC original PID/log on actual selected card; canonical native progress verified, efficacy UNKNOWN. Preserve the other original BTC/BCR job or its canonical terminal archive, and M206 user pause.' if verified else
            'Preserve canonical exact claim/request/PID/log/receipt and any uncertainty. Reconcile the original attempt read-only; no blind retry, cold fallback, signal or other-card launch.')
        experiment=monitor.load_experiment(str(ROOT),EXP)
        if experiment is not None:experiment['training_status']='running' if verified else final['status'];monitor.save_experiment(str(ROOT),experiment)
        work['updated_at']=datetime.now(timezone.utc).isoformat();work['next_action']=candidate['next_action'];save(ROOT/'pipeline/research_work.json',work)
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_dispatch_invoked_once':True,
            'events':events,'task_after':final,'running_after':monitor.load_running(str(ROOT)),'verified_native_progress':verified,
            'protected_BTC_BCR_M206_and_other_running_mappings_unchanged':True,'physical_gpu':SELECTED_GPU,'gpu_uuid':common.UUIDS[SELECTED_GPU],
            'signals_sent':False,'blind_relaunch_performed':False,'transport_calls':ref(HERE/'bfc_dispatch_transport_calls.json') if (HERE/'bfc_dispatch_transport_calls.json').exists() else None}
        save(HERE/'bfc_dispatch_result.json',result)
        print(json.dumps({'id':EXP,'status':final['status'],'launch_verified':final.get('launch_verified'),'pid':final.get('pid'),'log':final.get('log'),'physical_gpu':SELECTED_GPU,'evidence':ref(HERE/'bfc_dispatch_result.json')},ensure_ascii=False))
    finally:
        monitor.ssh=original_ssh
        if original_git_ssh is None:os.environ.pop('GIT_SSH_COMMAND',None)
        else:os.environ['GIT_SSH_COMMAND']=original_git_ssh
        lock.close()


if __name__=='__main__':main()
