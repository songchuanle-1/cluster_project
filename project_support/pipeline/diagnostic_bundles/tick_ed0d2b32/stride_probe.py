"""Observe the actual native first strided convolution, without changing it."""
import hashlib
import numpy as np
from native_runtime import STAGE,save,fingerprint

held={}
arrays={}
handles=[]
def attach(torch,model):
    from spconv.algo import CONV_CPP
    from spconv.pytorch.cppcore import _TORCH_DTYPE_TO_TV,get_arch
    from spconv import constants
    layer=model.unet.conv[2]
    assert type(layer).__name__=='SparseConv3d' and layer.indice_key=='spconv1'
    dtype=_TORCH_DTYPE_TO_TV[layer.weight.dtype]
    held['configuration']={k:str(getattr(constants,k)) for k in ('ALL_WEIGHT_IS_KRSC','SPCONV_CPP_GEMM','SPCONV_ALLOW_TF32','SPCONV_USE_DIRECT_TABLE','SPCONV_DO_SORT')}
    held['configuration'].update(layer_algo=str(layer.algo),matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32)
    held['weight_sha256']=fingerprint(torch,layer.state_dict())
    arrays['weight']=layer.weight.detach().cpu().numpy().copy()
    def query():
        r,found=CONV_CPP.get_tuned_algo(0,dtype,dtype,dtype,layer.out_channels,layer.in_channels,get_arch())
        return {'found':found,'descriptor':repr(r.algo_desp) if found else None,'arch':list(get_arch())}
    def pre(module,args):
        x=args[0]
        assert layer.indice_key not in x.indice_dict
        held['cache_before']=query()
        held['input']=x.features
        x.features.retain_grad()
        arrays['input_features']=x.features.detach().cpu().numpy().copy()
        arrays['input_indices']=x.indices.detach().cpu().numpy().copy()
    def post(module,args,y):
        held['cache_after']=query()
        held['output']=y.features
        y.features.retain_grad()
        arrays['output_features']=y.features.detach().cpu().numpy().copy()
        arrays['output_indices']=y.indices.detach().cpu().numpy().copy()
        indice=y.indice_dict[layer.indice_key]
        held['indice_class']=type(indice).__name__
        assert held['indice_class']=='ImplicitGemmIndiceData'
        def collect(value,name):
            if torch.is_tensor(value):arrays[name]=value.detach().cpu().numpy().copy()
            elif isinstance(value,np.ndarray):arrays[name]=value.copy()
            elif isinstance(value,(tuple,list)):
                for i,item in enumerate(value):collect(item,name+'_'+str(i))
            else:raise TypeError(type(value).__name__)
        for name in ('indices','out_indices','pair_fwd','pair_bwd','pair_mask_fwd_splits','pair_mask_bwd_splits','mask_argsort_fwd_splits','mask_argsort_bwd_splits','masks'):
            collect(getattr(indice,name),'indice_'+name)
        held['indice_metadata']={name:str(getattr(indice,name)) for name in ('spatial_shape','out_spatial_shape','is_subm','algo','ksize','stride','dilation','padding')}
    handles.extend([layer.register_forward_pre_hook(pre),layer.register_forward_hook(post)])

def finish(torch,model):
    for h in handles:h.remove()
    handles.clear()
    arrays['native_output_cotangent']=held['output'].grad.detach().cpu().numpy().copy()
    arrays['native_input_total_gradient']=held['input'].grad.detach().cpu().numpy().copy()
    assert np.isfinite(arrays['native_output_cotangent']).all() and np.any(arrays['native_output_cotangent']!=0)
    assert fingerprint(torch,model.unet.conv[2].state_dict())==held['weight_sha256']
    destination=STAGE/'native_stride_arrays.npz'
    assert not destination.exists()
    np.savez_compressed(destination,**arrays)
    with destination.open('rb') as f:
        h=hashlib.sha256()
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    result={'passed':True,'cache_before':held['cache_before'],'cache_after':held['cache_after'],
        'configuration':held['configuration'],'weight_sha256':held['weight_sha256'],
        'indice_class':held['indice_class'],'indice_metadata':held['indice_metadata'],
        'raw_sha256':h.hexdigest(),'raw_shapes':{k:list(v.shape) for k,v in arrays.items()},
        'scope':'actual original native call,not isolated kernel selection or trained benefit'}
    save('native_stride_result.json',result)
    return result
