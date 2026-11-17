"""CPU float64 conditional Jacobians, not production precision changes."""
import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
p=argparse.ArgumentParser()
p.add_argument('--root',required=True)
a=p.parse_args()
root=Path(a.root)
assert not torch.cuda.is_initialized()
torch.set_num_threads(1)
data=np.load(root/'rank_prefix.npz',allow_pickle=False)
def tensor(key):return torch.from_numpy(data[key].copy()).double()
points=tensor('points')
cotangents=tensor('native_cotangent')
mask=data['mask']
weights={n:tensor(n) for n in ('level_gate_weight','level_gate_bias','point_out_proj_weight','point_out_proj_bias','message_norm_weight','message_norm_bias')}
tokens=[tensor('tokens_'+str(i)) for i in range(3)]
eps=float(data['message_norm_eps'])
records=[]
def spectrum(jacobian,g):
    u,s,vh=torch.linalg.svd(jacobian,full_matrices=False)
    threshold=torch.finfo(torch.float64).eps*max(jacobian.shape)*float(s.max())
    rank=int((s>threshold).sum())
    gn=float(g.norm())
    fraction=None if gn==0 else float((u[:,:rank].T@g).square().sum()/g.square().sum())
    return {'rank':rank,'largest_singular_value':float(s.max()),'third_singular_value':float(s[2]),
        'rank_tolerance':threshold,'native_gradient_accessible_squared_fraction':fraction}
for b in range(points.shape[0]):
    valid=int((~mask[b]).sum())
    ids=[data['ids_'+str(level)+'_'+str(b)] for level in range(3)]
    mu=points[b].mean(0)
    for index in (0,valid//2,valid-1):
        path=[int(ids[0][index])]
        for level in (1,2):path.append(int(ids[level][path[-1]]))
        messages=torch.stack([tokens[level][b,path[level]] for level in range(3)])
        point=points[b,index]
        def output(mean,coarse):
            values=torch.stack((messages[0],messages[1],coarse))
            logits=F.linear(torch.cat((point,mean)),weights['level_gate_weight'],weights['level_gate_bias'])
            fused=(values*logits.softmax(-1).unsqueeze(-1)).sum(0)
            y=F.linear(fused,weights['point_out_proj_weight'],weights['point_out_proj_bias'])
            return F.layer_norm(y,(y.numel(),),weights['message_norm_weight'],weights['message_norm_bias'],eps)
        jmean=torch.autograd.functional.jacobian(lambda m:output(m,messages[2]),mu,vectorize=True)
        jown=torch.autograd.functional.jacobian(lambda c:output(mu,c),messages[2],vectorize=True)
        g=cotangents[b,index]
        mean=spectrum(jmean,g)
        own=spectrum(jown,g)
        assert mean['rank']<=2
        ranks=mean['rank']
        channels=g.numel()
        coordinate=torch.arange(channels,dtype=torch.float64)+.5
        basis=torch.stack([torch.cos(torch.pi*coordinate*k/channels)*(2./channels)**.5 for k in range(1,ranks+1)],dim=1) if ranks else torch.zeros(channels,0,dtype=torch.float64)
        negative=None if float(g.norm())==0 else float((basis.T@g).square().sum()/g.square().sum())
        records.append({'expression_index':b,'point_index':index,'cluster_path':path,
            'mean_context':mean,'own_coarse_token':own,'native_cotangent_norm':float(g.norm()),
            'rank_matched_fixed_DCT_accessible_squared_fraction':negative})
fractions=[r['mean_context']['native_gradient_accessible_squared_fraction'] for r in records if r['mean_context']['native_gradient_accessible_squared_fraction'] is not None]
ownfractions=[r['own_coarse_token']['native_gradient_accessible_squared_fraction'] for r in records if r['own_coarse_token']['native_gradient_accessible_squared_fraction'] is not None]
negativefractions=[r['rank_matched_fixed_DCT_accessible_squared_fraction'] for r in records if r['rank_matched_fixed_DCT_accessible_squared_fraction'] is not None]
result={'passed':True,'observed_at':datetime.now(timezone.utc).isoformat(),'expression_count':int(points.shape[0]),
    'scene_count':2,'fixed_readout_count':len(records),'cpu_jacobian_count':2*len(records),
    'records':records,'mean_context_ranks':sorted(set(r['mean_context']['rank'] for r in records)),
    'own_coarse_ranks':sorted(set(r['own_coarse_token']['rank'] for r in records)),
    'mean_accessible_squared_fraction_median':float(np.median(fractions)) if fractions else None,
    'own_coarse_accessible_squared_fraction_median':float(np.median(ownfractions)) if ownfractions else None,
    'rank_matched_fixed_DCT_squared_fraction_median':float(np.median(negativefractions)) if negativefractions else None,
    'zero_gradient_readouts':len(records)-len(fractions),'cuda_initialized':torch.cuda.is_initialized(),
    'claim':'conditional module rank only;not whole-network restriction,trained harm,novelty or scientific admission',
    'population_uncertainty':'UNKNOWN;only2scenes;not seedvariance or a populationCI'}
assert not torch.cuda.is_initialized()
with (root/'rank_math_result.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps({k:v for k,v in result.items() if k!='records'}))
