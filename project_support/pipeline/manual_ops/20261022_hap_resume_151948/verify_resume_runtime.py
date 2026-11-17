"""Fresh CPU full-state, frozen-asset and GPU0-only lease/idleness verification."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
PAYLOAD=r'''
import socket
assert socket.gethostname()=='dl04-MS-7E06'
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
import datetime as dt,fcntl,hashlib,json,math,subprocess
from pathlib import Path
import yaml
root=Path(PARAMS['remote_code_root'])
checkpoint=Path(PARAMS['resume_from'])
handles=[]
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def observe():
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
    f=[x.strip() for x in row.split(',')]
    assert f[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
    ctx=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=15).strip()
    return dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),inventory=row,contexts=ctx,idle=(not ctx and int(f[2])<1024 and int(f[3])<10))
before=observe()
try:
    for kind in ('training','diagnostic','exclusive'):
        h=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
        fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);handles.append(h)
    after=observe()
    assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PARAMS['code_commit']
    cfg=yaml.safe_load((root/PARAMS['config']).read_text())
    assert cfg['train']['seed']==1999 and cfg['train']['epochs']==50
    assert cfg['dataloader']['train']['num_workers']==4 and cfg['dataloader']['train']['persistent_workers'] is True
    assert Path(cfg['data']['train']['data_root']).is_dir() and Path(cfg['model']['data_root']).is_dir()
    assert cfg['data']['train']['training'] is True and cfg['data']['train']['prefix']=='train'
    assert cfg['train']['pretrain']==ASSETS['pretrain']
    checked={}
    for path,expected in [(root/'framework/dataset/scannetv2.py',ASSETS['dataset_source_sha256']),
        (root/'tools/train.py',ASSETS['native_train_source_sha256']),
        (Path(ASSETS['annotation_path']),ASSETS['annotation_sha256']),
        (Path(ASSETS['pretrain']),ASSETS['pretrain_sha256']),
        (checkpoint,PARAMS['checkpoint_sha256'])]:
        actual=digest(path);assert actual==expected,str(path)
        checked[str(path)]={'sha256':actual,'bytes':path.stat().st_size}
    st=checkpoint.stat();stable=(st.st_ino,st.st_size,st.st_mtime_ns)
    import torch
    assert not torch.cuda.is_initialized()
    value=torch.load(str(checkpoint),map_location='cpu',weights_only=False,mmap=True)
    assert isinstance(value,dict) and set(('meta','model','optimizer','scheduler'))<=set(value)
    assert value['model'] and value['optimizer']['state'] and value['optimizer']['param_groups'] and value['scheduler']
    def cpu(v):
        if torch.is_tensor(v):return v.device.type=='cpu'
        if isinstance(v,dict):return all(cpu(x) for x in v.values())
        if isinstance(v,(list,tuple)):return all(cpu(x) for x in v)
        return True
    assert cpu(value) and not torch.cuda.is_initialized()
    meta=value['meta'];assert meta['epoch']==18 and meta['epochs_no_improve']==0 and math.isfinite(float(meta['best_miou']))
    assert float(meta['best_miou'])==0.4975287616252899
    st=checkpoint.stat();assert stable==(st.st_ino,st.st_size,st.st_mtime_ns)
    final=observe()
    inspection=dict(load_succeeded=True,map_location='cpu',all_tensors_cpu=True,cuda_initialized=False,
        model_state_present=True,model_state_nonempty=True,optimizer_state_present=True,optimizer_state_nonempty=True,
        scheduler_state_present=True,scheduler_state_nonempty=True,optimizer_state_count=len(value['optimizer']['state']),
        optimizer_parameter_groups=len(value['optimizer']['param_groups']),scheduler_keys=list(value['scheduler']),
        meta=dict(epoch=int(meta['epoch']),best_miou=float(meta['best_miou']),epochs_no_improve=int(meta['epochs_no_improve'])))
    print(json.dumps(dict(observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),hostname=socket.gethostname(),
        source_checkpoint=PARAMS['resume_from'],checkpoint_sha256=PARAMS['checkpoint_sha256'],
        before=before,after_lock=after,final=final,three_flocks_acquired=True,flocks_released_on_process_exit=True,
        checked_assets=checked,cpu_inspection=inspection,torch_version=torch.__version__,
        native_yaml_preserved=True,original_failure_fixed=False,training_started=False,
        GPU1='NOT_QUERIED_RELEASED_TO_OTHERS',GPU_computation=False,signals_sent=False)))
finally:
    for h in reversed(handles):h.close()
'''

def main():
    plan_path=ROOT/'pipeline/diagnostic_bundles/tick_5c46f46a/hap_resume_plan.json'
    manifest_path=ROOT/'pipeline/diagnostic_bundles/tick_008137b4/hap_prepare/native_manifest.json'
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert manifest['candidate_id']=='hierarchy-affine-coarse-to-fine-prolongation' and manifest['code_commit']==plan['code_commit']
    payload='PARAMS='+repr(plan)+'\nASSETS='+repr(manifest['assets'])+'\n'+PAYLOAD
    args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
          'songcl@192.168.1.115','/home/songcl/.conda/envs/project_cluster/bin/python -B -']
    r=subprocess.run(args,input=payload,capture_output=True,text=True,encoding='utf-8',timeout=150)
    result=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),command=args,
        payload_sha256=hashlib.sha256(payload.encode()).hexdigest(),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,
        historical_asset_manifest=dict(path=manifest_path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest()),
        old_manifest_lease_executed=False)
    if r.returncode==0:result['data']=json.loads(r.stdout)
    p=BASE/'fresh_runtime_checkpoint_verification.json'
    with p.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),**result.get('data',{})),ensure_ascii=False))
    if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':main()
