"""Invoke the existing canonical FIFO dispatcher once on authorized GPU0."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
import shlex
import subprocess
import sys

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
TOKEN='dfb6440d1b69401da8e932239883e613';CALLS=[]

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ref(path):return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save(path,data):
    path=Path(path);tmp=path.with_name(path.name+'.'+TOKEN+'.tmp')
    with tmp.open('x',encoding='utf-8') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,path)

def owner_guard():
    o=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert o['token']==TOKEN and o['thread_id']==os.environ.get('CODEX_THREAD_ID')=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==o['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==o['pending_sha256']

def strict_ssh(host,user,command,timeout=8):
    owner_guard();assert (host,user)==('192.168.1.115','songcl')
    inventory='nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null'
    if command==inventory:command=command.replace('nvidia-smi ','nvidia-smi -i 0 ',1)
    launch='proc=subprocess.Popen(' in command and 'tools/train.py' in command
    guard="import socket;assert socket.gethostname()=='dl04-MS-7E06'"
    if launch:
        guard="""import socket,subprocess,fcntl
assert socket.gethostname()=='dl04-MS-7E06'
r=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().split(',')
assert r[0].strip()=='0' and r[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c' and int(r[2])<1024 and int(r[3])<10
assert not subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
handles=[]
try:
 for kind in ('training','diagnostic','exclusive'):
  f=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
finally:
 for f in handles:f.close()
"""
    checked='/usr/bin/python3 -B -c '+shlex.quote(guard)+' && '+command
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',user+'@'+host,checked]
    result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=max(timeout,150))
    CALLS.append({'recorded_at':datetime.now(timezone.utc).isoformat(),'command':args,'returncode':result.returncode,
                  'stdout':result.stdout,'stderr':result.stderr,'canonical_native_launch_request':launch})
    save(HERE/'dispatch_transport_calls.json',CALLS)
    if result.returncode:raise RuntimeError('Pinned canonical SSH request failed; preserve uncertainty: '+result.stderr[-1500:])
    return result.stdout.strip()

def main():
    owner_guard();sys.path.insert(0,str(SKILL))
    import pipeline_monitor as monitor
    import closure
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    original_ssh=monitor.ssh
    try:
        server=monitor.load_servers(str(ROOT))['server-4']
        assert server['allowed_gpus']==[0] and server['max_tasks_per_gpu']==1 and server['dispatch_enabled'] is True
        # load_servers returns normalized deployment fields, not expected_hostname.
        # Every actual SSH request below verifies the pinned hostname on the server.
        assert server['host']=='192.168.1.115'
        queue=monitor.load_queue(str(ROOT));m206=copy.deepcopy(next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M206-CGCA'))
        assert m206['status']=='waiting' and m206['resume_authorized'] is False and m206['dispatch_hold']
        admitted=[t for t in queue['gpu_queues']['server-4'] if t['id'] in ('M208-HRC','M209-PSBR')]
        assert [t['id'] for t in admitted]==['M208-HRC','M209-PSBR']
        assert all(t['status']=='waiting' and 'pid' not in t and 'resume_from' not in t for t in admitted)
        assert not any(t['status'] in ('running','claiming') for group in queue['gpu_queues'].values() for t in group)
        for task in admitted:closure.admission(ROOT,task);closure.validate_foreground_dispatch_budget(ROOT,queue,task)
        assert monitor.load_experiment(str(ROOT),'M207-HAP')['status']=='done_earlystop'
        monitor.ssh=strict_ssh;events=[]
        # One canonical gated call; no full monitor, legacy launcher, or blind retry.
        monitor._process_queue(queue,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,
            max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=server['remote_code_root'],current_tasks=0)
        after=monitor.load_queue(str(ROOT));tasks={t['id']:t for t in after['gpu_queues']['server-4']}
        assert tasks['M206-CGCA']==m206
        verified=tasks['M208-HRC'].get('status')=='running' and tasks['M208-HRC'].get('launch_verified') is True
        work=read(ROOT/'pipeline/research_work.json')
        for exp in ('M208-HRC','M209-PSBR'):
            task=tasks[exp];candidate=next(c for c in work['candidates'] if c.get('experiment_id')==exp)
            good=task['status']=='running' and task.get('launch_verified') is True
            candidate['stage']='training' if good else 'deployment'
            candidate['training_status']='running' if good else task['status']
            candidate['next_action']=('Monitor this exact newly launched original-YAML process/log on only GPU0; real native progress has been verified. Formal validation efficacy remains UNKNOWN; preserve all previous evidence and M206/GPU1 boundaries.' if good else
                                      'Retain tested receipt and FIFO position on GPU0; wait for current HRC natural completion. If claiming/uncertain, reconcile exact original request/PID/log and never retry blindly. No GPU1 or M206 resume.')
            exp_record=monitor.load_experiment(str(ROOT),exp)
            if exp_record is not None:
                exp_record['training_status']='running' if good else task['status']
                monitor.save_experiment(str(ROOT),exp_record)
        work['updated_at']=datetime.now(timezone.utc).isoformat()
        work['next_action']='Monitor verified HRC on onlyGPU0; admitted PSBR remains FIFO waiting. HAP is naturally early-stopped/archived. M206 stays human-paused andGPU1 released. Do not change original protocols/resources/scheduler or reopen old holds.'
        save(ROOT/'pipeline/research_work.json',work)
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'canonical_dispatch_invoked_once':True,
                'events':events,'tasks_after':{exp:tasks[exp] for exp in ('M208-HRC','M209-PSBR')},
                'running_after':monitor.load_running(str(ROOT)),'m206_queue_unchanged':True,
                'HRC_verified_native_progress':verified,'GPU1':'NOT_QUERIED_RELEASED_TO_OTHERS',
                'signals_sent':False,'training_process_retried':False,'existing_HAP_process_modified':False,
                'canonical_source_sync_attempted':any('merge --ff-only' in x['command'][-1] for x in CALLS),
                'transport_calls':ref(HERE/'dispatch_transport_calls.json')}
        save(HERE/'dispatch_result.json',result)
        print(json.dumps({'HRC_status':tasks['M208-HRC']['status'],'HRC_launch_verified':tasks['M208-HRC'].get('launch_verified'),
                          'HRC_pid':tasks['M208-HRC'].get('pid'),'HRC_log':tasks['M208-HRC'].get('log'),
                          'HRC_dispatch_hold':tasks['M208-HRC'].get('dispatch_hold'),'PSBR_status':tasks['M209-PSBR']['status'],
                          'm206_queue_unchanged':True,'evidence':ref(HERE/'dispatch_result.json')},ensure_ascii=False),flush=True)
    finally:monitor.ssh=original_ssh;lock.close()

if __name__=='__main__':main()
