"""Coordinate-aware saved-input sparse-convolution forward/VJP controls."""
import argparse
import copy
import hashlib
import importlib
import logging
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,fingerprint,sha,MANIFEST,NAME,ROOT,STAGE

p=argparse.ArgumentParser()
p.add_argument('--lease',required=True)
a=p.parse_args()
r={'passed':False,'native_forwards':0,'native_backwards':0,'operator_forwards':0,
   'operator_vjps':0,'zero_vjps':0,'optimizer_steps':0,'scheduler_steps':0,'new_VAL':False,
   'production_modified':False,'training_loop_started':False}
held={}
handles=[]

def order(coords):
    return np.lexsort(tuple(coords[:,i] for i in reversed(range(coords.shape[1]))))

def stats(x,y):
    assert x.shape==y.shape and x.dtype==y.dtype
    d=np.abs(x.astype(np.float64)-y.astype(np.float64))
    return {'different':int(np.count_nonzero(x!=y)),'elements':int(x.size),
        'max_absolute':float(d.max(initial=0)),'mean_absolute':float(d.mean()) if d.size else 0.}

try:
    r['before']=acquire(a.lease)
    torch,gorilla,cfg,model,meta=setup()
    assert meta['epoch']==MANIFEST['expected_epoch']
    flags=[(p,p.requires_grad) for p in model.parameters()]
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    import spconv.pytorch as spconv
    hierarchy=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('sparse-saved-input'))
    cohort=MANIFEST['cohort'][:2]
    for s in cohort:
        group=dataset.scene_inputs[s['group_index']]
        assert group[0]['scene_id']==s['scene_id']
        assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==s['expression_ids']
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,
        shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    r['input_sha256']=fingerprint(torch,batch)
    layer=model.unet.conv[2]
    r['layer_class']=type(layer).__name__
    r['layer_weight_sha256']=fingerprint(torch,layer.state_dict())
    assert r['layer_class']=='SparseConv3d' and layer.indice_key=='spconv1'
    def pre(module,args):
        x=args[0]
        assert layer.indice_key not in x.indice_dict
        held.update(xf=x.features.detach().cpu().numpy().copy(),xi=x.indices.detach().cpu().numpy().copy(),
            spatial_shape=list(x.spatial_shape),batch_size=x.batch_size,input_requires_grad=x.features.requires_grad,
            original_indice_keys=list(x.indice_dict))
    def post(module,args,y):
        y.features.retain_grad()
        held.update(y=y.features,yf=y.features.detach().cpu().numpy().copy(),yi=y.indices.detach().cpu().numpy().copy())
    handles=[layer.register_forward_pre_hook(pre),layer.register_forward_hook(post)]
    model.train()
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    loss,components=model(copy.deepcopy(batch),mode='loss')
    r['native_forwards']+=1
    assert bool(torch.isfinite(loss))
    loss.backward()
    r['native_backwards']+=1
    held['gy']=held['y'].grad.detach().cpu().numpy().copy()
    assert np.isfinite(held['gy']).all() and np.any(held['gy']!=0)
    r['native_loss']=float(loss.detach().cpu())
    r['native_target_gradient_norms']={n:float(m.weight.grad.norm().cpu()) for n,m in
        [('level_gate',model.dec.cluster_att.level_gate),('point_out_proj',model.dec.cluster_att.point_out_proj)]}
    assert all(v>0 for v in r['native_target_gradient_norms'].values())
    assert cfg.train.grad_clip==0.1
    torch.nn.utils.clip_grad_norm_(model.parameters(),cfg.train.grad_clip)
    for h in handles:h.remove()
    handles=[]
    destination=STAGE/'control_bundle.npz'
    assert not destination.exists()
    np.savez_compressed(destination,**{k:held[k] for k in ('xf','xi','yf','yi','gy')})
    source=MANIFEST.get('control_source')
    control_path=destination if source is None else __import__('pathlib').Path(source['path'])
    if source is not None:assert sha(control_path)==source['sha256']
    control=np.load(control_path,allow_pickle=False)
    r['control_source_sha256']=sha(control_path)
    r['native_input_equals_control']=bool(np.array_equal(held['xf'],control['xf']) and np.array_equal(held['xi'],control['xi']))
    assert r['native_input_equals_control']
    base_order=order(control['yi'])
    canonical_coords=control['yi'][base_order]
    cotangent=control['gy'][base_order]
    assert len(np.unique(canonical_coords,axis=0))==len(canonical_coords)
    r['saved_output_reload_control']=stats(control['yf'][base_order],control['yf'].copy()[base_order])
    native_order=order(held['yi'])
    assert np.array_equal(held['yi'][native_order],canonical_coords)
    r['native_vs_saved_coordinate_row_order_equal']=bool(np.array_equal(held['yi'],control['yi']))
    r['native_vs_saved_aligned_features']=stats(held['yf'][native_order],control['yf'][base_order])
    operator=[]
    outputs=[]
    for repeat in range(2):
        x=torch.from_numpy(control['xf'].copy()).cuda().requires_grad_(held['input_requires_grad'])
        indices=torch.from_numpy(control['xi'].copy()).cuda()
        sparse=spconv.SparseConvTensor(x,indices,held['spatial_shape'],held['batch_size'])
        y=layer(sparse)
        r['operator_forwards']+=1
        yi=y.indices.detach().cpu().numpy().copy()
        permutation=order(yi)
        assert np.array_equal(yi[permutation],canonical_coords)
        inverse=np.argsort(permutation)
        g=torch.from_numpy(cotangent[inverse].copy()).to(y.features)
        assert bool(torch.isfinite(y.features).all())
        gx,gw=torch.autograd.grad(y.features,(x,layer.weight),grad_outputs=g,retain_graph=(repeat==1))
        r['operator_vjps']+=1
        record={'yf':y.features.detach().cpu().numpy().copy()[permutation],
            'yi':yi,'gx':gx.detach().cpu().numpy().copy(),'gw':gw.detach().cpu().numpy().copy()}
        outputs.append(record)
        operator.append({'repeat':repeat+1,'output_row_order_equal_saved':bool(np.array_equal(yi,control['yi'])),
            'aligned_vs_saved':stats(record['yf'],control['yf'][base_order]),
            'input_vjp_finite':bool(torch.isfinite(gx).all()),'weight_vjp_finite':bool(torch.isfinite(gw).all())})
        if repeat==1:
            zx,zw=torch.autograd.grad(y.features,(x,layer.weight),grad_outputs=torch.zeros_like(g))
            r['zero_vjps']+=1
            r['zero_cotangent_max']={'input':float(zx.abs().max().cpu()),'weight':float(zw.abs().max().cpu())}
            assert all(v==0 for v in r['zero_cotangent_max'].values())
    r['operator_calls']=operator
    r['within_process_pair']={k:stats(outputs[0][k],outputs[1][k]) for k in ('yf','gx','gw')}
    r['within_process_row_order_equal']=bool(np.array_equal(outputs[0]['yi'],outputs[1]['yi']))
    replay_path=STAGE/'operator_arrays.npz'
    assert not replay_path.exists()
    np.savez_compressed(replay_path,**{str(i)+'_'+k:v for i,o in enumerate(outputs) for k,v in o.items()})
    r['parameter_flags_preserved']=all(p.requires_grad==v for p,v in flags)
    assert r['parameter_flags_preserved']
    assert fingerprint(torch,layer.state_dict())==r['layer_weight_sha256']
    assert fingerprint(torch,batch)==r['input_sha256']
    r['native_input_metadata']={k:held[k] for k in ('spatial_shape','batch_size','input_requires_grad','original_indice_keys')}
    r['control_bundle_sha256']=sha(destination)
    r['operator_arrays_sha256']=sha(replay_path)
    hierarchy.reset_orth_accum()
    verify()
    r.update(passed=True,after=observe(),efficacy='UNKNOWN',kernel_implementation_cause='UNESTABLISHED',
        scope='two fixed-input originalSparseConv forwards/VJPs,one nativebackward;not trainingvariance or fullmodelmax')
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    for h in handles:h.remove()
    try:save('native_sparse_result.json',r)
    finally:release()
