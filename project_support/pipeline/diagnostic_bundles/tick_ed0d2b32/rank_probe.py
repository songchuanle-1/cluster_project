"""Capture one actual native point-message cotangent and exact-prefix control."""
import numpy as np
from native_runtime import STAGE,save,fingerprint
held={}
handles=[]
def attach(torch,model):
    cluster=model.dec.cluster_att
    assert cluster.num_scales==3 and cluster.dropout.p==0
    held['original']=cluster._cluster_to_points
    held['parameter_flags']=[p.requires_grad for p in model.parameters()]
    def gather(*args,**kwargs):
        assert not kwargs
        held['args']=args
        return held['original'](*args,**kwargs)
    cluster._cluster_to_points=gather
    def post(module,args,out):
        y=out['point']
        y.retain_grad()
        held['message']=y
    handles.append(cluster.register_forward_hook(post))

def finish(torch,model):
    cluster=model.dec.cluster_att
    cluster._cluster_to_points=held['original']
    for h in handles:h.remove()
    handles.clear()
    x,tokens,ids,mask=held['args']
    y=held['message']
    assert y.grad is not None and bool(torch.isfinite(y.grad).all())
    flags=[p.requires_grad for p in model.parameters()]
    before=fingerprint(torch,[p.grad for p in cluster.parameters()])
    replay_args=(x.detach().requires_grad_(x.requires_grad),[t.detach().requires_grad_(t.requires_grad) for t in tokens],ids,mask)
    replay=cluster.message_norm(held['original'](*replay_args)).masked_fill(mask.unsqueeze(-1),0)
    error=float((replay-y.detach()).abs().max().cpu())
    result={'passed':False,'native_replay_max_absolute':error,'native_tolerance':1e-6,
        'parameter_flags_preserved':flags==held['parameter_flags'],'full_shape_replays':1,
        'native_readout_cotangent_nonzero':bool((y.grad!=0).any()),'new_training':False,'new_VAL':False}
    try:
        assert error<=1e-6 and result['parameter_flags_preserved'] and result['native_readout_cotangent_nonzero']
        controls=[]
        for b in range(x.shape[0]):
            valid=int((~mask[b]).sum().cpu())
            for index in (0,valid//2,valid-1):
                coarse_id=int(ids[0][b][index].cpu())
                for level in range(1,len(ids)):coarse_id=int(ids[level][b][coarse_id].cpu())
                g=y.grad[b,index].detach()
                if not bool((g!=0).any()):
                    controls.append({'batch':b,'point':index,'cotangent':'UNKNOWN zero nativegradient'})
                    continue
                token_gradient=torch.autograd.grad(replay[b,index],replay_args[1][-1],grad_outputs=g,retain_graph=True)[0]
                own=float(token_gradient[b,coarse_id].norm().cpu())
                remote=token_gradient[b].detach().clone()
                remote[coarse_id]=0
                remote_max=float(remote.abs().max().cpu())
                assert own>0 and remote_max==0
                controls.append({'batch':b,'point':index,'coarse_id':coarse_id,'own_gradient_norm':own,'remote_gradient_max':remote_max})
        result['native_token_vjp_controls']=controls
        result['native_token_vjps']=sum('own_gradient_norm' in c for c in controls)
        raw={'points':x.detach().cpu().numpy().copy(),'mask':mask.cpu().numpy().copy(),
            'message':y.detach().cpu().numpy().copy(),'native_cotangent':y.grad.detach().cpu().numpy().copy()}
        for i,t in enumerate(tokens):raw['tokens_'+str(i)]=t.detach().cpu().numpy().copy()
        for i,level in enumerate(ids):
            for b,item in enumerate(level):raw['ids_'+str(i)+'_'+str(b)]=item.detach().cpu().numpy().copy()
        for name,module in [('level_gate',cluster.level_gate),('point_out_proj',cluster.point_out_proj),('message_norm',cluster.message_norm)]:
            for key,value in module.state_dict().items():raw[name+'_'+key]=value.detach().cpu().numpy().copy()
        raw['message_norm_eps']=np.array(cluster.message_norm.eps,dtype=np.float64)
        assert not (STAGE/'rank_prefix.npz').exists()
        np.savez_compressed(STAGE/'rank_prefix.npz',**raw)
        assert fingerprint(torch,[p.grad for p in cluster.parameters()])==before
        result.update(passed=True,batch_expressions=int(x.shape[0]),scene_count=2,readouts_per_expression=3,
            original_parameter_gradients_unchanged=True,scope='one native conditionalmodule diagnosis;not whole-network rank,efficacy or novelty')
    finally:save('native_rank_capture_result.json',result)
    return result
