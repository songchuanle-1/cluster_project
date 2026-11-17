"""Real frozen M95 message-prefix controls on CPU; no proxy mask claim."""
from ops import *
guard(180)
program=r'''import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
import sys,json,hashlib,importlib.util
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import torch
torch.set_num_threads(1)
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
sys.path[:0]=[str(root),str(root/'framework/lib')]
source=root/'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
prefix=Path('/data/songcl/Project/Cluster_project/pipeline/native_stride_ed0d2b32/rank_m95/rank_prefix.npz')
assert hashlib.sha256(prefix.read_bytes()).hexdigest()=='46733f80cebfb2a3afe5a790d3b5ee6921beea2025de6803287940eca0d75132'
spec=importlib.util.spec_from_file_location('_m95_cached_scale_28fc',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
model=module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256,nhead=8,cluster_layer_nums=[256,64,8],per_layer_topk_list=[4,6,8],dropout=0.0).eval()
with np.load(prefix,allow_pickle=False) as data:
 tensor=lambda key:torch.from_numpy(data[key].copy())
 x=tensor('points');mask=tensor('mask');tokens=[tensor('tokens_'+str(s)) for s in range(3)]
 ids=[[tensor('ids_'+str(s)+'_'+str(b)) for b in range(x.shape[0])] for s in range(3)]
 expected=tensor('message')
 for name in ('level_gate','point_out_proj','message_norm'):
  layer=getattr(model,name)
  with torch.no_grad():
   layer.weight.copy_(tensor(name+'_weight'));layer.bias.copy_(tensor(name+'_bias'))
 model.message_norm.eps=float(data['message_norm_eps'])
 controls=[]
 with torch.no_grad():
  for dtype in (torch.float32,torch.float64):
   model=model.to(dtype);points=x.to(dtype);banks=[v.to(dtype) for v in tokens]
   original=model.message_norm(model._cluster_to_points(points,banks,ids,mask)).masked_fill(mask.unsqueeze(-1),0)
   p=[torch.cat([torch.arange(len(ids[0][b])).roll(1),torch.arange(len(ids[0][b]),points.shape[1])]) for b in range(points.shape[0])]
   xp=torch.stack([points[b,index] for b,index in enumerate(p)]);mp=torch.stack([mask[b,index] for b,index in enumerate(p)])
   ip=[[ids[0][b][p[b][:len(ids[0][b])]] for b in range(points.shape[0])],ids[1],ids[2]]
   perm=model.message_norm(model._cluster_to_points(xp,banks,ip,mp)).masked_fill(mp.unsqueeze(-1),0)
   pe=float((perm-torch.stack([original[b,index] for b,index in enumerate(p)])).abs().max())
   activities=[];deletion_controls=[]
   weights=torch.softmax(model.level_gate(torch.cat([points,points.mean(1,keepdim=True).expand_as(points)],-1)),-1)
   fullraw=model._cluster_to_points(points,banks,ids,mask)
   for scale in range(3):
    copied=list(banks);copied[scale]=torch.zeros_like(banks[scale])
    deleted=model.message_norm(model._cluster_to_points(points,copied,ids,mask)).masked_fill(mask.unsqueeze(-1),0)
    gathered=torch.zeros_like(points)
    for b in range(points.shape[0]):
     index=ids[0][b]
     for s in range(1,scale+1):index=ids[s][b][index]
     gathered[b,:len(index)]=banks[scale][b,index]
    subtract=model.message_norm(fullraw-torch.nn.functional.linear(gathered*weights[:,:,scale:scale+1],model.point_out_proj.weight,None)).masked_fill(mask.unsqueeze(-1),0)
    deletion_controls.append(float((deleted-subtract).abs().max()))
    activities.append(float((deleted-original).abs().max()))
   controls.append({'dtype':str(dtype),'source_reconstruction_vs_cached_gpu_max_error':float((original-expected.to(dtype)).abs().max()),'receiver_permutation_max_error':pe,'deletion_form_equivalence_max_errors':deletion_controls,'deletion_activity_max_abs':activities,'permutation_strict_1e_minus6_passed':pe<=1e-6,'deletion_equivalence_strict_1e_minus6_passed':max(deletion_controls)<=1e-6,'source_vs_cache_strict_1e_minus6_passed':float((original-expected.to(dtype)).abs().max())<=1e-6})
 assert not torch.cuda.is_initialized()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'frozen_prefix_sha256':'46733f80cebfb2a3afe5a790d3b5ee6921beea2025de6803287940eca0d75132','trained_prefix_used':True,'expression_count':len(x),'independent_scenes':2,'valid_receivers_per_expression':(~mask).sum(1).tolist(),'controls':controls,'full_suffix_cache_available':False,'actual_task_masks_replayed':False,'native_targets_in_this_cache':False,'scientific_diagnosis_passed':False,'new_training':0,'cuda_initialized':False}))
'''
result=remote('server-4',program,conda=True,timeout=150)
save('cached_scale_cpu_result.json',result)
advance([OUT/'cached_scale_cpu.py',OUT/'cached_scale_cpu_result.json'],gate_result='Real trained M95 prefix source/deletion/permutation controls measured on CPU;actual mask/target suffix is not stored in this prefix. All original numeric failures retained. Scientific task diagnosis remains pending.')
print(json.dumps(result,ensure_ascii=True,indent=2))
