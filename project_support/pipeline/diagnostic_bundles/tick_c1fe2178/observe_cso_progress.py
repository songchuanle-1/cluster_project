"""Fresh bounded read-only observations of the newly registered CSO process."""
from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, json, os, shlex, subprocess, sys
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
owner=read(HERE/'current_owner_binding.json'); live=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
assert {k:live[k] for k in owner}==owner and owner['thread_id']==os.environ['CODEX_THREAD_ID']
assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
task=next(t for t in read(ROOT/'pipeline/queue.json')['gpu_queues']['server-4'] if t['id']=='M236-CSO')
assert task['status']=='running' and task['launch_verified'] is True
assert str(task['gpu'])=='0' and task['code_commit']=='5413102c57b526035f3920b5e7a81f3b58ad764d'
params=dict(pid=int(task['pid']),log=task['log'],source=task['code_commit'],owner=owner)
BODY=r'''
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,socket,subprocess,time
assert socket.gethostname()=='dl04-MS-7E06' and os.getuid()==os.geteuid()==1001
ROOT=Path('/data/songcl/Project/Cluster_project/Cluster_nsd_20261107')
def sample():
 assert datetime.now(timezone.utc)<datetime.fromisoformat(P['owner']['deadline_at'])
 assert subprocess.check_output(['/usr/bin/git','--no-optional-locks','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==P['source']
 proc=Path('/proc')/str(P['pid']); assert proc.exists() and proc.stat().st_uid==1001
 assert (proc/'cwd').resolve()==ROOT
 argv=[v.decode('utf8','replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v]
 assert '-B' in argv and any(v=='tools/train.py' or v.endswith('/tools/train.py') for v in argv)
 assert any(v.endswith('_csort_cso.yaml') for v in argv)
 path=Path(P['log']); assert path.resolve().is_relative_to(ROOT/'logs')
 with path.open('rb') as f:
  f.seek(0,2); size=f.tell(); f.seek(max(0,size-65536)); raw=f.read(65536)
 text=raw.decode('utf8','replace')
 patterns=[r'Train\[(\d+)/(\d+)\][^\r\n]*?\s(\d+)/(\d+)\s*\[',r'Epoch \[(\d+)/(\d+)\]\[(\d+)/(\d+)\]']
 found=[]
 for pattern in patterns:
  found.extend((m.end(),tuple(map(int,m.groups()))) for m in re.finditer(pattern,text))
 assert found,'No native progress in bounded log tail'
 _,(epoch,epochs,batch,total)=max(found)
 gpu=subprocess.check_output(['/usr/bin/nvidia-smi','-i','0','--query-gpu=index,uuid,memory.free,memory.used,memory.total,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
 assert gpu.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
 all_locks=Path('/proc/locks').read_text(); locks=[]
 for kind,ino in [('training',92537152),('diagnostic',92537153),('exclusive',92537154)]:
  p=Path('/tmp/cluster_project_gpu0_'+kind+'.lock'); st=p.lstat(); assert (st.st_dev,st.st_ino)==(66308,ino)
  rows=[line for line in all_locks.splitlines() if re.search(r':'+str(ino)+r'\s',line)]
  locks.append(dict(kind=kind,device=st.st_dev,inode=st.st_ino,kernel_rows=rows))
 return dict(observed_at=datetime.now(timezone.utc).isoformat(),pid=P['pid'],argv=argv,runtime_HEAD=P['source'],epoch=epoch,epochs=epochs,batch=batch,total_batches=total,log_size=size,tail_bytes=len(raw),tail_sha256=hashlib.sha256(raw).hexdigest(),fatal_markers=[v for v in ['Traceback (most recent call last)','AttributeError:','RuntimeError:','CUDA error:'] if v in text],gpu0=gpu,original_locks=locks)
a=sample();time.sleep(12);b=sample()
assert (b['epoch'],b['batch'])>(a['epoch'],a['batch'])
print(json.dumps(dict(owner=P['owner'],samples=[a,b],native_progress_increased=True,complete_training=False,validation_efficacy='UNKNOWN',Torch_imported=False,remote_mutations=False,signals_sent=False)))
'''
body='P='+repr(params)+'\n'+BODY
argv=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','-o','PasswordAuthentication=no','songcl@192.168.1.115','/usr/bin/python3 -I -B -c '+shlex.quote(body)]
run=subprocess.run(argv,capture_output=True,timeout=55)
actual=dict(owner=owner,kind='BOUNDED_NATIVE_TRAINING_PROGRESS',producer_sha256=sha(Path(__file__)),body_sha256=hashlib.sha256(body.encode()).hexdigest(),returncode=run.returncode,stderr_tail=run.stderr[-4096:].decode('utf8','replace'))
if run.returncode==0: actual['observation']=json.loads(run.stdout)
else: actual['stdout_tail']=run.stdout[-4096:].decode('utf8','replace')
dest=HERE/'cso_training_progress.actual.json'
with dest.open('x',encoding='utf8') as f: json.dump(actual,f,ensure_ascii=False,indent=2); f.write('\n')
assert run.returncode==0,'Preserve observation failure; do not relaunch'
samples=actual['observation']['samples']
print(json.dumps(dict(path=str(dest),sha256=sha(dest),pid=params['pid'],progress=[dict(epoch=s['epoch'],batch=s['batch'],total=s['total_batches']) for s in samples],native_progress_increased=True)))
