"""Independent package backward and unchanged-standard paired resources."""
import argparse
import copy
import gc
import importlib
import importlib.util
import logging
from pathlib import Path
import sys
import time
import numpy as np
from native_runtime import acquire,release,setup,save,verify,observe,fingerprint,sha,MANIFEST,STAGE

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--lease',required=True)
    parser.add_argument('--target',choices=('candidate','champion'),required=True)
    args=parser.parse_args()
    r={'execution_completed':False,'target':args.target,'native_train_forwards':0,'native_train_backwards':0,
       'native_predict_calls':0,'optimizer_steps':0,'scheduler_steps':0,'training_started':False,
       'VAL_accuracy_for_selection':False,'production_modified':False,'train_records':[],'scientific_admission':False}
    hooks=[]
    try:
        r['before']=acquire(args.lease)
        torch,gorilla,cfg,model,meta=setup()
        assert meta['epoch']==16
        state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        original_flags={k:p.requires_grad for k,p in model.named_parameters()}
        if args.target=='candidate':
            model.cpu()
            del model
            gc.collect()
            torch.cuda.empty_cache()
            name=MANIFEST['candidate_name']
            qualified='framework.model.Quard_model.'+name
            path=STAGE/name
            spec=importlib.util.spec_from_file_location(qualified,path/'__init__.py',submodule_search_locations=[str(path)])
            module=importlib.util.module_from_spec(spec)
            sys.modules[qualified]=module
            spec.loader.exec_module(module)
            cfg=gorilla.Config.fromfile(str(STAGE/(name+'.yaml')))
            gorilla.set_random_seed(1999)
            model=module.Network(**cfg.model)
            model.load_state_dict(state,strict=True)
            model.cuda()
            hierarchy=importlib.import_module(qualified+'.hier_postprocess')
        else:
            hierarchy=importlib.import_module('framework.model.Quard_model.'+MANIFEST['name']+'.hier_postprocess')
        assert {k:p.requires_grad for k,p in model.named_parameters()}==original_flags
        assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
        assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
        r['parameters']=sum(p.numel() for p in model.parameters())
        from framework.dataset import build_dataset,build_dataloader
        from torch.utils.data import DataLoader,Subset
        dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('coarse-native-independent'))
        cohort=MANIFEST['cohort'][:4]
        for scene in cohort:
            group=dataset.scene_inputs[scene['group_index']]
            assert group[0]['scene_id']==scene['scene_id']
            assert [{'object_id':str(x['object_id']),'ann_id':str(x['ann_id'])} for x in group]==scene['expression_ids']
        held={}
        original_attention=None
        if args.target=='candidate':
            original_attention=hierarchy.coarse_readback
            def capture_attention(*values,**keywords):
                output,weights=original_attention(*values,**keywords)
                if torch.is_grad_enabled():
                    assert weights.requires_grad
                    weights.retain_grad()
                    held['attention']=weights
                return output,weights
            hierarchy.coarse_readback=capture_attention
        for workers in (0,4):
            model.load_state_dict(state,strict=True)
            model.train()
            gorilla.set_random_seed(1999)
            loader=DataLoader(Subset(dataset,[s['group_index'] for s in cohort]),batch_size=2,
                shuffle=False,num_workers=workers,persistent_workers=bool(workers),collate_fn=dataset.collate_fn)
            iterator=iter(loader)
            for batch_index in range(2):
                batch=next(iterator)
                signature=fingerprint(torch,batch)
                model.zero_grad(set_to_none=True)
                held.clear()
                gorilla.set_random_seed(1999)
                torch.cuda.reset_peak_memory_stats()
                loss,components=model(copy.deepcopy(batch),mode='loss')
                r['native_train_forwards']+=1
                assert bool(torch.isfinite(loss))
                loss.backward()
                r['native_train_backwards']+=1
                assert all(bool(torch.isfinite(p.grad).all()) for p in model.parameters() if p.grad is not None)
                gradients={k:float(p.grad.norm().cpu()) if p.grad is not None else None
                           for k,p in model.named_parameters() if k.startswith('dec.cluster_att.cluster_ffn.2.') or k.startswith('dec.cluster_att.cluster_ffn_norm.2.')}
                assert gradients and all(v is not None and v>0 for v in gradients.values())
                record={'workers':workers,'batch_index':batch_index,'input_sha256':signature,
                    'scene_ids':[s['scene_id'] for s in cohort[2*batch_index:2*batch_index+2]],
                    'loss':float(loss.detach().cpu()),'coarse_ffn_parameter_gradient_norms':gradients,
                    'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
                    'orth_reg_loss':float(components['orth_reg_loss'].detach().cpu()),'full_optimizer_peak':'UNKNOWN;no optimizer instantiated'}
                if args.target=='candidate':
                    weights=held['attention']
                    assert weights.grad is not None and bool(torch.isfinite(weights.grad).all()) and bool((weights.grad!=0).any())
                    record['actual_attention_loss_gradient_norm']=float(weights.grad.norm().cpu())
                    record['attention_shape']=list(weights.shape)
                    assert model.dec.cluster_att._raw_coarse_keys is None
                r['train_records'].append(record)
                del loss,components,batch
            del iterator,loader
            gc.collect()
        if original_attention is not None:hierarchy.coarse_readback=original_attention
        model.zero_grad(set_to_none=True)
        held.clear()
        gc.collect()
        torch.cuda.empty_cache()
        cfg.data.val.lang_num_max=1
        val=build_dataset(copy.deepcopy(cfg.data.val),logging.getLogger('coarse-resource-only'))
        loader_cfg=copy.deepcopy(cfg.dataloader.val)
        loader_cfg.batch_size=1;loader_cfg.num_workers=0;loader_cfg.persistent_workers=False
        gorilla.set_random_seed(1999)
        sample=next(iter(build_dataloader(val,training=False,**loader_cfg)))
        assert len(sample['ann_ids'])==len(sample['scan_ids'])==1
        sig=fingerprint(torch,sample)
        import fvcore
        from fvcore.nn import FlopCountAnalysis
        files={n:sha(Path(importlib.import_module('fvcore.nn.'+n).__file__)) for n in ('flop_count','jit_analysis','jit_handles')}
        expected={'flop_count':'b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba','jit_analysis':'110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31','jit_handles':'ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129'}
        assert files==expected,'Unchanged historical standard handlers required'
        model.eval()
        with torch.no_grad():
            analysis=FlopCountAnalysis(model,(sample,'predict'))
            analysis.unsupported_ops_warnings(False);analysis.uncalled_modules_warnings(False)
            total=analysis.total()
            r['native_predict_calls']+=1
            r['profile']={'flops':float(total),'flops_g':float(total/1e9),'within10G':bool(total<=10e9),
                'by_operator':{k:float(v) for k,v in analysis.by_operator().items()},
                'unsupported_ops':dict(analysis.unsupported_ops()),'profiler_file_sha256':files,'fvcore_version':fvcore.__version__}
            for _ in range(20):
                model(sample,mode='predict');r['native_predict_calls']+=1
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
            times=[]
            for _ in range(100):
                torch.cuda.synchronize();start=time.perf_counter()
                prediction=model(sample,mode='predict')
                torch.cuda.synchronize();times.append((time.perf_counter()-start)*1000)
                r['native_predict_calls']+=1
            assert prediction['piou'] and all(bool(torch.isfinite(v).all()) for v in prediction['piou'])
        assert fingerprint(torch,sample)==sig
        assert {k:p.requires_grad for k,p in model.named_parameters()}==original_flags
        verify()
        r.update(execution_completed=True,resource_input_sha256=sig,batch_size=1,lang_num_max=1,warmup=20,repeat=100,
            median_ms=float(np.median(times)),p90_ms=float(np.percentile(times,90)),measurements_ms=times,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            full_training_peak='UNKNOWN;no optimizer/scheduler steps',original_no_cluster_resource_delta='UNKNOWN;original baseline config unavailable',
            validation_accuracy_evaluated_for_selection=False,parameter_flags_preserved=True,after=observe())
    except BaseException as error:
        r.update(error_type=type(error).__name__,error=str(error))
        raise
    finally:
        try:save('native_package_'+args.target+'_result.json',r)
        finally:release()

if __name__=='__main__':main()
