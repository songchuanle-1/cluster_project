"""Pinned-host live checks and one CPU-only fixture execution."""
import json
import shlex
from ops import guard,save,run,ssh,OUT,ROOT,NAME,STAGE,REMOTE_ROOT

guard()
experiment=json.loads((ROOT/'pipeline/experiments/M203-FLE.json').read_text())
for label,host,gpu,hostname,uuid in (
    ('server4','192.168.1.115',0,'dl04-MS-7E06','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'),
    ('server3','192.168.1.120',1,'sysu311-MS-7C59','GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0')):
    program=r'''import os,json,socket,re,subprocess
from pathlib import Path
from datetime import datetime,timezone
assert socket.gethostname()==%r
def command(args):return subprocess.check_output(args,universal_newlines=True,timeout=10).strip()
gpu=command(['nvidia-smi','-i',%r,'--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'])
assert gpu.split(',')[1].strip()==%r
contexts=command(['nvidia-smi','-i',%r,'--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'])
record={'observed_at':datetime.now(timezone.utc).isoformat(),'hostname':socket.gethostname(),'gpu':gpu,'contexts':contexts,'occupied':bool(contexts),'new_cuda_calls':0}
if %r=='server4':
 pid=%r;record['pid_alive']=Path('/proc/'+str(pid)).exists()
 if record['pid_alive']:
  record['command']=Path('/proc/'+str(pid)+'/cmdline').read_bytes().replace(b'\0',b' ').decode()
  assert %r in record['command']
  targets=[]
  for fd in Path('/proc/'+str(pid)+'/fd').iterdir():
   try:
    target=os.readlink(str(fd))
    if 'Cluster_checkpoints' in target and target.endswith('.log'):targets.append(target)
   except OSError:pass
  assert len(targets)==1
  log=Path(targets[0]);text=log.read_text(errors='replace')
  record['validation_miou']=[float(v) for v in re.findall(r'mIoU\s*:\s*([0-9.]+)',text)]
  record['epoch_steps']=re.findall(r'Epoch \[(\d+)/(\d+)\]\[(\d+)/(\d+)\]',text)[-2:]
  record['native_log']=str(log)
 locks=Path('/proc/locks').read_text().splitlines();held={}
 for kind in ('training','diagnostic','exclusive'):
  p=Path('/tmp/cluster_project_gpu0_'+kind+'.lock')
  held[kind]=[int(line.split()[4]) for line in locks if line.split()[5].split(':')[-1]==str(p.stat().st_ino)] if p.exists() else []
 record['lock_owner_pids']=held
print(json.dumps(record))
'''%(hostname,str(gpu),uuid,str(gpu),label,experiment['pid'],NAME)
    value=ssh(program,host);save(label+'_live.json',value)
    print(json.dumps({'server':label,'observed_at':value['observed_at'],'occupied':value['occupied'],
        'steps':value.get('epoch_steps'),'validation_miou':value.get('validation_miou')}))
assets=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/frozen_assets.json').read_text())
program='''import json,hashlib,socket
from pathlib import Path
assert socket.gethostname()=='dl04-MS-7E06'
assets=%r;root=Path(%r);name=%r
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
actual={k:sha(root/'framework/model/Quard_model'/name/k) for k in assets['source_hashes']}
assert actual==assets['source_hashes']
assert sha(assets['config_path'])==assets['config_sha256']
assert sha(assets['annotation_path'])==assets['annotation_sha256']
assert sha(root/'framework/dataset/scannetv2.py')==assets['dataset_source_sha256']
Path(%r).mkdir(parents=True,exist_ok=False)
print(json.dumps({'source_hashes':actual,'config_sha256':assets['config_sha256'],'annotation_sha256':assets['annotation_sha256'],'dataset_source_sha256':assets['dataset_source_sha256'],'unchanged':True}))
'''%(assets,REMOTE_ROOT,NAME,STAGE)
verified=ssh(program);save('source_verification.json',verified)
manifest={'operator_path':assets['operator_path'],'operator_sha256':assets['operator_sha256'],'root':REMOTE_ROOT,'name':NAME,
    'source_hashes':assets['source_hashes'],'config_path':assets['config_path'],'config_sha256':assets['config_sha256'],
    'annotation_path':assets['annotation_path'],'annotation_sha256':assets['annotation_sha256'],'dataset_source_sha256':assets['dataset_source_sha256'],
    'cohort':json.loads((ROOT/'pipeline/diagnostic_bundles/tick_dbeca5d6/native_manifest.json').read_text())['cohort']}
save('manifest.json',manifest)
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',str(OUT/'metric_cpu.py'),str(OUT/'manifest.json'),'songcl@192.168.1.115:'+STAGE+'/'])
save('upload.json',dict(returncode=upload.returncode,stdout=upload.stdout,stderr=upload.stderr));assert upload.returncode==0
guard()
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 python -B '+shlex.quote(STAGE+'/metric_cpu.py')
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],180)
save('cpu_execution.json',dict(returncode=execution.returncode,stdout=execution.stdout,stderr=execution.stderr,cuda_visible_devices=''))
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/metric_cpu_result.json',str(OUT/'metric_cpu_result.json')])
save('cpu_fetch.json',dict(returncode=fetch.returncode,stdout=fetch.stdout,stderr=fetch.stderr));assert fetch.returncode==0
result=json.loads((OUT/'metric_cpu_result.json').read_text())
print(json.dumps({'execution_passed':result['execution_passed'],'cases':len(result['cases']),'failures':result.get('metric_failures'),'error':result.get('error')}))
for row in result['cases']:
    if row.get('counterexample'):
        name=row['counterexample']
        fetched=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/'+name,str(OUT/name)])
        assert fetched.returncode==0,fetched.stderr
