"""Two-context source/clone/mutation discrimination, not replay-until-pass."""
import argparse
import copy
import hashlib
import importlib
import logging
from pathlib import Path
from native_runtime import acquire,release,setup,save,fingerprint,MANIFEST,ROOT,NAME

parser=argparse.ArgumentParser()
parser.add_argument('--lease',required=True)
args=parser.parse_args()
result={'execution_completed':False,'scientific_admission':False,'new_training':0,
    'native_backwards':0,'fixed_repetitions_per_mode':3,'records':[],
    'scope':'Instrumented original native lossforward;fixed source-reference versus bitwiseclone mean reductions and input/outputmutation controls. No gate waiver,precision change,operatorreplacement or favorable-repeatselection.'}
bank=None
original_build=None
module=None
original_aggregate=None
hook=None
try:
    result['before']=acquire(args.lease)
    torch,gorilla,cfg,model,meta=setup()
    assert meta['epoch']==16
    from torch.utils.data import DataLoader,Subset
    from framework.dataset import build_dataset
    module=importlib.import_module('framework.model.Quard_model.'+NAME+'.hier_postprocess')
    original_aggregate=module.aggregate_cluster
    bank=model.dec.cluster_bank
    original_build=bank.build_cluster_feats
    cohort=MANIFEST['cohort'][:2]
    assert len(cohort)==2
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('aggregation-cause'))
    for scene in cohort:
        group=dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id']==scene['scene_id']
        assert [{'object_id':str(row['object_id']),'ann_id':str(row['ann_id'])} for row in group]==scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[scene['group_index'] for scene in cohort]),
        batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    held={'record_on':False,'reductions':[]}

    def clone(value):
        if torch.is_tensor(value):return value.detach().clone()
        if isinstance(value,tuple):return tuple(clone(part) for part in value)
        if isinstance(value,list):return [clone(part) for part in value]
        if isinstance(value,dict):return {key:clone(part) for key,part in value.items()}
        return value

    def error(a,b):
        return float((a-b).abs().max().cpu())

    def capture_aggregate(feats,ids,pool_type='mean'):
        output=original_aggregate(feats,ids,pool_type=pool_type)
        if held['record_on']:
            held['reductions'].append({'source':feats,'ids':ids,'input_clone':feats.detach().clone(),
                'ids_clone':ids.detach().clone(),'output_reference':output,'output_clone':output.detach().clone(),
                'pool_type':pool_type,'input_version':feats._version,'ids_version':ids._version})
        return output

    def capture_build(*values):
        assert not held['record_on']
        held['build_source_args']=values
        held['build_clone_args']=clone(values)
        held['bank_ids_sha256']=fingerprint(torch,bank.cluster_ids_list)
        held['record_on']=True
        try:
            output=original_build(*values)
        finally:
            held['record_on']=False
        held['tokens_before_cluster']=clone(output)
        return output

    def capture_cluster(owner,values,output):
        held['tokens_after_cluster']=clone(values[3])
        held['point']=clone(output['point'])

    module.aggregate_cluster=capture_aggregate
    bank.build_cluster_feats=capture_build
    hook=model.dec.cluster_att.register_forward_hook(capture_cluster)
    with torch.no_grad():
        loss,_=model(copy.deepcopy(batch),mode='loss')
    bank.build_cluster_feats=original_build
    module.aggregate_cluster=original_aggregate
    hook.remove()
    hook=None
    assert len(held['reductions'])==3
    assert fingerprint(torch,bank.cluster_ids_list)==held['bank_ids_sha256']
    result['native_loss']=float(loss.cpu())
    result['scene_ids']=[scene['scene_id'] for scene in cohort]
    result['captured_expression_count']=8
    result['input_clone_identical']=fingerprint(torch,held['build_source_args'])==fingerprint(torch,held['build_clone_args'])
    result['token_mutation_errors']=[error(a,b) for a,b in zip(held['tokens_before_cluster'],held['tokens_after_cluster'])]
    fixture=[]
    with torch.no_grad():
        for level,record in enumerate(held['reductions']):
            source,ids=record['source'],record['ids']
            copied=record['input_clone']
            assert record['pool_type']=='mean'
            assert torch.equal(source,copied) and torch.equal(ids,record['ids_clone'])
            item={'level':level,'shape':list(source.shape),'dtype':str(source.dtype),
                'source_stride':list(source.stride()),'clone_stride':list(copied.stride()),
                'source_storage_offset':source.storage_offset(),'clone_storage_offset':copied.storage_offset(),
                'input_sha256':fingerprint(torch,source),'ids_sha256':fingerprint(torch,ids),
                'source_unchanged_since_capture':source._version==record['input_version'],
                'ids_unchanged_since_capture':ids._version==record['ids_version'],
                'original_output_mutation_error':error(record['output_reference'],record['output_clone']),
                'source_errors':[],'clone_errors':[]}
            outputs={}
            for mode,value in (('source',source),('clone',copied)):
                values=[]
                for repeat in range(3):
                    torch.cuda.synchronize()
                    actual=original_aggregate(value,ids,pool_type='mean')
                    torch.cuda.synchronize()
                    item[mode+'_errors'].append(error(actual,record['output_clone']))
                    values.append(actual)
                outputs[mode]=values
                item[mode+'_within_repeat_max']=max(error(a,b) for a in values for b in values)
            item['source_clone_cross_max']=max(error(a,b) for a in outputs['source'] for b in outputs['clone'])
            zeros=original_aggregate(torch.zeros_like(source),ids,pool_type='mean')
            item['zero_input_output_max']=float(zeros.abs().max().cpu())
            assert fingerprint(torch,source)==item['input_sha256'] and fingerprint(torch,ids)==item['ids_sha256']
            result['records'].append(item)
            fixture.append({'input':copied.cpu(),'ids':record['ids_clone'].cpu(),'original_output':record['output_clone'].cpu()})
        result['cascade_source_errors']=[error(a,b) for a,b in zip(original_build(*held['build_source_args']),held['tokens_before_cluster'])]
        result['cascade_clone_errors']=[error(a,b) for a,b in zip(original_build(*held['build_clone_args']),held['tokens_before_cluster'])]
    path=Path(__file__).with_name('native_aggregation_fixture.pt')
    with path.open('xb') as stream:
        torch.save({'cohort':cohort,'reductions':fixture,'protocol':MANIFEST['protocol'],'scope':'Native captured tensors only;not modelweights or checkpoint.'},stream)
    result['fixture']={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
    result['source_pointer_reuse_preserves_strict_control']=max(result['cascade_source_errors'])<=MANIFEST['tolerance'] and all(max(row['source_errors'])<=MANIFEST['tolerance'] for row in result['records'])
    result['clone_branch_preserves_strict_control']=max(result['cascade_clone_errors'])<=MANIFEST['tolerance'] and all(max(row['clone_errors'])<=MANIFEST['tolerance'] for row in result['records'])
    result['fixed_input_native_variation_observed']=any(row['source_within_repeat_max']>0 for row in result['records'])
    result['admissible_measurement_repair_proved']=False
    result['execution_completed']=True
except BaseException as error_value:
    result.update(error_type=type(error_value).__name__,error=str(error_value))
    raise
finally:
    if bank is not None and original_build is not None:bank.build_cluster_feats=original_build
    if module is not None and original_aggregate is not None:module.aggregate_cluster=original_aggregate
    if hook is not None:hook.remove()
    try:save('native_aggregation_cause_result.json',result)
    finally:release()
