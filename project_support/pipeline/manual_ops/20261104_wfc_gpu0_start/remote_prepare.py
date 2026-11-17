import socket
assert socket.gethostname()=='dl04-MS-7E06'
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1')
from datetime import datetime,timezone
import hashlib,json,math,shutil,subprocess
from pathlib import Path
import yaml

old=Path(PARAMS['old_root']); root=Path(PARAMS['remote_code_root']); base=old.parent.resolve()
assert root.parent.resolve()==base and root.name=='Cluster_resume_wfc_20261104' and not root.exists()
def git(where,*args): return subprocess.check_output(['git','--no-optional-locks','-c','core.fsmonitor=false','-C',str(where),*args])
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()
old_head=git(old,'rev-parse','HEAD').decode().strip(); assert old_head==PARAMS['old_head']
old_status=git(old,'status','--porcelain=v1','--untracked-files=all','-z')
assert git(old,'rev-parse',PARAMS['code_commit']+'^{commit}').decode().strip()==PARAMS['code_commit']
checkpoint=Path(PARAMS['resume_from']); checkpoint_sha=sha(checkpoint); assert checkpoint_sha==PARAMS['checkpoint_sha256']
saved_stat=checkpoint.stat(); stable=(saved_stat.st_ino,saved_stat.st_size,saved_stat.st_mtime_ns)
import torch
assert not torch.cuda.is_initialized()
value=torch.load(str(checkpoint),map_location='cpu',weights_only=False,mmap=True)
assert all(k in value for k in ('model','optimizer','scheduler','meta'))
assert value['model'] and value['optimizer']['state'] and value['optimizer']['param_groups'] and value['scheduler']
meta=value['meta']; assert int(meta['epoch'])==25 and int(meta['epochs_no_improve'])==5 and float(meta['best_miou'])==0.49711745977401733
def all_cpu(v):
    if torch.is_tensor(v): return v.device.type=='cpu'
    if isinstance(v,dict): return all(all_cpu(x) for x in v.values())
    if isinstance(v,(list,tuple)): return all(all_cpu(x) for x in v)
    return True
assert all_cpu(value) and not torch.cuda.is_initialized()
inspection=dict(load_succeeded=True,map_location='cpu',all_tensors_cpu=True,cuda_initialized=False,
    model_state_present=True,model_state_nonempty=True,optimizer_state_present=True,optimizer_state_nonempty=True,
    scheduler_state_present=True,scheduler_state_nonempty=True,optimizer_state_count=len(value['optimizer']['state']),
    optimizer_parameter_groups=len(value['optimizer']['param_groups']),scheduler_keys=list(value['scheduler']),
    meta=dict(epoch=int(meta['epoch']),best_miou=float(meta['best_miou']),epochs_no_improve=int(meta['epochs_no_improve'])))
del value
for name,want in PARAMS['hashes'].items():
    expected=PARAMS['deployed_yaml_sha'] if name.endswith('.yaml') else want
    assert sha(old/name)==expected,name
assets=PARAMS['assets']; checked={}
for name,want in [(str(old/'tools/train.py'),assets['native_train_source_sha256']),
    (str(old/'framework/dataset/scannetv2.py'),assets['dataset_source_sha256']),
    (assets['annotation_path'],assets['annotation_sha256']),(assets['pretrain'],assets['pretrain_sha256'])]:
    assert sha(name)==want,name; checked[name]=dict(sha256=want,bytes=Path(name).stat().st_size)
assert shutil.disk_usage(base).free>2*1024**3
created=subprocess.run(['git','-C',str(old),'worktree','add','--detach',str(root),PARAMS['code_commit']],text=True,capture_output=True,timeout=120)
assert created.returncode==0,created.stderr
assert git(root,'rev-parse','HEAD').decode().strip()==PARAMS['code_commit']
cfgpath=root/PARAMS['config']; original=yaml.safe_load(cfgpath.read_text())
def adapt(v):
    if isinstance(v,dict): return {k:adapt(x) for k,x in v.items()}
    if isinstance(v,list): return [adapt(x) for x in v]
    if isinstance(v,str):
        for a,b in PARAMS['mappings']: v=v.replace(a,b)
    return v
deployed=(old/PARAMS['config']).read_bytes(); assert yaml.safe_load(deployed)==adapt(original)
cfgpath.write_bytes(deployed); cfg=yaml.safe_load(cfgpath.read_text())
assert sha(cfgpath)==PARAMS['deployed_yaml_sha']
assert cfg['train']['seed']==1999 and cfg['train']['epochs']==50 and cfg['train']['pretrain']==assets['pretrain']
assert Path(cfg['model']['data_root']).is_dir() and Path(cfg['data']['train']['data_root']).is_dir()
extension='framework/lib/pointgroup_ops/pointgroup_ops_ext.cpython-310-x86_64-linux-gnu.so'
source=old/extension; destination=root/extension; assert source.is_file() and not destination.exists()
shutil.copyfile(source,destination); assert sha(source)==sha(destination)
for name,want in PARAMS['hashes'].items(): assert sha(root/name)==(PARAMS['deployed_yaml_sha'] if name.endswith('.yaml') else want),name
for relative in ('tools/train.py','framework/dataset/scannetv2.py'): assert sha(root/relative)==sha(old/relative),relative
(root/'logs').mkdir(exist_ok=True)
assert os.access(root/'logs',os.W_OK) and os.access(Path(cfg['work_dir']),os.W_OK)
assert git(old,'rev-parse','HEAD').decode().strip()==old_head and git(old,'status','--porcelain=v1','--untracked-files=all','-z')==old_status
last_stat=checkpoint.stat(); assert stable==(last_stat.st_ino,last_stat.st_size,last_stat.st_mtime_ns)
inventory=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
assert inventory.split(',')[1].strip()=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
print(json.dumps(dict(observed_at=datetime.now(timezone.utc).isoformat(),hostname=socket.gethostname(),
    isolated_original_version_prepared=True,remote_code_root=str(root),code_commit=PARAMS['code_commit'],
    old_runtime_root=str(old),old_runtime_head=old_head,old_runtime_source_and_status_unchanged=True,
    checkpoint_sha256=checkpoint_sha,checkpoint_bytes=saved_stat.st_size,cpu_inspection=inspection,
    checked_assets=checked,compiled_extension=dict(path=str(destination),sha256=sha(destination),source=str(source)),
    native_yaml_exact_original_deployed_bytes=True,torch_cuda_initialized=False,training_started=False,
    inventory_gpu0=inventory,contexts_gpu0=contexts,gpu1='NOT_QUERIED_NOT_AUTHORIZED',signals_sent=False)))
