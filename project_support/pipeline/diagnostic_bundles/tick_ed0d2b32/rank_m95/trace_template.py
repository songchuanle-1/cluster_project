"""Original native train backward with observational boundary tracing."""
import argparse
import copy
import hashlib
import importlib
import logging
import random
import time
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,fingerprint,MANIFEST,NAME,ROOT,STAGE

p=argparse.ArgumentParser()
p.add_argument('--lease',required=True)
a=p.parse_args()
r={'passed':False,'native_forwards':0,'native_backwards':0,'optimizer_steps':0,
   'scheduler_steps':0,'new_VAL':False,'production_modified':False,'training_loop_started':False,
   'scope':'instrumented ORIGINAL native.train fixedbatch,not efficacy'}
trace=[]
restores=[]
handles=[]
raw={}

def rng_hashes(torch):
    state=np.random.get_state()
    return {'torch_cpu':hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
        'torch_cuda':hashlib.sha256(torch.cuda.get_rng_state().cpu().numpy().tobytes()).hexdigest(),
        'numpy':hashlib.sha256(state[1].tobytes()+repr((state[0],*state[2:])).encode()).hexdigest(),
        'python':hashlib.sha256(repr(random.getstate()).encode()).hexdigest()}

try:
    r['before']=acquire(a.lease)
    torch,gorilla,cfg,model,meta=setup()
    assert meta['epoch']==MANIFEST['expected_epoch']
    flags=[(p,p.requires_grad) for p in model.parameters()]
    r['model_loaded_sha256']=fingerprint(torch,model.state_dict())
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    network=importlib.import_module('framework.model.Quard_model.'+NAME+'.network')
    hierarchy=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('prefix-localization'))
    cohort=MANIFEST['cohort'][:2]
    for scene in cohort:
        group=dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id']==scene['scene_id']
        assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,
        shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    r['input_sha256']=fingerprint(torch,batch)

    def record(label,phase,value,save_raw=False):
        arrays={}
        scalars={}
        def flatten(item,key):
            if torch.is_tensor(item):arrays[key]=item.detach().cpu().contiguous().numpy().copy()
            elif hasattr(item,'features') and hasattr(item,'indices'):
                flatten(item.features,key+'.features')
                flatten(item.indices,key+'.indices')
                scalars[key+'.sparse_shape']=str((item.spatial_shape,item.batch_size))
            elif isinstance(item,dict):
                for name in sorted(item):flatten(item[name],key+'.'+str(name))
            elif isinstance(item,(tuple,list)):
                for index,child in enumerate(item):flatten(child,key+'.'+str(index))
            else:scalars[key]=repr(item)
        flatten(value,'x')
        event={'sequence':len(trace),'label':label,'phase':phase,'scalars':scalars,'tensors':{}}
        for name,array in arrays.items():
            event['tensors'][name]={'sha256':hashlib.sha256(array.tobytes()).hexdigest(),
                'shape':list(array.shape),'dtype':str(array.dtype)}
            if save_raw:
                key=str(event['sequence'])+'__'+name
                raw[key]=array
                event['tensors'][name]['raw_key']=key
        trace.append(event)

    def wrap_method(obj,name,label,save_raw=False):
        original=getattr(obj,name)
        def wrapped(*values,**keywords):
            record(label,'pre',(values,keywords),save_raw)
            output=original(*values,**keywords)
            record(label,'post',output,save_raw)
            return output
        setattr(obj,name,wrapped)
        restores.append((obj,name,original))

    wrap_method(network.pointgroup_ops,'voxelization','voxelization',True)
    wrap_method(network,'scatter_mean','network.scatter_mean',True)
    wrap_method(model,'extract_feat','extract_feat')
    wrap_method(model,'expand_and_fps','expand_and_fps')
    wrap_method(model.dec.cluster_att,'_cluster_to_points','cluster_to_points',True)
    def pre_hook(label):
        def hook(module,values):record(label,'pre',values)
        return hook
    def post_hook(label):
        def hook(module,values,output):record(label,'post',output)
        return hook
    for name,module in model.named_modules():
        backbone=name.startswith(('input_conv','unet','output_layer'))
        leaf=not any(module.children())
        coarse=(name in ('text_encoder','dec','dec.input_proj','dec.lang_proj','dec.lang_norm','dec.cluster_att')
            or name.startswith('dec.encoder_layers.') and name.count('.')==2
            or name.startswith('dec.decoder_layers.') and name.count('.')==2)
        if backbone and leaf or coarse:
            handles.append(module.register_forward_pre_hook(pre_hook(name)))
            handles.append(module.register_forward_hook(post_hook(name)))
    model.train()
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    r['rng_before']=rng_hashes(torch)
    torch.cuda.reset_peak_memory_stats()
    start=time.perf_counter()
    loss,components=model(copy.deepcopy(batch),mode='loss')
    r['native_forwards']+=1
    assert bool(torch.isfinite(loss))
    r['loss']=float(loss.detach().cpu())
    r['rng_after_forward']=rng_hashes(torch)
    loss.backward()
    r['native_backwards']+=1
    gradients=[(n,p.grad) for n,p in model.named_parameters() if p.grad is not None]
    assert gradients and all(bool(torch.isfinite(g).all()) for n,g in gradients)
    r['target_gradient_norms']={name:float(module.weight.grad.norm().detach().cpu())
        for name,module in [('level_gate',model.dec.cluster_att.level_gate),('point_out_proj',model.dec.cluster_att.point_out_proj)]}
    assert all(value>0 for value in r['target_gradient_norms'].values())
    assert cfg.train.grad_clip==0.1
    r['gradient_norm_before_clip']=float(torch.nn.utils.clip_grad_norm_(model.parameters(),cfg.train.grad_clip).cpu())
    torch.cuda.synchronize()
    r['elapsed_ms']=(time.perf_counter()-start)*1000
    r['parameter_flags_preserved']=all(p.requires_grad==v for p,v in flags)
    assert r['parameter_flags_preserved']
    assert fingerprint(torch,batch)==r['input_sha256']
    r['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
    destination=STAGE/'trace_arrays.npz'
    assert not destination.exists()
    np.savez_compressed(destination,**raw)
    save('trace_events.json',{'events':trace,'trace_event_count':len(trace)})
    r['raw_array_count']=len(raw)
    r['trace_event_count']=len(trace)
    hierarchy.reset_orth_accum()
    verify()
    r.update(passed=True,after=observe())
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    for handle in handles:handle.remove()
    for obj,name,original in reversed(restores):setattr(obj,name,original)
    try:save('native_trace_result.json',r)
    finally:release()
