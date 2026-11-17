"""Duplicate-seed regression: finite gradients and physical-set weighting."""
import importlib.util
import json
import sys
import torch
spec = importlib.util.spec_from_file_location("helper",sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
results = []
for device in ["cpu"] + (["cuda"] if torch.cuda.is_available() else []):
    ids = torch.tensor([[0,0,1],[0,1,1]],device=device)
    labels = [torch.tensor([1,2],device=device)]*2
    z = torch.tensor([[[0.,1.],[0.,3.],[0.,-1.]],
                      [[0.,-2.],[0.,2.],[0.,4.]]],dtype=torch.double,device=device,requires_grad=True)
    fn = lambda v:m.paired_switch(v,ids,labels,[[1],[2]],[2])[0]
    expected = torch.nn.functional.softplus(z.new_tensor(-8.))
    torch.testing.assert_close(fn(z),expected)
    assert torch.autograd.gradcheck(fn,(z,))
    grad = torch.autograd.grad(fn(z),z)[0]
    torch.testing.assert_close(grad[0,0],grad[0,1])
    torch.testing.assert_close(grad[1,1],grad[1,2])
    perm = torch.tensor([2,0,1],device=device)
    torch.testing.assert_close(m.paired_switch(z[:,perm],ids[:,perm],labels,[[1],[2]],[2])[0],fn(z))
    biased = z.detach().clone()
    biased[:,:,1] += torch.tensor([[10.,10.,20.],[13.,23.,23.]],device=device)
    torch.testing.assert_close(fn(biased),fn(z))
    # Duplicating an identical observation cannot reweight its physical seed.
    doubled = torch.repeat_interleave(z,2,dim=1)
    doubled_ids = torch.repeat_interleave(ids,2,dim=1)
    torch.testing.assert_close(m.paired_switch(doubled,doubled_ids,labels,[[1],[2]],[2])[0],fn(z))
    assert m.paired_switch(z,ids,labels,[[1],[2]],[2])[1]["duplicate_queries"]==2
    results.append(dict(device=device,gradcheck=True,mean_reference=True,
                        replication_invariance=True,bias_cancellation=True,permutation=True))
print(json.dumps(dict(status="PASS",tests=results),indent=2))
