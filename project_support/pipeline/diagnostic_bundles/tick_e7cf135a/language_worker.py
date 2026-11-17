"""Isolate the actual final ILA language-side activation source."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import argparse
import copy
import logging
from native_runtime import acquire,release,setup,save,verify,observe,fingerprint,MANIFEST


def main(lease):
    result={'execution_completed':False,'scientific_admission':False,'new_training':0,'optimizer_steps':0,
        'native_loss_forwards':0,'ila_replay_calls':0,'batches':[],
        'scope':'Final ILA language-side multimodal activation pairing only; not pure language, the whole network, new routing, training or full-source admission.'}
    hooks=[]
    try:
        result['before']=acquire(lease)
        torch,gorilla,cfg,model,metadata=setup()
        from torch.utils.data import DataLoader,Subset
        from framework.dataset import build_dataset
        active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
        assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
        ila,decoder=active[0].ila,model.dec.decoder_layers[-1]
        dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('ila-source-diagnostic'))
        for scene in MANIFEST['cohort']:
            group=dataset.scene_inputs[scene['group_index']]
            assert group[0]['scene_id']==scene['scene_id']
            assert [{'object_id':str(row['object_id']),'ann_id':str(row['ann_id'])} for row in group]==scene['expression_ids']
        def clone(value):
            if torch.is_tensor(value):return value.detach().clone()
            if isinstance(value,dict):return {k:clone(v) for k,v in value.items()}
            if isinstance(value,(list,tuple)):return type(value)(clone(v) for v in value)
            return copy.deepcopy(value)
        def error(a,b):return float((a-b).abs().max().detach().cpu())
        def mean(value):return float(value.mean()) if value.numel() else None
        gorilla.set_random_seed(1999)
        loader=DataLoader(Subset(dataset,[scene['group_index'] for scene in MANIFEST['cohort']]),batch_size=2,
            shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
        for pair_index,batch in enumerate(loader):
            held={}
            def capture_input(owner,values,keywords):held.update(ila_args=clone(values),ila_kwargs=clone(keywords))
            def capture_output(owner,values,output):held['ila_output']=clone(output[0])
            def capture_decoder(owner,values,output):
                held.update(final_query=clone(output[0]),native_masks=clone(output[2]),native_indis=clone(output[3]),
                    final_features=clone(values[2]),padding=clone(values[3]))
            hooks=[ila.register_forward_pre_hook(capture_input,with_kwargs=True),ila.register_forward_hook(capture_output),
                decoder.register_forward_hook(capture_decoder)]
            with torch.no_grad():loss,_=model(copy.deepcopy(batch),mode='loss')
            result['native_loss_forwards']+=1
            for hook in hooks:hook.remove()
            hooks=[]
            args,kwargs=held['ila_args'],held['ila_kwargs']
            assert len(args)==4 and args[3] is None and not kwargs
            signature=fingerprint(torch,(args,kwargs,held['final_query'],held['padding']))
            point_signature=fingerprint(torch,args[1])
            source=args[0];B=source.shape[0]
            donor=torch.arange(B,device=source.device)
            offset=0
            for count in batch['scenes_len']:
                count=int(count);indices=torch.arange(offset,offset+count,device=source.device)
                donor[offset:offset+count]=indices.roll(1);offset+=count
            inverse=torch.argsort(donor)
            changed=list(clone(args));changed[0]=args[0][donor];changed[2]=args[2][donor]
            restored=list(clone(changed));restored[0]=changed[0][inverse];restored[2]=changed[2][inverse]
            with torch.no_grad():
                own=ila(*args,**kwargs)[0]
                swapped=ila(*changed,**kwargs)[0]
                undo=ila(*restored,**kwargs)[0]
                result['ila_replay_calls']+=3
                _,head_identity=decoder.prediction_head(held['final_query'],held['final_features'],held['padding'])
                _,own_masks=decoder.prediction_head(held['final_query'],own,held['padding'])
                _,swapped_masks=decoder.prediction_head(held['final_query'],swapped,held['padding'])
                _,undo_masks=decoder.prediction_head(held['final_query'],undo,held['padding'])
                controls={'native_ila_equals_final_inst_feats':error(held['ila_output'],held['final_features']),
                    'ila_own_replay':error(own,held['ila_output']),
                    'native_head_identity':error(head_identity,held['native_masks']),
                    'own_fixed_query_mask_identity':error(own_masks,held['native_masks']),
                    'cycle_inverse_source_identity':error(restored[0],args[0]),
                    'cycle_inverse_mask_identity':error(restored[2].float(),args[2].float()),
                    'cycle_inverse_output_identity':error(undo,own),
                    'cycle_inverse_readout_identity':error(undo_masks,own_masks)}
                record={'pair_index':pair_index,'native_loss':float(loss.cpu()),'controls':controls,
                    'captured_input_sha256':signature,'receiving_point_query_sha256':point_signature,'readouts':[]}
                result['batches'].append(record)
                assert max(controls.values())<=MANIFEST['tolerance'],'Native ILA/source/head identity failed'
                assert fingerprint(torch,changed[1])==point_signature
                selected=held['native_indis'].softmax(-1)[...,1].argmax(-1)
                # Labels are first accessed only after intervention and all controls.
                offset=0
                for local_scene,count in enumerate(batch['scenes_len']):
                    count=int(count);scene=MANIFEST['cohort'][pair_index*2+local_scene]
                    assert count==len(scene['expression_ids'])
                    for local_index in range(count):
                        b=offset+local_index;other=int(donor[b]);other_local=other-offset
                        assert offset<=other<offset+count
                        target=torch.as_tensor(batch['gt_spmasks'][b],device=source.device).reshape(-1).float()
                        n=len(target);foreground=target>.5;query=int(selected[b])
                        native_logits=held['native_masks'][b,query,:n]
                        changed_logits=swapped_masks[b,query,:n]
                        delta=(changed_logits.sigmoid()-target).abs()-(native_logits.sigmoid()-target).abs()
                        feature_difference=(swapped[b,:n]-own[b,:n]).abs()
                        record['readouts'].append({'scene_id':scene['scene_id'],
                            'object_id':scene['expression_ids'][local_index]['object_id'],'ann_id':scene['expression_ids'][local_index]['ann_id'],
                            'donor_object_id':scene['expression_ids'][other_local]['object_id'],'donor_ann_id':scene['expression_ids'][other_local]['ann_id'],
                            'same_target_annotation':scene['expression_ids'][local_index]['object_id']==scene['expression_ids'][other_local]['object_id'],
                            'donor_selection_used_labels':False,'supports':n,'foreground_supports':int(foreground.sum()),
                            'native_language_valid_tokens':int((~args[2][b]).sum()),'donor_language_valid_tokens':int((~changed[2][b]).sum()),
                            'frozen_native_query':query,'inst_feats_max_abs':float(feature_difference.max()),
                            'changed_receivers_above_tolerance':int((feature_difference.max(-1)[0]>1e-6).sum()),
                            'selected_mask_logit_max_abs':error(changed_logits,native_logits),
                            'native_probability_mae':float((native_logits.sigmoid()-target).abs().mean()),
                            'all_mae_delta':float(delta.mean()),'foreground_mae_delta':mean(delta[foreground]),
                            'other_mae_delta':mean(delta[~foreground])})
                    offset+=count
                assert fingerprint(torch,(args,kwargs,held['final_query'],held['padding']))==signature
                record['captured_inputs_unchanged']=True
            del held,batch,loss,own,swapped,undo,own_masks,swapped_masks,undo_masks
            torch.cuda.empty_cache()
        verify()
        result.update(execution_completed=True,after=observe(),summary={
            'distinct_scenes':len(MANIFEST['cohort']),'expressions':sum(len(b['readouts']) for b in result['batches']),
            'all_identity_controls_passed':True,'full_source_numeric_admission':False,'trained_efficacy':'UNKNOWN'})
    except BaseException as error_value:
        result.update(error_type=type(error_value).__name__,error=str(error_value));raise
    finally:
        for hook in hooks:hook.remove()
        try:save('native_ila_result.json',result)
        finally:release()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True);main(parser.parse_args().lease)
