"""Unmodified standard FVCore handlers plus synchronized whole-model resources."""
import argparse
import copy
import inspect
import logging
from pathlib import Path
import time
import numpy as np
from runtime import acquire, release, setup, save, verify, observe, fingerprint, sha, remaining

parser=argparse.ArgumentParser()
parser.add_argument("--target",choices=["candidate","champion"],required=True)
parser.add_argument("--label",required=True)
args=parser.parse_args()
before=acquire()
result={"passed_measurement":False,"target":args.target,"before":before,"native_predict_calls":0}
try:
    torch,gorilla,cfg,model,removed=setup(candidate=args.target=="candidate")
    from framework.dataset import build_dataset,build_dataloader
    import fvcore
    import fvcore.nn.flop_count as flop_module
    import importlib
    files={name:sha(Path(importlib.import_module("fvcore.nn."+name).__file__)) for name in ("flop_count","jit_analysis","jit_handles")}
    expected={"flop_count":"b5a02604a883bcda75deb918d68639d207c433938cf27e7034dd6de26a2956ba", "jit_analysis":"110f30463ba9f20a86dc1f7a447bed29fe6d55dfedff4a30e05e955e47cacb31", "jit_handles":"ef3a1d20ccad504bfdab7d2a127bce9483de1125d170d915d22f4addbc36c129"}
    assert files==expected,"Profiler code differs from historical standard"
    cfg.data.val.lang_num_max=1
    dataset=build_dataset(copy.deepcopy(cfg.data.val),logging.getLogger("fle-resource-only"))
    loader_cfg=copy.deepcopy(cfg.dataloader.val)
    loader_cfg.batch_size=1;loader_cfg.num_workers=0;loader_cfg.persistent_workers=False
    gorilla.set_random_seed(1999)
    sample=next(iter(build_dataloader(dataset,training=False,**loader_cfg)))
    assert len(sample["ann_ids"])==len(sample["scan_ids"])==1
    original_fingerprint=fingerprint(torch,sample)
    model.eval()
    shape=[]
    hook=None
    if args.target=="candidate":
        def capture_shape(module,inputs,value):
            features,padding,positions,ids=inputs
            shape.append({"valid_points":[int(len(x)) for x in ids],"channels":int(features.shape[-1]),"k":int(module.k),"heads":int(module.heads)})
        hook=model.dec.cluster_att.fine_exchange.register_forward_hook(capture_shape)
    with torch.no_grad():
        from fvcore.nn import FlopCountAnalysis
        analysis=FlopCountAnalysis(model,(sample,"predict"))
        analysis.unsupported_ops_warnings(False);analysis.uncalled_modules_warnings(False)
        total=analysis.total()
        result["native_predict_calls"]+=1
        by_module=analysis.by_module()
        profile={"status":"counted","flops":float(total),"flops_g":float(total/1e9),"counted_flops_within_original10G":bool(total<=10e9),
            "unsupported_ops":dict(analysis.unsupported_ops()),"key_modules":{k:float(by_module[k]) for k in ("","dec","dec.cluster_att")},
            "by_operator":{k:float(v) for k,v in analysis.by_operator().items()},"fvcore_version":fvcore.__version__,"profiler_file_sha256":files}
        if hook:hook.remove();hook=None
        for _ in range(20):
            assert remaining()>150
            model(sample,mode="predict");result["native_predict_calls"]+=1
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
        measurements=[]
        for _ in range(100):
            assert remaining()>150
            torch.cuda.synchronize();start=time.perf_counter()
            prediction=model(sample,mode="predict")
            torch.cuda.synchronize();measurements.append((time.perf_counter()-start)*1000)
            result["native_predict_calls"]+=1
        assert prediction["piou"] and all(bool(torch.isfinite(x).all()) for x in prediction["piou"])
    assert fingerprint(torch,sample)==original_fingerprint
    verify()
    result.update(passed_measurement=True,profile=profile,parameters=sum(p.numel() for p in model.parameters()),
        median_ms=float(np.median(measurements)),p90_ms=float(np.percentile(measurements,90)),measurements_ms=measurements,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
        input_sha256=original_fingerprint,scan_ids=sample["scan_ids"],ann_ids=sample["ann_ids"],batch_size=1,lang_num_max=1,warmup=20,repeat=100,
        fine_shapes=shape,supplemental_fine_qk_av_fma_work=sum(2*sum(s["valid_points"])*s["k"]*s["channels"] for s in shape),
        supplemental_count_is_not_a_new_standard=True,full_training_peak="unknown",evaluated_accuracy_for_selection=False,
        original_baseline_resource_delta="unmeasured_original_config_not_located",device=torch.cuda.get_device_name(),after=observe())
except BaseException as exc:
    result.update(error_type=type(exc).__name__,error=str(exc));raise
finally:
    save(args.label+"_result.json",result);release()
print("FLE_RESOURCE_MEASUREMENT_PASS="+args.target)
