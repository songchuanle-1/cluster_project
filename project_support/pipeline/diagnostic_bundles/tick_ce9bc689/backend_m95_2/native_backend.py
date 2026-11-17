"""Read chosen sparse algorithm without modifying tuner or backend settings."""
import argparse
import hashlib
from pathlib import Path
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,sha,MANIFEST,STAGE,fingerprint

p=argparse.ArgumentParser()
p.add_argument('--lease',required=True)
a=p.parse_args()
r={'passed':False,'native_forwards':0,'native_backwards':0,'operator_forwards':0,
   'operator_vjps':0,'zero_vjps':0,'optimizer_steps':0,'scheduler_steps':0,'production_modified':False}
def order(x):return np.lexsort(tuple(x[:,i] for i in reversed(range(x.shape[1]))))
try:
    r['before']=acquire(a.lease)
    torch,gorilla,cfg,model,meta=setup()
    model.train()
    import spconv.pytorch as spconv
    from spconv import constants
    from spconv.algo import CONV_CPP
    from spconv.pytorch.cppcore import _TORCH_DTYPE_TO_TV,get_arch
    source=MANIFEST['control_source']
    assert sha(source['path'])==source['sha256']
    data=np.load(source['path'],allow_pickle=False)
    layer=model.unet.conv[2]
    r['weight_sha256']=fingerprint(torch,layer.state_dict())
    assert r['weight_sha256']==source['weight_sha256']
    flags=[p.requires_grad for p in layer.parameters()]
    r['configuration']={k:str(getattr(constants,k)) for k in ('SPCONV_CPP_GEMM','SPCONV_ALLOW_TF32','SPCONV_USE_DIRECT_TABLE','SPCONV_DO_SORT')}
    r['configuration'].update(layer_algo=str(layer.algo),layer_fp32_accum=str(layer.fp32_accum),
        matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32,arch=list(get_arch()))
    dtype=_TORCH_DTYPE_TO_TV[torch.float32]
    def query():
        result,found=CONV_CPP.get_tuned_algo(0,dtype,dtype,dtype,layer.out_channels,layer.in_channels,get_arch())
        return {'found':found,'descriptor':repr(result.algo_desp) if found else None,
            'fields':{n:str(getattr(result,n)) for n in ('split_k_slices','mask_width','arch') if found and hasattr(result,n)}}
    r['cache_before']=query()
    permutation=order(data['yi'])
    coordinates=data['yi'][permutation]
    cotangent=data['gy'][permutation]
    records=[]
    arrays={}
    for i in range(2):
        x=torch.from_numpy(data['xf'].copy()).cuda().requires_grad_(True)
        indices=torch.from_numpy(data['xi'].copy()).cuda()
        sparse=spconv.SparseConvTensor(x,indices,source['spatial_shape'],source['batch_size'])
        y=layer(sparse)
        r['operator_forwards']+=1
        yi=y.indices.detach().cpu().numpy()
        sort=order(yi)
        assert np.array_equal(yi[sort],coordinates)
        g=torch.from_numpy(cotangent[np.argsort(sort)].copy()).to(y.features)
        gs=torch.autograd.grad(y.features,(x,layer.weight),grad_outputs=g,retain_graph=i==1)
        r['operator_vjps']+=1
        assert all(bool(torch.isfinite(v).all()) for v in gs)
        arrays[str(i)+'_yf']=y.features.detach().cpu().numpy().copy()[sort]
        arrays[str(i)+'_gx']=gs[0].detach().cpu().numpy().copy()
        arrays[str(i)+'_gw']=gs[1].detach().cpu().numpy().copy()
        records.append({'cache_after':query(),'output_sha256':hashlib.sha256(arrays[str(i)+'_yf'].tobytes()).hexdigest()})
        if i==1:
            zeros=torch.autograd.grad(y.features,(x,layer.weight),grad_outputs=torch.zeros_like(g))
            r['zero_vjps']+=1
            r['zero_cotangent_max']=[float(v.abs().max().cpu()) for v in zeros]
            assert all(v==0 for v in r['zero_cotangent_max'])
    assert [p.requires_grad for p in layer.parameters()]==flags
    assert fingerprint(torch,layer.state_dict())==r['weight_sha256']
    r['calls']=records
    r['within_process_forward_max_abs']=float(np.abs(arrays['0_yf'].astype(np.float64)-arrays['1_yf'].astype(np.float64)).max())
    np.savez_compressed(STAGE/'backend_arrays.npz',**arrays)
    verify()
    r.update(passed=True,after=observe(),scope='read-only selectedalgorithm observation,not causalityproof or efficacy')
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    try:save('native_backend_result.json',r)
    finally:release()
