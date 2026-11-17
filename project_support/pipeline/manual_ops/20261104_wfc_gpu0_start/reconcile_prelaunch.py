"""Recover only a proven wrapper failure before native command/Popen execution."""
import json,subprocess,shlex
import prepare_and_queue as op
from prepare_and_queue import ROOT,P,OUT,ID,NEW_ROOT,now,load,save,ref,guard,mon,strict_ssh

guard(); lock=mon.acquire_lock(str(ROOT)); assert lock is not None
previous=mon.ssh
try:
    guard(); q=load(P/'queue.json'); task=next(t for t in q['gpu_queues']['server-4'] if t['id']==ID)
    assert task['status']=='claiming' and not task.get('pid') and not task.get('log') and 'Launch uncertain' in task['dispatch_hold']
    prior=load(OUT/'transport_calls.json'); launches=[c for c in prior if c.get('launch_request')]
    assert len(launches)==1 and launches[0]['returncode']!=0 and 'line 9' in launches[0]['stderr'] and launches[0]['stdout']==''
    a=shlex.split(launches[0]['command']); wrapper=a[a.index('-c')+1].splitlines()
    assert wrapper[8].startswith('assert not subprocess.check_output') and wrapper[9].startswith('p=subprocess.run(')
    program=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
cfg='configs/Quard/ctf_hcg_csort_wfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_wfc.yaml'
rows=[]
for i in range(3):
 r=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
 c=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
 fields=[s.strip() for s in r.split(',')]; actual=[line for line in c.splitlines() if line.split(',')[0].strip()==fields[1]]
 rows.append(dict(observed_at=datetime.now(timezone.utc).isoformat(),gpu=r,matching_contexts=actual,idle=fields[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'] and int(fields[2])<1024 and int(fields[3])<10 and not actual))
 if i<2: time.sleep(1)
found=[]
for f in Path('/proc').glob('[0-9]*/cmdline'):
 try:
  args=f.read_bytes().split(b'\0')
  if b'tools/train.py' in args and cfg.encode() in args: found.append(int(f.parent.name))
 except OSError: pass
logs=list((Path('/data/songcl/Project/Cluster_project/Cluster_resume_wfc_20261104')/'logs').glob('train_*.log'))
assert not found and not logs,'Possible native launch; preserve uncertain state'
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),samples=rows,WFC_processes=found,WFC_logs=[str(x) for x in logs],no_native_launch_confirmed=True,all_idle=all(x['idle'] for x in rows))))
'''
    cp=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','/usr/bin/python3 -B -'],input=program,text=True,encoding='utf-8',capture_output=True,timeout=35)
    proof=dict(recorded_at=now(),returncode=cp.returncode,stdout=cp.stdout,stderr=cp.stderr,failed_transport=ref(OUT/'transport_calls.json'),failed_wrapper_before_native_command=True)
    if cp.returncode==0: proof['data']=json.loads(cp.stdout)
    save(OUT/'known_prelaunch_reconciliation.json',proof); assert cp.returncode==0,cp.stderr[-1200:]
    task.update(status='waiting',dispatch_phase='resume_waiting',launch_verification='waiting_full_resume')
    task.pop('dispatch_hold'); task.pop('claimed_gpu',None); mon.save_queue(str(ROOT),q)
    if proof['data']['all_idle']:
        op.CALLS=prior; mon.ssh=strict_ssh; server=mon.load_servers(str(ROOT))['server-4']; events=[]
        mon._process_queue(q,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=NEW_ROOT,current_tasks=0)
        current=next(t for t in load(P/'queue.json')['gpu_queues']['server-4'] if t['id']==ID)
        result=dict(recorded_at=now(),task_after=current,events=events,running_after=load(P/'running.json'),
            verified_native_progress=current.get('status')=='running' and current.get('launch_verified') is True,
            previous_wrapper_blocked_before_native_command=True,prior_reconciliation=ref(OUT/'known_prelaunch_reconciliation.json'),no_duplicate_training_process=True)
        save(OUT/'reconciled_dispatch_result.json',result)
        print(json.dumps(dict(status=current['status'],pid=current.get('pid'),log=current.get('log'),launch_verified=current.get('launch_verified'),dispatch_hold=current.get('dispatch_hold')),ensure_ascii=False),flush=True)
    else: print('Known prelaunch block reconciled; remains waiting for actual GPU0 opening.',flush=True)
finally: mon.ssh=previous; lock.close()
