"""Exact enumeration and numerical tests for BCA; no production registry."""
import importlib.util
import itertools
import json
import sys
import torch
spec=importlib.util.spec_from_file_location("bca",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
torch.set_num_threads(1)
checks=[]
for device in ["cpu"]+(["cuda"] if torch.cuda.is_available() else []):
    for n in range(2,8):
        for k in range(1,n):
            z=torch.linspace(-2,3,n,device=device,dtype=torch.double).requires_grad_()
            y=torch.arange(n,device=device)<k
            scores=torch.stack([z[list(s)].sum() for s in itertools.combinations(range(n),k)])
            exact=(torch.logsumexp(scores,0)-z[y].sum())/n
            loss=m.conditional_assignment(z,y)
            torch.testing.assert_close(loss,exact)
            g=torch.autograd.grad(loss,z,retain_graph=True)[0]
            ge=torch.autograd.grad(exact,z)[0]
            torch.testing.assert_close(g,ge)
            assert abs(float(g.sum()))<1e-10
            torch.testing.assert_close(m.conditional_assignment(z+100,y),loss)
            torch.testing.assert_close(m.conditional_assignment(-z,~y),loss)
            torch.testing.assert_close(m.conditional_assignment(z.flip(0),y.flip(0)),loss)
    z=torch.randn(2,5,device=device,dtype=torch.double,requires_grad=True)
    y=torch.tensor([1,0,1,0,1],device=device,dtype=torch.bool)
    assert torch.autograd.gradcheck(lambda v:m.conditional_assignment(v,y),(z,))
    for dtype in ([torch.bfloat16] if device=="cpu" else [torch.float16,torch.bfloat16]):
        z=torch.tensor([[1000.,-1000.,500.,-500.]],device=device,dtype=dtype,requires_grad=True)
        with torch.autocast(device,dtype=dtype):
            loss=m.conditional_assignment(z,torch.tensor([0,1,0,1],device=device)).sum()
        assert loss.dtype==torch.float32 and torch.isfinite(loss)
        assert torch.isfinite(torch.autograd.grad(loss,z)[0]).all()
    empty=torch.zeros(2,0,device=device,requires_grad=True)
    zero=m.conditional_assignment(empty,torch.empty(0,device=device,dtype=torch.bool))
    assert zero.sum()==0
    assert torch.autograd.grad(zero.sum(),empty)[0].numel()==0
    checks.append(dict(device=device,enumeration=True,gradcheck=True,invariances=True,amp_extremes=True,empty=True))
print(json.dumps(dict(status="PASS",checks=checks),indent=2))
