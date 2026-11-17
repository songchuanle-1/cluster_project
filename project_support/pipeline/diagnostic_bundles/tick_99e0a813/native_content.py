"""Scene-disjoint TRAIN content/magnitude controls, frozen model only."""
import os
os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID",CUDA_VISIBLE_DEVICES="0",PYTHONDONTWRITEBYTECODE="1",HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",TOKENIZERS_PARALLELISM="false",OMP_NUM_THREADS="1")
import copy
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib
import json
import logging
from pathlib import Path
import signal
import socket
import subprocess
import sys
from matched_control import permute_message

signal.alarm(900)
STAGE=Path(__file__).resolve().parent
manifest=json.loads((STAGE/"content_manifest.json").read_text())
deadline=datetime.fromisoformat(manifest["deadline_at"])
assert (deadline-datetime.now(timezone.utc)).total_seconds()>1020
assert socket.gethostname()=="dl04-MS-7E06"
ROOT=Path(manifest["root"])

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b""):h.update(block)
    return h.hexdigest()

def gpu():
    row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],text=True,timeout=10).strip()
    cells=[v.strip() for v in row.split(",")]
    assert cells[:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
    contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],text=True,timeout=10).strip()
    own=0
    for line in contexts.splitlines():
        pid,used=[int(v.strip()) for v in line.split(",")]
        assert pid==os.getpid(),"Foreign context;no eviction"
        own+=used
    assert int(cells[4])+own>=int(cells[2])-1024
    return {"gpu":row,"contexts":contexts}

before=gpu();assert not before["contexts"]
locks=[]
progress={"started_at":datetime.now(timezone.utc).isoformat(),"passed_controls":False,"native_forwards":0,"suffix_replays":0,"backwards":0,"optimizer_steps":0,"val_forwards":0,"rows":[],"controls":[]}
try:
    for kind in ("training","diagnostic","exclusive"):
        handle=open("/tmp/cluster_project_gpu0_"+kind+".lock","a+b")
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
    gpu()
    for name,expected in manifest["source_hashes"].items():assert sha(ROOT/name)==expected,name
    for name,expected in manifest["producer_hashes"].items():assert sha(STAGE/name)==expected,name
    assert sha(manifest["checkpoint"])==manifest["checkpoint_sha256"]
    assert sha(manifest["annotation_path"])==manifest["annotation_sha256"]
    assert sha(ROOT/"framework/dataset/scannetv2.py")==manifest["dataset_source_sha256"]
    sys.path[:0]=[str(ROOT),str(ROOT/"framework/lib")]
    from tools import train as native_train
    import torch,gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    torch.set_num_threads(1);torch.cuda.set_per_process_memory_fraction(.25,0)
    cfg=gorilla.Config.fromfile(str(ROOT/manifest["config"]))
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4 and cfg.data.train.lang_num_max==4
    cfg.model.data_root=cfg.data.train.data_root="/home/songcl/data/data/"
    gorilla.set_random_seed(1999)
    package="framework.model.Quard_model."+manifest["model"]
    native=importlib.import_module(package+".network")
    model=native.Network(**cfg.model)
    state=torch.load(manifest["checkpoint"],map_location="cpu")["model"]
    extra=set(state)-set(model.state_dict())
    assert extra<={"text_encoder.embeddings.position_ids","text_encoder.embeddings.token_type_ids"}
    assert all(torch.equal(state[name],dict(model.named_buffers())[name]) for name in extra)
    model.load_state_dict({name:value for name,value in state.items() if name not in extra},strict=True);del state
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger("matched-content"))
    for selected in manifest["selected"]:
        group=dataset.scene_inputs[selected["group"]]
        identities=[{"split":"train","scene_id":r["scene_id"],"object_ids":[int(r["object_id"])],"ann_id":int(r["ann_id"])} for r in group]
        assert identities==selected["identities"]
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[s["group"] for s in manifest["selected"]]),batch_size=1,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    inputs=list(loader);assert len(inputs)==8
    model.cuda().eval();torch.cuda.reset_peak_memory_stats()
    active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active)==1 and active[0].cluster_message_type=="context"
    cluster=model.dec.cluster_att

    def clone(value):
        if torch.is_tensor(value):return value.detach().clone()
        if isinstance(value,tuple):return tuple(clone(v) for v in value)
        if isinstance(value,list):return [clone(v) for v in value]
        return value

    def error(a,b):return float((a-b).abs().max().detach().cpu())

    def capture(batch):
        held={"cluster_calls":0}
        def point(module,args,result):
            held["cluster_calls"]+=1
            held.update(x=clone(args[0]),padding=clone(args[2]),message=clone(result["point"]))
        def ila(module,args):held["ila_args"]=clone(args)
        def decoder(module,args):held["decoder_args"]=clone(args)
        def head(module,args,result):held.update(q=module.out_norm(result[0]).detach().clone(),f=clone(args[2]),logits=clone(result[2]),indis=clone(result[3]))
        hooks=[cluster.register_forward_hook(point),active[0].ila.register_forward_pre_hook(ila),model.dec.decoder_layers[-1].register_forward_pre_hook(decoder),model.dec.decoder_layers[-1].register_forward_hook(head)]
        try:
            gorilla.set_random_seed(1999)
            with torch.no_grad():
                progress["native_forwards"]+=1
                held["prediction"]=model(copy.deepcopy(batch),mode="predict")
        finally:
            for hook in hooks:hook.remove()
        assert held["cluster_calls"]==1
        held["injection_error"]=error(held["ila_args"][1],held["x"]+torch.sigmoid(active[0].cluster_att_gate)*held["message"])
        assert held["injection_error"]<=1e-6
        return held

    @torch.no_grad()
    def replay(prefix,message):
        args=list(clone(prefix["ila_args"]))
        args[1]=prefix["x"]+torch.sigmoid(active[0].cluster_att_gate)*message
        feature=active[0].ila(*args)[0]
        decoder_args=list(clone(prefix["decoder_args"]));decoder_args[2]=feature
        progress["suffix_replays"]+=1
        result=model.dec.decoder_layers[-1](*decoder_args)
        query=model.dec.decoder_layers[-1].out_norm(result[0])
        rebuilt=torch.einsum("bnd,bmd->bnm",query,feature)
        maximum=error(rebuilt,result[2]);assert maximum<=1e-6
        return query,feature,result[2],torch.softmax(result[3],-1)[...,1].argmax(-1),maximum

    def readout(logits,gt):
        assert bool(torch.isfinite(logits).all())
        return {"point_iou":float(native.get_iou(logits,gt).detach().cpu()),"point_bce":float(torch.nn.functional.binary_cross_entropy_with_logits(logits,gt).detach().cpu())}

    for selected,batch in zip(manifest["selected"],inputs):
        assert (deadline-datetime.now(timezone.utc)).total_seconds()>120
        gpu();prefix=capture(batch)
        identity,identity_check=permute_message(torch,prefix["message"],prefix["padding"],identity=True)
        assert torch.equal(identity,prefix["message"])
        shuffled,norm_check=permute_message(torch,prefix["message"],prefix["padding"])
        with torch.no_grad():
            empty=cluster.point_out_proj(cluster.dropout(torch.zeros_like(prefix["x"])))
            empty=empty.masked_fill(prefix["padding"].unsqueeze(-1),0)
            empty=cluster.message_norm(empty).masked_fill(prefix["padding"].unsqueeze(-1),0)
        messages={"native":identity,"true_zero":torch.zeros_like(identity),"bias_retained_empty":empty,"permuted_norm_matched":shuffled}
        selection=torch.softmax(prefix["indis"],-1)[...,1].argmax(-1)
        sp=batch["superpoints"].cuda().long()
        rows=[]
        for i,expected in enumerate(selected["identities"]):
            obj=batch["object_idss"][i]
            if torch.is_tensor(obj):obj=obj.detach().cpu().reshape(-1).tolist()
            if not isinstance(obj,(list,tuple)):obj=[obj]
            actual={"split":"train","scene_id":str(batch["scan_ids"][0]),"object_ids":[int(v) for v in obj],"ann_id":int(batch["ann_ids"][i])}
            assert actual==expected,(actual,expected)
            rows.append({**actual,"group":selected["group"],"normal_query_index":int(selection[i]),"conditions":{}})
        native_errors=None;head_error=0.0
        for condition,message in messages.items():
            q,f,logits,own_selection,maximum=replay(prefix,message)
            head_error=max(head_error,maximum)
            with torch.no_grad():fixed_query=torch.einsum("bnd,bmd->bnm",prefix["q"],f)
            if condition=="native":
                native_errors={key:error(a,b) for key,a,b in (("q",q,prefix["q"]),("f",f,prefix["f"]),("logits",logits,prefix["logits"]))}
                assert max(native_errors.values())<=1e-6,native_errors
            for i,row in enumerate(rows):
                gt=batch["gt_pmasks"][i].cuda().float();normal=int(selection[i]);own=int(own_selection[i])
                values={"fixed_query_point":readout(fixed_query[i,normal][sp],gt),"joint_fixed_selection":readout(logits[i,normal][sp],gt),"joint_own_selection":readout(logits[i,own][sp],gt),"own_query_index":own}
                if condition=="native":assert abs(values["fixed_query_point"]["point_iou"]-float(prefix["prediction"]["piou"][i]))<=1e-6
                row["conditions"][condition]=values
            del q,f,logits,fixed_query
        progress["rows"].extend(rows)
        progress["controls"].append({"scene_id":selected["scene_id"],"group":selected["group"],"native_suffix_max_errors":native_errors,"injection_error":prefix["injection_error"],"head_error":head_error,"identity_control":identity_check,"norm_control":norm_check,"same_captured_proposals_and_fps":True,"native_message_norm":float(identity.norm().cpu()),"empty_message_norm":float(empty.norm().cpu())})
        del prefix,messages,identity,shuffled,empty
    rows=progress["rows"]
    assert len(rows)==sum(len(s["identities"]) for s in manifest["selected"])
    keys=[(r["split"],r["scene_id"],tuple(r["object_ids"]),r["ann_id"]) for r in rows]
    assert len(set(keys))==len(keys)
    scenes=sorted({r["scene_id"] for r in rows});assert len(scenes)==8
    scene_means={s:sum(r["conditions"]["native"]["fixed_query_point"]["point_iou"]-r["conditions"]["permuted_norm_matched"]["fixed_query_point"]["point_iou"] for r in rows if r["scene_id"]==s)/sum(r["scene_id"]==s for r in rows) for s in scenes}
    mean=sum(scene_means.values())/8
    for name,expected in manifest["source_hashes"].items():assert sha(ROOT/name)==expected,name
    assert sha(manifest["checkpoint"])==manifest["checkpoint_sha256"]
    assert progress["native_forwards"]==8 and progress["suffix_replays"]==32
    progress.update(observed_at=datetime.now(timezone.utc).isoformat(),passed_controls=True,checkpoint_sha256=manifest["checkpoint_sha256"],expressions=len(rows),independent_scenes=8,scene_native_minus_permuted_fixed_query_iou=scene_means,mean_scene_native_minus_permuted_fixed_query_iou=mean,local_aligned_content_premise_supported=mean>0,peak_diagnostic_allocated_bytes=torch.cuda.max_memory_allocated(),last_resources=gpu(),scope="8scene-disjoint TRAIN groups,outcome-blind selection,same-prefix off-distribution counterfactuals; not retrained ablations,VAL improvement,generalization,independent whole-network repeats or admission.")
    (STAGE/"content_result.json").write_text(json.dumps(progress,indent=2,allow_nan=False))
    print("CONTENT_NATIVE_PASS",flush=True)
except BaseException as error:
    progress.update(failed_at=datetime.now(timezone.utc).isoformat(),error_type=type(error).__name__,error=str(error),passed_controls=False)
    (STAGE/"content_result.json").write_text(json.dumps(progress,indent=2,allow_nan=False))
    raise
finally:
    for handle in reversed(locks):handle.close()
