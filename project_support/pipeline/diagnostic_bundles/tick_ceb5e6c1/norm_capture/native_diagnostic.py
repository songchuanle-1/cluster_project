"""Same-prefix trained FLE nonself-content diagnostic; no optimizer or resume."""
import argparse
import copy
import importlib
import logging
import numpy as np
from native_runtime import acquire,release,verify,observe,setup,save,fingerprint,MANIFEST,NAME,STAGE
from neighbor_content import padded_intervention

parser=argparse.ArgumentParser()
parser.add_argument('--lease',required=True)
args=parser.parse_args()
result={'passed':False,'native_forwards':0,'native_backwards':0,'optimizer_steps':0,'suffix_replays':0,'scenes':[],
    'scientific_status':'early_checkpoint_mechanistic_diagnostic_not_terminal_efficacy','new_model_revision':False}
try:
    result['before']=acquire(args.lease)
    torch,gorilla,cfg,model,meta=setup()
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    operator=importlib.import_module('framework.model.Quard_model.'+NAME+'.fine_exchange')
    hierarchy=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    get_iou=importlib.import_module('framework.model.Quard_model.'+NAME+'.loss').get_iou
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('fle-nonself'))
    cohort=MANIFEST['cohort']
    for row in cohort:
        group=dataset.scene_inputs[row['group_index']]
        assert group[0]['scene_id']==row['scene_id']
        assert [{'object_id':str(r['object_id']),'ann_id':str(r['ann_id'])} for r in group]==row['expression_ids']
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[r['group_index'] for r in cohort]),batch_size=1,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
    cluster=model.dec.cluster_att;fine=cluster.fine_exchange
    assert fine.k==32 and fine.heads==8
    def clone(value):
        if torch.is_tensor(value):return value.detach().clone()
        if isinstance(value,list):return [clone(v) for v in value]
        if isinstance(value,tuple):return tuple(clone(v) for v in value)
        if isinstance(value,dict):return {k:clone(v) for k,v in value.items()}
        return value
    def maximum(a,b):return float((a-b).abs().max().cpu())
    result['checkpoint_meta']={k:v for k,v in meta.items() if isinstance(v,(int,float,str,bool))}
    with torch.no_grad():
        for scene,batch in zip(cohort,loader):
            observe();before=fingerprint(torch,batch);held={}
            def core(module,arguments,keywords,value):held.update(core_args=clone(arguments),core_kwargs=clone(keywords),message=clone(value['point']))
            def ila(module,arguments):held['ila']=clone(arguments)
            def decoder(module,arguments,value):held.update(decoder=clone(arguments),decoder_output=clone(value))
            hooks=[cluster.register_forward_hook(core,with_kwargs=True),active[0].ila.register_forward_pre_hook(ila),model.dec.decoder_layers[-1].register_forward_hook(decoder)]
            gorilla.set_random_seed(1999)
            try:
                loss,components=model(copy.deepcopy(batch),mode='loss');result['native_forwards']+=1
                assert bool(torch.isfinite(loss));native_loss=float(loss.cpu())
            finally:
                for hook in hooks:hook.remove()
            assert fingerprint(torch,batch)==before
            arguments=held['core_args'];keywords=held['core_kwargs']
            normal=cluster(*arguments,**keywords)['point']
            normal2=cluster(*arguments,**keywords)['point']
            errors={'message_replay':maximum(normal,held['message']),'repeat':maximum(normal,normal2)}
            original=fine.forward;receipts=[]
            def controlled(identity):
                def replace(features,padding,positions,fine_ids):
                    expected=original(features,padding,positions,fine_ids)
                    decomposed,altered,rows=padded_intervention(features,padding,positions,fine_ids,operator.build_graph,identity=identity)
                    source_error=maximum(expected,decomposed)
                    assert source_error<=1e-6
                    attempt={'scene':scene['scene_id'],'identity':identity,'source_error':source_error,'rows':rows}
                    result.setdefault('control_attempts',[]).append(attempt)
                    if max(r['norm_max_error'] for r in rows)>1e-6:
                        from neighbor_content import decompose,permute_nonself
                        arrays={'features':features.detach().cpu().numpy(),'padding':padding.detach().cpu().numpy(),
                            'positions':positions.detach().cpu().numpy()}
                        for b,ids in enumerate(fine_ids):
                            n=len(ids);coordinates=positions[b,:n].detach().cpu().numpy();leaves=ids.detach().cpu().numpy()
                            parts=decompose(features[b,:n],operator.build_graph(coordinates,leaves))
                            replacement,receipt=permute_nonself(parts['nonself'],coordinates,leaves,identity=identity)
                            arrays['leaves_'+str(b)]=leaves
                            arrays['nonself_'+str(b)]=parts['nonself'].detach().cpu().numpy()
                            arrays['replacement_'+str(b)]=replacement.detach().cpu().numpy()
                            arrays['native_norm_'+str(b)]=parts['nonself'].reshape(n,8,32).norm(dim=-1).detach().cpu().numpy()
                            arrays['native_replacement_norm_'+str(b)]=replacement.reshape(n,8,32).norm(dim=-1).detach().cpu().numpy()
                        path=STAGE/'failed_norm_input.npz'
                        assert not path.exists()
                        np.savez_compressed(path,**arrays)
                        attempt['failure_capture']=path.name
                    assert max(r['norm_max_error'] for r in rows)<=1e-6
                    receipts.append({'identity':identity,'source_error':source_error,'rows':rows})
                    return altered
                try:
                    fine.forward=replace
                    return cluster(*arguments,**keywords)['point']
                finally:fine.forward=original
            identity_message=controlled(True);altered_message=controlled(False)
            errors['identity_message']=maximum(normal,identity_message)
            def suffix(message):
                ila_args=list(clone(held['ila']))
                ila_args[1]=arguments[0]+torch.sigmoid(active[0].cluster_att_gate)*message
                features=active[0].ila(*ila_args)[0]
                decoder_args=list(clone(held['decoder']));decoder_args[2]=features
                result['suffix_replays']+=1
                return model.dec.decoder_layers[-1](*decoder_args)
            normal_out=suffix(normal);identity_out=suffix(identity_message);altered_out=suffix(altered_message)
            for index in (2,3):
                errors['native_suffix_'+str(index)]=maximum(normal_out[index],held['decoder_output'][index])
                errors['identity_suffix_'+str(index)]=maximum(normal_out[index],identity_out[index])
            assert max(errors.values())<=1e-6,errors
            rows=[]
            # A one-scene batch preserves original global superpoint indexing.
            sp=batch['superpoints'].to(normal_out[2].device).long()
            for expression in range(len(batch['ann_ids'])):
                a=normal_out[2][expression];b=altered_out[2][expression]
                q=int(normal_out[3][expression].softmax(-1)[:,1].argmax())
                other=int(altered_out[3][expression].softmax(-1)[:,1].argmax())
                gt=batch['gt_pmasks'][expression].to(a.device).float()
                original_point=a[q][sp];fixed_point=b[q][sp];own_point=b[other][sp]
                rows.append({'ann_id':int(batch['ann_ids'][expression]),'normal_query':q,'intervention_query':other,
                    'normal_piou':float(get_iou(original_point,gt).cpu()),'fixed_query_piou':float(get_iou(fixed_point,gt).cpu()),
                    'own_query_piou':float(get_iou(own_point,gt).cpu()),
                    'normal_bce':float(torch.nn.functional.binary_cross_entropy_with_logits(original_point,gt).cpu()),
                    'fixed_query_bce':float(torch.nn.functional.binary_cross_entropy_with_logits(fixed_point,gt).cpu()),
                    'final_mask_max_change':maximum(a,b)})
            result['scenes'].append({'scene':scene['scene_id'],'group_index':scene['group_index'],'input_sha256':before,
                'native_loss':native_loss,'controls':errors,'interventions':receipts,'expressions':rows})
            hierarchy.reset_orth_accum()
            del held,normal,normal2,identity_message,altered_message,normal_out,identity_out,altered_out,loss,components
            torch.cuda.empty_cache()
    verify();result['after']=observe()
    assert len(result['scenes'])==8
    scene_deltas=np.array([np.mean([r['normal_piou']-r['fixed_query_piou'] for r in s['expressions']]) for s in result['scenes']])
    bootstrap=np.random.default_rng(1999).choice(scene_deltas,(10000,8),replace=True).mean(1)
    result.update(passed=True,scene_mean_normal_minus_intervention_piou=float(scene_deltas.mean()),
        scene_bootstrap_95ci=np.quantile(bootstrap,[.025,.975]).tolist(),uncertainty='eight TRAIN scenes only,not generalization or fullVAL',
        new_training_started=False,efficacy='unknown',material_novelty='unestablished')
except BaseException as error:
    result.update(error_type=type(error).__name__,error=str(error));raise
finally:
    save('native_diagnostic_result.json',result);release()
