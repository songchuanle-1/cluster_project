"""Native M95 readback/target contracts,CPU only;not trained task evidence."""
from ops import *
guard(180)
path=CODE/'framework/model/Quard_model'/NAME/'hier_postprocess.py'
expected=tick.digest(path)
assert expected=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
program=r'''import os
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
import json,hashlib,sys,importlib.util
from pathlib import Path
from datetime import datetime,timezone
import torch
torch.set_num_threads(1);torch.manual_seed(1999)
root=Path('/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b')
sys.path[:0]=[str(root),str(root/'framework/lib')]
source=root/'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()==EXPECTED
spec=importlib.util.spec_from_file_location('_m95_scale_contract_28fc',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
model=module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256,nhead=8,cluster_layer_nums=[256,64,8],per_layer_topk_list=[4,6,8],dropout=0.0).eval()
points=torch.randn(2,6,256)
mask=torch.tensor([[False]*6,[False]*4+[True]*2])
points[1,4:]=0
query=torch.randn(2,2,256)
ids=[[torch.tensor([0,0,1,1,2,2]),torch.tensor([0,1,1,2])],[torch.tensor([0,0,1]),torch.tensor([0,0,1])],[torch.tensor([0,0]),torch.tensor([0,0])]]
banks=[torch.randn(2,k,256) for k in (3,2,1)]
with torch.no_grad():
 baseline=model(points,query,mask,banks,[],ids)['point']
 alternate_query=model(points,query.flip(1)+1,mask,banks,[],ids)['point']
 refined=[value+model.cluster_ffn[i](model.cluster_ffn_norm[i](value)) for i,value in enumerate(banks)]
 composed=[]
 for b in range(2):
  cur=ids[0][b];levels=[cur]
  for scale in (1,2):cur=ids[scale][b][cur];levels.append(cur)
  composed.append(levels)
 messages=[]
 for scale in range(3):
  message=torch.zeros_like(points)
  for b in range(2):message[b,:len(composed[b][scale])]=refined[scale][b,composed[b][scale]]
  messages.append(message)
 weights=torch.softmax(model.level_gate(torch.cat([points,points.mean(1,keepdim=True).expand_as(points)],dim=-1)),dim=-1)
 def replay(active):
  stack=torch.stack([messages[i] if i in active else torch.zeros_like(messages[i]) for i in range(3)],dim=-1)
  value=model.point_out_proj(model.dropout((stack*weights.unsqueeze(-2)).sum(-1)))
  value=model.message_norm(value)
  return value.masked_fill(mask.unsqueeze(-1),0)
 rebuilt=replay((0,1,2))
 deltas={str(i):float((replay([j for j in range(3) if j!=i])-baseline).abs().max()) for i in range(3)}
 original_logits=torch.einsum('bqd,bnd->bqn',query,baseline)
 reconstructed_logits=torch.einsum('bqd,bnd->bqn',query,rebuilt)
 permutations=[torch.tensor([5,2,1,4,3,0]),torch.tensor([3,1,0,2,4,5])]
 perm_points=torch.stack([points[b,p] for b,p in enumerate(permutations)])
 perm_mask=torch.stack([mask[b,p] for b,p in enumerate(permutations)])
 perm_ids=[[ids[0][b][permutations[b][:len(ids[0][b])]] for b in range(2)],ids[1],ids[2]]
 perm_output=model(perm_points,query,perm_mask,banks,[],perm_ids)['point']
 expected_perm=torch.stack([baseline[b,p] for b,p in enumerate(permutations)])
 targets=[torch.tensor([True,False,True,True,False,False]),torch.tensor([True,False,True,False])]
 group_counts=[]
 for b,target in enumerate(targets):
  labels=ids[0][b];mixed=torch.zeros(len(target),dtype=torch.bool)
  for cell in labels.unique():
   chosen=labels==cell
   if target[chosen].any() and (~target[chosen]).any():mixed[chosen]=True
  group_counts.append({'valid':len(target),'mixed_fine_cell':int(mixed.sum()),'interior':int((~mixed).sum()),'positive':int(target.sum())})
 identity=float((baseline-rebuilt).abs().max());query_control=float((baseline-alternate_query).abs().max())
 permutation=float((perm_output-expected_perm).abs().max());mask_error=float(baseline[mask].abs().max())
 logits_error=float((original_logits-reconstructed_logits).abs().max())
 numeric_contract_pass=max(identity,query_control,permutation,mask_error,logits_error)<=1e-6
 assert all(value>0 for value in deltas.values())
 assert group_counts==[{'valid':6,'mixed_fine_cell':2,'interior':4,'positive':3},{'valid':4,'mixed_fine_cell':2,'interior':2,'positive':2}]
 assert not torch.cuda.is_initialized()
print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),'source_path':str(source),'source_sha256':EXPECTED,'identity_max_error':identity,'same_query_readout_reconstruction_max_error':logits_error,'query_independence_max_error':query_control,'receiver_permutation_max_error':permutation,'padded_output_max_abs':mask_error,'per_scale_deletion_activity_max_abs':deltas,'fixed_fixture_target_counts':group_counts,'bias_retained_empty_scale_message_max_abs':float(replay(()).abs().max()),'tolerance':1e-6,'contracts_passed':numeric_contract_pass,'trained_weights_used':False,'native_task_masks_tested':False,'synthetic_fixture_only':True,'cuda_initialized':torch.cuda.is_initialized(),'new_training':0,'scientific_diagnosis_passed':False}))
'''
result=remote('server-4','EXPECTED='+repr(expected)+'\n'+program,conda=True,timeout=150)
save('native_scale_cpu_measured.json',result)
advance([OUT/'native_scale_cpu_measured.json',OUT/'measure_native_scale_cpu.py'],stage='validation',gate_result=('CPU source contracts measured;numeric tests pass at unchanged1e-6,synthetic only,not task diagnosis' if result['contracts_passed'] else 'CPU numeric control FAILED unchanged1e-6;preserve exact errors and investigate precision versus indexing before any task conclusion'),next_action='Bind frozen M95 TRAIN scenes/checkpoint/native full suffix replay and execute paired scale-deletion task readout when a live authorized exclusive GPU slot is available. Keep query and original target indexing exact;do not train a new variant.')
print(json.dumps(result,ensure_ascii=True,indent=2))
