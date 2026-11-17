"""Fixed TRAIN trained-message intervention and fixed-query cross readouts."""
import os
os.environ.update(CUDA_DEVICE_ORDER="PCI_BUS_ID",CUDA_VISIBLE_DEVICES="0",PYTHONDONTWRITEBYTECODE="1",
                  HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",TOKENIZERS_PARALLELISM="false",OMP_NUM_THREADS="1")
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

signal.alarm(600)
STAGE=Path(__file__).resolve().parent
manifest=json.loads((STAGE/"trained_feature_manifest.json").read_text())
deadline=datetime.fromisoformat(manifest["deadline_at"])
assert (deadline-datetime.now(timezone.utc)).total_seconds()>720
assert socket.gethostname()=="dl04-MS-7E06"
ROOT=Path(manifest["root"])
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()
def gpu():
    row=subprocess.check_output(['nvidia-smi','-i','0','--query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    cells=[c.strip() for c in row.split(',')]
    assert cells[:2]==['0','GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c']
    contexts=subprocess.check_output(['nvidia-smi','-i','0','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits'],text=True,timeout=10).strip()
    own=0
    for line in contexts.splitlines():
        pid,used=[int(value.strip()) for value in line.split(',')]
        assert pid==os.getpid(),'Other GPU context;no overlap or eviction'
        own+=used
    assert int(cells[4])+own>=int(cells[2])-1024
    return {'gpu':row,'contexts':contexts}
before=gpu();assert not before['contexts']
locks=[]
try:
    for kind in ('training','diagnostic','exclusive'):
        handle=open('/tmp/cluster_project_gpu0_'+kind+'.lock','a+b')
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(handle)
    gpu()
    for relative,expected in manifest['source_hashes'].items():assert sha(ROOT/relative)==expected,relative
    for name,expected in manifest['producer_hashes'].items():assert sha(STAGE/name)==expected,name
    assert sha(manifest['checkpoint'])==manifest['checkpoint_sha256']
    sys.path[:0]=[str(ROOT),str(ROOT/'framework/lib')]
    from tools import train as native_train
    import torch,gorilla
    from framework.dataset import build_dataset
    from torch.utils.data import DataLoader,Subset
    from aligned_evidence import export_prediction
    torch.set_num_threads(1);torch.cuda.set_per_process_memory_fraction(.25,0)
    cfg=gorilla.Config.fromfile(str(ROOT/manifest['config']))
    assert cfg.train.seed==1999 and cfg.train.epochs==50 and cfg.lr_scheduler.max_iters==70
    assert cfg.dataloader.train.batch_size==2 and cfg.dataloader.train.num_workers==4
    cfg.model.data_root=cfg.data.train.data_root='/home/songcl/data/data/'
    gorilla.set_random_seed(1999)
    package='framework.model.Quard_model.'+manifest['model']
    native=importlib.import_module(package+'.network')
    model=native.Network(**cfg.model)
    state=torch.load(manifest['checkpoint'],map_location='cpu')['model']
    extra=set(state)-set(model.state_dict())
    assert extra<={'text_encoder.embeddings.position_ids','text_encoder.embeddings.token_type_ids'}
    assert all(torch.equal(state[name],dict(model.named_buffers())[name]) for name in extra)
    model.load_state_dict({name:value for name,value in state.items() if name not in extra},strict=True);del state
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('trained-point-feature'))
    gorilla.set_random_seed(1999)
    loader=DataLoader(Subset(dataset,[0,60,101,124]),batch_size=1,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn)
    inputs=list(loader);assert len(inputs)==4
    model.cuda().eval();torch.cuda.reset_peak_memory_stats()
    active=[layer for layer in model.dec.encoder_layers if layer.use_cluster]
    assert len(active)==1 and active[0].cluster_message_type=='context'
    gate=float(torch.sigmoid(active[0].cluster_att_gate).detach().cpu())
    def capture(batch,zero=False):
        held={'cluster_calls':0}
        def point_hook(module,args,result):
            held['cluster_calls']+=1
            message=result['point']
            actual=torch.zeros_like(message) if zero else message
            held['message_before_norm']=float(message.norm().detach().cpu())
            held['message_after_norm']=float(actual.norm().detach().cpu())
            if zero:
                changed=dict(result);changed['point']=actual;return changed
        def head_hook(module,args,result):
            held.update(q=module.out_norm(result[0]).detach().clone(),f=args[2].detach().clone(),
                        mask=args[3].detach().clone(),logits=result[2].detach().clone(),indis=result[3].detach().clone())
        hooks=[model.dec.cluster_att.register_forward_hook(point_hook),model.dec.decoder_layers[-1].register_forward_hook(head_hook)]
        try:
            gorilla.set_random_seed(1999)
            with torch.no_grad():prediction=model(copy.deepcopy(batch),mode='predict')
        finally:
            for hook in hooks:hook.remove()
        assert held['cluster_calls']==1
        if zero:assert held['message_after_norm']==0
        held['prediction']=prediction
        for value in (held['q'],held['f'],held['logits']):assert torch.isfinite(value).all()
        return held
    def maximum(left,right):return float((left-right).abs().max().detach().cpu())
    rows=[];controls=[]
    for group,batch in zip([0,60,101,124],inputs):
        assert (deadline-datetime.now(timezone.utc)).total_seconds()>90;gpu()
        on=capture(batch);repeat=capture(batch);off=capture(batch,zero=True)
        repeat_errors={name:maximum(on[name],repeat[name]) for name in ('q','f','logits')}
        assert max(repeat_errors.values())<=1e-6,repeat_errors
        assert torch.equal(on['mask'],off['mask'])
        for field in ('seed_ind','sample_ind'):
            assert len(on['prediction'][field])==len(off['prediction'][field])
            assert all(torch.equal(a,b) for a,b in zip(on['prediction'][field],off['prediction'][field]))
        logits={label:torch.einsum('bnd,bmd->bnm',q,f) for label,q,f in
                (('on_on',on['q'],on['f']),('on_off',on['q'],off['f']),
                 ('off_on',off['q'],on['f']),('off_off',off['q'],off['f']))}
        head_error=max(maximum(logits['on_on'],on['logits']),maximum(logits['off_off'],off['logits']))
        assert head_error<=1e-6,head_error
        exported,_=export_prediction(on['prediction'],batch,'train')
        selection=torch.softmax(on['indis'],dim=-1)[...,1].argmax(-1)
        off_selection=torch.softmax(off['indis'],dim=-1)[...,1].argmax(-1)
        sp=batch['superpoints'].cuda().long()
        for i,identity in enumerate(exported):
            selected=int(selection[i]);gt=batch['gt_pmasks'][i].cuda().float()
            values={}
            for condition,mask in logits.items():
                point_logits=mask[i,selected][sp]
                values[condition]={'point_iou':float(native.get_iou(point_logits,gt).detach().cpu()),
                                  'point_bce':float(torch.nn.functional.binary_cross_entropy_with_logits(point_logits,gt).detach().cpu())}
            assert abs(values['on_on']['point_iou']-identity['piou'])<=1e-6
            assert abs(identity['piou']-float(repeat['prediction']['piou'][i]))<=1e-6
            native_off=float(off['prediction']['piou'][i])
            rebuilt_off=float(native.get_iou(logits['off_off'][i,int(off_selection[i])][sp],gt).detach().cpu())
            assert abs(native_off-rebuilt_off)<=1e-6
            rows.append({**identity,'group':group,'selected_query_on':selected,'selected_query_off':int(off_selection[i]),
                         'readouts':values,'native_off_own_selection_iou':native_off,
                         'fixed_query_point_feature_delta':values['on_on']['point_iou']-values['on_off']['point_iou'],
                         'query_change_norm':float((on['q'][i]-off['q'][i]).norm().detach().cpu()),
                         'feature_change_norm':float((on['f'][i]-off['f'][i]).norm().detach().cpu())})
        controls.append({'group':group,'repeat_max_errors':repeat_errors,'head_reconstruction_max_error':head_error,
                         'expressions':len(exported),'zero_message_norm':off['message_after_norm'],
                         'normal_message_norm':on['message_after_norm'],'unchanged_fps_and_proposal_ids':True})
        del on,repeat,off,logits
    assert len(rows)==16 and len({row['scene_id'] for row in rows})==4
    scene_means={scene:sum(row['fixed_query_point_feature_delta'] for row in rows if row['scene_id']==scene)/sum(row['scene_id']==scene for row in rows)
                 for scene in sorted({row['scene_id'] for row in rows})}
    mean=sum(row['fixed_query_point_feature_delta'] for row in rows)/len(rows)
    assert sha(manifest['checkpoint'])==manifest['checkpoint_sha256']
    for relative,expected in manifest['source_hashes'].items():assert sha(ROOT/relative)==expected,relative
    result={'passed_controls':True,'observed_at':datetime.now(timezone.utc).isoformat(),'checkpoint_sha256':manifest['checkpoint_sha256'],
            'train_groups':[0,60,101,124],'expressions':16,'independent_scenes':4,'native_forwards':12,'optimizer_steps':0,
            'learned_original_gate':gate,'native_controls':controls,'rows':rows,
            'mean_fixed_query_point_feature_iou_delta':mean,'scene_means':scene_means,
            'local_preregistered_hypothesis_supported':mean>0,'peak_diagnostic_allocated_bytes':torch.cuda.max_memory_allocated(),
            'last_resources':gpu(),'scope':'Fixed4TRAINscene trained-network counterfactual only; no retraining,population efficacy,new mechanism selection,gate tuning or revision3. Counterfactual may be off distribution.'}
    (STAGE/'trained_feature_result.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print('TRAINED_FEATURE_RESULT='+json.dumps({key:result[key] for key in ('passed_controls','expressions','independent_scenes','native_forwards','mean_fixed_query_point_feature_iou_delta','scene_means','local_preregistered_hypothesis_supported')}),flush=True)
finally:
    for handle in reversed(locks):handle.close()
