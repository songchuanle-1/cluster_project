"""Project-local manual launch guard; the candidate model and native loop are unchanged."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from datetime import datetime,timezone
import fcntl

parser=argparse.ArgumentParser()
parser.add_argument('--manifest',required=True)
parser.add_argument('native',nargs=argparse.REMAINDER)
args=parser.parse_args()
manifest=json.loads(Path(args.manifest).read_text())
root=Path(manifest['root'])
uuid='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
handles=[]

def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):result.update(block)
    return result.hexdigest()

def observe():
    assert socket.gethostname()=='dl04-MS-7E06'
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    cells=[cell.strip() for cell in row.split(',')]
    assert cells[:2]==['0',uuid]
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    assert not contexts and int(cells[2])<1024 and int(cells[3])<10,'GPU0 busy;no sharing,eviction or reset'
    return row

status={'started_at':datetime.now(timezone.utc).isoformat(),'scientific_admission':False,'return_status':'starting'}
try:
    assert args.native==['tools/train.py',manifest['config'],'--gpu_ids','0','--num_gpus','1']
    assert sha(Path(__file__))==manifest['guard_sha256']
    auth_path=Path(manifest['authorization_path'])
    assert sha(auth_path)==manifest['authorization_sha256']
    auth=json.loads(auth_path.read_text())
    assert auth['authorized'] is True and auth['maximum_training_launches']==1
    assert auth['candidate_id']=='coarse-semantic-point-cross-attention' and auth['scientific_admission'] is False
    assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==manifest['code_commit']
    for path,digest in manifest['runtime_files'].items():assert sha(root/path)==digest,path
    assert sha(manifest['pretrain'])==manifest['pretrain_sha256']
    assert sha(manifest['annotation'])==manifest['annotation_sha256']
    for cmdfile in Path('/proc').glob('[0-9]*/cmdline'):
        if cmdfile.parent.name==str(os.getpid()):continue
        try:command=cmdfile.read_bytes().split(b'\0')
        except OSError:continue
        if b'tools/train.py' in command and manifest['config'].encode() in command:
            raise RuntimeError('Exact candidate already running;do not relaunch')
    before=observe()
    for kind in ('training','diagnostic','exclusive'):
        handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:handle.close();raise
        handles.append(handle)
    observe()
    os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES=uuid,PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
    sys.path[:0]=[str(root),str(root/'framework/lib')]
    os.chdir(root)
    sys.argv=args.native
    from tools import train
    assert not train.torch.cuda.is_initialized()
    native=train.get_args()
    assert native.resume is None and native.gpu_ids==[0] and native.num_gpus==1
    cfg=train.gorilla.Config.fromfile(native.config)
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
    assert cfg.model.dec.cluster_mode=='ctf_hcg_cpa_csort' and cfg.train.pretrain==manifest['pretrain']
    train.gorilla.set_cuda_visible_devices(gpu_ids=native.gpu_ids,num_gpu=1)
    os.environ['CUDA_VISIBLE_DEVICES']=uuid
    status.update(return_status='training',pid=os.getpid(),physical_gpu=0,gpu_uuid=uuid,before=before,locks=['training','diagnostic','exclusive'])
    print('CPA_EXPLORATORY_STARTUP_GUARD='+json.dumps(status),flush=True)
    train.gorilla.launch(train.main,1,num_machines=native.num_machines,machine_rank=native.machine_rank,dist_url=native.dist_url,args=(native,))
    status['return_status']='native_training_returned'
except BaseException as error:
    status.update(return_status='failed',error_type=type(error).__name__,error=str(error))
    raise
finally:
    status['finished_at']=datetime.now(timezone.utc).isoformat()
    try:
        with (Path(args.manifest).parent/'native_exit.json').open('x') as stream:json.dump(status,stream,indent=2)
    finally:
        for handle in reversed(handles):handle.close()
