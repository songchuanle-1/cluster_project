"""Matched M95 full-native training-memory comparator; no optimizer steps."""
import copy
import logging
import math
from runtime import acquire,release,setup,save,verify,observe,fingerprint,MANIFEST,remaining

before=acquire()
result={"passed":False,"native_forwards":0,"native_backwards":0,"pairs":[],"before":before,"purpose":"paired M95 training memory,not model selection"}
try:
    torch,gorilla,cfg,model,removed=setup(candidate=False)
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger("fle-m95-memory"))
    gorilla.set_random_seed(1999)
    batches=list(DataLoader(Subset(dataset,MANIFEST["train_groups"]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn))
    cluster=model.dec.cluster_att
    active=[m for m in model.dec.encoder_layers if m.use_cluster];assert len(active)==1
    def clone(value):
        if torch.is_tensor(value):return value.detach().clone()
        if isinstance(value,tuple):return tuple(clone(x) for x in value)
        if isinstance(value,list):return [clone(x) for x in value]
        if isinstance(value,dict):return {k:clone(v) for k,v in value.items()}
        return value
    for index,batch in enumerate(batches):
        assert remaining()>180
        fp=fingerprint(torch,batch)
        held={"calls":0}
        def core(module,args,kwargs,output):
            held["calls"]+=1;held.update(args=clone(args),kwargs=clone(kwargs),message=output["point"],x=args[0])
            output["point"].retain_grad();args[0].retain_grad()
        def fine(module,args,value):held["fine"]=value;value.retain_grad()
        def ila(module,args):held["ila"]=clone(args)
        def decoder(module,args,value):held.update(decoder=clone(args),logits=clone(value[2]))
        hooks=[cluster.register_forward_hook(core,with_kwargs=True),cluster.cluster_ffn[0].register_forward_hook(fine),
            active[0].ila.register_forward_pre_hook(ila),model.dec.decoder_layers[-1].register_forward_hook(decoder)]
        model.train();model.zero_grad(set_to_none=True);gorilla.set_random_seed(1999);torch.cuda.reset_peak_memory_stats()
        try:
            result["native_forwards"]+=1
            loss,losses=model(copy.deepcopy(batch),mode="loss")
            assert bool(torch.isfinite(loss)) and held["calls"]==1
            loss.backward();result["native_backwards"]+=1;torch.cuda.synchronize()
            used={name:float(p.grad.norm().cpu()) for name,p in cluster.named_parameters() if not name.startswith(("query_linear.","k_linear.","v_linear.")) and p.grad is not None}
            assert len(used)==24 and all(math.isfinite(v) and v>0 for v in used.values())
            gradients={k:float(held[k].grad.norm().cpu()) for k in ("fine","message","x")}
            assert all(math.isfinite(v) and v>0 for v in gradients.values())
            result["pairs"].append({"pair":index,"groups":MANIFEST["native_pairs"][index],"scenes":list(batch["scan_ids"]),"ann_ids":list(batch["ann_ids"]),
                "input_sha256":fp,"native_loss":float(loss.detach().cpu()),"native_training_peak_bytes":torch.cuda.max_memory_allocated(),
                "used_parameter_gradients":used,"path_gradients":gradients,"same_capture_lifetime_as_candidate":True,"after":observe()})
        finally:
            for hook in hooks:hook.remove()
        assert fingerprint(torch,batch)==fp
        model.zero_grad(set_to_none=True);del held,loss,losses;torch.cuda.empty_cache()
    verify();result.update(passed=True,independent_scenes=4,expressions=16,full_training_peak="unknown")
except BaseException as exc:
    result.update(error_type=type(exc).__name__,error=str(exc));raise
finally:
    save("native_m95_result.json",result);release()
print("M95_MATCHED_NATIVE_MEMORY_PASS")
