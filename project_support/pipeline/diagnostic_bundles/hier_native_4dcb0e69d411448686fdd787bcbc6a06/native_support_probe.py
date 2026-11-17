"""Native-input support controls; CPU diagnostic, not an admitted implementation."""
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1')
ROOT=Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
CAPTURE=ROOT.parent/'pipeline/server3_fallback_abdff23d/native_capture.pt'
SOURCE=ROOT/'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort/hier_postprocess.py'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
assert subprocess.check_output(['hostname'],text=True,timeout=5).strip()=='sysu311-MS-7C59'
assert sha(CAPTURE)=='e4a7e63605bb60d9e9a543cd22ac2635a37627ee3db22d870122e1a254342e08'
assert sha(SOURCE)=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
import torch
torch.set_num_threads(1)
capture=torch.load(CAPTURE,map_location='cpu')
assert capture['preparation']['frozen_groups']==[0,60,101,124] and capture['optimizer_steps']==0
spec=importlib.util.spec_from_file_location('native_support_frozen_hierarchy',str(SOURCE))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def selections(leaf,leaves,p1,p2):
    middle=p1[leaves].unique(sorted=True)
    coarse=p2[middle].unique(sorted=True)
    own_mid=p1[leaf]
    own_coarse=p2[own_mid]
    return (leaves[p1[leaves]==own_mid],middle[(p2[middle]==own_coarse)&(middle!=own_mid)],coarse[coarse!=own_coarse])

def attend(q,key,uniform=False):
    if not len(key):return q*0
    if uniform:return key.mean(dim=0,keepdim=True).expand_as(q)
    qh=q.reshape(-1,8,32).transpose(0,1)
    kh=key.reshape(-1,8,32).transpose(0,1)
    probabilities=((qh@kh.transpose(-1,-2))/math.sqrt(32)).softmax(dim=-1)
    return (probabilities@kh).transpose(0,1).reshape_as(q)

def point_probe(q,banks,chosen):
    return [attend(q,bank.index_select(0,ids)) for bank,ids in zip(banks,chosen)]

def fused_readout(net,p,mask,refined,ids,uniform=False):
    raw=torch.zeros_like(p)
    raw_uniform=torch.zeros_like(p)
    weights=net.level_gate(torch.cat([p,p.mean(dim=1,keepdim=True).expand_as(p)],dim=-1)).softmax(dim=-1)
    summaries=[]
    for b in range(p.shape[0]):
        n=int((~mask[b]).sum())
        leaf_ids=ids[0][b].long()
        assert len(leaf_ids)==n
        leaves=leaf_ids.unique(sorted=True)
        p1,p2=ids[1][b].long(),ids[2][b].long()
        banks=[bank[b] for bank in refined]
        degree=[]
        coverage=True
        empty=[0,0,0]
        for leaf in leaves.tolist():
            support=selections(leaf,leaves,p1,p2)
            row=torch.nonzero(leaf_ids==leaf,as_tuple=False).flatten()
            q=p[b].index_select(0,row)
            hit=torch.zeros_like(leaves)
            for level,col in enumerate(support):
                empty[level]+=int(len(col)==0)*len(row)
                ancestors=leaves if level==0 else p1[leaves] if level==1 else p2[p1[leaves]]
                hit+=torch.isin(ancestors,col).to(hit.dtype)
                message=attend(q,banks[level].index_select(0,col))
                average=attend(q,banks[level].index_select(0,col),uniform=True)
                raw[b,row]+=message*weights[b,row,level:level+1]
                raw_uniform[b,row]+=average*weights[b,row,level:level+1]
            coverage=coverage and bool((hit==1).all())
            degree.extend([sum(len(c) for c in support)]*len(row))
        first_leaf=int(leaf_ids[0])
        chosen=selections(first_leaf,leaves,p1,p2)
        q=p[b,:1]
        own_top=int(p2[p1[first_leaf]])
        baseline=point_probe(q,banks,chosen)
        excluded=[bank.clone() for bank in banks]
        excluded[2][own_top,0]+=1.0
        excluded_out=point_probe(q,excluded,chosen)
        included=[bank.clone() for bank in banks]
        included[0][first_leaf,0]+=1.0
        included_out=point_probe(q,included,chosen)
        dense_errors=[]
        for level,bank in enumerate(banks):
            allowed=torch.zeros(len(bank),dtype=torch.bool)
            allowed[chosen[level]]=True
            if not allowed.any():dense=q*0
            else:
                qh=q.reshape(1,8,32).transpose(0,1)
                kh=bank.reshape(-1,8,32).transpose(0,1)
                score=(qh@kh.transpose(-1,-2))/math.sqrt(32)
                score=score.masked_fill(~allowed[None,None,:],-torch.inf)
                dense=(score.softmax(dim=-1)@kh).transpose(0,1).reshape_as(q)
            dense_errors.append((dense-baseline[level]).abs().max().item())
        summaries.append({'valid_points':n,'coverage_exact':coverage,'empty_support_point_counts':empty,
            'degree_min':min(degree),'degree_max':max(degree),'edges':sum(degree),
            'excluded_own_coarse_delta':max((a-c).abs().max().item() for a,c in zip(baseline,excluded_out)),
            'included_own_fine_delta':max((a-c).abs().max().item() for a,c in zip(baseline,included_out)),
            'first_point_dense_masked_comparison_max':max(dense_errors)})
    def project(value):
        value=net.point_out_proj(net.dropout(value)).masked_fill(mask.unsqueeze(-1),0)
        return net.message_norm(value).masked_fill(mask.unsqueeze(-1),0)
    return project(raw),project(raw_uniform),summaries

results=[]
with torch.no_grad():
    for record in capture['records']:
        if record['trial']!=0:continue
        p,q,mask,tokens,children,ids=record['cluster']['inputs']
        net=module.C2F_ClusterAttn_CTF_HCG_CSORT(d_model=256,nhead=8,
            cluster_layer_nums=[256,64,8],per_layer_topk_list=[32,16,8],dropout=0.0).eval()
        net.load_state_dict(record['cluster']['state'],strict=True)
        module.reset_orth_accum()
        ancestor=net(p,q,mask,tokens,children,ids)['point']
        module.get_orth_loss()
        refined=[cf+net.cluster_ffn[i](net.cluster_ffn_norm[i](cf)) for i,cf in enumerate(tokens)]
        content,uniform,rows=fused_readout(net,p,mask,refined,ids)
        repeated,uniform_repeat,_=fused_readout(net,p,mask,refined,ids)
        query=record['head']['normalized_query']
        content_local=torch.einsum('bqd,bnd->bqn',query,content)
        uniform_local=torch.einsum('bqd,bnd->bqn',query,uniform)
        ancestor_local=torch.einsum('bqd,bnd->bqn',query,ancestor)
        expanded=[scan for scan,count in zip(record['scan_ids'],record['scenes_len']) for _ in range(int(count))]
        assert len(expanded)==len(rows)==len(record['ann_ids'])
        for b,row in enumerate(rows):
            valid=~mask[b]
            row.update(scan_id=expanded[b],ann_id=int(record['ann_ids'][b]),
                content_vs_uniform_message_max=(content[b,valid]-uniform[b,valid]).abs().max().item(),
                uniform_vs_ancestor_message_max=(uniform[b,valid]-ancestor[b,valid]).abs().max().item(),
                content_vs_uniform_local_probe_max=(content_local[b,:,valid]-uniform_local[b,:,valid]).abs().max().item(),
                content_vs_ancestor_local_probe_max=(content_local[b,:,valid]-ancestor_local[b,:,valid]).abs().max().item())
        results.append({'pair':record['pair'],'expressions':rows,
            'content_repeat_max':(content-repeated).abs().max().item(),
            'uniform_repeat_max':(uniform-uniform_repeat).abs().max().item(),
            'padding_zero':bool((content[mask]==0).all()) and bool((uniform[mask]==0).all())})
rows=[row for batch in results for row in batch['expressions']]
assert len(rows)==16
assert all(row['coverage_exact'] and row['excluded_own_coarse_delta']==0 for row in rows)
assert all(batch['content_repeat_max']==batch['uniform_repeat_max']==0 and batch['padding_zero'] for batch in results)
assert not torch.cuda.is_initialized()
print('HIER_NATIVE_RESULT='+json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),
    'capture_sha256':sha(CAPTURE),'source_sha256':sha(SOURCE),'expressions':16,'scenes':4,
    'coverage_passed':sum(r['coverage_exact'] for r in rows),'excluded_controls_passed':sum(r['excluded_own_coarse_delta']==0 for r in rows),
    'included_path_changed':sum(r['included_own_fine_delta']>1e-6 for r in rows),
    'first_point_dense_strict1e6_failed':sum(r['first_point_dense_masked_comparison_max']>1e-6 for r in rows),
    'new_core_admitted':False,'old_failures_reclassified':False,'native_task_effect':'unknown',
    'cuda_initialized':False,'network_forwards_this_probe':0,'optimizer_steps':0,'batches':results,
    'scope':'Native-input module support/weight controls only; local query probe is not downstream final mask, trained efficacy, whole-model backward or resource admission.'}))
