"""CPU integration contracts on the authorized host, not native backward."""
import importlib.util
import numpy as np
from runtime import STAGE, NAME, acquire, release, save

before = acquire()
result = {"passed": False, "cuda_initialized": False, "checks": []}
try:
    import torch
    torch.set_num_threads(1); torch.manual_seed(1999)
    spec = importlib.util.spec_from_file_location("fle_operator", STAGE / NAME / "fine_exchange.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    import fine_exchange_operator_v1 as reference
    for tied in (False, True):
        coords = np.zeros((40,3)) if tied else np.arange(120).reshape(40,3).astype(float)
        ids = np.zeros(40,dtype=np.int64)
        x = torch.randn(40,16,dtype=torch.float64,requires_grad=True)
        a = module.exchange(x, module.build_graph(coords,ids))
        b = reference.exchange(x, reference.build_graph(coords,ids))
        error = float((a-b).abs().max().detach())
        assert error <= 1e-12
        permutation = torch.randperm(40)
        permuted = module.exchange(x[permutation],module.build_graph(coords[permutation],ids[permutation]))
        equivariance = float((permuted-a[permutation]).abs().max().detach())
        assert equivariance <= 1e-12
        gradient = torch.autograd.grad(a.sum(),x)[0]
        assert bool(torch.isfinite(gradient).all())
        if tied: assert float((gradient-1).abs().max())<=1e-12
        result["checks"].append({"name":"tied" if tied else "untied", "prototype_max_error":error,"permutation_max_error":equivariance})
    field = module.FineLeafExchange(k=32,heads=8).double()
    points = torch.randn(2,7,16,dtype=torch.float64,requires_grad=True)
    positions = torch.arange(42,dtype=torch.float64).reshape(2,7,3)
    padding = torch.tensor([[False]*7,[False]*4+[True]*3])
    leaves = [torch.zeros(7,dtype=torch.long),torch.tensor([0,0,1,1])]
    output = field(points,padding,positions,leaves)
    assert torch.equal(output[1,4:],torch.zeros_like(output[1,4:]))
    expected = module.exchange(points[1,:4],module.build_graph(positions[1,:4].numpy(),leaves[1].numpy()))
    assert torch.equal(output[1,:4],expected)
    neighbor_gradient = torch.autograd.grad(output[0,0].sum(),points,retain_graph=True)[0]
    assert float(neighbor_gradient[0,1:].abs().sum())>0 and float(neighbor_gradient[1].abs().sum())==0
    result["checks"].append({"name":"ragged_padding_expression_isolation_and_offdiagonal_gradient","passed":True})
    one = field(points[:1,:1],padding[:1,:1],positions[:1,:1],[torch.zeros(1,dtype=torch.long)])
    assert torch.equal(one,points[:1,:1])
    result["checks"].append({"name":"singleton_identity","passed":True})
    # More than K members is needed to make geometry change actual support.
    p = torch.randn(1,40,16,dtype=torch.float64)
    c = torch.arange(120,dtype=torch.float64).reshape(1,40,3)
    mask = torch.zeros(1,40,dtype=torch.bool); ids=[torch.zeros(40,dtype=torch.long)]
    first = field(p,mask,c,ids)
    altered = c.clone(); altered[0,1]=100000
    second = field(p,mask,altered,ids)
    assert float((first-second).abs().max())>0
    assert not any("graph" in name or "cache" in name for name in vars(field))
    result["checks"].append({"name":"fresh_geometry_no_persistent_graph","passed":True})
    coords=np.array([[0.,0.,0.],[1.,2.,0.],[3.,0.,0.]])
    graph=module.build_graph(coords,np.zeros(3,dtype=np.int64))
    x=torch.randn(3,16,dtype=torch.float64,requires_grad=True)
    assert torch.autograd.gradcheck(lambda v:module.exchange(v,graph),(x,))
    result.update(passed=True, gradcheck=True, operator_parameters=sum(p.numel() for p in field.parameters()),
        before=before, native_backward="unmeasured", cuda_initialized=torch.cuda.is_initialized())
except BaseException as exc:
    result.update(error_type=type(exc).__name__,error=str(exc));raise
finally:
    save("contracts_result.json",result); release()
print("FLE_CPU_CONTRACTS_PASS")
