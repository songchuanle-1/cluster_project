"""Conditional native fixed-query mask readout of recomputed row relabeling."""
import argparse
import copy
import logging
from native_runtime import acquire,release,setup,save,fingerprint,MANIFEST

parser=argparse.ArgumentParser()
parser.add_argument('--lease',required=True)
parser.add_argument('--pair',type=int,choices=range(2),required=True)
args=parser.parse_args()
result={'execution_completed':False,'controls_passed':False,'scientific_admission':False,
    'new_training':0,'native_backwards':0,'records':[],
    'scope':'Frozen native TRAIN prefix/query/targets;row relabeling recomputes original hierarchy only. Failed strict controls make task interpretation INCONCLUSIVE,not a trained repair or efficacy test.'}
hooks=[]
bank=None
original_build=None
try:
    result['before']=acquire(args.lease)
    torch,gorilla,cfg,model,meta=setup()
    assert meta['epoch']==16
    from torch.utils.data import DataLoader,Subset
    from framework.dataset import build_dataset
    model.eval()
    cohort=MANIFEST['cohort'][2*args.pair:2*args.pair+2]
    assert len(cohort)==2
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('native-relabel-mask'))
    expressions=[]
    for scene in cohort:
        group=dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id']==scene['scene_id']
        ids=[{'object_id':str(row['object_id']),'ann_id':str(row['ann_id'])} for row in group]
        assert ids==scene['expression_ids'] and len(ids)==4
        expressions.extend([{'scene_id':scene['scene_id'],**row} for row in ids])
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,
        shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    cluster=model.dec.cluster_att
    bank=model.dec.cluster_bank
    active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active)==1 and active[0] is model.dec.encoder_layers[-1]
    last=model.dec.decoder_layers[-1]

    def clone(value):
        if torch.is_tensor(value):
            return value.detach().clone()
        if isinstance(value,tuple):
            return tuple(clone(item) for item in value)
        if isinstance(value,list):
            return [clone(item) for item in value]
        if isinstance(value,dict):
            return {key:clone(item) for key,item in value.items()}
        return value

    def error(left,right):
        return float((left-right).abs().max().cpu())

    held={}
    original_build=bank.build_cluster_feats

    def capture_build(*values):
        held['build_args']=clone(values)
        return original_build(*values)

    def capture_cluster(module,values,output):
        held['core']=clone(values)
        held['message']=clone(output['point'])

    def capture_ila(module,values):
        held['ila']=clone(values)

    def capture_last(module,values,output):
        held['last_args']=clone(values)
        held['last']=clone(output)

    def capture_criterion(module,values):
        held['criterion']=clone(values)

    bank.build_cluster_feats=capture_build
    hooks=[cluster.register_forward_hook(capture_cluster),active[0].ila.register_forward_pre_hook(capture_ila),
        last.register_forward_hook(capture_last),model.criterion.register_forward_pre_hook(capture_criterion)]
    with torch.no_grad():
        native_loss,_=model(copy.deepcopy(batch),mode='loss')
    bank.build_cluster_feats=original_build
    for hook in hooks:
        hook.remove()
    hooks=[]
    core=held['core']
    x,_,mask,original_tokens,original_children,original_ids=core
    query=held['last'][0]
    coordinates=held['last_args'][5]
    assert len(x)==len(expressions)==8
    query_hash=fingerprint(torch,query)
    prefix_hash=fingerprint(torch,x)
    output=held['criterion'][0]
    assert torch.equal(output['masks'],held['last'][2])
    matches=[]
    loss_masks=model.criterion.loss_masks

    def collect(pred_masks,pred_scores,targets,indices,num_boxes):
        if all(torch.equal(pred_masks[b],output['masks'][b,:,~mask[b]]) for b in range(len(pred_masks))):
            matches.append(clone((targets,indices)))
        return loss_masks(pred_masks,pred_scores,targets,indices,num_boxes)

    model.criterion.loss_masks=collect
    try:
        with torch.no_grad():
            model.criterion(*held['criterion'])
    finally:
        model.criterion.loss_masks=loss_masks
    assert len(matches)==1
    targets,indices=matches[0]

    def suffix(message):
        values=list(clone(held['ila']))
        values[1]=x+torch.sigmoid(active[0].cluster_att_gate)*message
        features=active[0].ila(*values)[0]
        scores,logits=last.prediction_head(query,features,mask)
        return scores,logits,features

    def groups(ids):
        labels=ids[0].long()
        answer=[]
        for level in range(3):
            if level:
                labels=ids[level].long().gather(0,labels)
            cpu=labels.detach().cpu()
            answer.append(tuple(sorted(tuple(torch.nonzero(cpu==v).flatten().tolist()) for v in torch.unique(cpu).tolist())))
        return answer

    with torch.no_grad():
        original_message=cluster(*core)['point']
        own=suffix(original_message)
        identity=suffix(held['message'].clone())
        rebuilt=original_build(*held['build_args'])
        controls={'native_point_message':error(original_message,held['message']),
            'native_features':error(own[2],held['last_args'][2]),'native_mask':error(own[1],held['last'][2]),
            'native_score':error(own[0],held['last'][1]),'identity_message_mask':error(identity[1],own[1]),
            'native_token_reaggregation':max(error(a,b) for a,b in zip(rebuilt,original_tokens))}
        counts=[int((~mask[b]).sum()) for b in range(len(x))]
        assert counts[:4]==[cohort[0]['exact_train_support_count']]*4
        assert counts[4:]==[cohort[1]['exact_train_support_count']]*4
        assert min(counts)>=256
        new_ids=[[] for _ in range(3)]
        new_children=[[] for _ in range(2)]
        geometry=[]
        for b,n in enumerate(counts):
            coords=coordinates[b,:n]
            perm=torch.arange(n-1,-1,-1,device=coords.device)
            inverse=torch.argsort(perm)
            assert torch.equal(coords[perm][inverse],coords)
            offsets=torch.tensor([0,n],dtype=held['build_args'][1].dtype,device=coords.device)
            ids,children=bank.partitioner(coords[perm].contiguous(),offsets)
            labels=[ids[level][0] for level in range(3)]
            labels[0]=labels[0][inverse]
            prior=[original_ids[level][b] for level in range(3)]
            geometry.append({'expression_index':b,'scene_id':expressions[b]['scene_id'],
                'exact_inverse_permutation':True,'physical_co_membership_changed':[a!=c for a,c in zip(groups(prior),groups(labels))]})
            for level in range(3):
                new_ids[level].append(labels[level])
            for level in range(2):
                new_children[level].append(children[level][0])
        saved_ids=bank.cluster_ids_list
        try:
            bank.cluster_ids_list=new_ids
            changed_tokens=original_build(*held['build_args'])
        finally:
            bank.cluster_ids_list=saved_ids
        changed=list(clone(core))
        changed[3:6]=[changed_tokens,new_children,new_ids]
        changed_message=cluster(*changed)['point']
        intervention=suffix(changed_message)
        result['controls']=controls
        result['controls_passed']=max(controls.values())<=MANIFEST['tolerance']
        result['valid_supports']=counts
        result['geometry']=geometry
        result['point_message_max_delta']=error(changed_message,original_message)
        result['mask_max_delta']=error(intervention[1],own[1])
        result['task_interpretation']='CONDITIONAL_DIAGNOSTIC_ONLY' if result['controls_passed'] else 'INCONCLUSIVE_STRICT_CONTROL_FAILURE'
        for b,(qi,ti) in enumerate(indices):
            n=counts[b]
            primary=held['criterion'][4][b][:n]==int(expressions[b]['object_id'])
            for q,t in zip(qi.tolist(),ti.tolist()):
                target=targets[b]['masks'][t]
                if not torch.equal(target.bool(),primary):
                    continue
                target=target.to(dtype=own[1].dtype)
                old_error=float((own[1][b,q,:n].sigmoid()-target).abs().mean().cpu())
                new_error=float((intervention[1][b,q,:n].sigmoid()-target).abs().mean().cpu())
                result['records'].append({'scene_id':expressions[b]['scene_id'],'expression_index':b,'native_query':q,
                    'original_probability_error':old_error,'relabeled_probability_error':new_error,
                    'relabeled_minus_original_probability_error':new_error-old_error})
        assert fingerprint(torch,query)==query_hash and fingerprint(torch,x)==prefix_hash
    result.update(execution_completed=True,scene_ids=[s['scene_id'] for s in cohort],
        fixed_query_sha256=query_hash,fixed_prefix_sha256=prefix_hash,native_loss=float(native_loss.cpu()),
        matching_sha256=fingerprint(torch,matches),population_uncertainty='UNKNOWN;four fixed TRAIN scenes,correlated query/expression rows,not a population efficacy estimate.')
except BaseException as error_value:
    result.update(error_type=type(error_value).__name__,error=str(error_value))
    raise
finally:
    if bank is not None and original_build is not None:
        bank.build_cluster_feats=original_build
    for hook in hooks:
        hook.remove()
    try:
        save('native_relabel_mask_pair_'+str(args.pair)+'.json',result)
    finally:
        release()
