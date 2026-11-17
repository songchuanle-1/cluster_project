"""Bounded unchanged native M95/HDS target-runtime validation, not training."""
import os
os.environ.update(CUDA_DEVICE_ORDER='PCI_BUS_ID',CUDA_VISIBLE_DEVICES='0',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import copy, fcntl, hashlib, importlib, json, logging, math, signal, subprocess, sys, time
from datetime import datetime,timezone
from pathlib import Path
signal.alarm(600)
ROOT=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
STAGE=ROOT.parent/'pipeline/hds_server4_3c22e34d'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
NAME=BASE+'_hds_canon_r1'
CONFIG=ROOT/'configs/Quard/ctf_hcg_csort_hds_canon_r1'/(NAME+'.yaml')
UUID='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
condition=sys.argv[1]
assert condition in ('baseline','candidate','transport')
assert subprocess.check_output(['hostname'],text=True).strip()=='dl04-MS-7E06'
locks=[]
for name in ('training','diagnostic','exclusive'):
    h=open('/tmp/cluster_project_gpu0_'+name+'.lock','a+b');fcntl.flock(h,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(h)
def gpu():
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip()
    assert row.split(',')[1].strip()==UUID
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True).strip()
    assert all(int(line.split(',')[0])==os.getpid() for line in contexts.splitlines()),'Foreign GPU context; no eviction.'
    return dict(observed_at=datetime.now(timezone.utc).isoformat(),gpu=row,contexts=contexts)
before=gpu(); assert not before['contexts']
sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
from tools import train as native_train
import torch,gorilla,numpy as np
from framework.dataset import build_dataset,build_dataloader
from torch.utils.data import DataLoader,Subset
torch.set_num_threads(1)
cfg=gorilla.Config.fromfile(str(CONFIG))
assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
cfg.model.data_root=cfg.data.train.data_root=cfg.data.val.data_root='/home/songcl/data/data/'
gorilla.set_random_seed(1999)
dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('server4-frozen-native'))
if condition=='transport':
    loader=DataLoader(Subset(dataset,[0,60,101,124]),batch_size=2,shuffle=False,num_workers=4,persistent_workers=True,pin_memory=True,collate_fn=dataset.collate_fn)
    identity=[]
    for batch in loader:identity.append(dict(scan_ids=batch['scan_ids'],ann_ids=batch['ann_ids']))
    assert len(identity)==2 and identity[0]['scan_ids']==['scene0000_00','scene0002_00']
    assert identity[0]['ann_ids']==[0,1,2,3,0,1,2,3]
    del loader
    result=dict(condition=condition,passed=True,train_workers=4,persistent_workers=True,sharing_strategy=torch.multiprocessing.get_sharing_strategy(),batches=identity,cuda_initialized=torch.cuda.is_initialized(),optimizer_steps=0)
else:
    checkpoint=STAGE/'frozen_m95.pth'
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest()=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
    module=importlib.import_module('framework.model.Quard_model.'+(BASE if condition=='baseline' else NAME))
    model=module.Network(**cfg.model)
    state=torch.load(checkpoint,map_location='cpu')['model']
    extra=set(state)-set(model.state_dict())
    assert extra<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    assert all(torch.equal(state[k],dict(model.named_buffers())[k]) for k in extra)
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True);del state
    torch.cuda.set_per_process_memory_fraction(.25,0)
    dummy=torch.zeros(1,device='cuda');torch.cuda.synchronize()
    own=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader,nounits'],text=True)
    assert any(int(row.split(',')[0])==os.getpid() and UUID in row for row in own.splitlines())
    del dummy
    model.cuda().train();rows=[]
    for pair in ([0,60],[101,124]):
        gorilla.set_random_seed(1999)
        loader=DataLoader(Subset(dataset,pair),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
        batch=next(iter(loader))
        if pair==[0,60]:
            assert batch['scan_ids']==['scene0000_00','scene0002_00'] and batch['ann_ids']==[0,1,2,3,0,1,2,3]
            assert batch['batch_offsets'].tolist()==[0,667,2996]
        model.zero_grad(set_to_none=True);retained={}
        def hook(module,args,out):
            retained['point']=out['point'];retained['point'].retain_grad()
        handle=model.dec.cluster_att.register_forward_hook(hook)
        gorilla.set_random_seed(1999);torch.cuda.reset_peak_memory_stats()
        loss,_=model(copy.deepcopy(batch),mode='loss');torch.cuda.synchronize();assert torch.isfinite(loss).all()
        loss.backward();torch.cuda.synchronize()
        gradient=retained['point'].grad;assert gradient is not None and torch.isfinite(gradient).all() and gradient.norm().item()>0
        norms={n:float(p.grad.norm().detach().cpu()) for n,p in model.dec.cluster_att.named_parameters() if p.grad is not None}
        assert len(norms)==24 and all(math.isfinite(v) and v>0 for v in norms.values())
        rows.append(dict(pair=pair,scan_ids=batch['scan_ids'],ann_ids=batch['ann_ids'],batch_offsets=batch['batch_offsets'].tolist(),loss=float(loss.detach().cpu()),active_point_path_tensors=len(norms),point_gradient_norm=float(gradient.norm().detach().cpu()),gradient_norms=norms,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),gpu=gpu()))
        handle.remove();model.zero_grad(set_to_none=True);del loss,batch,loader,retained,gradient
    cfg.data.val.lang_num_max=1
    validation=build_dataset(copy.deepcopy(cfg.data.val),logging.getLogger('server4-resource-only'))
    loader=build_dataloader(validation,batch_size=1,num_workers=0,persistent_workers=False,training=False)
    gorilla.set_random_seed(1999);sample=next(iter(loader));assert len(sample['ann_ids'])==1
    model.eval()
    with torch.no_grad():
        for _ in range(20):model(sample,mode='predict')
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();times=[]
        for _ in range(100):
            torch.cuda.synchronize();start=time.perf_counter();prediction=model(sample,mode='predict');torch.cuda.synchronize();times.append((time.perf_counter()-start)*1000)
        assert prediction['piou'] and all(torch.isfinite(v).all() for v in prediction['piou'])
    result=dict(condition=condition,passed=True,torch=torch.__version__,cuda=torch.version.cuda,train_rows=rows,parameters=sum(p.numel() for p in model.parameters()),inference=dict(batch_size=1,warmup=20,repeat=100,scan_ids=sample['scan_ids'],ann_ids=sample['ann_ids'],median_ms=float(np.median(times)),p90_ms=float(np.percentile(times,90)),peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()),allocator_fraction=.25,optimizer_steps=0,cuda_device=torch.cuda.get_device_name(),last_gpu=gpu())
result.update(observed_at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),before=before,scope='Fixed four TRAIN scenes and one VAL expression resource-only. No training/efficacy/whole-training-memory guarantee or reconstructing the failed source batch.')
print('HDS_SERVER4_NATIVE_RESULT='+json.dumps(result),flush=True)
