"""One fresh-process matched full native memory/gradient diagnosis."""
import copy
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib
import json
import logging
import math
import os
from pathlib import Path
import subprocess
import sys
import types

os.environ.update(CUDA_VISIBLE_DEVICES='1',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
STAGE=ROOT.parent/'pipeline/server3_fallback_abdff23d'
UUID='GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0'
assert subprocess.check_output(['hostname'],text=True,timeout=5).strip()=='sysu311-MS-7C59'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
assert sha(STAGE/'frozen_m95.pth')=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
assert sha(ROOT/'configs/Quard/ctf_hcg_csort'/(MODEL+'.yaml'))=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
def observe(stage):
    line=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
    cells=[c.strip() for c in line.split(',')]
    assert cells[:2]==['1',UUID]
    text=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
    entries=[{'pid':int(row.split(',')[0]),'memory_mib':int(row.split(',')[1])} for row in text.splitlines()]
    assert all(entry['pid']==os.getpid() for entry in entries),'Foreign context; no allocation.'
    own=sum(entry['memory_mib'] for entry in entries)
    row={'stage':stage,'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':line,'contexts':entries,
        'own_mib':own,'post_budget_limit_mib':int(int(cells[2])*.25)+1024,
        'post_budget_passed':own<=int(int(cells[2])*.25)+1024}
    if 'torch' in globals() and torch.cuda.is_initialized():
        row.update(torch_allocated_bytes=torch.cuda.memory_allocated(),torch_reserved_bytes=torch.cuda.memory_reserved(),
            torch_peak_allocated_bytes=torch.cuda.max_memory_allocated(),torch_peak_reserved_bytes=torch.cuda.max_memory_reserved())
    assert int(cells[4])+own>=int(cells[2])-1024
    return row
observations=[observe('before')]
assert observations[-1]['own_mib']==0
locks=[]
try:
    for name in ('/tmp/cluster_project_gpu1_m201_migration.lock','/tmp/cluster_project_gpu1_exclusive.lock','/tmp/cluster_project_gpu1_parameter_transport.lock'):
        handle=open(name,'a+b')
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks.append(handle)
    sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
    import torch,gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    cfg=gorilla.Config.fromfile(str(ROOT/'configs/Quard/ctf_hcg_csort'/(MODEL+'.yaml')))
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    cfg.model.data_root=cfg.data.train.data_root='/sdc1/songcl/IPDN/data/'
    gorilla.set_random_seed(1999)
    module=importlib.import_module('framework.model.Quard_model.'+MODEL)
    model=module.Network(**cfg.model)
    state=torch.load(STAGE/'frozen_m95.pth',map_location='cpu')['model']
    extra=set(state)-set(model.state_dict())
    assert extra<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    assert all(torch.equal(state[k],dict(model.named_buffers())[k]) for k in extra)
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
    del state
    dataset=build_dataset(cfg.data.train,logging.getLogger('same-pair-memory'))
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[0,60]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    assert batch['scan_ids']==['scene0000_00','scene0002_00'] and batch['ann_ids']==[0,1,2,3,0,1,2,3]
    assert batch['batch_offsets'].tolist()==[0,667,2996]
    if MEMORY_CONDITION=='canonical':
        assert hashlib.sha256(CANONICAL_SOURCE.encode()).hexdigest()=='18ce8dde33c99f3f4fa7efd037cf38d54b9978f4f996429ec9f9bfcddffa5d93'
        core={}
        exec(compile(CANONICAL_SOURCE,'<revision1-full-native-memory>','exec'),core)
        def readout(self,p,banks,ids,mask):
            weights=self.level_gate(torch.cat([p,p.mean(1,keepdim=True).expand_as(p)],-1)).softmax(-1)
            messages=[core['canonical'](p[b],[bank[b] for bank in banks],ids[0][b].long(),ids[1][b].long(),ids[2][b].long(),weights[b]) for b in range(p.shape[0])]
            return self.point_out_proj(self.dropout(torch.stack(messages))).masked_fill(mask.unsqueeze(-1),0)
        model.dec.cluster_att._cluster_to_points=types.MethodType(readout,model.dec.cluster_att)
    observations.append(observe('before_cuda_allocation'))
    torch.cuda.set_per_process_memory_fraction(.25,0)
    model.cuda().train()
    model.zero_grad(set_to_none=True)
    observations.append(observe('model_loaded'))
    assert observations[-1]['post_budget_passed']
    retained={}
    def hook(module,inputs,output):
        retained['message']=output['point']
        retained['message'].retain_grad()
    handle=model.dec.cluster_att.register_forward_hook(hook)
    outcome={'condition':MEMORY_CONDITION,'full_forward_completed':False,'full_backward_completed':False}
    try:
        assert (datetime.fromisoformat(FOREGROUND_DEADLINE)-datetime.now(timezone.utc)).total_seconds()>120
        gorilla.set_random_seed(1999)
        torch.cuda.reset_peak_memory_stats()
        loss,_=model(copy.deepcopy(batch),mode='loss')
        torch.cuda.synchronize()
        assert torch.isfinite(loss).all()
        outcome.update(full_forward_completed=True,native_loss=float(loss.detach().cpu()))
        observations.append(observe('after_forward'))
        assert observations[-1]['post_budget_passed'],'Original post-budget guard after forward refused.'
        loss.backward()
        torch.cuda.synchronize()
        gradient=retained['message'].grad
        assert gradient is not None and torch.isfinite(gradient).all() and gradient.norm().item()>0
        active={name:float(parameter.grad.norm().detach().cpu()) for name,parameter in model.dec.cluster_att.named_parameters() if parameter.grad is not None}
        assert active and all(math.isfinite(value) and value>0 for value in active.values())
        outcome.update(full_backward_completed=True,message_gradient_norm=float(gradient.norm().detach().cpu()),
            active_existing_cluster_tensors=len(active),gradient_norms=active)
        observations.append(observe('after_backward'))
    except (RuntimeError,AssertionError) as exc:
        outcome.update(error_type=type(exc).__name__,error=str(exc))
        observations.append(observe('after_exception'))
    finally:handle.remove()
    outcome['budget_passed_all_observations']=all(r['post_budget_passed'] for r in observations)
    outcome['passed_this_diagnostic']=outcome['full_backward_completed'] and outcome['budget_passed_all_observations']
    result={'observed_at':datetime.now(timezone.utc).isoformat(),'token':FOREGROUND_TOKEN,
        'outcome':outcome,'observations':observations,'train_groups':[0,60],'scenes':2,'expressions':8,
        'allocator_fraction':.25,'optimizer_steps':0,'new_training':False,'source_independent_model':False,
        'scope':'Matched fresh-process first-pair memory/gradient diagnosis only; not full-cohort admission, physical24GB insufficiency or trained efficacy.'}
    print('HIER_NATIVE_RESULT='+json.dumps(result))
    model.zero_grad(set_to_none=True)
finally:
    for handle in reversed(locks):handle.close()
