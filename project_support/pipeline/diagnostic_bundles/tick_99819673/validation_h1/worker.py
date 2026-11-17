"""Independent RSTR full-source controls, native criterion backward and resources."""
import os
os.environ.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='1')
import argparse
import copy
import importlib
import importlib.util
import logging
from pathlib import Path
import sys
import time
from native_runtime import acquire,release,save,sha,verify,observe,fingerprint,MANIFEST,STAGE,ROOT,NAME


def setup(target):
    sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
    from tools import train
    import torch,gorilla,yaml
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(.75,0)
    parent=yaml.safe_load(Path(MANIFEST['assets']['config_path']).read_text())
    candidate=yaml.safe_load((STAGE/'candidate.yaml').read_text())
    assert parent==candidate
    cfg=gorilla.Config.fromfile(str(STAGE/'candidate.yaml') if target=='candidate' else MANIFEST['assets']['config_path'])
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    gorilla.set_random_seed(1999)
    qualified='framework.model.Quard_model.'+NAME
    if target=='candidate':
        qualified+='_rstr'
        directory=STAGE/'candidate_model'
        for name,expected in MANIFEST['candidate_source_hashes'].items():assert sha(directory/name)==expected
        spec=importlib.util.spec_from_file_location(qualified,directory/'__init__.py',submodule_search_locations=[str(directory)])
        module=importlib.util.module_from_spec(spec);sys.modules[qualified]=module;spec.loader.exec_module(module)
    else:module=importlib.import_module(qualified)
    model=module.Network(**cfg.model)
    checkpoint=torch.load(MANIFEST['assets']['checkpoint'],map_location='cpu',weights_only=False,mmap=True)
    state=checkpoint['model'];extra=set(state)-set(model.state_dict())
    assert extra<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    model.load_state_dict({k:v for k,v in state.items() if k not in extra},strict=True)
    assert checkpoint['meta']['epoch']==16
    del checkpoint,state
    model.cuda().eval()
    return torch,gorilla,cfg,model,qualified


def controls(torch,gorilla,cfg,model,qualified,result):
    from torch.utils.data import DataLoader,Subset
    from framework.dataset import build_dataset
    hierarchy=importlib.import_module(qualified+'.hier_postprocess')
    transport_module=importlib.import_module(qualified+'.sibling_transport')
    encoder=[x for x in model.dec.encoder_layers if x.use_cluster][0]
    attention,bank=model.dec.cluster_att,model.dec.cluster_bank
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('rstr-source-controls'))
    for scene in MANIFEST['cohort']:
        group=dataset.scene_inputs[scene['group_index']]
        assert group[0]['scene_id']==scene['scene_id']
        assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==scene['expression_ids']
    gorilla.set_random_seed(1999)
    batch=next(iter(DataLoader(Subset(dataset,[x['group_index'] for x in MANIFEST['cohort']]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)))
    held={}
    def clone(v):
        if torch.is_tensor(v):return v.detach().clone()
        if isinstance(v,dict):return {k:clone(x) for k,x in v.items()}
        if isinstance(v,(tuple,list)):return type(v)(clone(x) for x in v)
        return copy.deepcopy(v)
    def before(owner,values,keywords):held.update(args=clone(values),kwargs=clone(keywords))
    def after(owner,values,output):held['output']=clone(output)
    hooks=[encoder.register_forward_pre_hook(before,with_kwargs=True),encoder.register_forward_hook(after)]
    try:
        with torch.no_grad():loss,_=model(copy.deepcopy(batch),mode='loss')
        result['native_loss_forwards']+=1;result['native_eval_loss']=float(loss.cpu())
    finally:
        for hook in hooks:hook.remove()
    args,kwargs=held['args'],held['kwargs'];ids,maps=clone(bank.cluster_ids_list),clone(bank.child_cluster_maps)
    signature=fingerprint(torch,(args,kwargs))
    def error(a,b):return float((a-b).abs().max().detach().cpu())
    def execute(values=args):
        hierarchy.reset_orth_accum();result['full_source_encoder_calls']+=1
        return encoder(*values,**kwargs)
    result['controls']={}
    original_transport=hierarchy._sibling_fine
    with torch.no_grad():
        repetitions=[]
        for _ in range(3):
            bank.cluster_ids_list,bank.child_cluster_maps=clone(ids),clone(maps)
            output=execute()
            repetitions.append({'language_max_abs':error(output[0],held['output'][0]),'inst_feats_max_abs':error(output[1],held['output'][1])})
        result['controls']['identity_repeats']=repetitions
        width=args[2].shape[1];permutations=[];inverses=[]
        for mask in args[3]:
            n=int((~mask).sum());p=torch.cat((torch.arange(n-1,-1,-1,device=mask.device),torch.arange(n,width,device=mask.device)))
            permutations.append(p);inverses.append(torch.argsort(p))
        changed=list(clone(args))
        for index in (2,3,5):changed[index]=torch.stack([v[p] for v,p in zip(args[index],permutations)])
        bank.cluster_ids_list,bank.child_cluster_maps=clone(ids),clone(maps)
        for b,value in enumerate(ids[0]):bank.cluster_ids_list[0][b]=value[permutations[b][:len(value)]]
        permuted=execute(tuple(changed))
        restored=torch.stack([value[inverse] for value,inverse in zip(permuted[1],inverses)])
        result['controls']['full_source_row_permutation']={'language_max_abs':error(permuted[0],held['output'][0]),'inst_feats_max_abs':error(restored,held['output'][1])}
        bank.cluster_ids_list,bank.child_cluster_maps=clone(ids),clone(maps)
        hierarchy._sibling_fine=lambda fine,identifiers,heads:fine
        try:
            disabled=execute()
            import types
            parent_path=ROOT/'framework/model/Quard_model'/NAME/'hier_postprocess.py'
            assert sha(parent_path)==MANIFEST['assets']['source_hashes']['hier_postprocess.py']
            spec=importlib.util.spec_from_file_location('verified_original_hierarchy',parent_path)
            parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
            original_forward=attention.forward
            attention.forward=types.MethodType(parent.C2F_ClusterAttn_CTF.forward,attention)
            try:parent_result=execute()
            finally:attention.forward=original_forward
        finally:hierarchy._sibling_fine=original_transport
        result['controls']['disabled_vs_original_parent']={'language_max_abs':error(disabled[0],parent_result[0]),'inst_feats_max_abs':error(disabled[1],parent_result[1])}
        result['native_transport_feature_effect']=error(disabled[1],held['output'][1])
        assert fingerprint(torch,(args,kwargs))==signature
    # Keep the complete criterion/backbone/source graph: no frozen bank replacement.
    captured=[];operator_records=[]
    def capture_transport(fine,identifiers,heads):
        output=original_transport(fine,identifiers,heads)
        fine.retain_grad();output.retain_grad();captured.append((fine,output))
        with torch.no_grad():
            for b in range(fine.shape[0]):
                parent=identifiers[1][b].long();counts=torch.bincount(identifiers[0][b].long(),minlength=parent.numel())
                _,groups=transport_module.transport(fine[b,:parent.numel()],parent,counts,heads=heads,matrices=True)
                for g in groups:
                    p,pi=g['p'],g['pi'];flow=pi[None,:,None]*p
                    mean=(g['before'].double()*pi.double()[None,:,None]).sum(1,keepdim=True)
                    before=((g['before'].double()-mean).square().sum(-1)*pi.double()[None,:]).sum(-1)
                    after=((g['after'].double()-mean).square().sum(-1)*pi.double()[None,:]).sum(-1)
                    operator_records.append({'row_sum_error':float((p.sum(-1)-1).abs().max()),
                        'detailed_balance_error':float((flow-flow.transpose(1,2)).abs().max()),'minimum_p':float(p.min()),
                        'variance_before_sum':float(before.sum()),'variance_after_sum':float(after.sum())})
        return output
    hierarchy.reset_orth_accum();model.train();model.zero_grad(set_to_none=True);gorilla.set_random_seed(1999)
    hierarchy._sibling_fine=capture_transport
    try:
        loss,_=model(copy.deepcopy(batch),mode='loss');result['native_loss_forwards']+=1
        assert bool(torch.isfinite(loss));loss.backward();result['native_criterion_backwards']+=1
    finally:hierarchy._sibling_fine=original_transport
    gradients=[v.grad for v in model.parameters() if v.grad is not None]
    result['native_train_loss']=float(loss.detach().cpu())
    result['all_observed_gradients_finite']=bool(gradients) and all(bool(torch.isfinite(g).all()) for g in gradients)
    result['gradient_tensor_count']=len(gradients)
    result['transport_path_gradients']=[{'input_finite':bool(torch.isfinite(a.grad).all()),'output_finite':bool(torch.isfinite(b.grad).all()),
        'input_abs_max':float(a.grad.abs().max()),'output_abs_max':float(b.grad.abs().max())} for a,b in captured]
    result['fine_ffn_gradients']={name:{'finite':bool(torch.isfinite(v.grad).all()),'abs_max':float(v.grad.abs().max())} for name,v in attention.cluster_ffn[0].named_parameters() if v.grad is not None}
    result['native_operator']={'groups':len(operator_records),'row_sum_max':max(x['row_sum_error'] for x in operator_records),
        'detailed_balance_max':max(x['detailed_balance_error'] for x in operator_records),'minimum_p':min(x['minimum_p'] for x in operator_records),
        'weighted_variance_before':sum(x['variance_before_sum'] for x in operator_records),'weighted_variance_after':sum(x['variance_after_sum'] for x in operator_records)}
    errors=[v for x in repetitions for v in x.values()]+list(result['controls']['full_source_row_permutation'].values())+list(result['controls']['disabled_vs_original_parent'].values())
    result.update(execution_completed=True,maximum_full_source_control_error=max(errors),all_full_source_controls_passed=max(errors)<=1e-6,
        original_numeric_threshold_preserved=True,frozen_bank_replacements=0,train_scenes_actually_executed=2,unique_expressions=8,
        full_model_point_renumbering_tested=False,source_scope='Entire actual hierarchy pooling and active encoder; reverse valid SP rows with transported fixed FPS membership; not upstream-backbone FPS equivariance.',
        after=observe())
    verify()


def resources(torch, gorilla, cfg, model, result):
    import numpy as np
    from framework.dataset import build_dataset, build_dataloader
    import fvcore
    from fvcore.nn import FlopCountAnalysis
    cfg.data.val.lang_num_max = 1
    dataset = build_dataset(copy.deepcopy(cfg.data.val), logging.getLogger('rstr-resource-only'))
    loader_cfg = copy.deepcopy(cfg.dataloader.val)
    loader_cfg.batch_size = 1
    loader_cfg.num_workers = 0
    loader_cfg.persistent_workers = False
    gorilla.set_random_seed(1999)
    sample = next(iter(build_dataloader(dataset, training=False, **loader_cfg)))
    assert len(sample['ann_ids']) == len(sample['scan_ids']) == 1
    signature = fingerprint(torch, sample)
    handlers = {name: sha(Path(importlib.import_module('fvcore.nn.' + name).__file__))
        for name in ('flop_count', 'jit_analysis', 'jit_handles')}
    expected = {'flop_count': 'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba',
        'jit_analysis': '110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31',
        'jit_handles': 'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
    assert handlers == expected, 'Historical profiler handlers must not change'
    model.eval()
    flags = {key: value.requires_grad for key, value in model.named_parameters()}
    with torch.no_grad():
        analysis = FlopCountAnalysis(model, (sample, 'predict'))
        analysis.unsupported_ops_warnings(False)
        analysis.uncalled_modules_warnings(False)
        total = analysis.total()
        result['native_predict_calls'] += 1
        result['profile'] = {'flops': float(total), 'flops_g': float(total / 1e9),
            'within10G': bool(total <= 10e9), 'fvcore_version': fvcore.__version__,
            'profiler_file_sha256': handlers, 'by_operator': {key: float(value) for key, value in analysis.by_operator().items()},
            'unsupported_ops': dict(analysis.unsupported_ops())}
        for _ in range(20):
            model(sample, mode='predict')
            result['native_predict_calls'] += 1
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(100):
            torch.cuda.synchronize()
            start = time.perf_counter()
            prediction = model(sample, mode='predict')
            torch.cuda.synchronize()
            times.append((time.perf_counter() - start) * 1000)
            result['native_predict_calls'] += 1
        assert prediction['piou'] and all(bool(torch.isfinite(value).all()) for value in prediction['piou'])
    assert fingerprint(torch, sample) == signature
    assert {key: value.requires_grad for key, value in model.named_parameters()} == flags
    verify()
    result.update(execution_completed=True, input_sha256=signature, scan_ids=sample['scan_ids'],
        ann_ids=sample['ann_ids'], parameters=sum(value.numel() for value in model.parameters()),
        batch_size=1, lang_num_max=1, warmup=20, repeat=100, median_ms=float(np.median(times)),
        p90_ms=float(np.percentile(times, 90)), measurements_ms=times,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved(),
        full_optimizer_training_peak='UNKNOWN; no optimizer or scheduler steps',
        original_no_cluster_resource_delta='UNKNOWN; original baseline package/config not verified',
        validation_accuracy_evaluated_for_selection=False, parameter_flags_preserved=True,
        source_body_executed_without_replacement=True, after=observe())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True);parser.add_argument('--mode',choices=('resources','controls'),required=True);parser.add_argument('--target',choices=('champion','candidate'),required=True)
    args=parser.parse_args()
    result={'execution_completed':False,'mode':args.mode,'target':args.target,'scientific_admission':False,'new_training':0,'optimizer_steps':0,'native_predict_calls':0,'native_loss_forwards':0,'native_criterion_backwards':0,'full_source_encoder_calls':0}
    try:
        result['before']=acquire(args.lease)
        torch,gorilla,cfg,model,qualified=setup(args.target)
        if args.mode=='resources':resources(torch,gorilla,cfg,model,result)
        else:
            assert args.target=='candidate';controls(torch,gorilla,cfg,model,qualified,result)
    except BaseException as value:
        result.update(error_type=type(value).__name__,error=str(value));raise
    finally:
        try:save(args.mode+'_'+args.target+'_result.json',result)
        finally:release()


if __name__=='__main__':main()
