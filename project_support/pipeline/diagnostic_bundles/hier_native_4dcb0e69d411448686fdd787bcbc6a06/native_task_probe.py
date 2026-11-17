"""Full original native task path with paired diagnostic readout interventions."""
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

ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
STAGE=ROOT.parent/'pipeline/server3_fallback_abdff23d'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
UUID='GPU-340de111-e7e4-ed2d-15c9-8ab6a253e4a0'
os.environ.update(CUDA_VISIBLE_DEVICES='1',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def deadline_guard():
    assert (datetime.fromisoformat(FOREGROUND_DEADLINE)-datetime.now(timezone.utc)).total_seconds()>90
def resource_guard():
    raw=subprocess.check_output(['nvidia-smi','-i','1','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
    cells=[x.strip() for x in raw.split(',')]
    assert cells[:2]==['1',UUID]
    processes=subprocess.check_output(['nvidia-smi','-i','1','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
    own=0
    for row in processes.splitlines():
        pid,memory=[int(x.strip()) for x in row.split(',')]
        assert pid==os.getpid(),'Foreign context; refuse use.'
        own+=memory
    assert int(cells[4])+own>=int(cells[2])-1024
    assert own<=int(int(cells[2])*.25)+1024
    return {'observed_at':datetime.now(timezone.utc).isoformat(),'gpu':raw,'contexts':processes}

assert subprocess.check_output(['hostname'],text=True,timeout=5).strip()=='sysu311-MS-7C59'
assert sha(ROOT/'configs/Quard/ctf_hcg_csort'/(MODEL+'.yaml'))=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
assert sha(ROOT/'framework/model/Quard_model'/MODEL/'hier_postprocess.py')=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
assert sha(STAGE/'frozen_m95.pth')=='fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
deadline_guard()
resources=[resource_guard()]
locks=[]
try:
    for name in ('/tmp/cluster_project_gpu1_m201_migration.lock','/tmp/cluster_project_gpu1_exclusive.lock','/tmp/cluster_project_gpu1_parameter_transport.lock'):
        handle=open(name,'a+b')
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        locks.append(handle)
    resources.append(resource_guard())
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
    mod=importlib.import_module('framework.model.Quard_model.'+MODEL)
    model=mod.Network(**cfg.model)
    state=torch.load(STAGE/'frozen_m95.pth',map_location='cpu')['model']
    extra=set(state)-set(model.state_dict())
    assert extra<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    buffers=dict(model.named_buffers())
    assert all(k in buffers and torch.equal(state[k],buffers[k]) for k in extra)
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
    del state
    dataset=build_dataset(cfg.data.train,logging.getLogger('native-task-paired'))
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[0,60,101,124]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    batches=list(loader)
    expected=[(['scene0000_00','scene0002_00'],[0,1,2,3,0,1,2,3],[0,667,2996]),
              (['scene0003_00','scene0004_00'],[0,1,2,3,36,37,38,39],[0,406,1847])]
    assert len(batches)==2
    for batch,(scans,anns,offsets) in zip(batches,expected):
        assert batch['scan_ids']==scans and batch['ann_ids']==anns
        assert batch['batch_offsets'].tolist()==offsets
    resources.append(resource_guard())
    deadline_guard()
    torch.cuda.set_per_process_memory_fraction(.25,0)
    model.cuda().train()
    initial_buffers={name:buf.detach().clone() for name,buf in model.named_buffers()}
    original_readout=model.dec.cluster_att._cluster_to_points
    condition='m95'
    branch_calls=0
    def attend(query,key,uniform):
        if not len(key):return query*0
        if uniform:return key.mean(0,keepdim=True).expand_as(query)
        qh=query.reshape(-1,8,32).transpose(0,1)
        kh=key.reshape(-1,8,32).transpose(0,1)
        return ((((qh@kh.transpose(-1,-2))/math.sqrt(32)).softmax(-1)@kh).transpose(0,1).reshape_as(query))
    def intervention(self,point_feats,banks,cluster_ids_list,point_mask):
        global branch_calls
        branch_calls+=1
        if condition=='m95':return original_readout(point_feats,banks,cluster_ids_list,point_mask)
        B,N,C=point_feats.shape
        fused=torch.zeros_like(point_feats)
        weights=self.level_gate(torch.cat([point_feats,point_feats.mean(1,keepdim=True).expand_as(point_feats)],-1)).softmax(-1)
        for b in range(B):
            leaf_ids=cluster_ids_list[0][b].long()
            p1,p2=cluster_ids_list[1][b].long(),cluster_ids_list[2][b].long()
            leaves=leaf_ids.unique(sorted=True)
            mids=p1[leaves].unique(sorted=True)
            tops=p2[mids].unique(sorted=True)
            for leaf in leaves.tolist():
                mid=p1[leaf]
                top=p2[mid]
                selections=(leaves[p1[leaves]==mid],mids[(p2[mids]==top)&(mids!=mid)],tops[tops!=top])
                rows=torch.nonzero(leaf_ids==leaf,as_tuple=False).flatten()
                q=point_feats[b].index_select(0,rows)
                for level,cols in enumerate(selections):
                    message=attend(q,banks[level][b].index_select(0,cols),condition=='uniform')
                    fused[b,rows]+=message*weights[b,rows,level:level+1]
        return self.point_out_proj(self.dropout(fused)).masked_fill(point_mask.unsqueeze(-1),0)
    model.dec.cluster_att._cluster_to_points=types.MethodType(intervention,model.dec.cluster_att)
    head={}
    def hook(module,inputs,result):
        head['masks']=result[2].detach().cpu().clone()
        head['indis']=result[3].detach().cpu().clone()
    handle=model.dec.decoder_layers[-1].register_forward_hook(hook)
    records=[]
    def iou(pred,target):
        pred=pred>0
        target=target>0
        union=(pred|target).sum().item()
        return (pred&target).sum().item()/max(union,1)
    try:
        for pair,batch in enumerate(batches):
            scans=[(scene,scene_index) for scene_index,(scene,count) in enumerate(zip(batch['scan_ids'],batch['scenes_len'])) for _ in range(int(count))]
            for trial in range(2):
                for condition in ('m95','uniform','content'):
                    deadline_guard()
                    resource_guard()
                    with torch.no_grad():
                        for name,buf in model.named_buffers():buf.copy_(initial_buffers[name])
                    gorilla.set_random_seed(1999)
                    head.clear()
                    branch_calls=0
                    torch.cuda.reset_peak_memory_stats(0)
                    with torch.no_grad():loss,parts=model(copy.deepcopy(batch),mode='loss')
                    torch.cuda.synchronize()
                    assert torch.isfinite(loss).all() and branch_calls>0
                    assert set(head)=={'masks','indis'} and torch.isfinite(head['masks']).all()
                    expressions=[]
                    for b,(scan,scene_index) in enumerate(scans):
                        top=int(head['indis'][b].softmax(-1)[:,1].argmax())
                        sp_target=batch['gt_spmasks'][b].detach().cpu()
                        selected=head['masks'][b,top,:len(sp_target)]
                        low,high=[int(v) for v in batch['batch_offsets'][scene_index:scene_index+2]]
                        native_sp=batch['superpoints']
                        local_sp=native_sp[(native_sp>=low)&(native_sp<high)].long()-low
                        point_target=batch['gt_pmasks'][b].detach().cpu()
                        assert len(local_sp)==len(point_target)
                        expressions.append({'scan_id':scan,'ann_id':int(batch['ann_ids'][b]),'selected_query':top,
                            'train_sp_iou':iou(selected,sp_target),'train_point_iou':iou(selected[local_sp],point_target)})
                    records.append({'pair':pair,'trial':trial,'condition':condition,'loss':float(loss.detach().cpu()),
                        'loss_components':{k:float(v.detach().cpu()) if torch.is_tensor(v) else float(v) for k,v in parts.items()},
                        'branch_calls':branch_calls,'peak_allocated_bytes':torch.cuda.max_memory_allocated(0),
                        'peak_reserved_bytes':torch.cuda.max_memory_reserved(0),'expressions':expressions,
                        '_masks':head['masks'],'_indis':head['indis']})
                    print('NATIVE_TASK_PROGRESS='+json.dumps({'pair':pair,'trial':trial,'condition':condition,'loss':records[-1]['loss']}),flush=True)
    finally:
        handle.remove()
        model.dec.cluster_att._cluster_to_points=original_readout
    comparisons=[]
    for pair in (0,1):
        for trial in (0,1):
            base=next(r for r in records if r['pair']==pair and r['trial']==trial and r['condition']=='m95')
            for name in ('uniform','content'):
                row=next(r for r in records if r['pair']==pair and r['trial']==trial and r['condition']==name)
                comparisons.append({'pair':pair,'trial':trial,'condition':name,
                    'loss_delta':row['loss']-base['loss'],'final_mask_max_delta':(row['_masks']-base['_masks']).abs().max().item(),
                    'selected_query_changes':sum(a['selected_query']!=b['selected_query'] for a,b in zip(base['expressions'],row['expressions']))})
    repeats=[]
    for pair in (0,1):
        for name in ('m95','uniform','content'):
            a,b=[next(r for r in records if r['pair']==pair and r['trial']==t and r['condition']==name) for t in (0,1)]
            repeats.append({'pair':pair,'condition':name,'loss_delta':abs(a['loss']-b['loss']),
                'mask_max_delta':(a['_masks']-b['_masks']).abs().max().item()})
    for row in records:
        row.pop('_masks')
        row.pop('_indis')
    result={'observed_at':datetime.now(timezone.utc).isoformat(),'token':FOREGROUND_TOKEN,
        'network_forwards':len(records),'train_groups':[0,60,101,124],'unique_scenes':4,'unique_expressions':16,
        'optimizer_steps':0,'backward_executions':0,'new_training':False,'resources':resources,
        'comparisons':comparisons,'repeats':repeats,'records':records,
        'old_failures_reclassified':False,'all_new_core_admission_gates_remain_unpassed':True,
        'scope':'Full native TRAIN path response to diagnostic readout interventions. Not new-model admission, official VAL mIoU, trained efficacy or population harm.'}
    print('HIER_NATIVE_RESULT='+json.dumps(result))
finally:
    for handle in reversed(locks):handle.close()
