"""Isolated differentiable sparse point exchange, not integrated or admitted."""
import math
import numpy as np
from scipy.spatial import cKDTree
import torch

def build_neighbors(coordinates,leaves,k=32):
    coordinates=np.asarray(coordinates,dtype=np.float64)
    leaves=np.asarray(leaves,dtype=np.int64)
    n=len(leaves)
    assert coordinates.shape==(n,3) and n>0 and k>0
    indices=np.repeat(np.arange(n)[:,None],k,axis=1)
    allowed=np.zeros((n,k),dtype=bool)
    for leaf in np.unique(leaves):
        members=np.flatnonzero(leaves==leaf);degree=min(k,len(members))
        _,local=cKDTree(coordinates[members]).query(coordinates[members],k=list(range(1,degree+1)))
        indices[members,:degree]=members[np.asarray(local)]
        allowed[members,:degree]=True
    assert np.array_equal(leaves[indices[allowed]],np.repeat(leaves[:,None],k,axis=1)[allowed])
    return torch.from_numpy(indices),torch.from_numpy(allowed)

def point_exchange(features,indices,allowed,heads=8):
    assert features.ndim==2 and features.shape[1]%heads==0
    n,channels=features.shape;dim=channels//heads
    assert indices.shape==allowed.shape and indices.shape[0]==n and bool(allowed.any(-1).all())
    gathered=features[indices].reshape(n,indices.shape[1],heads,dim)
    query=features.reshape(n,1,heads,dim)
    score=(query*gathered).sum(-1)/math.sqrt(dim)
    score=score.masked_fill(~allowed.unsqueeze(-1),-torch.inf)
    probability=score.softmax(dim=1)
    return (probability.unsqueeze(-1)*gathered).sum(dim=1).reshape(n,channels)

def standalone_controls():
    torch.set_num_threads(1);torch.manual_seed(1999)
    coordinates=np.array([[0.,0.,0.],[1.,.2,0.],[3.,0.,0.],[10.,0.,0.],[11.,.2,0.],[13.,0.,0.]])
    leaves=np.array([0,0,0,1,1,1]);indices,allowed=build_neighbors(coordinates,leaves)
    x=torch.randn(6,16,dtype=torch.float64,requires_grad=True)
    actual=point_exchange(x,indices,allowed)
    assert indices.shape==(6,32) and int(allowed.sum())==18
    assert not torch.allclose(actual[0],actual[1])
    delta=x.detach().clone();delta[1]+=1
    changed=point_exchange(delta,indices,allowed)
    assert not torch.equal(changed[0],actual[0]) and torch.equal(changed[3:],actual[3:])
    singleton_i,singleton_a=build_neighbors(coordinates[:1],leaves[:1])
    assert torch.equal(point_exchange(x[:1],singleton_i,singleton_a),x[:1])
    permutation=torch.tensor([2,0,1,5,3,4]);pi,pa=build_neighbors(coordinates[permutation],leaves[permutation])
    permuted=point_exchange(x[permutation],pi,pa)
    permutation_error=float((permuted-actual[permutation]).abs().max().detach())
    assert permutation_error<=1e-12
    assert torch.autograd.gradcheck(lambda value:point_exchange(value,indices,allowed),(x,),raise_exception=True)
    reference=[]
    for i in range(len(x)):
        selected=indices[i,allowed[i]];q=x[i].reshape(8,2);bank=x[selected].reshape(-1,8,2)
        score=(q.unsqueeze(0)*bank).sum(-1)/math.sqrt(2)
        reference.append((score.softmax(0).unsqueeze(-1)*bank).sum(0).reshape(-1))
    equivalent_error=float((actual-torch.stack(reference)).abs().max().detach())
    assert equivalent_error<=1e-12
    return {"passed":True,"checks":["bounded_sameleaf_neighbors","recipient_specific_offdiagonal_dependence","singleton_identity","permutation_equivariance","isolated_CPU_autograd_gradcheck","standard_scalar_attention_equivalence"],
        "permutation_max_error":permutation_error,"standard_attention_equivalence_error":equivalent_error,
        "new_parameters":0,"prototype_backward_kind":"CPU_gradcheck_only_not_native_model_backward",
        "full_model_resources":"unmeasured","native_integration":"unimplemented","scientific_novelty":"not_established_by_standard_attention"}
