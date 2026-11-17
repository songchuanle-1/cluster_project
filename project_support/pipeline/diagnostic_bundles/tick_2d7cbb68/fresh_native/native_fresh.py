import argparse,copy,gc,importlib,importlib.util,logging,sys
from pathlib import Path
from native_runtime import acquire,release,save,verify,observe,fingerprint,sha,MANIFEST,STAGE
def setup_candidate_direct():
    import torch, gorilla
    import importlib.util
    sys.path[:0] = [MANIFEST['root'], str(Path(MANIFEST['root']) / 'framework/lib')]
    from tools import train
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    torch.cuda.set_per_process_memory_fraction(0.75, 0)
    importlib.import_module('framework.model.Quard_model')
    name = MANIFEST['candidate_name']
    qualified = 'framework.model.Quard_model.' + name
    path = STAGE / name
    spec = importlib.util.spec_from_file_location(qualified, path / '__init__.py', submodule_search_locations=[str(path)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)
    cfg = gorilla.Config.fromfile(str(STAGE / (name + '.yaml')))
    assert cfg.train.seed == 1999 and cfg.train.epochs == 50 and (cfg.lr_scheduler.max_iters == 70)
    assert cfg.dataloader.train.batch_size == 2 and cfg.dataloader.train.num_workers == 4
    gorilla.set_random_seed(1999)
    model = module.Network(**cfg.model)
    assert cfg.train.pretrain == '/home/songcl/data/data/sp_unet_backbone.pth'
    assert sha(cfg.train.pretrain) == 'a6f400bcf9bd722230d16ea7c3424b0d7658730126df604f67b4cccf42e25c1f'
    gorilla.load_checkpoint(model, cfg.train.pretrain, strict=False, map_location='cpu')
    meta = {'epoch': 0, 'initialization': 'new_native_network_and_backbone_only'}
    model.cuda().eval()
    return (torch, gorilla, cfg, model, meta)
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
