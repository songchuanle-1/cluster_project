"""One frozen-row-order BatchNorm causal control with actual native cotangent."""
import copy
import json
from pathlib import Path
import numpy as np
from native_runtime import MANIFEST,STAGE,sha,save,fingerprint

held={}
handles=[]
def order(x):return np.lexsort(tuple(x[:,i] for i in reversed(range(x.shape[1]))))
def stats(x,y):
    d=np.abs(x.astype(np.float64)-y.astype(np.float64))
    return {'different':int(np.count_nonzero(x!=y)),'max_absolute':float(d.max(initial=0)),
        'mean_absolute':float(d.mean()) if d.size else 0.}

def attach(torch,model):
    bn=model.unet.u.blocks[0].conv_branch[0]
    assert type(bn).__name__=='BatchNorm1d' and bn.training and not model.norm_eval
    held['state']={k:v.detach().clone() for k,v in bn.state_dict().items()}
    held['flags']=[p.requires_grad for p in bn.parameters()]
    def sparse_hook(module,args,y):held['coords']=y.indices.detach().cpu().numpy().copy()
    def bn_hook(module,args,y):
        y.retain_grad()
        held['out']=y
        held['native_input']=args[0].detach().cpu().numpy().copy()
    handles.extend([model.unet.conv[2].register_forward_hook(sparse_hook),bn.register_forward_hook(bn_hook)])

def measure(torch,model):
    r={'passed':False,'operator_forwards':0,'operator_vjps':0,'zero_vjps':0,
        'production_modified':False,'optimizer_steps':0,'scheduler_steps':0}
    try:
        for h in handles:h.remove()
        handles.clear()
        bn=model.unet.u.blocks[0].conv_branch[0]
        native_grad=held['out'].grad.detach().cpu().numpy().copy()
        assert np.isfinite(native_grad).all() and np.any(native_grad!=0)
        canonical_grad=native_grad[order(held['coords'])]
        pairs=[]
        for source in MANIFEST['comparison_sources']:
            directory=Path(source['path'])
            for filename,digest in source['hashes'].items():assert sha(directory/filename)==digest
            events=json.loads((directory/'trace_events.json').read_text())['events']
            arrays=np.load(directory/'trace_arrays.npz',allow_pickle=False)
            ds=next(e for e in events if e['label']=='unet.conv.2' and e['phase']=='post')
            be=next(e for e in events if e['label']=='unet.u.blocks.block0.conv_branch.0' and e['phase']=='post')
            coords=arrays[ds['tensors']['x.indices']['raw_key']]
            permutation=order(coords)
            pairs.append({'coords':coords,'permutation':permutation,
                'input':arrays[ds['tensors']['x.features']['raw_key']],
                'output':arrays[be['tensors']['x']['raw_key']]})
        assert np.array_equal(pairs[0]['coords'][pairs[0]['permutation']],pairs[1]['coords'][pairs[1]['permutation']])
        assert np.array_equal(pairs[0]['coords'][pairs[0]['permutation']],held['coords'][order(held['coords'])])
        canonical=pairs[0]['input'][pairs[0]['permutation']]
        assert np.array_equal(canonical,pairs[1]['input'][pairs[1]['permutation']])
        original_grad=fingerprint(torch,[p.grad for p in bn.parameters()])
        outputs=[]
        gradients=[]
        for i,source_index in enumerate((0,0,1)):
            sample=pairs[source_index]
            permutation=sample['permutation']
            inverse=np.argsort(permutation)
            layer=copy.deepcopy(bn)
            layer._forward_hooks.clear()
            layer._forward_pre_hooks.clear()
            layer._backward_hooks.clear()
            layer.load_state_dict(held['state'],strict=True)
            assert [p.requires_grad for p in layer.parameters()]==held['flags']
            x=torch.from_numpy(canonical[inverse].copy()).cuda().requires_grad_(True)
            y=layer(x)
            r['operator_forwards']+=1
            g=torch.from_numpy(canonical_grad[inverse].copy()).to(y)
            parameters=tuple(p for p in layer.parameters() if p.requires_grad)
            gs=torch.autograd.grad(y,(x,*parameters),grad_outputs=g,retain_graph=i==2)
            r['operator_vjps']+=1
            assert all(bool(torch.isfinite(v).all()) for v in gs)
            outputs.append(y.detach().cpu().numpy().copy()[permutation])
            gradients.append([gs[0].detach().cpu().numpy().copy()[permutation],
                *[v.detach().cpu().numpy().copy() for v in gs[1:]]])
            if i==2:
                zeros=torch.autograd.grad(y,(x,*parameters),grad_outputs=torch.zeros_like(g))
                r['zero_vjps']+=1
                r['zero_cotangent_max']=[float(v.abs().max().cpu()) for v in zeros]
                assert all(v==0 for v in r['zero_cotangent_max'])
        r['native_A_reconstruction']=stats(outputs[0],pairs[0]['output'][pairs[0]['permutation']])
        r['native_B_reconstruction']=stats(outputs[2],pairs[1]['output'][pairs[1]['permutation']])
        r['exact_A_repeat_output']=stats(outputs[0],outputs[1])
        r['row_permutation_output']=stats(outputs[0],outputs[2])
        r['exact_A_repeat_vjps']=[stats(x,y) for x,y in zip(gradients[0],gradients[1])]
        r['row_permutation_vjps']=[stats(x,y) for x,y in zip(gradients[0],gradients[2])]
        r['original_gradients_unchanged']=fingerprint(torch,[p.grad for p in bn.parameters()])==original_grad
        assert r['original_gradients_unchanged']
        assert r['native_A_reconstruction']['max_absolute']<=1e-6 and r['native_B_reconstruction']['max_absolute']<=1e-6
        assert r['exact_A_repeat_output']['max_absolute']==0
        r['native_cotangent_sha256']=fingerprint(torch,torch.from_numpy(canonical_grad))
        r['native_cotangent_nonzero']=True
        r['native_current_input_vs_saved_A']=stats(held['native_input'][order(held['coords'])],canonical)
        r.update(passed=True,bn_training=bn.training,eps=bn.eps,momentum=bn.momentum,
            scope='fixedbatch row-order-only local control,not trainedvariance/CI,wholemodelcause or method efficacy')
    except BaseException as e:
        r.update(error_type=type(e).__name__,error=str(e))
        raise
    finally:
        save('bn_probe_result.json',r)
    return r
