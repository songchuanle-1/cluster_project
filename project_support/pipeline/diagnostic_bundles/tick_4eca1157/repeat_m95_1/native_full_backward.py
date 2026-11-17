"""One native train-mode backward/clip; never constructs or steps optimizer."""
import argparse
import copy
import importlib
import logging
import time
import hashlib
import random
import numpy as np
from types import MethodType
from native_runtime import acquire,release,verify,observe,setup,save,fingerprint,MANIFEST,NAME,ROOT,STAGE
from padding_contract import build

p=argparse.ArgumentParser()
p.add_argument('--lease',required=True)
p.add_argument('--condition',choices=['original','reference'],required=True)
a=p.parse_args()
r={'passed':False,'condition':a.condition,'native_forwards':0,'native_backwards':0,
   'full_model_training_backwards':0,'optimizer_steps':0,'scheduler_steps':0,'gather_calls':0,
   'production_modified':False,'training_loop_started':False,'new_VAL':False,
   'scope':'single frozenbatch native.train forward/backward/clip,not efficacy or alltrainingpeak'}
try:
    r['before']=acquire(a.lease)
    torch,gorilla,cfg,model,meta=setup()
    assert meta['epoch']==MANIFEST['expected_epoch']
    flags=[(p,p.requires_grad) for p in model.parameters()]
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    hierarchy=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('native-backward-smoke'))
    cohort=MANIFEST['cohort'][:2]
    for s in cohort:
        group=dataset.scene_inputs[s['group_index']]
        assert group[0]['scene_id']==s['scene_id']
        assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==s['expression_ids']
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,
        shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    before=fingerprint(torch,batch)
    cluster=model.dec.cluster_att
    original=cluster._cluster_to_points
    source=ROOT/'framework/model/Quard_model'/NAME/'hier_postprocess.py'
    _,reference,binding=build(source,MANIFEST['assets']['source_hashes']['hier_postprocess.py'],torch)
    reference=MethodType(reference,cluster)
    r['binding']=binding
    held={}
    def gather(*arguments,**keywords):
        r['gather_calls']+=1
        x=arguments[0]
        held['point']=x
        held['mask']=arguments[3].detach()
        if x.requires_grad:x.retain_grad()
        r['prefix_sha256']=fingerprint(torch,{'args':arguments,'kwargs':keywords})
        arrays={}
        def flatten(value,key):
            if torch.is_tensor(value):arrays[key]=value.detach().cpu().numpy()
            elif isinstance(value,(list,tuple)):
                for i,item in enumerate(value):flatten(item,key+'_'+str(i))
            elif isinstance(value,dict):
                for name,item in value.items():flatten(item,key+'_'+name)
            else:raise TypeError(type(value).__name__)
        flatten(arguments,'arg')
        flatten(keywords,'kw')
        destination=STAGE/'prefix_arrays.npz'
        assert not destination.exists()
        np.savez_compressed(destination,**arrays)
        cpu_rng=torch.get_rng_state().numpy().tobytes()
        cuda_rng=torch.cuda.get_rng_state().cpu().numpy().tobytes()
        numpy_rng=np.random.get_state()
        r['rng_sha256']={'torch_cpu':hashlib.sha256(cpu_rng).hexdigest(),
            'torch_cuda':hashlib.sha256(cuda_rng).hexdigest(),
            'numpy':hashlib.sha256(numpy_rng[1].tobytes()+repr((numpy_rng[0],*numpy_rng[2:])).encode()).hexdigest(),
            'python':hashlib.sha256(repr(random.getstate()).encode()).hexdigest()}
        r['prefix_arrays_file']=destination.name
        return (reference if a.condition=='reference' else original)(*arguments,**keywords)
    model.train()
    model.zero_grad(set_to_none=True)
    gorilla.set_random_seed(1999)
    torch.cuda.synchronize()
    r['baseline_allocated_bytes']=torch.cuda.memory_allocated()
    torch.cuda.reset_peak_memory_stats()
    started=time.perf_counter()
    try:
        cluster._cluster_to_points=gather
        loss,components=model(copy.deepcopy(batch),mode='loss')
        r['native_forwards']+=1
        r['loss']=float(loss.detach().cpu())
        assert bool(torch.isfinite(loss))
        assert r['gather_calls']==1
        loss.backward()
        r['native_backwards']+=1
        r['full_model_training_backwards']+=1
    finally:
        cluster._cluster_to_points=original
    torch.cuda.synchronize()
    r['forward_backward_elapsed_ms']=(time.perf_counter()-started)*1000
    assert fingerprint(torch,batch)==before
    gradients=[(name,p.grad) for name,p in model.named_parameters() if p.grad is not None]
    assert gradients
    finite=torch.stack([torch.isfinite(g).all() for name,g in gradients])
    norms=torch.stack([g.norm() for name,g in gradients])
    assert bool(finite.all())
    assert bool((norms>0).any())
    r['gradient_parameter_count']=len(gradients)
    r['nonzero_gradient_parameter_count']=int((norms>0).sum().cpu())
    r['trainable_parameter_tensor_count']=sum(p.requires_grad for p in model.parameters())
    r['trainable_missing_gradient_count']=sum(p.requires_grad and p.grad is None for p in model.parameters())
    r['trainable_missing_gradient_names']=[n for n,p in model.named_parameters() if p.requires_grad and p.grad is None]
    r['target_gradient_norms_before_clip']={}
    for name,module in [('level_gate',cluster.level_gate),('point_out_proj',cluster.point_out_proj)]:
        g=module.weight.grad
        assert g is not None and bool(torch.isfinite(g).all())
        norm=float(g.norm().detach().cpu())
        assert norm>0
        r['target_gradient_norms_before_clip'][name]=norm
    if cfg.train.grad_clip>0:
        clipped=torch.nn.utils.clip_grad_norm_(model.parameters(),cfg.train.grad_clip)
        r['native_gradient_clip_limit']=float(cfg.train.grad_clip)
        r['total_gradient_norm_before_clip']=float(clipped.detach().cpu())
    r['target_gradient_norms_after_clip']={name:float(module.weight.grad.norm().detach().cpu())
        for name,module in [('level_gate',cluster.level_gate),('point_out_proj',cluster.point_out_proj)]}
    point=held['point']
    mask=held['mask']
    r['point_feature_requires_grad']=point.requires_grad
    r['whole_point_feature_gradient']={'masked_max':float(point.grad[mask].abs().max().detach().cpu()),
        'valid_max':float(point.grad[~mask].abs().max().detach().cpu()),
        'scope':'all actual downstream paths,not isolatedgather partialderivative'} if point.grad is not None else None
    r['parameter_flags_preserved']=all(p.requires_grad==v for p,v in flags)
    assert r['parameter_flags_preserved']
    r.update(epoch=meta['epoch'],input_sha256=before,scene_ids=[s['scene_id'] for s in cohort],
        allocated_peak_bytes=torch.cuda.max_memory_allocated(),reserved_peak_bytes=torch.cuda.max_memory_reserved(),
        single_step_scope=True,full_training_max='UNKNOWN',efficacy='UNKNOWN',novelty='UNESTABLISHED')
    hierarchy.reset_orth_accum()
    verify()
    r.update(passed=True,after=observe())
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    try:save('native_full_backward_result.json',r)
    finally:release()
