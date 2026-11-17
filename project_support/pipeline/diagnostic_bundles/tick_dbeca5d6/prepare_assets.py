"""Freeze diagnostic-only assets and run CPU contracts without CUDA."""
import json
import shlex
import yaml
from ops import guard,save,ssh,run,OUT,ROOT,NAME,REMOTE_ROOT,STAGE

guard()
expected=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_0571f421/final_source.json').read_text())
local_config=ROOT/'Cluster/configs/Quard/ctf_hcg_csort_fle_r1'/(NAME+'.yaml')
config_expected=yaml.safe_load(local_config.read_text())
assert config_expected['work_dir']=='./work_dirs' or isinstance(config_expected['work_dir'],str)
config_expected['work_dir']='/data/songcl/Project/Cluster_project/Cluster_checkpoints'
save('preparation_precheck_failure.json',{'failure':'Initial deployment config raw SHA assertion failed before stage creation or checkpoint copy; diagnosed work_dir adaptation','model_source_files_matched':9,'native_forwards':0,'cuda_calls':0,'cpu_tests_run':0,'disposition':'Require structured config equality with only previously authorized work_dir adaptation, preserve original hashes'})
program='''import os,json,socket,hashlib,subprocess,shutil,time,yaml
from pathlib import Path
from datetime import datetime,timezone
root=Path(%r);name=%r;stage=Path(%r);expected=%r
assert socket.gethostname()=='dl04-MS-7E06'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
source=root/'framework/model/Quard_model'/name
hashes={k:sha(source/k) for k in expected['source_hashes']}
assert hashes==expected['source_hashes']
config=root/'configs/Quard/ctf_hcg_csort_fle_r1'/(name+'.yaml')
assert yaml.safe_load(config.read_text())==%r,'Non-path configuration changed'
stage.mkdir(parents=True,exist_ok=False)
annotation=Path('/home/songcl/data/data/scanrefer/ScanRefer_train_new.json')
assert sha(annotation)=='018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d'
dataset=root/'framework/dataset/scannetv2.py'
assert sha(dataset)=='2fb59f598a05cd37cedbf883a5a47df02caf68e86776b097bfcb1d833b40829d'
runroot=Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints')/name
files=sorted(runroot.glob('*/last.pth'))
assert len(files)==1, [str(p) for p in files]
checkpoint=files[0]
def open_writers():
 result=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   for fd in (proc/'fd').iterdir():
    try:
     if fd.resolve()==checkpoint:
      info=(proc/'fdinfo'/fd.name).read_text()
      flags=int(next(v.split(':',1)[1].strip() for v in info.splitlines() if v.startswith('flags:')),8)
      if flags&3:result.append(int(proc.name))
    except (OSError,StopIteration):pass
  except OSError:pass
 return result
assert not open_writers(),'Checkpoint currently open for writing'
before=checkpoint.stat();digest=sha(checkpoint)
assert before.st_size<shutil.disk_usage(stage).free//3
snapshot=stage/'time_selected_last.pth'
with checkpoint.open('rb') as src,snapshot.open('xb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
after=checkpoint.stat()
assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
assert sha(checkpoint)==sha(snapshot)==digest and not open_writers()
record={'observed_at':datetime.now(timezone.utc).isoformat(),'source_hashes':hashes,'config_path':str(config),'config_sha256':sha(config),
 'operator_path':str(source/'fine_exchange.py'),'operator_sha256':hashes['fine_exchange.py'],
 'annotation_path':str(annotation),'annotation_sha256':sha(annotation),'dataset_source_sha256':sha(dataset),
 'checkpoint':str(snapshot),'checkpoint_sha256':digest,'original_checkpoint':str(checkpoint),'checkpoint_bytes':before.st_size,
 'checkpoint_mtime_ns':before.st_mtime_ns,'selection':'first stable closed last.pth observed;time selected,not best score',
 'writers_before_and_after':[],'cuda_calls':0,'training_checkpoint_unchanged':True}
print(json.dumps(record))
'''%(REMOTE_ROOT,NAME,STAGE,expected,config_expected)
assets=ssh(program,timeout=180)
save('frozen_assets.json',assets)
save('cpu_manifest.json',{k:assets[k] for k in ('operator_path','operator_sha256')})
files=['cpu_manifest.json','neighbor_content.py','cpu_contracts.py']
guard()
upload=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',*[str(OUT/f) for f in files],
 'songcl@192.168.1.115:'+STAGE+'/'],60)
save('cpu_upload.json',{'returncode':upload.returncode,'stdout':upload.stdout,'stderr':upload.stderr})
assert upload.returncode==0
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 python -B '+shlex.quote(STAGE+'/cpu_contracts.py')
guard()
execution=run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115',shlex.join(['bash','-lc',command])],180)
save('cpu_execution.json',{'returncode':execution.returncode,'stdout':execution.stdout,'stderr':execution.stderr,'cuda_visible_devices':''})
fetch=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+STAGE+'/cpu_contracts_result.json',str(OUT/'cpu_contracts_result.json')],60)
save('cpu_fetch.json',{'returncode':fetch.returncode,'stdout':fetch.stdout,'stderr':fetch.stderr})
assert fetch.returncode==0
result=json.loads((OUT/'cpu_contracts_result.json').read_text())
print(json.dumps({'passed':result['passed'],'checks':len(result['checks']),'cuda_initialized':result.get('cuda_initialized'),'checkpoint_sha256':assets['checkpoint_sha256'],'execution_returncode':execution.returncode,'error':result.get('error')}))
