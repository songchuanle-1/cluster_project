"""Native M95 scale diagnostics with fixed queries and no training updates."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
    TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import argparse
import copy
import importlib
import logging
from pathlib import Path
import numpy as np
from native_runtime import acquire,release,setup,save,verify,observe,fingerprint,MANIFEST,NAME


def main(lease):
    result={'execution_completed':False,'scientific_admission':False,'new_training':0,'optimizer_steps':0,
        'native_loss_forwards':0,'frozen_bank_encoder_calls':0,'batches':[],
        'scope':'Label-free output decomposition of existing frozen M95 scale interventions; no calibration model, full-source admission or trained efficacy.'}
    bank=attention=None
    original_build=original_gather=None
    hooks=[]
    try:
        result['before']=acquire(lease)
        torch,gorilla,cfg,model,metadata=setup()
        from torch.utils.data import DataLoader,Subset
        from framework.dataset import build_dataset
        module=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
        bank,attention=model.dec.cluster_bank,model.dec.cluster_att
        original_build,original_gather=bank.build_cluster_feats,attention._cluster_to_points
        active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
        assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
        encoder,decoder=active[0],model.dec.decoder_layers[-1]
        dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('native-scale-diagnostic'))
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
        def mean_or_none(values,weights=None):
            if weights is None:return float(values.mean()) if values.numel() else None
            return float((values*weights).sum()/weights.sum()) if float(weights.sum())>0 else None

        gorilla.set_random_seed(1999)
        loader=DataLoader(Subset(dataset,[scene['group_index'] for scene in MANIFEST['cohort']]),
            batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
        for pair_index,batch in enumerate(loader):
            held={}
            def capture_build(*values):
                output=original_build(*values);held['raw_banks']=clone(output);return output
            def capture_gather(*values):
                output=original_gather(*values)
                held['gather_args'],held['gather_output']=clone(values),clone(output)
                return output
            def capture_encoder_input(owner,values,keywords):
                held['encoder_args'],held['encoder_kwargs']=clone(values),clone(keywords)
            def capture_encoder_output(owner,values,output):held['encoder_output']=clone(output)
            def capture_decoder(owner,values,output):
                held['final_query'],held['native_masks'],held['native_indis']=clone(output[0]),clone(output[2]),clone(output[3])
                held['final_features'],held['padding']=clone(values[2]),clone(values[3])
            bank.build_cluster_feats,attention._cluster_to_points=capture_build,capture_gather
            hooks=[encoder.register_forward_pre_hook(capture_encoder_input,with_kwargs=True),
                encoder.register_forward_hook(capture_encoder_output),decoder.register_forward_hook(capture_decoder)]
            with torch.no_grad():loss,_=model(copy.deepcopy(batch),mode='loss')
            result['native_loss_forwards']+=1
            for hook in hooks:hook.remove()
            hooks=[]
            bank.build_cluster_feats=lambda *values:held['raw_banks']
            attention._cluster_to_points=original_gather
            features,refined,identifiers,padding=held['gather_args']
            positions=held['encoder_args'][5]
            signature=fingerprint(torch,(held['encoder_args'],held['raw_banks'],held['gather_args']))
            B,width,channels=features.shape
            assert len(refined)==3
            composed=[]
            for b in range(B):
                ids=identifiers[0][b].long().clamp(0,refined[0].shape[1]-1)
                levels=[ids]
                for level in range(1,3):
                    parent=identifiers[level][b].long().clamp(0,refined[level].shape[1]-1)
                    levels.append(parent.gather(0,levels[-1]))
                composed.append(levels)
            messages=[]
            for level in range(3):
                message=torch.zeros_like(features)
                for b in range(B):
                    ids=composed[b][level]
                    message[b,:len(ids)]=refined[level][b,ids]
                messages.append(message)
            with torch.no_grad():
                global_mean=features.mean(dim=1,keepdim=True).expand_as(features)
                weights=attention.level_gate(torch.cat((features,global_mean),dim=-1)).softmax(-1)
            def fuse(point_messages):
                stack=torch.stack(point_messages,dim=-1)
                fused=(stack*weights.unsqueeze(-2)).sum(-1)
                return attention.point_out_proj(attention.dropout(fused)).masked_fill(padding.unsqueeze(-1),0)
            def execute(point_messages):
                attention._cluster_to_points=lambda *values:fuse(point_messages)
                module.reset_orth_accum()
                output=encoder(*held['encoder_args'],**held['encoder_kwargs'])
                result['frozen_bank_encoder_calls']+=1
                _,masks=decoder.prediction_head(held['final_query'],output[1],held['padding'])
                return output,masks

            with torch.no_grad():
                reconstructed=fuse(messages)
                _,head_identity=decoder.prediction_head(held['final_query'],held['final_features'],held['padding'])
                identity,identity_masks=execute(messages)
                controls={'readback_replica_max_abs':error(reconstructed,held['gather_output']),
                    'native_head_identity_max_abs':error(head_identity,held['native_masks']),
                    'frozen_bank_encoder_identity_max_abs':error(identity[1],held['final_features']),
                    'fixed_query_identity_mask_max_abs':error(identity_masks,held['native_masks'])}
                record={'pair_index':pair_index,'native_loss':float(loss.cpu()),'controls':controls,
                    'control_tolerance':1e-6,'readouts':[],'correspondence_controls':[]}
                result['batches'].append(record)
                assert max(controls.values())<=MANIFEST['tolerance'],'Frozen native identity control failed; no intervention result is valid'
                permutations=[]
                for b in range(B):
                    n=len(composed[b][0]);xyz=positions[b,:n].cpu().numpy()
                    order=np.lexsort((xyz[:,2],xyz[:,1],xyz[:,0]))
                    donor=np.arange(width);donor[order]=np.roll(order,1)
                    permutations.append(torch.as_tensor(donor,device=features.device))
                arms={}
                for level,label in enumerate(('omit_fine','omit_middle','omit_coarse')):
                    changed=list(messages);changed[level]=torch.zeros_like(messages[level]);arms[label]=changed
                rotated=messages[2].clone()
                for b in range(B):
                    ids=composed[b][2];K=int(identifiers[2][b].max())+1
                    rotated[b,:len(ids)]=refined[2][b,:K].roll(1,dims=0)[ids]
                arms['rotate_coarse_tokens']=list(messages[:2])+[rotated]
                middle=torch.stack([messages[1][b,permutations[b]] for b in range(B)])
                coarse=torch.stack([messages[2][b,permutations[b]] for b in range(B)])
                arms['cycle_middle_messages']=[messages[0],middle,messages[2]]
                arms['cycle_coarse_messages']=[messages[0],messages[1],coarse]
                arms['cycle_middle_coarse_messages']=[messages[0],middle,coarse]
                arms={key:value for key,value in arms.items() if key in ('omit_middle','omit_coarse','cycle_middle_messages','cycle_coarse_messages')}
                for b in range(B):
                    n=len(composed[b][0]);inverse=torch.argsort(permutations[b])
                    record['correspondence_controls'].append({'expression':b,
                        'middle_multiset_inverse_error':error(middle[b,inverse],messages[1][b]),
                        'coarse_multiset_inverse_error':error(coarse[b,inverse],messages[2][b]),
                        'middle_changed_receivers':int((middle[b,:n]!=messages[1][b,:n]).any(-1).sum()),
                        'coarse_changed_receivers':int((coarse[b,:n]!=messages[2][b,:n]).any(-1).sum()),
                        'supports':n,'permutation_uses_labels':False})
                selected=held['native_indis'].softmax(-1)[...,1].argmax(-1)
                arm_outputs={label:execute(values) for label,values in arms.items()}
                decompositions={}
                for label,(output,masks) in arm_outputs.items():
                    decompositions[label]=[]
                    for b in range(B):
                        n=len(composed[b][0]);query=int(selected[b])
                        baseline_logits=held['native_masks'][b,query,:n]
                        intervention_logits=masks[b,query,:n]
                        delta=intervention_logits-baseline_logits
                        constant=delta.mean();residual=delta-constant
                        reconstructed_delta=constant+residual
                        reconstructed_logits=baseline_logits+reconstructed_delta
                        delta_error=error(reconstructed_delta,delta)
                        logits_error=error(reconstructed_logits,intervention_logits)
                        assert max(delta_error,logits_error)<=MANIFEST['tolerance'],'Constant/residual reconstruction failed'
                        energy=float(delta.square().sum())
                        decompositions[label].append({'constant':constant,'residual':residual,
                            'constant_logits':baseline_logits+constant,'residual_logits':baseline_logits+residual,
                            'reconstructed_logits':reconstructed_logits,
                            'stats':{'constant_logit_shift':float(constant),
                                'delta_max_abs':float(delta.abs().max()),'delta_rms':float(delta.square().mean().sqrt()),
                                'residual_max_abs':float(residual.abs().max()),'residual_rms':float(residual.square().mean().sqrt()),
                                'residual_mean_abs':float(residual.mean().abs()),
                                'constant_energy_fraction':float(constant.square()*n)/energy if energy else None,
                                'residual_energy_fraction':float(residual.square().sum())/energy if energy else None,
                                'delta_reconstruction_max_abs':delta_error,'logits_reconstruction_max_abs':logits_error,
                                'labels_used_for_decomposition':False}})
                scene_offset=0
                for local_scene,scene_length in enumerate(batch['scenes_len']):
                    scene=MANIFEST['cohort'][pair_index*2+local_scene]
                    assert int(scene_length)==len(scene['expression_ids'])
                    for local_expression in range(int(scene_length)):
                        b=scene_offset+local_expression;n=len(composed[b][0])
                        target=torch.as_tensor(batch['gt_spmasks'][b],device=features.device).reshape(-1).float()
                        assert target.numel()==n and bool(((target>=0)&(target<=1)).all())
                        foreground=target>.5;other=~foreground
                        contamination=[];purities=[]
                        for level in range(3):
                            ids=composed[b][level]
                            counts=torch.bincount(ids,minlength=refined[level].shape[1]).to(target.dtype)
                            sums=torch.zeros_like(counts);sums.index_add_(0,ids,target)
                            purity=sums/counts.clamp_min(1)
                            purities.append(purity[ids])
                            contamination.append(mean_or_none(1-purity[ids],foreground.float()))
                        impurity_weights=foreground.float()*(1-purities[2])
                        query=int(selected[b]);native_logits=held['native_masks'][b,query,:n]
                        native_probability=native_logits.sigmoid();native_error=(native_probability-target).abs()
                        row={'scene_id':scene['scene_id'],'group_index':scene['group_index'],
                            'object_id':scene['expression_ids'][local_expression]['object_id'],
                            'ann_id':scene['expression_ids'][local_expression]['ann_id'],
                            'supports':n,'target_supports':int(foreground.sum()),'other_supports':int(other.sum()),
                            'foreground_contamination_by_scale':contamination,
                            'coarse_impurity_foreground_weight':float(impurity_weights.sum()),
                            'frozen_native_query':query,
                            'native_mae':float(native_error.mean()),'arms':{}}
                        for label,(output,masks) in arm_outputs.items():
                            logits=masks[b,query,:n];probability=logits.sigmoid()
                            delta=(probability-target).abs()-native_error
                            decomposition=decompositions[label][b]
                            explained={}
                            for part in ('constant','residual','reconstructed'):
                                part_error=(decomposition[part+'_logits'].sigmoid()-target).abs()-native_error
                                explained[part]={'all_mae_delta':float(part_error.mean()),
                                    'foreground_mae_delta':mean_or_none(part_error[foreground]),
                                    'other_mae_delta':mean_or_none(part_error[other])}
                            row.setdefault('bias_arms',{})[label]={'decomposition':decomposition['stats'],'readouts':explained,
                                'nonlinear_all_mae_interaction':float(delta.mean())-explained['constant']['all_mae_delta']-explained['residual']['all_mae_delta']}
                            row['arms'][label]={'all_mae_delta':float(delta.mean()),
                                'foreground_mae_delta':mean_or_none(delta[foreground]),
                                'other_mae_delta':mean_or_none(delta[other]),
                                'impurity_weighted_foreground_mae_delta':mean_or_none(delta,impurity_weights),
                                'selected_mask_logit_max_abs':error(logits,native_logits),
                                'inst_feats_max_abs':error(output[1][b,:n],held['final_features'][b,:n])}
                        record['readouts'].append(row)
                    scene_offset+=int(scene_length)
                assert fingerprint(torch,(held['encoder_args'],held['raw_banks'],held['gather_args']))==signature
                record['captured_inputs_unchanged']=True
                record['all_labels_readout_only']=True
            bank.build_cluster_feats,attention._cluster_to_points=original_build,original_gather
            module.reset_orth_accum()
            del held,arm_outputs,arms,features,refined,messages,batch,loss
            torch.cuda.empty_cache()
        verify()
        result.update(execution_completed=True,after=observe(),
            summary={'distinct_scenes':len(MANIFEST['cohort']),
                'expressions':sum(len(batch['readouts']) for batch in result['batches']),
                'all_frozen_identity_controls_passed':all(max(batch['controls'].values())<=1e-6 for batch in result['batches']),
                'full_source_numeric_admission':False,'new_structural_model':False,
                'full_backward_executed':False,'trained_efficacy':'UNKNOWN'})
    except BaseException as error_value:
        result.update(error_type=type(error_value).__name__,error=str(error_value))
        raise
    finally:
        for hook in hooks:hook.remove()
        if bank is not None and original_build is not None:bank.build_cluster_feats=original_build
        if attention is not None and original_gather is not None:attention._cluster_to_points=original_gather
        try:save('native_constant_result.json',result)
        finally:release()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True)
    main(parser.parse_args().lease)
