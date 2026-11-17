"""One execution-flag/order probe, preserving original arithmetic/tolerances."""
import argparse
import copy
import gc
import importlib
import logging
from types import MethodType
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,fingerprint,MANIFEST,NAME,ROOT
from padding_contract import build

p = argparse.ArgumentParser()
p.add_argument('--lease',required=True)
a = p.parse_args()
r = {'passed':False,'native_forwards':0,'native_backwards':0,'native_interface_backwards':0,
     'full_model_training_backwards':0,'optimizer_steps':0,'suffix_replays':0,
     'production_modified':False,'scope':'native captured gather-interface gradients,not trainingadmission or efficacy'}
try:
    r['before'] = acquire(a.lease)
    torch,gorilla,cfg,model,meta = setup()
    parameter_flags=[(p,p.requires_grad) for p in model.parameters()]
    assert meta['epoch']==MANIFEST['expected_epoch']
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    hierarchy = importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    dataset = build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('padding-contract'))
    cohort = MANIFEST['cohort'][:2]
    for s in cohort:
        group = dataset.scene_inputs[s['group_index']]
        assert group[0]['scene_id']==s['scene_id']
        assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==s['expression_ids']
    gorilla.set_random_seed(1999)
    batch = next(iter(DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,
        shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    before = fingerprint(torch,batch)
    cluster = model.dec.cluster_att
    active = [x for x in model.dec.encoder_layers if x.use_cluster]
    assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
    original = cluster._cluster_to_points
    source = ROOT/'framework/model/Quard_model'/NAME/'hier_postprocess.py'
    compiled_original,compiled_reference,binding = build(source,MANIFEST['assets']['source_hashes']['hier_postprocess.py'],torch)
    source_original = MethodType(compiled_original,cluster)
    reference = MethodType(compiled_reference,cluster)
    r['binding'] = binding
    held = {}
    def clone(v):
        if torch.is_tensor(v): return v.detach().clone()
        if isinstance(v,list): return [clone(x) for x in v]
        if isinstance(v,tuple): return tuple(clone(x) for x in v)
        if isinstance(v,dict): return {k:clone(x) for k,x in v.items()}
        return v
    def error(x,y): return float((x-y).abs().max().detach().cpu())
    def gather(*arguments,**keywords):
        value = original(*arguments,**keywords)
        held.update(args=clone(arguments),kwargs=clone(keywords),gather=clone(value))
        return value
    def core(module,arguments,value): held.update(core=clone(arguments),message=clone(value['point']))
    def ila(module,arguments): held['ila']=clone(arguments)
    def dec(module,arguments,value): held.update(decoder=clone(arguments),decoder_output=clone(value))
    hooks = [cluster.register_forward_hook(core),active[0].ila.register_forward_pre_hook(ila),
             model.dec.decoder_layers[-1].register_forward_hook(dec)]
    gorilla.set_random_seed(1999)
    try:
        cluster._cluster_to_points=gather
        with torch.no_grad(): loss,components=model(copy.deepcopy(batch),mode='loss')
        r['native_forwards']+=1
        assert bool(torch.isfinite(loss))
    finally:
        cluster._cluster_to_points=original
        for h in hooks:h.remove()
    assert fingerprint(torch,batch)==before
    features,tokens,ids,mask=held['args']
    kw=held['kwargs']
    B,N,C=features.shape
    assert bool(mask.any()) and bool((~mask.any(1)).any())
    denominator=int((~mask).sum())*C
    def initial_replay(message,label):
        with torch.no_grad():
            iargs=list(clone(held['ila']))
            iargs[1]=held['core'][0]+torch.sigmoid(active[0].cluster_att_gate)*message
            f=active[0].ila(*iargs)[0]
            dargs=list(clone(held['decoder']))
            dargs[2]=f
            value=model.dec.decoder_layers[-1](*dargs)
            r['suffix_replays']+=1
        errors={str(i):error(value[i],held['decoder_output'][i]) for i in (2,3)}
        r.setdefault('execution_probes',[]).append({'context':label,'errors':errors})
        return errors
    with torch.no_grad():
        early_message=cluster.message_norm(original(*held['args'],**kw)).masked_fill(mask.unsqueeze(-1),0)
    early_original=initial_replay(early_message,'initial_flags_before_autograd')
    try:
        for parameter,flag in parameter_flags:parameter.requires_grad_(False)
        initial_replay(early_message,'all_flags_false_before_autograd')
    finally:
        for parameter,flag in parameter_flags:parameter.requires_grad_(flag)
    restored_early=initial_replay(early_message,'restored_initial_flags_before_autograd')
    def differentiated(function,t= tokens,k=kw):
        x=features.detach().clone().requires_grad_(True)
        y=function(x,t,ids,mask,**k)
        scalar=y.square().sum()/denominator
        gradient,=torch.autograd.grad(scalar,x)
        r['native_backwards']+=1
        r['native_interface_backwards']+=1
        assert bool(torch.isfinite(y).all()) and bool(torch.isfinite(gradient).all())
        return y.detach(),gradient.detach()
    base,old_grad=differentiated(original)
    changed,new_grad=differentiated(reference)
    zero_tokens=[torch.zeros_like(x) for x in tokens]
    zero_kw={k:torch.zeros_like(v) for k,v in kw.items()}
    zero,zero_grad=differentiated(reference,zero_tokens,zero_kw)
    with torch.no_grad():
        source_replay=source_original(*held['args'],**kw)
        no_padding=~mask.any(1)
        controls={'native_gather':error(base,held['gather']),'source_extract':error(base,source_replay),
            'no_padding_output':error(base[no_padding],changed[no_padding]),
            'no_padding_gradient':error(old_grad[no_padding],new_grad[no_padding]),
            'masked_reference_gradient':float(new_grad[mask].abs().max().cpu()),
            'zero_scale_gradient':float(zero_grad.abs().max().cpu())}
        valid_gradient=float(new_grad[~mask].abs().max().cpu())
        assert valid_gradient>0
        values=[]
        valid_mean=features.masked_fill(mask.unsqueeze(-1),0).sum(1,keepdim=True)/(~mask).sum(1).view(B,1,1)
        for label,fill in [('zero',torch.zeros_like(valid_mean)),('one',torch.ones_like(valid_mean)),('valid_mean',valid_mean)]:
            replacement=torch.where(mask.unsqueeze(-1),fill.expand_as(features),features)
            assert torch.equal(replacement[~mask],features[~mask])
            value=reference(replacement,tokens,ids,mask,**kw)
            e=error(changed,value)
            controls['masked_value_'+label]=e
            values.append({'case':label,'reference_invariance_error':e,'valid_features_bitwise_unchanged':True})
        base_message=cluster.message_norm(base).masked_fill(mask.unsqueeze(-1),0)
        ref_message=cluster.message_norm(changed).masked_fill(mask.unsqueeze(-1),0)
        controls['message_reconstruction']=error(base_message,held['message'])
        def suffix(message):
            iargs=list(clone(held['ila']))
            iargs[1]=held['core'][0]+torch.sigmoid(active[0].cluster_att_gate)*message
            f=active[0].ila(*iargs)[0]
            dargs=list(clone(held['decoder']))
            dargs[2]=f
            r['suffix_replays']+=1
            return model.dec.decoder_layers[-1](*dargs)
        normal,reference_out=suffix(base_message),suffix(ref_message)
        for index in (2,3):controls['native_suffix_'+str(index)]=error(normal[index],held['decoder_output'][index])
        for key,value in early_original.items():controls['before_grad_suffix_'+key]=value
        for key,value in restored_early.items():controls['restored_before_grad_suffix_'+key]=value
        r['controls']=controls
        r['parameter_flags_preserved']=all(p.requires_grad==flag for p,flag in parameter_flags)
        r['parameter_gradients_accumulated']=sum(p.grad is not None for p,flag in parameter_flags)
        assert r['parameter_flags_preserved'] and not r['parameter_gradients_accumulated']
        assert max(controls.values())<=1e-6,controls
        r.update(epoch=meta['epoch'],input_sha256=before,scene_ids=[s['scene_id'] for s in cohort],
            controls=controls,native_loss=float(loss.cpu()),masked_value_controls=values,
            original_masked_gradient_max=float(old_grad[mask].abs().max().cpu()),
            reference_valid_gradient_max=valid_gradient,
            reference_message_max_change=error(base_message,ref_message),
            reference_mask_logits_max_change=error(normal[2],reference_out[2]))
        save('native_interface_partial.json',r)
        del base,changed,zero,old_grad,new_grad,zero_grad,normal,reference_out,loss,components
        gc.collect()
        x=features[:1]
        t=[v[:1] for v in tokens]
        i=[[level[0]] for level in ids]
        m=mask[:1]
        k={key:value[:1] for key,value in kw.items()}
        resources={}
        for label,function in [('original',original),('reference',reference)]:
            observe()
            for _ in range(20):
                y=function(x,t,i,m,**k)
                del y
            torch.cuda.synchronize()
            gc.collect()
            torch.cuda.empty_cache()
            baseline=torch.cuda.memory_allocated()
            torch.cuda.reset_peak_memory_stats()
            start,end=torch.cuda.Event(enable_timing=True),torch.cuda.Event(enable_timing=True)
            samples=[]
            for _ in range(100):
                start.record()
                y=function(x,t,i,m,**k)
                end.record()
                end.synchronize()
                samples.append(float(start.elapsed_time(end)))
                del y
            resources[label]={'batch_size':1,'warmup':20,'repeats':100,'median_ms':float(np.median(samples)),
                'p90_ms':float(np.percentile(samples,90)),'samples_ms':samples,
                'allocated_peak_bytes':torch.cuda.max_memory_allocated(),
                'reserved_peak_bytes':torch.cuda.max_memory_reserved(),
                'baseline_allocated_bytes':baseline,'incremental_allocated_peak_bytes':torch.cuda.max_memory_allocated()-baseline,
                'scope':'gatherinterfaceonly;not fullmodel/wholetrainingresourcePASS'}
        r['resources']=resources
        hierarchy.reset_orth_accum()
    verify()
    r.update(passed=True,efficacy='UNKNOWN',generalization='UNKNOWN',full_training_memory='UNKNOWN',
             after=observe(),new_training=False,new_VAL=False)
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    try:save('native_contract_result.json',r)
    finally:release()
