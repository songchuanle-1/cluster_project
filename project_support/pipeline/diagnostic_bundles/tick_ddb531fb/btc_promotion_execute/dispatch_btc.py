"""Disabled private root draft: one canonical dispatch only after actual BTC admission."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import shlex
import subprocess
import sys
import argparse
import promotion_common as common

ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent.parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='ddb531fb89824389b3b2e2df5779a5ef'; COMMIT='00e2b18c6b8d568a64edb496e6979d766440883c'
EXP='M211-BTC'; CALLS=[]

def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path): return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(path,data):
    common.execution_enabled(True); owner_guard()
    path=Path(path); tmp=path.with_name(path.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2); stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp,path)

def owner_guard():
    return common.owner_guard()

def strict_ssh(host,user,command,timeout=8):
    common.execution_enabled(True); owner_guard(); assert (host,user)==('192.168.1.115','songcl')
    inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
    if command==inventory: command=command.replace('nvidia-smi ','nvidia-smi -i 0 ',1)
    launch='proc=subprocess.Popen(' in command and 'tools/train.py' in command
    guard="import socket;assert socket.gethostname()=='dl04-MS-7E06'"
    if launch:
        guard="""import socket,subprocess,fcntl,os,sys
assert socket.gethostname()=='dl04-MS-7E06'
handles=[]
try:
 for kind in ('training','diagnostic','exclusive'):
  f=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b'); handles.append(f); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')
 assert r[0].strip()=='0' and r[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' and int(r[2])<1024 and int(r[3])<10
 assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
 env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
 result=subprocess.run(['/bin/bash','-lc',COMMAND],env=env,capture_output=True,text=True,timeout=120)
 sys.stdout.write(result.stdout); sys.stderr.write(result.stderr)
 if result.returncode: raise SystemExit(result.returncode)
finally:
 for f in handles: f.close()
""".replace('COMMAND',repr(command))
    # Preserve canonical YAML/train arguments; bytecode suppression is inherited
    # by its detached training child. No persistent conda/source change.
    checked='export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(guard)
    if not launch: checked+=' && '+command
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,checked]
    run=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(timeout,150))
    CALLS.append({'recorded_at':datetime.now(timezone.utc).isoformat(),'command':args,'returncode':run.returncode,
                  'stdout':run.stdout,'stderr':run.stderr,'canonical_native_launch_request':launch})
    save(HERE/'btc_dispatch_transport_calls.json',CALLS)
    if run.returncode: raise RuntimeError('Pinned SSH request failed; preserve uncertainty: '+run.stderr[-1500:])
    return run.stdout.strip()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-root',action='store_true')
    args=parser.parse_args()
    if not args.execute_root:
        print('DRAFT_DISABLED: canonical dispatcher and transport were not invoked')
        return
    common.execution_enabled(args.execute_root)
    owner_guard(); manifest, raw_hashes, review_refs = common.reviewed_four_raw()
    common.protected()
    expected_sources=common.source_paths(manifest)
    common.require(all(sha(ROOT/'Cluster'/p)==h for p,h in expected_sources.items()),'Primary differs from actual tested BTC bytes')
    sys.path.insert(0,str(SKILL))
    import pipeline_monitor as monitor
    import closure
    assert not any((HERE/n).exists() for n in ('btc_dispatch_request.json','btc_dispatch_result.json','btc_dispatch_transport_calls.json'))
    lock=monitor.acquire_lock(str(ROOT)); assert lock is not None
    original_ssh=monitor.ssh
    original_git_ssh=os.environ.get('GIT_SSH_COMMAND')
    try:
        server=monitor.load_servers(str(ROOT))['server-4']
        assert server['host']=='192.168.1.115' and server['allowed_gpus']==[0] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True
        queue=monitor.load_queue(str(ROOT)); tasks=queue['gpu_queues']['server-4']
        m206_rows=[t for t in tasks if t['id']=='M206-CGCA']; assert len(m206_rows)==1
        m206=copy.deepcopy(m206_rows[0])
        assert m206['resume_authorized'] is False and m206['dispatch_hold']
        task=next(t for t in tasks if t['id']==EXP)
        assert task['status']=='waiting' and task['code_commit']==COMMIT and 'pid' not in task and 'resume_from' not in task
        assert task.get('dispatch_phase') not in ('launch_requested','progress_pending')
        assert task.get('launch_verification')!='pending_progress'
        assert [t['id'] for t in tasks if t['status']=='waiting' and not t.get('dispatch_hold')]==[EXP]
        assert not any(t['status'] in ('running','claiming') for group in queue['gpu_queues'].values() for t in group)
        closure.admission(ROOT,task); closure.validate_foreground_dispatch_budget(ROOT,queue,task)
        assert closure.git(ROOT/'Cluster','rev-parse','HEAD')==COMMIT
        assert monitor.load_experiment(str(ROOT),'M210-PSNC')['status']=='done_earlystop'
        monitor.ssh=strict_ssh
        os.environ['GIT_SSH_COMMAND']='ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=8'
        events=[]
        owner_guard(); common.reviewed_four_raw(); common.protected()
        intent={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':common.EXPECTED_OWNER,
                'id':EXP,'code_commit':COMMIT,'operation':'one_canonical_FIFO_dispatch',
                'execution_state':'NOT_YET_OBSERVED','actual_raw_hashes':raw_hashes,'actual_review_refs':review_refs}
        with (HERE/'btc_dispatch_request.json').open('x',encoding='utf-8') as stream:
            json.dump(intent,stream,ensure_ascii=False,indent=2); stream.write('\n')
        monitor._process_queue(queue,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,
                               max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=server['remote_code_root'],current_tasks=0)
        after=monitor.load_queue(str(ROOT)); final=next(t for t in after['gpu_queues']['server-4'] if t['id']==EXP)
        assert [t for t in after['gpu_queues']['server-4'] if t['id']=='M206-CGCA']==[m206]
        owner_guard(); common.protected()
        common.require(all(sha(ROOT/'Cluster'/p)==h for p,h in expected_sources.items()),'Tested BTC primary source changed')
        verified=final.get('status')=='running' and final.get('launch_verified') is True
        work=read(ROOT/'pipeline/research_work.json')
        candidate=next(c for c in work['candidates'] if c.get('experiment_id')==EXP)
        candidate['stage']='training' if verified else 'deployment'
        candidate['training_status']='running' if verified else final['status']
        candidate['next_action']=('Monitor only this exact BTC process/log and natural terminal outcome on server4 GPU0; native steps verified, efficacy UNKNOWN. Efficacy remains UNKNOWN; GPU1 released and M206 user-paused.' if verified else
                                  'Preserve canonical dispatch phase/receipt/exact request identity. Reconcile any uncertain original PID/log read-only; no blind retry. Actual idle/source verification required for any known prelaunch retry. GPU1 and M206 protected.')
        exp=monitor.load_experiment(str(ROOT),EXP)
        if exp is not None:
            exp['training_status']='running' if verified else final['status']; monitor.save_experiment(str(ROOT),exp)
        work['updated_at']=datetime.now(timezone.utc).isoformat(); work['next_action']=candidate['next_action']
        save(ROOT/'pipeline/research_work.json',work)
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_dispatch_invoked_once':True,
                'events':events,'task_after':final,'running_after':monitor.load_running(str(ROOT)),
                'verified_native_progress':verified,'m206_queue_unchanged':True,'GPU1':'NOT_QUERIED_NOT_USED',
                'signals_sent':False,'blind_relaunch_performed':False,'transport_calls':(ref(HERE/'btc_dispatch_transport_calls.json') if (HERE/'btc_dispatch_transport_calls.json').exists() else None)}
        save(HERE/'btc_dispatch_result.json',result)
        print(json.dumps({'id':EXP,'status':final['status'],'launch_verified':final.get('launch_verified'),'pid':final.get('pid'),
                          'log':final.get('log'),'dispatch_hold':final.get('dispatch_hold'),'evidence':ref(HERE/'btc_dispatch_result.json')},ensure_ascii=False))
    finally:
        monitor.ssh=original_ssh
        if original_git_ssh is None: os.environ.pop('GIT_SSH_COMMAND',None)
        else: os.environ['GIT_SSH_COMMAND']=original_git_ssh
        lock.close()

if __name__=='__main__': main()
