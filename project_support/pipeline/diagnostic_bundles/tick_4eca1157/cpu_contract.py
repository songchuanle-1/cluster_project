"""Actual trained gate weights, exactsource CPU contract/derivative fixtures."""
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace, MethodType
import torch
from padding_contract import build, sha

ROOT = Path(__file__).resolve().parent
models = json.loads((ROOT/'models.json').read_text())
r = {'passed': False, 'models': [], 'synthetic_cpu_backwards': 0, 'native_backwards': 0,
     'optimizer_steps': 0, 'scope': 'synthetic exactsource/trainedweights CPU contract,not nativeadmission'}
try:
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(1)
    for tag, manifest in models.items():
        assets = manifest['assets']
        source = Path(manifest['root'])/'framework/model/Quard_model'/manifest['name']/'hier_postprocess.py'
        original, reference, binding = build(source, assets['source_hashes']['hier_postprocess.py'], torch)
        assert sha(assets['checkpoint']) == assets['checkpoint_sha256']
        checkpoint = torch.load(assets['checkpoint'], map_location='cpu', weights_only=False, mmap=True)
        assert checkpoint['meta']['epoch'] == manifest['expected_epoch']
        state = checkpoint['model']
        prefix = 'dec.cluster_att.'
        gate = torch.nn.Linear(512, 3).double()
        projection = torch.nn.Linear(256, 256).double()
        for name, module in [('level_gate', gate), ('point_out_proj', projection)]:
            module.load_state_dict({key: state[prefix+name+'.'+key].double() for key in ('weight', 'bias')}, strict=True)
        model = SimpleNamespace(num_scales=3, level_gate=gate, point_out_proj=projection, dropout=torch.nn.Identity())
        old, new = MethodType(original, model), MethodType(reference, model)
        fine_argument = 'fine_message' in original.__code__.co_varnames[:original.__code__.co_argcount]
        torch.manual_seed(1999)
        features = torch.randn(1, 6, 256, dtype=torch.float64)
        base_tokens = [torch.randn(1, n, 256, dtype=torch.float64) for n in (2, 1, 1)]
        fine = torch.randn_like(features)
        cases = []
        for case, valid_count, zero in [('general',4,False),('no_padding',6,False),('all_masked',0,False),('zero_scale',4,True)]:
            mask = torch.arange(6).view(1,6) >= valid_count
            ids = [[torch.tensor(([0,0,1,1,0,1])[:valid_count], dtype=torch.long)],
                   [torch.tensor([0,0])], [torch.tensor([0])]]
            tokens = [torch.zeros_like(t) for t in base_tokens] if zero else base_tokens
            f = torch.zeros_like(fine) if zero else fine
            kw = {'fine_message': f} if fine_argument else {}
            x = features.clone().requires_grad_(True)
            output = new(x,tokens,ids,mask,**kw)
            loss = output.square().mean()
            grad, = torch.autograd.grad(loss,x)
            r['synthetic_cpu_backwards'] += 1
            assert bool(torch.isfinite(output).all()) and bool(torch.isfinite(grad).all())
            masked = float(grad[mask].abs().max()) if bool(mask.any()) else 0.
            valid = float(grad[~mask].abs().max()) if bool((~mask).any()) else 0.
            assert masked <= 1e-12
            if zero or valid_count == 0: assert valid <= 1e-12
            else: assert valid > 1e-12
            changed = torch.where(mask.unsqueeze(-1), torch.ones_like(x), x.detach())
            invariant = float((new(changed,tokens,ids,mask,**kw)-output.detach()).abs().max())
            assert invariant <= 1e-12
            append = torch.cat([x.detach(), x.new_zeros(1,3,256)],1)
            append_mask = torch.cat([mask,torch.ones(1,3,dtype=torch.bool)],1)
            append_kw = {'fine_message':torch.cat([f,f.new_zeros(1,3,256)],1)} if fine_argument else {}
            appended = new(append,tokens,ids,append_mask,**append_kw)
            append_error = float((appended[:,:6]-output.detach()).abs().max())
            assert append_error <= 1e-12
            identity_output = identity_grad = None
            if case == 'no_padding':
                y = features.clone().requires_grad_(True)
                old_output = old(y,tokens,ids,mask,**kw)
                old_grad, = torch.autograd.grad(old_output.square().mean(),y)
                r['synthetic_cpu_backwards'] += 1
                identity_output = float((old_output-output.detach()).abs().max())
                identity_grad = float((old_grad-grad).abs().max())
                assert max(identity_output,identity_grad) <= 1e-12
            direction = torch.randn_like(x)
            direction = direction/direction.norm()
            step = 1e-5
            plus = new(x.detach()+step*direction,tokens,ids,mask,**kw).square().mean()
            minus = new(x.detach()-step*direction,tokens,ids,mask,**kw).square().mean()
            fd = float((plus-minus)/(2*step))
            analytic = float((grad*direction).sum())
            fd_error = abs(fd-analytic)
            assert fd_error <= 1e-8+1e-5*abs(analytic)
            cases.append({'case':case,'masked_gradient_max':masked,'valid_gradient_max':valid,
                'masked_value_invariance_error':invariant,'append_invariance_error':append_error,
                'no_padding_output_error':identity_output,'no_padding_gradient_error':identity_grad,
                'directional_finite_difference_error':fd_error})
        r['models'].append({'tag':tag,'epoch':manifest['expected_epoch'],'binding':binding,'cases':cases})
        del checkpoint,state
    r.update(passed=True,cuda_initialized=torch.cuda.is_initialized())
except BaseException as e:
    r.update(error_type=type(e).__name__,error=str(e))
    raise
finally:
    r['observed_at'] = datetime.now(timezone.utc).isoformat()
    with (ROOT/'cpu_contract_result.json').open('x') as stream: json.dump(r,stream,indent=2,allow_nan=False)
    print(json.dumps({'passed':r['passed'],'models':r['models'],'synthetic_cpu_backwards':r['synthetic_cpu_backwards'],
                      'error':r.get('error')}))
