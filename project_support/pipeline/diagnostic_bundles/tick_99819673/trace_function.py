def trace(torch,gorilla,cfg,model,qualified,result):
    from torch.utils.data import DataLoader,Subset
    from framework.dataset import build_dataset
    hierarchy=importlib.import_module(qualified+'.hier_postprocess')
    encoder=[x for x in model.dec.encoder_layers if x.use_cluster][0]
    attention,bank=model.dec.cluster_att,model.dec.cluster_bank
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('rstr-numeric-localization'))
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[x['group_index'] for x in MANIFEST['cohort'][:2]]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    held={};phase=['native'];captures={}
    def clone(v):
        if torch.is_tensor(v):return v.detach().clone()
        if isinstance(v,dict):return {k:clone(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return type(v)(clone(x) for x in v)
        return copy.deepcopy(v)
    original_build,original_gather=bank.build_cluster_feats,attention._cluster_to_points
    def build(*values):
        output=original_build(*values);captures.setdefault(phase[0],{})['raw_banks']=clone(output);return output
    def gather(*values):
        output=original_gather(*values);captures.setdefault(phase[0],{}).update(refined=clone(values[1]),gather=clone(output));return output
    def before(owner,values,keywords):
        if phase[0]=='native':held.update(reference_args=values,reference_kwargs=keywords,args=clone(values),kwargs=clone(keywords))
    def after(owner,values,output):captures.setdefault(phase[0],{})['encoder']=clone(output)
    hooks=[encoder.register_forward_pre_hook(before,with_kwargs=True),encoder.register_forward_hook(after)]
    bank.build_cluster_feats,attention._cluster_to_points=build,gather
    try:
        with torch.no_grad():
            loss,_=model(copy.deepcopy(batch),mode='loss');result['native_loss_forwards']+=1
            ids,maps=clone(bank.cluster_ids_list),clone(bank.child_cluster_maps)
            signature=fingerprint(torch,(held['reference_args'],held['reference_kwargs']))
            for label in ('reference_replay1','reference_replay2','clone_replay1','clone_replay2'):
                phase[0]=label;bank.cluster_ids_list,bank.child_cluster_maps=clone(ids),clone(maps);hierarchy.reset_orth_accum()
                values=held['args'] if label.startswith('clone') else held['reference_args']
                keywords=held['kwargs'] if label.startswith('clone') else held['reference_kwargs']
                encoder(*values,**keywords);result['full_source_encoder_calls']+=1
            assert fingerprint(torch,(held['reference_args'],held['reference_kwargs']))==signature
    finally:
        for hook in hooks:hook.remove()
        bank.build_cluster_feats,attention._cluster_to_points=original_build,original_gather
    def error(a,b):return float((a-b).abs().max().cpu())
    result['trace']={}
    for label,data in captures.items():
        if label=='native':continue
        native=captures['native']
        result['trace'][label]={'raw_bank_errors':[error(a,b) for a,b in zip(data['raw_banks'],native['raw_banks'])],
            'refined_bank_errors':[error(a,b) for a,b in zip(data['refined'],native['refined'])],
            'gather_error':error(data['gather'],native['gather']),
            'encoder_errors':[error(a,b) for a,b in zip(data['encoder'],native['encoder'])]}
    result['input_layouts']={str(i):{'reference':{'stride':list(a.stride()),'offset':a.storage_offset(),'contiguous':a.is_contiguous()},
        'clone':{'stride':list(b.stride()),'offset':b.storage_offset(),'contiguous':b.is_contiguous()},'value_error':error(a,b)}
        for i,(a,b) in enumerate(zip(held['reference_args'],held['args'])) if torch.is_tensor(a)}
    verify();result.update(execution_completed=True,after=observe(),model_source_changed=False,optimizer_steps=0)
