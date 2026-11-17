"""Existing full-model FVCore/predict and bs1/warmup20/repeat100 protocol."""
import time
import numpy as np
from framework.dataset import build_dataloader

cfg.data.val.data_root='/sdc1/songcl/IPDN/data/'
cfg.data.val.lang_num_max=1
validation=build_dataset(copy.deepcopy(cfg.data.val),logging.getLogger('matched-resource-only'))
loader_cfg=copy.deepcopy(cfg.dataloader.val)
loader_cfg.batch_size=1
loader_cfg.num_workers=0
loader_cfg.persistent_workers=False
loader=build_dataloader(validation,training=False,**loader_cfg)
gorilla.set_random_seed(1999)
sample=next(iter(loader))
assert len(sample['ann_ids'])==1 and len(sample['scan_ids'])==1
model.eval()
parameters=sum(p.numel() for p in model.parameters())
profile={'status':'unknown','flops':None,'flops_g':None,'unsupported_ops':None}
with torch.no_grad():
    try:
        from fvcore.nn import FlopCountAnalysis
        analysis=FlopCountAnalysis(model,(sample,'predict'))
        analysis.unsupported_ops_warnings(False)
        analysis.uncalled_modules_warnings(False)
        total=analysis.total()
        profile={'status':'counted','flops':float(total),'flops_g':float(total/1e9),
            'by_module':dict(analysis.by_module()),'unsupported_ops':dict(analysis.unsupported_ops()),
            'counted_flops_within_original10G':bool(total<=10e9)}
    except (ImportError,RuntimeError,ValueError,AssertionError) as exc:
        profile.update(error_type=type(exc).__name__,error=str(exc))
    for _ in range(20):
        assert (datetime.fromisoformat(FOREGROUND_DEADLINE)-datetime.now(timezone.utc)).total_seconds()>120
        model(sample,mode='predict')
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    measurements=[]
    for _ in range(100):
        assert (datetime.fromisoformat(FOREGROUND_DEADLINE)-datetime.now(timezone.utc)).total_seconds()>120
        torch.cuda.synchronize()
        start=time.perf_counter()
        prediction=model(sample,mode='predict')
        torch.cuda.synchronize()
        measurements.append((time.perf_counter()-start)*1000)
    assert prediction['piou'] and all(torch.isfinite(value).all() for value in prediction['piou'])
observations.append(observe('after_matched_profile'))
result={'observed_at':datetime.now(timezone.utc).isoformat(),'token':FOREGROUND_TOKEN,
    'condition':PROFILE_CONDITION,'profile':profile,'parameters':parameters,
    'median_ms':float(np.median(measurements)),'p90_ms':float(np.percentile(measurements,90)),
    'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),
    'batch_size':1,'warmup':20,'repeat':100,'lang_num_max':1,
    'scan_ids':sample['scan_ids'],'ann_ids':sample['ann_ids'],
    'device':torch.cuda.get_device_name(),'allocator_fraction':.25,
    'budget_passed_all_observations':all(r['post_budget_passed'] for r in observations),
    'observations':observations,'optimizer_steps':0,'new_training':False,
    'scope':'Existing full-model counted-FLOPs and real synchronized latency/memory on first VAL expression only; not efficacy or a new one-sided counting protocol.'}
print('HIER_NATIVE_RESULT='+json.dumps(result))
