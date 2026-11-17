"""Pinned live observations and finite CPU saved-storage execution."""
import json,shlex
from ops import guard,save,ssh,run,evidence,ROOT,OUT,STAGE,REMOTE_ROOT,NAME
import foreground_tick as tick
guard();experiment=tick.load(ROOT/'pipeline/experiments/M203-FLE.json')
for label,host,gpu,hostname,uuid in (
    ('server4','192.168.1.115',0,'dl04-MS-7E06','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),
    ('server3','192.168.1.120',1,'sysu311-MS-7C59','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')):
    program=r'''import os,json,socket,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()==%r
def command(args):return subprocess.check_output(args,universal_newlines=True,timeout=10).strip()
row=command(['nvidia-smi','-i',%r,'--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
assert row.split(',')[1].strip()==%r
contexts=command(['nvidia-smi','-i',%r,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
value={'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':row,'contexts':contexts,'occupied':bool(contexts),'new_cuda_calls':0}
if %r=='server4':
 pid=%r;value['pid_alive']=Path('/proc/'+str(pid)).exists()
 if value['pid_alive']:
  value['command']=Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(b'\0',b' ').decode();assert %r in value['command']
  paths=[]
  for fd in Path('/proc/'+str(pid)+'/fd').iterdir():
   try:
    p=os.readlink(str(fd))
    if 'Cluster_checkpoints' in p and p.endswith('.log'):paths.append(p)
   except OSError:pass
  assert len(paths)==1
  text=Path(paths[0]).read_text(errors='replace');value['native_log']=paths[0]
  value['epoch_steps']=re.findall(r'Epoch \[(\d+)/(\d+)\]\[(\d+)/(\d+)\]',text)[-2:]
  value['validation_miou']=[float(v) for v in re.findall(r'mIoU\s*:\s*([0-9.]+)',text)]
 locks=Path('/proc/locks').read_text().splitlines();held={}
 for kind in ('training','diagnostic','exclusive'):
  p=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
  held[kind]=[int(line.split()[4]) for line in locks if line.split()[5].split(':')[-1]==str(p.stat().st_ino)] if p.exists() else []
 value['lock_owner_pids']=held
print(json.dumps(value))
'''%(hostname,str(gpu),uuid,str(gpu),label,experiment['pid'],NAME)
    value=ssh(program,host);save(label+'_live.json',value);metrics=value.get('validation_miou',[])
    print(json.dumps({'server':label,'observed_at':value['observed_at'],'occupied':value['occupied'],'epoch_steps':value.get('epoch_steps'),
        'best_miou':max(metrics) if metrics else None,'native_validation_count':len(metrics)}))
base=tick.load(ROOT/'pipeline/diagnostic_bundles/tick_b4174e26/manifest.json')
manifest={key:base[key] for key in ('operator_path','operator_sha256','source_hashes','config_path','config_sha256')}
manifest['prereg_sha256']=evidence(OUT/'saved_storage_prereg.md')['sha256'];save('manifest.json',manifest)
program='''import json,hashlib,socket
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
base=%r;root=Path(%r);name=%r
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
actual={k:sha(root/'framework/model/Quard_model'/name/k) for k in base['source_hashes']}
assert actual==base['source_hashes'] and sha(base['config_path'])==base['config_sha256']
Path(%r).mkdir(parents=True,exist_ok=False)
print(json.dumps({'source_hashes':actual,'config_sha256':base['config_sha256'],'unchanged':True}))
'''%(manifest,REMOTE_ROOT,NAME,STAGE)
save('source_verification.json',ssh(program))
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'saved_storage_cpu.py'),str(OUT/'manifest.json'),
    str(OUT/'saved_storage_prereg.md'),'songcl@192.168.1.115:'+STAGE+'/'])
save('upload.json',dict(returncode=upload.returncode,stdout=upload.stdout,stderr=upload.stderr));assert upload.returncode==0
guard()
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 python -B '+shlex.quote(STAGE+'/saved_storage_cpu.py')
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],180)
save('execution.json',dict(returncode=execution.returncode,stdout=execution.stdout,stderr=execution.stderr,cuda_visible_devices=''))
print(execution.stdout)
if execution.returncode:print(execution.stderr)
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/saved_storage_result.json',str(OUT/'saved_storage_result.json')])
save('fetch.json',dict(returncode=fetch.returncode,stdout=fetch.stdout,stderr=fetch.stderr));assert fetch.returncode==0
assert execution.returncode==0
