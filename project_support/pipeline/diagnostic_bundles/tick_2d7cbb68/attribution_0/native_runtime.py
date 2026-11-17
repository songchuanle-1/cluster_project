"""Frozen diagnostic runtime; explicit fresh execution lease before any CUDA."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys

STAGE=Path(__file__).resolve().parent
MANIFEST=json.loads((STAGE/'native_manifest.json').read_text())
ASSETS=MANIFEST['assets'];ROOT=Path(MANIFEST['root']);NAME=MANIFEST['name']
HANDLES=[]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def verify():
    for name,value in ASSETS['source_hashes'].items():assert sha(ROOT/'framework/model/Quard_model'/NAME/name)==value,name
    for name in ('config','checkpoint','annotation'):
        path=ASSETS['config_path'] if name=='config' else ASSETS['annotation_path'] if name=='annotation' else ASSETS['checkpoint']
        assert sha(path)==ASSETS[name+'_sha256'],name
    assert sha(ROOT/'framework/dataset/scannetv2.py')==ASSETS['dataset_source_sha256']
    for name,value in MANIFEST['diagnostic_files'].items():assert sha(STAGE/name)==value,name
    assert MANIFEST['tolerance']==1e-6

def observe(require_idle=False):
    assert socket.gethostname()=='dl04-MS-7E06'
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    fields=[s.strip() for s in row.split(',')]
    assert fields[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    foreign=[s for s in contexts.splitlines() if int(s.split(',')[0])!=os.getpid()]
    assert not foreign,'Occupied authorized GPU;no sharing or eviction'
    if require_idle:assert not contexts and int(fields[2])<1024 and int(fields[3])<10
    return {'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':row,'contexts':contexts}

def acquire(lease_path):
    lease=json.loads(Path(lease_path).read_text())
    assert lease['project']=='cluster_project' and lease['thread_id']=='01a04987-fdbe-7301-b2f0-f9b6ab60f74c'
    assert lease['native_manifest_sha256']==sha(STAGE/'native_manifest.json')
    remaining=(datetime.fromisoformat(lease['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
    assert 300<remaining<=3600,'Require fresh current-tick lease with sufficient deadline'
    before=observe(True)
    try:
        for kind in ('training','diagnostic','exclusive'):
            handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BaseException:handle.close();raise
            HANDLES.append(handle)
        observe(True);verify()
        os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c')
        signal.alarm(min(1200,int(remaining)-150))
        return before
    except BaseException:release();raise

def release():
    for handle in reversed(HANDLES):handle.close()
    HANDLES.clear()

def fingerprint(torch,value):
    h=hashlib.sha256()
    def feed(item):
        if torch.is_tensor(item):
            item=item.detach().cpu().contiguous();h.update(str((str(item.dtype),tuple(item.shape))).encode());h.update(item.numpy().tobytes())
        elif isinstance(item,dict):
            for key in sorted(item):h.update(str(key).encode());feed(item[key])
        elif isinstance(item,(tuple,list)):
            for part in item:feed(part)
        else:h.update(repr(item).encode())
    feed(value);return h.hexdigest()

def save(name,value):
    value['observed_at']=datetime.now(timezone.utc).isoformat()
    with (STAGE/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)

def setup():
    import importlib
    sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
    from tools import train
    import torch,gorilla
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1);torch.cuda.set_per_process_memory_fraction(.75,0)
    module=importlib.import_module('framework.model.Quard_model.'+NAME)
    cfg=gorilla.Config.fromfile(ASSETS['config_path'])
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
    gorilla.set_random_seed(1999)
    model=module.Network(**cfg.model)
    checkpoint=torch.load(ASSETS['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
    state=checkpoint['model'];expected=model.state_dict();extra=set(state)-set(expected)
    buffers={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    assert extra<=buffers
    assert all(torch.equal(state[k],dict(model.named_buffers())[k]) for k in extra)
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
    meta=checkpoint['meta'];del checkpoint,state
    model.cuda().eval()
    return torch,gorilla,cfg,model,meta
