"""Fixed saved-prefix source-interface null/active channel controls only."""
import argparse
from pathlib import Path
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,sha,MANIFEST,STAGE,fingerprint
p=argparse.ArgumentParser()
p.add_argument('--lease',required=True)
a=p.parse_args()
r={'passed':False,'native_forwards':0,'native_backwards':0,'source_interface_forwards':0,
   'optimizer_steps':0,'scheduler_steps':0,'new_VAL':False,'production_modified':False}
try:
    r['before']=acquire(a.lease)
    torch,gorilla,cfg,model,meta=setup()
    model.train()
    assert meta['epoch']==MANIFEST['expected_epoch']
    source=MANIFEST['prefix_source']
    assert sha(source['path'])==source['sha256']
    raw=np.load(source['path'],allow_pickle=False)
    def gpu(key):return torch.from_numpy(raw[key].copy()).cuda()
    x=gpu('points').requires_grad_(True)
    mask=gpu('mask')
    tokens=[gpu('tokens_'+str(i)).requires_grad_(True) for i in range(3)]
    ids=[[gpu('ids_'+str(level)+'_'+str(b)) for b in range(x.shape[0])] for level in range(3)]
    cluster=model.dec.cluster_att
    flags=[p.requires_grad for p in cluster.parameters()]
    assert cluster.dropout.p==0
    def call(points,ts):
        y=cluster.message_norm(cluster._cluster_to_points(points,ts,ids,mask)).masked_fill(mask.unsqueeze(-1),0)
        r['source_interface_forwards']+=1
        return y
    base=call(x,tokens)
    r['native_saved_prefix_reconstruction_max']=float((base.detach()-gpu('message')).abs().max().cpu())
    assert r['native_saved_prefix_reconstruction_max']<=1e-6
    weight=cluster.level_gate.weight.detach().cpu().double()[:,x.shape[-1]:]
    centered=weight-weight.mean(0,keepdim=True)
    u,s,vh=torch.linalg.svd(centered,full_matrices=False)
    rank=int((s>torch.finfo(torch.float64).eps*max(centered.shape)*s.max()).sum())
    assert rank<=2
    basis=vh[:rank]
    records=[]
    points_cpu=raw['points']
    for b in range(x.shape[0]):
        valid=int((~mask[b]).sum().cpu())
        coarse=ids[0][b].long()
        for level in (1,2):coarse=ids[level][b].long()[coarse]
        for index in (0,valid//2,valid-1):
            candidates=(coarse!=coarse[index]).nonzero().flatten()
            if not len(candidates):
                records.append({'expression':b,'point':index,'result':'UNKNOWN no remote coarsecluster'})
                continue
            remote=int(candidates[0].cpu())
            d=torch.from_numpy(points_cpu[b,remote].copy()).double()-torch.from_numpy(points_cpu[b,index].copy()).double()
            row=basis.T@(basis@d)
            null=d-row
            norm=torch.from_numpy(points_cpu[b,remote].copy()).double().norm()
            if min(float(row.norm()),float(null.norm()),float(norm))<=1e-12:
                records.append({'expression':b,'point':index,'result':'UNKNOWN degenerate direction'})
                continue
            row=row/row.norm()*norm
            null=null/null.norm()*norm
            null_residual=float((centered@null).abs().max())
            assert null_residual<=1e-12
            directions=[null.to(x),row.to(x)]
            changes=[]
            for direction in directions:
                changed=x.detach().clone().requires_grad_(True)
                changed=changed.clone()
                changed[b,remote]=changed[b,remote]+direction
                y=call(changed,tokens)
                changes.append((y[b,index]-base[b,index]).detach().cpu().double().numpy())
                del y,changed
            ts=[t.detach().clone().requires_grad_(True) for t in tokens]
            ts[-1]=ts[-1].clone()
            ts[-1][b,coarse[index]]=ts[-1][b,coarse[index]]+directions[0]
            y=call(x,ts)
            changes.append((y[b,index]-base[b,index]).detach().cpu().double().numpy())
            del y,ts
            g=raw['native_cotangent'][b,index].astype(np.float64)
            record={'expression':b,'point':index,'remote_point':remote,'direction_norm':float(norm),
                'float64_centered_weight_null_residual':null_residual,
                'conditions':{name:{'message_max_absolute_change':float(np.abs(delta).max()),
                    'message_l2_change':float(np.linalg.norm(delta)),
                    'native_cotangent_linear_surrogate_change':float(g@delta)}
                    for name,delta in zip(('remote_null','remote_row','own_coarse_null'),changes)}}
            assert record['conditions']['remote_null']['message_max_absolute_change']<=1e-6
            records.append(record)
    assert [p.requires_grad for p in cluster.parameters()]==flags
    assert all(p.grad is None for p in cluster.parameters())
    verify()
    r.update(passed=True,records=records,readouts=len(records),tested_readouts=sum('conditions'in v for v in records),
        centered_global_weight_rank=rank,parameter_flags_preserved=True,parameter_gradients_unaccumulated=True,
        scope='fixed conditional nativeinterface only;linear surrogate is NOT measured new taskloss/efficacy/novelty',after=observe())
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    try:save('native_channel_null_result.json',r)
    finally:release()
