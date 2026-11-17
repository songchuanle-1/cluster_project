"""Fixed M95 sibling-transport diagnostic; predictions never select protocol."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import argparse
import copy
import importlib
import logging
from native_runtime import acquire,release,setup,save,verify,observe,fingerprint,MANIFEST,NAME


def main(lease):
    result={'execution_completed':False,'scientific_admission':False,'new_training':0,'optimizer_steps':0,'native_loss_forwards':0,'batches':[]}
    bank=attention=None
    original_build=original_gather=None
    hooks=[]
    try:
        result['before']=acquire(lease)
        torch,gorilla,cfg,model,metadata=setup()
        from transport import transport,primitive_tests
        result['primitive']=primitive_tests('cuda')
        assert result['primitive']['passed'],'Primitive invariants failed; no native efficacy interpretation'
        from torch.utils.data import DataLoader,Subset
        from framework.dataset import build_dataset
        module=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
        bank,attention=model.dec.cluster_bank,model.dec.cluster_att
        original_build,original_gather=bank.build_cluster_feats,attention._cluster_to_points
        active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
        assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
        encoder,decoder=active[0],model.dec.decoder_layers[-1]
        dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('sibling-transport'))
        for scene in MANIFEST['cohort']:
            group=dataset.scene_inputs[scene['group_index']]
            assert group[0]['scene_id']==scene['scene_id']
            assert [{'object_id':str(row['object_id']),'ann_id':str(row['ann_id'])} for row in group]==scene['expression_ids']

        def clone(value):
            if torch.is_tensor(value):return value.detach().clone()
            if isinstance(value,dict):return {key:clone(item) for key,item in value.items()}
            if isinstance(value,(list,tuple)):return type(value)(clone(item) for item in value)
            return copy.deepcopy(value)
        def error(left,right):return float((left-right).abs().max().detach().cpu())
        def average(value):return float(value.mean()) if value.numel() else None

        gorilla.set_random_seed(1999)
        loader=DataLoader(Subset(dataset,[scene['group_index'] for scene in MANIFEST['cohort']]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
        for pair_index,batch in enumerate(loader):
            held={}
            def capture_build(*values):
                output=original_build(*values);held['raw_banks']=clone(output);return output
            def capture_gather(*values):
                output=original_gather(*values);held['gather_args'],held['gather_output']=clone(values),clone(output);return output
            def capture_encoder_input(owner,values,keywords):held.update(encoder_args=clone(values),encoder_kwargs=clone(keywords))
            def capture_encoder_output(owner,values,output):held['encoder_output']=clone(output)
            def capture_decoder(owner,values,output):
                held.update(final_query=clone(output[0]),native_masks=clone(output[2]),native_indis=clone(output[3]),final_features=clone(values[2]),padding=clone(values[3]))
            bank.build_cluster_feats,attention._cluster_to_points=capture_build,capture_gather
            hooks=[encoder.register_forward_pre_hook(capture_encoder_input,with_kwargs=True),encoder.register_forward_hook(capture_encoder_output),decoder.register_forward_hook(capture_decoder)]
            with torch.no_grad():loss,_=model(copy.deepcopy(batch),mode='loss')
            result['native_loss_forwards']+=1
            for hook in hooks:hook.remove()
            hooks=[]
            bank.build_cluster_feats=lambda *values:held['raw_banks']
            attention._cluster_to_points=original_gather
            features,refined,identifiers,padding=held['gather_args']
            signature=fingerprint(torch,(held['encoder_args'],held['raw_banks'],held['gather_args']))
            B,width,channels=features.shape
            def execute(changed):
                attention._cluster_to_points=lambda f,r,i,p:original_gather(f,changed,i,p)
                module.reset_orth_accum()
                output=encoder(*held['encoder_args'],**held['encoder_kwargs'])
                _,masks=decoder.prediction_head(held['final_query'],output[1],held['padding'])
                return output,masks
            with torch.no_grad():
                _,head=decoder.prediction_head(held['final_query'],held['final_features'],held['padding'])
                identity,identity_masks=execute(refined)
                controls={'readback_identity':error(original_gather(*held['gather_args']),held['gather_output']),
                    'head_identity':error(head,held['native_masks']),'encoder_identity':error(identity[1],held['final_features']),
                    'fixed_query_identity':error(identity_masks,held['native_masks'])}
                record={'pair_index':pair_index,'native_loss':float(loss.cpu()),'controls':controls,'operator':[],'readouts':[]}
                result['batches'].append(record)
                assert max(controls.values())<=1e-6,'Native frozen identity failed'
                arms={label:refined[0].clone() for label in ('content','wrong_cycle','wrong_equal_mass')}
                counts_by_b=[]
                for b in range(B):
                    parent=identifiers[1][b].long()
                    K=parent.numel()
                    ids=identifiers[0][b].long()
                    counts=torch.bincount(ids,minlength=K)
                    assert len(counts)==K and bool((counts>0).all())
                    counts_by_b.append(counts)
                    native=refined[0][b,:K]
                    content,groups=transport(native,parent,counts,matrices=True)
                    arms['content'][b,:K]=content
                    arms['wrong_cycle'][b,:K]=transport(native,parent,counts,True)
                    arms['wrong_equal_mass'][b,:K]=transport(native,parent,counts,'equal_mass')
                    stationary_error=mean_error=0.
                    mobility=[];group_sizes=[];moved=torch.zeros(K,device=features.device,dtype=torch.bool)
                    strict_conjugacy=0.
                    for g in groups:
                        idx,pi,p=g['indices'],g['pi'],g['p']
                        stationary_error=max(stationary_error,float(((pi[None,:,None]*p).sum(1)-pi).abs().max()))
                        before=(g['before'].double()*counts[idx].double()[None,:,None]).sum(1)/counts[idx].sum()
                        after=(g['after'].double()*counts[idx].double()[None,:,None]).sum(1)/counts[idx].sum()
                        mean_error=max(mean_error,float((before-after).abs().max()))
                        mobility.extend((1-p.diagonal(dim1=1,dim2=2)).flatten().cpu().tolist())
                        group_sizes.append(len(idx))
                        donor=torch.arange(len(idx),device=features.device)
                        for size in counts[idx].unique(sorted=True):
                            positions=torch.nonzero(counts[idx]==size,as_tuple=False).flatten()
                            donor[positions]=positions.roll(1)
                        moved[idx]=donor!=torch.arange(len(idx),device=features.device)
                        _,wrong_groups=transport(native[idx],torch.zeros(len(idx),device=features.device,dtype=torch.long),counts[idx],'equal_mass',matrices=True)
                        strict_conjugacy=max(strict_conjugacy,error(wrong_groups[0]['p'],p[:,donor][:,:,donor]))
                    record['operator'].append({'expression':b,'fine_tokens':K,'superpoint_rows':len(ids),
                        'sibling_group_sizes':group_sizes,'sum_group_squared':sum(k*k for k in group_sizes),
                        'stationarity_error':stationary_error,'weighted_fine_mean_error':mean_error,
                        'strict_equal_mass_conjugacy_error':strict_conjugacy,
                        'offdiag_mean':sum(mobility)/len(mobility),'offdiag_max':max(mobility),
                        'strict_moved_tokens':int(moved.sum()),'strict_moved_superpoint_rows':int(counts[moved].sum()),
                        'fine_token_change':error(content,native),
                        'content_wrong_cycle_token_change':error(content,arms['wrong_cycle'][b,:K]),
                        'content_wrong_equal_mass_token_change':error(content,arms['wrong_equal_mass'][b,:K])})
                outputs={label:execute([changed,*refined[1:]]) for label,changed in arms.items()}
                selected=held['native_indis'].softmax(-1)[...,1].argmax(-1)
                offset=0
                for local_scene,scene_length in enumerate(batch['scenes_len']):
                    scene=MANIFEST['cohort'][pair_index*2+local_scene]
                    for local_expression in range(int(scene_length)):
                        b=offset+local_expression;ids=identifiers[0][b].long();parent=identifiers[1][b].long();n=len(ids)
                        target=torch.as_tensor(batch['gt_spmasks'][b],device=features.device).reshape(-1).float()
                        assert target.numel()==n
                        foreground=target>.5;other=~foreground
                        query=int(selected[b]);native_logits=held['native_masks'][b,query,:n]
                        native_error=(native_logits.sigmoid()-target).abs()
                        target_leaves=ids[foreground].unique()
                        target_parent_count=parent[target_leaves].unique().numel()
                        row={'scene_id':scene['scene_id'],'group_index':scene['group_index'],
                            **scene['expression_ids'][local_expression],'supports':n,'target_supports':int(foreground.sum()),
                            'target_fine_leaves':len(target_leaves),'target_middle_parents':target_parent_count,
                            'native_all_mae':float(native_error.mean()),'native_fg_mae':average(native_error[foreground]),
                            'native_other_mae':average(native_error[other]),'frozen_native_query':query,'arms':{}}
                        for label,(output,masks) in outputs.items():
                            logits=masks[b,query,:n];delta=(logits.sigmoid()-target).abs()-native_error
                            row['arms'][label]={'all_mae_delta':float(delta.mean()),'foreground_mae_delta':average(delta[foreground]),
                                'other_mae_delta':average(delta[other]),'inst_feats_max_abs':error(output[1][b,:n],held['final_features'][b,:n]),
                                'selected_mask_logit_max_abs':error(logits,native_logits)}
                        row['content_vs_wrong_cycle_mask_max_abs']=error(outputs['content'][1][b,query,:n],outputs['wrong_cycle'][1][b,query,:n])
                        row['content_vs_wrong_equal_mass_mask_max_abs']=error(outputs['content'][1][b,query,:n],outputs['wrong_equal_mass'][1][b,query,:n])
                        record['readouts'].append(row)
                    offset+=int(scene_length)
                assert fingerprint(torch,(held['encoder_args'],held['raw_banks'],held['gather_args']))==signature
                record.update(captured_inputs_unchanged=True,labels_readout_only=True)
            bank.build_cluster_feats,attention._cluster_to_points=original_build,original_gather
            module.reset_orth_accum()
            del held,outputs,arms,features,refined,batch,loss
            torch.cuda.empty_cache()
        verify()
        result.update(execution_completed=True,after=observe(),summary={'distinct_scenes':len(MANIFEST['cohort']),
            'expressions':sum(len(b['readouts']) for b in result['batches']),
            'native_backward_executed':False,'full_source_numerical_admission':False,'trained_efficacy':'UNKNOWN'})
    except BaseException as value:
        result.update(error_type=type(value).__name__,error=str(value))
        raise
    finally:
        for hook in hooks:hook.remove()
        if bank is not None and original_build is not None:bank.build_cluster_feats=original_build
        if attention is not None and original_gather is not None:attention._cluster_to_points=original_gather
        try:save('native_transport_result.json',result)
        finally:release()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True)
    main(parser.parse_args().lease)
