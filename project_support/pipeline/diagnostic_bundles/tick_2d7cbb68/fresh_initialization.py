"""Native cold initialization test;no trained diagnostic heads or updates."""
import ast
import copy
from datetime import datetime,timezone
import shutil
from ops import *
owner=guard(450)
protocol={'preregistered_at':datetime.now(timezone.utc).isoformat(),'candidate_id':CID,
 'scope':'Same independent revision1,new native Network(seed1999) plus original backbone pretrain ONLY;production dataloaderbatch2/workers4,first4frozenTRAINscenes;AdamW/PolyLR constructed but never stepped',
 'pretrain_sha256':'a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f',
 'prediction':'Actual coarse attention weights and existing coarseFFN/norm receive finite nonzero native loss gradients from cold initialization. No task efficacy/diagnosis inference or M95head reuse.',
 'scientific_admission':False}
save('fresh_initialization_protocol.json',protocol)
prior=ast.parse((OUT/'package_isolated/native_package_isolated.py').read_text())
setup=next(n for n in prior.body if isinstance(n,ast.FunctionDef) and n.name=='setup_candidate_direct')
start=next(i for i,n in enumerate(setup.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='checkpoint')
end=next(i for i in range(start,len(setup.body)) if isinstance(setup.body[i],ast.Delete))
setup.body[start:end+1]=ast.parse("""assert cfg.train.pretrain=='/home/songcl/data/data/sp_unet_backbone.pth'
assert sha(cfg.train.pretrain)=='a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f'
gorilla.load_checkpoint(model,cfg.train.pretrain,strict=False,map_location='cpu')
meta={'epoch':0,'initialization':'new_native_network_and_backbone_only'}
""").body
ast.fix_missing_locations(setup)
worker='''import argparse,copy,gc,importlib,importlib.util,logging,sys
from pathlib import Path
from native_runtime import acquire,release,save,verify,observe,fingerprint,sha,MANIFEST,STAGE
'''+ast.unparse(setup)+'''
parser=argparse.ArgumentParser();parser.add_argument('--lease',required=True);args=parser.parse_args()
r={'execution_completed':False,'native_forwards':0,'native_backwards':0,'optimizer_steps':0,'scheduler_steps':0,'training_started':False,'records':[],'M95_head_reused':False,'scientific_admission':False}
try:
    r['before']=acquire(args.lease)
    torch,gorilla,cfg,model,meta=setup_candidate_direct()
    assert meta['epoch']==0
    flags=[p.requires_grad for p in model.parameters()]
    optimizer=gorilla.build_optimizer(model,cfg.optimizer)
    scheduler=gorilla.build_lr_scheduler(optimizer,cfg.lr_scheduler)
    scheduler_epoch=scheduler.last_epoch
    from framework.dataset import build_dataset,build_dataloader
    from torch.utils.data import Subset
    dataset=build_dataset(copy.deepcopy(cfg.data.train),logging.getLogger('coarse-fresh-native'))
    subset=Subset(dataset,[s['group_index'] for s in MANIFEST['cohort'][:4]])
    subset.collate_fn=dataset.collate_fn
    gorilla.set_random_seed(1999)
    loader=build_dataloader(subset,training=True,**copy.deepcopy(cfg.dataloader.train))
    assert loader.batch_size==2 and loader.num_workers==4 and loader.persistent_workers
    iterator=iter(loader)
    try:batches=list(iterator)
    finally:iterator._shutdown_workers()
    assert len(batches)==2
    hierarchy=importlib.import_module('framework.model.Quard_model.'+MANIFEST['candidate_name']+'.hier_postprocess')
    original_attention=hierarchy.coarse_readback
    held={}
    def capture(*values,**keywords):
        output,weights=original_attention(*values,**keywords)
        weights.retain_grad();held['weights']=weights
        return output,weights
    hierarchy.coarse_readback=capture
    for i,batch in enumerate(batches):
        model.train();model.zero_grad(set_to_none=True);gorilla.set_random_seed(1999)
        signature=fingerprint(torch,batch)
        held.clear()
        loss,components=model(copy.deepcopy(batch),mode='loss');r['native_forwards']+=1
        assert bool(torch.isfinite(loss))
        loss.backward();r['native_backwards']+=1
        weights=held['weights']
        assert weights.grad is not None and bool(torch.isfinite(weights.grad).all()) and bool((weights.grad!=0).any())
        grads={k:float(p.grad.norm().cpu()) if p.grad is not None else None for k,p in model.named_parameters() if k.startswith('dec.cluster_att.cluster_ffn.2.') or k.startswith('dec.cluster_att.cluster_ffn_norm.2.')}
        assert grads and all(v is not None and v>0 for v in grads.values())
        assert all(bool(torch.isfinite(p.grad).all()) for p in model.parameters() if p.grad is not None)
        r['records'].append({'batch':i,'input_sha256':signature,'loss':float(loss.detach().cpu()),'coarse_parameter_gradient_norms':grads,'actual_attention_gradient_norm':float(weights.grad.norm().cpu()),'orth_reg_loss':float(components['orth_reg_loss'].detach().cpu())})
        assert fingerprint(torch,batch)==signature
        model.zero_grad(set_to_none=True);del loss,components
    hierarchy.coarse_readback=original_attention
    assert [p.requires_grad for p in model.parameters()]==flags
    assert not optimizer.state and scheduler.last_epoch==scheduler_epoch
    verify()
    r.update(execution_completed=True,independent_scenes=4,expressions=16,batch_size=2,workers=4,optimizer_class=type(optimizer).__name__,scheduler_class=type(scheduler).__name__,optimizer_state_entries=0,pretrain_sha256=sha(cfg.train.pretrain),after=observe())
except BaseException as error:
    r.update(error_type=type(error).__name__,error=str(error));raise
finally:
    try:save('fresh_native_result.json',r)
    finally:release()
'''
label='fresh_native'
local=OUT/label
local.mkdir(exist_ok=False)
(local/'native_fresh.py').write_text(worker,encoding='utf-8')
info=tick.load(OUT/'independent_package.json');name=info['name']
shutil.copytree(Path(info['source_path']),local/name)
shutil.copyfile(ROOT/info['candidate_config']['path'],local/(name+'.yaml'))
shutil.copyfile(ROOT/'pipeline/diagnostic_bundles/tick_ce9bc689/trace_m95_1/native_runtime.py',local/'native_runtime.py')
manifest=copy.deepcopy(tick.load(OUT/'package_isolated/native_manifest.json'))
stage=STAGE+'/'+label
manifest.update(stage=stage,fresh_protocol=evidence(OUT/'fresh_initialization_protocol.json'))
manifest['diagnostic_files']={p.relative_to(local).as_posix():tick.digest(p) for p in local.rglob('*') if p.is_file()}
save(label+'/native_manifest.json',manifest)
save(label+'/execution_lease.json',{'project':'cluster_project','thread_id':THREAD,'token':TOKEN,'deadline_at':owner['deadline_at'],'native_manifest_sha256':tick.digest(local/'native_manifest.json')})
advance([OUT/'fresh_initialization_protocol.json',local/'native_manifest.json',local/'native_fresh.py'],next_action='Execute cold original-backbone initialization/native4worker gradients;retain unresolved semantic task diagnosis')
ssh('from pathlib import Path\nimport json\nPath('+repr(stage)+').mkdir(parents=True,exist_ok=False)\nprint(json.dumps({"created":True}))')
sc=run(['scp',*SSH,'-r',*[str(p) for p in local.iterdir()],'songcl@192.168.1.115:'+stage+'/'])
assert sc.returncode==0,sc.stderr
guard(350)
remaining=(datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds()
command='source /data/songcl/Project/Cluster_project/pipeline/runtime/server4_conda_4ca73fba.sh && conda activate project_cluster && python -B '+shlex.quote(stage+'/native_fresh.py')+' --lease '+shlex.quote(stage+'/execution_lease.json')
result=run(['ssh',*SSH,'songcl@192.168.1.115',shlex.join(['bash','-lc',command])],min(500,int(remaining)-150))
save('fresh_native_execution.json',{'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'finished_at':datetime.now(timezone.utc).isoformat()})
pull=run(['scp',*SSH,'songcl@192.168.1.115:'+stage+'/fresh_native_result.json',str(local/'fresh_native_result.json')])
assert pull.returncode==0,pull.stderr
value=tick.load(local/'fresh_native_result.json')
advance([local/'fresh_native_result.json',OUT/'fresh_native_execution.json'],gate_result='Cold native initialization test complete='+str(value.get('execution_completed'))+';diagnosis/admission/efficacy still unpassed')
print(json.dumps({k:v for k,v in value.items() if k not in ('before','after','records')},ensure_ascii=False))
