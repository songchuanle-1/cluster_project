"""Graph contracts and matched BCE/conditional-likelihood gradient controls."""
import importlib.util
import itertools
import json
import sys
import numpy as np
import torch
spec=importlib.util.spec_from_file_location("bca",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
torch.set_num_threads(1)
# Two scenes reuse local SP IDs but must not create cross-scene contacts.
vox=torch.tensor([[0,0,0,0],[0,1,0,0],[0,2,0,0],
                  [1,0,0,0],[1,1,0,0]])
mapping=torch.tensor([0,0,1,2,3,4])
sp=torch.tensor([0,1,1,2,3,4])
graphs=m.scene_contacts(vox,mapping,sp,torch.tensor([0,3,5]))
assert np.array_equal(graphs[0],np.array([[0,1],[1,2]]))
assert np.array_equal(graphs[1],np.array([[0,1]]))
# Point and occupied-voxel order must not change physical edges.
perm=torch.tensor([4,2,0,3,1]);back=torch.argsort(perm)
again=m.scene_contacts(vox[perm],back[mapping],sp,torch.tensor([0,3,5]))
assert all(np.array_equal(a,b) for a,b in zip(graphs,again))
z=torch.tensor([1.,-2.,2.,-1.],dtype=torch.double,requires_grad=True)
y=torch.tensor([1,1,0,0],dtype=torch.bool)
H=torch.autograd.functional.hessian(lambda v:m.conditional_assignment(v,y),z)
Hb=torch.autograd.functional.hessian(lambda v:torch.nn.functional.binary_cross_entropy_with_logits(v,y.double()),z)
assert (H-torch.diag(H.diag())).abs().max()>1e-5
assert torch.equal(Hb-torch.diag(Hb.diag()),torch.zeros_like(Hb))
g=torch.autograd.grad(m.conditional_assignment(z,y),z)[0]
assert (g[y]<0).all() and (g[~y]>0).all()
assert abs(float(g.sum()))<1e-10
permuted_y=y[torch.tensor([2,3,0,1])]
gp=torch.autograd.grad(m.conditional_assignment(z,permuted_y),z)[0]
assert (gp[y]>0).all()
try:
    m.conditional_assignment(torch.tensor([float("nan"),0.]),torch.tensor([1,0]))
    raise AssertionError("Accepted NaN")
except ValueError:
    pass
pred=[torch.randn(2,3,dtype=torch.double,requires_grad=True)]
target=[dict(masks=torch.tensor([[1,0,0],[1,0,0]]))]
indices=[(torch.tensor([0,1]),torch.tensor([0,1]))]
loss,stats=m.boundary_loss(pred,target,indices,[np.array([[0,1],[1,2]])],[1],torch.tensor([2.]))
assert stats["valid_masks"]==2
assert torch.isfinite(torch.autograd.grad(loss,pred[0])[0]).all()
zero,_=m.boundary_loss(pred,target,indices,[np.empty((0,2),int)],[1],torch.tensor([2.]))
assert zero==0 and torch.equal(torch.autograd.grad(zero,pred[0])[0],torch.zeros_like(pred[0]))
print(json.dumps(dict(status="PASS",scene_isolation=True,point_voxel_permutation=True,
    majority_tie=True,empty_graph=True,valid_nan_rejected=True,
    bce_offdiagonal_hessian=0,bca_offdiagonal_hessian=float((H-torch.diag(H.diag())).abs().max()),
    correct_gradient=g.detach().tolist(),permuted_label_gradient=gp.detach().tolist()),indent=2))
