"""Full native loss/backward and same-prefix fine mechanism controls."""
import copy
import importlib
import logging
import math
from runtime import acquire, release, setup, save, verify, observe, fingerprint, MANIFEST, NAME, remaining

before=acquire()
result={"passed":False,"native_forwards":0,"native_backwards":0,"suffix_replays":0,"pairs":[],"before":before}
try:
    torch,gorilla,cfg,model,removed=setup()
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger("fle-native"))
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,MANIFEST["train_groups"]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    batches=list(loader);assert len(batches)==2
    active=[m for m in model.dec.encoder_layers if m.use_cluster]
    assert len(active)==1 and active[0].cluster_message_type=="context"
    cluster=model.dec.cluster_att
    fine_module=cluster.fine_exchange
    assert sum(p.numel() for p in fine_module.parameters())==0
    assert not list(cluster.cluster_ffn[0].parameters()) and not list(cluster.cluster_ffn_norm[0].parameters())
    operator=importlib.import_module("framework.model.Quard_model."+NAME+".fine_exchange")
    hierarchy=importlib.import_module("framework.model.Quard_model."+NAME+".hier_postprocess")

    def clone(value):
        if torch.is_tensor(value):return value.detach().clone()
        if isinstance(value,tuple):return tuple(clone(x) for x in value)
        if isinstance(value,list):return [clone(x) for x in value]
        if isinstance(value,dict):return {k:clone(v) for k,v in value.items()}
        return value

    def maximum(a,b):return float((a-b).abs().max().detach().cpu())

    for pair_index,batch in enumerate(batches):
        assert remaining()>240
        observe()
        original_fingerprint=fingerprint(torch,batch)
        held={"calls":0}
        def capture_core(module,args,kwargs,value):
            held["calls"]+=1
            held.update(args=clone(args),kwargs=clone(kwargs),message=value["point"],x=args[0])
            value["point"].retain_grad();args[0].retain_grad()
        def capture_fine(module,args,value):
            held["fine"]=value;value.retain_grad()
        def capture_ila(module,args):held["ila"]=clone(args)
        def capture_decoder(module,args,value):held.update(decoder=clone(args),logits=clone(value[2]))
        hooks=[cluster.register_forward_hook(capture_core,with_kwargs=True),fine_module.register_forward_hook(capture_fine),
            active[0].ila.register_forward_pre_hook(capture_ila),model.dec.decoder_layers[-1].register_forward_hook(capture_decoder)]
        model.train();model.zero_grad(set_to_none=True);gorilla.set_random_seed(1999)
        torch.cuda.reset_peak_memory_stats()
        try:
            result["native_forwards"]+=1
            loss,losses=model(copy.deepcopy(batch),mode="loss")
            assert bool(torch.isfinite(loss)) and held["calls"]==1
            loss.backward();result["native_backwards"]+=1
            torch.cuda.synchronize()
            gradients={name:(None if p.grad is None else {"norm":float(p.grad.norm().detach().cpu()),"finite":bool(torch.isfinite(p.grad).all())}) for name,p in cluster.named_parameters()}
            legacy_dead={name:value for name,value in gradients.items() if name.startswith(("query_linear.","k_linear.","v_linear."))}
            used={name:value for name,value in gradients.items() if name not in legacy_dead}
            assert len(used)==18 and all(v is not None and v["finite"] and v["norm"]>0 for v in used.values()),used
            path_gradients={name:float(held[name].grad.norm().detach().cpu()) for name in ("fine","message","x")}
            assert all(math.isfinite(v) and v>0 for v in path_gradients.values())
            native_message=clone(held["message"])
            row={"pair":pair_index,"groups":MANIFEST["native_pairs"][pair_index],"scenes":list(batch["scan_ids"]),"ann_ids":list(batch["ann_ids"]),
                "expressions":len(batch["ann_ids"]),"input_sha256":original_fingerprint,"native_loss":float(loss.detach().cpu()),
                "loss_components":{k:float(v.detach().cpu()) for k,v in losses.items()},"point_path_gradients":path_gradients,
                "used_parameter_gradients":used,"legacy_dead_QKV":legacy_dead,"native_training_peak_bytes":torch.cuda.max_memory_allocated(),
                "removed_fine_trainable_tensors":6,"new_trainable_tensors":0}
        finally:
            for hook in hooks:hook.remove()
        model.zero_grad(set_to_none=True)
        del loss,losses
        for name in ("fine","message","x"):held.pop(name)
        assert fingerprint(torch,batch)==original_fingerprint,"Native input mutated"
        model.eval()
        with torch.no_grad():
            args=held["args"];kwargs=held["kwargs"]
            normal=cluster(*args,**kwargs)["point"]
            repeated=cluster(*args,**kwargs)["point"]
            controls={"native_replay_error":maximum(normal,native_message),"same_prefix_repeat_error":maximum(normal,repeated)}
            assert max(controls.values())<=1e-6,controls
            original_forward=fine_module.forward
            def uniform(features,padding,positions,fine_ids):
                output=torch.zeros_like(features)
                for b,ids in enumerate(fine_ids):
                    n=len(ids)
                    graph=operator.build_graph(positions[b,:n].detach().cpu().numpy(),ids.detach().cpu().numpy(),fine_module.k)
                    index=graph["indices"].to(features.device);allowed=graph["allowed"].to(features.device)
                    values=(features[b,:n][index]*allowed.unsqueeze(-1)).sum(1)/allowed.sum(1,keepdim=True)
                    if bool(graph["fallback"].any()):
                        groups=graph["group_ids"].to(features.device)
                        count=torch.bincount(groups).to(features.dtype).unsqueeze(-1)
                        means=features.new_zeros(len(count),features.shape[-1]).index_add(0,groups,features[b,:n])/count
                        values=torch.where(graph["fallback"].to(features.device).unsqueeze(-1),means[groups],values)
                    output[b,:n]=values
                return output
            try:
                fine_module.forward=uniform
                uniform_message=cluster(*args,**kwargs)["point"]
            finally:fine_module.forward=original_forward
            controls["normal_minus_uniform_message_max"]=maximum(normal,uniform_message)
            assert controls["normal_minus_uniform_message_max"]>0

            def suffix(message):
                ila_args=list(clone(held["ila"]))
                ila_args[1]=args[0]+torch.sigmoid(active[0].cluster_att_gate)*message
                feature=active[0].ila(*ila_args)[0]
                decoder=list(clone(held["decoder"]));decoder[2]=feature
                result["suffix_replays"]+=1
                return model.dec.decoder_layers[-1](*decoder)[2]
            native_logits=suffix(normal)
            uniform_logits=suffix(uniform_message)
            controls["native_suffix_logits_error"]=maximum(native_logits,held["logits"])
            controls["normal_minus_uniform_final_masks_max"]=maximum(native_logits,uniform_logits)
            assert controls["native_suffix_logits_error"]<=1e-6
            assert controls["normal_minus_uniform_final_masks_max"]>0
            row["controls"]=controls
        hierarchy.reset_orth_accum()
        row["after"]=observe()
        result["pairs"].append(row)
        del held,args,kwargs,normal,repeated,uniform_message,native_message,native_logits,uniform_logits
        torch.cuda.empty_cache()
    verify()
    assert result["native_forwards"]==result["native_backwards"]==2
    result.update(passed=True,removed_checkpoint_aliases=removed,independent_scenes=4,expressions=16,
        full_training_peak="unknown",trained_efficacy="unmeasured",material_novelty="unestablished",after=observe())
except BaseException as exc:
    result.update(error_type=type(exc).__name__,error=str(exc));raise
finally:
    save("native_result.json",result);release()
print("FLE_NATIVE_BACKWARD_AND_CONTROLS_PASS")
