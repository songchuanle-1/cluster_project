import os
os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES='0',
                  PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
                  TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
                  OMP_NUM_THREADS='1')
import copy
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib
import json
import logging
from pathlib import Path
import signal
import socket
import subprocess
import sys

signal.alarm(600)
ROOT = Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
NAME = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_hds_canon_r1'
CONFIG = ROOT / 'configs/Quard/ctf_hcg_csort_hds_canon_r1' / (NAME+'.yaml')
CHECKPOINT = Path('/data/songcl/Project/Cluster_project/Cluster_checkpoints') / NAME / '20261016_173442/last.pth'
CHECKPOINT_SHA = 'fe4301ec2607f0ee0604173ea31422ae91df8e15b082657c557955c2c4d67e6c'
UUID = 'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
assert socket.gethostname() == 'dl04-MS-7E06'
handles=[]
for kind in ('training','diagnostic','exclusive'):
    handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
    fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    handles.append(handle)
def gpu():
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
    assert UUID in row
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
    assert all(int(line.split(',')[0])==os.getpid() for line in contexts.splitlines())
    return {'row':row,'contexts':contexts}
before=gpu()
assert not before['contexts'] and int(before['row'].split(',')[2])<1000
assert hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()==CHECKPOINT_SHA
sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
from tools import train as native_train
import torch
import gorilla
from framework.dataset import build_dataset
from torch.utils.data import DataLoader, Subset
torch.set_num_threads(1)
cfg=gorilla.Config.fromfile(str(CONFIG))
assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
gorilla.set_random_seed(1999)
module=importlib.import_module('framework.model.Quard_model.'+NAME)
model=module.Network(**cfg.model).cuda()
optimizer=gorilla.build_optimizer(model,cfg.optimizer)
scheduler=gorilla.build_lr_scheduler(optimizer,cfg.lr_scheduler)
checkpoint=torch.load(CHECKPOINT,map_location='cpu')
metadata=checkpoint['meta']
assert metadata['epoch']==7 and metadata['epochs_no_improve']==0
identities={name:id(parameter) for name,parameter in model.named_parameters()}
resume_meta=gorilla.resume(model=model,filename=str(CHECKPOINT),optimizer=optimizer,
                          scheduler=scheduler,strict=False,map_location='cpu')
def equivalent(actual,expected):
    if torch.is_tensor(expected):
        return torch.is_tensor(actual) and actual.dtype==expected.dtype and torch.equal(actual.detach().cpu(),expected.detach().cpu())
    if isinstance(expected,dict):
        return isinstance(actual,dict) and actual.keys()==expected.keys() and all(equivalent(actual[k],v) for k,v in expected.items())
    if isinstance(expected,(list,tuple)):
        return isinstance(actual,(list,tuple)) and len(actual)==len(expected) and all(equivalent(a,b) for a,b in zip(actual,expected))
    return bool(actual==expected)
assert equivalent(resume_meta,metadata)
actual_state=model.state_dict()
assert all(name in checkpoint['model'] and equivalent(value,checkpoint['model'][name]) for name,value in actual_state.items())
extras=set(checkpoint['model'])-set(actual_state)
assert extras<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
assert equivalent(optimizer.state_dict(),checkpoint['optimizer'])
assert equivalent(scheduler.state_dict(),checkpoint['scheduler'])
checks=[]
def conversion(phase,count):
    for _ in range(count):
        assert all(callable(parameter.cuda) for parameter in model.parameters())
        model.cuda()
        assert identities=={name:id(parameter) for name,parameter in model.named_parameters()}
        assert all(id(parameter) in set(identities.values()) for group in optimizer.param_groups for parameter in group['params'])
    checks.append({'phase':phase,'repeated_cuda_calls':count,'parameter_identity_unchanged':True})
conversion('after_native_resume',32)
assert equivalent(optimizer.state_dict(),checkpoint['optimizer'])
dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('m202-native-recovery'))
model.train()
rows=[]
for pair in ([0,60],[101,124]):
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,pair),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    batch=next(iter(loader))
    model.zero_grad(set_to_none=True)
    torch.cuda.reset_peak_memory_stats()
    loss,log_vars=model(copy.deepcopy(batch),mode='loss')
    assert torch.isfinite(loss).all()
    loss.backward()
    torch.cuda.synchronize()
    gradients={name:float(parameter.grad.norm().detach().cpu()) for name,parameter in model.dec.cluster_att.named_parameters() if parameter.grad is not None}
    assert len(gradients)==24 and all(value>0 and value<float('inf') for value in gradients.values())
    conversion('after_backward_'+str(pair),8)
    rows.append({'pair':pair,'scan_ids':batch['scan_ids'],'ann_ids':batch['ann_ids'],
                 'batch_offsets':batch['batch_offsets'].tolist(),'loss':float(loss.detach().cpu()),
                 'point_path_gradient_count':len(gradients),'point_path_gradient_norms':gradients,
                 'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
                 'peak_reserved_bytes':torch.cuda.max_memory_reserved()})
    model.zero_grad(set_to_none=True)
    del loss,batch,loader
assert equivalent(optimizer.state_dict(),checkpoint['optimizer'])
assert equivalent(scheduler.state_dict(),checkpoint['scheduler'])
assert hashlib.sha256(CHECKPOINT.read_bytes()).hexdigest()==CHECKPOINT_SHA
result={'observed_at':datetime.now(timezone.utc).isoformat(),'passed':True,
        'torch':torch.__version__,'pid':os.getpid(),'gpu_before':before,'gpu_after':gpu(),
        'checkpoint_sha256':CHECKPOINT_SHA,'meta':{'epoch':int(resume_meta['epoch']),
            'best_miou':float(resume_meta['best_miou']),
            'epochs_no_improve':int(resume_meta['epochs_no_improve'])},
        'metadata_extra':{key:str(value) for key,value in resume_meta.items() if key not in ('epoch','best_miou','epochs_no_improve')},
        'model_entries':len(actual_state),'optimizer_states':len(optimizer.state),
        'model_optimizer_scheduler_exactly_restored':True,'native_resume_executed':True,
        'conversion_checks':checks,'native_backward':rows,'optimizer_steps':0,
        'root_cause':'UNCONFIRMED; historical TypeError not reproduced by this bounded fresh-process test',
        'scope':'Recovery feasibility only; no source change, efficacy, exact stochastic replay, or full-run guarantee.'}
print('M202_RECOVERY_RESULT='+json.dumps(result),flush=True)
