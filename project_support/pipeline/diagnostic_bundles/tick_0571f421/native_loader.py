"""Actual configured batch2/four-worker CPU transport and native backward."""
import argparse
import copy
import logging
import math
from torch.utils.data import Subset
from runtime import acquire,release,setup,save,verify,observe,fingerprint,MANIFEST,remaining

parser=argparse.ArgumentParser()
parser.add_argument("--target",choices=["candidate","champion"],required=True)
parser.add_argument("--label",required=True)
args=parser.parse_args()
before=acquire()
result={"passed":False,"target":args.target,"native_forwards":0,"native_backwards":0,"pairs":[],"before":before}
try:
    torch,gorilla,cfg,model,removed=setup(candidate=args.target=="candidate")
    from framework.dataset import build_dataset,build_dataloader
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger("fle-native-workers4"))
    subset=Subset(dataset,MANIFEST["train_groups"])
    subset.collate_fn=dataset.collate_fn
    loader_cfg=copy.deepcopy(cfg.dataloader.train)
    assert loader_cfg.batch_size==2 and loader_cfg.num_workers==4 and loader_cfg.persistent_workers
    gorilla.set_random_seed(1999)
    loader=build_dataloader(subset,training=True,**loader_cfg)
    iterator=iter(loader)
    try:batches=list(iterator)
    finally:iterator._shutdown_workers()
    assert len(batches)==2
    result["actual_native_loader"]={"batch_size":loader.batch_size,"num_workers":loader.num_workers,"persistent_workers":loader.persistent_workers,"sharing_strategy":torch.multiprocessing.get_sharing_strategy(),"shutdown_workers":True}
    del loader,iterator
    cluster=model.dec.cluster_att
    for index,batch in enumerate(batches):
        assert remaining()>150
        fp=fingerprint(torch,batch)
        held={}
        def hook(module,inputs,value):held["message"]=value["point"];value["point"].retain_grad()
        handle=cluster.register_forward_hook(hook)
        model.train();model.zero_grad(set_to_none=True);gorilla.set_random_seed(1999);torch.cuda.reset_peak_memory_stats()
        try:
            result["native_forwards"]+=1
            loss,losses=model(copy.deepcopy(batch),mode="loss")
            assert bool(torch.isfinite(loss))
            loss.backward();result["native_backwards"]+=1;torch.cuda.synchronize()
            gradient=held["message"].grad
            assert gradient is not None and bool(torch.isfinite(gradient).all()) and float(gradient.norm())>0
            result["pairs"].append({"pair":index,"scenes":list(batch["scan_ids"]),"ann_ids":list(batch["ann_ids"]),"input_sha256":fp,
                "native_loss":float(loss.detach().cpu()),"message_gradient_norm":float(gradient.norm().cpu()),"native_training_peak_bytes":torch.cuda.max_memory_allocated(),"after":observe()})
        finally:handle.remove()
        assert fingerprint(torch,batch)==fp
        model.zero_grad(set_to_none=True);del held,loss,losses;torch.cuda.empty_cache()
    verify();result.update(passed=True,independent_scenes=4,expressions=16,full_training_peak="unknown",all_population_or_rare_runtime_safety="unmeasured")
except BaseException as exc:
    result.update(error_type=type(exc).__name__,error=str(exc));raise
finally:
    save(args.label+"_result.json",result);release()
print("NATIVE_CONFIGURED_WORKERS_PASS="+args.target)
