"""Read-only GPU0 original memory-budget observation; overlay is permitted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shlex
import subprocess

ROOT = Path('D:/project/cluster_project')
HERE = Path(__file__).resolve().parent
raw = json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text(encoding='utf8'))
owner = {k:raw[k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')}
assert owner['token'] == '4a0ed3c167ac4a87aa16ff5473b0cd4b' and owner['thread_id'] == os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner['deadline_at'])
body = r'''import os,socket,json,pathlib,subprocess
from datetime import datetime,timezone
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
def query(argv):
 r=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=15)
 assert r.returncode==0,r.stderr[-1000:]
 return r.stdout.strip()
row=query(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'])
f=[i.strip() for i in row.split(',')]
assert f[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'] and len(f)==6
contexts=query(['nvidia-smi','-i','0','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])
locks=[];kernel=pathlib.Path('/proc/locks').read_text()
for kind,ino in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
 p=pathlib.Path('/tmp/cluster_project_gpu0_'+kind+'.lock');s=p.stat()
 assert s.st_dev==66308 and s.st_ino==ino
 locks.append(dict(kind=kind,device=s.st_dev,inode=s.st_ino,kernel_rows=[l for l in kernel.splitlines() if ':'+str(ino)+' ' in l]))
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),uid=os.getuid(),physical_gpu=0,uuid=f[1],memory_free_mib=int(f[2]),memory_used_mib=int(f[3]),memory_total_mib=int(f[4]),utilization_percent=int(f[5]),compute_contexts=contexts,original_locks=locks,original_pid_exists=pathlib.Path('/proc/2248650').exists(),Torch_imported=False,GPU_context_created=False,signals_sent=False,remote_mutations=False)))
'''
command=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=15','songcl@192.168.1.115','python3 -B -c '+shlex.quote(body)]
r=subprocess.run(command,capture_output=True,text=True,encoding='utf8',timeout=65)
assert r.returncode==0,r.stderr[-1500:]
observation=json.loads(r.stdout)
queue=json.loads((ROOT/'pipeline/queue.json').read_text(encoding='utf8'))
active=[t['id'] for t in queue['gpu_queues'].get('server-4',[]) if t.get('status') in ('running','claiming') and str(t.get('gpu'))=='0']
record=dict(owner=owner,kind='ORIGINAL_20000_MIB_GPU0_OVERLAY_BUDGET_READ_ONLY_CHECK',required_server='server-4',required_gpu=0,minimum_free_mib=20000,max_project_tasks_per_gpu=1,allow_external_overlay=True,require_empty_device=False,require_zero_contexts=False,require_low_utilization=False,observation=observation,canonical_gpu0_active=active,memory_budget_satisfied=observation['memory_free_mib']>=20000,project_cap1_available=not active,source_or_runtime_changed=False,body_sha256=hashlib.sha256(body.encode()).hexdigest(),producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),returncode=r.returncode,stderr_tail=r.stderr[-1000:])
record['test_allowed_under_observed_memory_and_queue'] = record['memory_budget_satisfied'] and record['project_cap1_available']
dest=HERE/'gpu0_overlay_budget.actual.json'
with dest.open('x',encoding='utf8') as f:
 json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(free_mib=observation['memory_free_mib'],required_mib=20000,project_cap1_available=not active,memory_budget_satisfied=record['memory_budget_satisfied'],test_allowed_under_observed_memory_and_queue=record['test_allowed_under_observed_memory_and_queue'],path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest())))
