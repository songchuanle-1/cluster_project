"""Bounded invariant degeneracy fallback for the independent prototype."""
import math
import numpy as np
from scipy.spatial import cKDTree
import torch
from fine_exchange_operator import build_neighbors,point_exchange,standalone_controls

def build_graph(coordinates,leaves,k=32):
    coordinates=np.asarray(coordinates,dtype=np.float64);leaves=np.asarray(leaves,dtype=np.int64)
    indices,allowed=build_neighbors(coordinates,leaves,k)
    fallback=np.zeros(len(leaves),dtype=bool);groups=[]
    group_ids=np.zeros(len(leaves),dtype=np.int64)
    for group,leaf in enumerate(np.unique(leaves)):
        members=np.flatnonzero(leaves==leaf);groups.append(torch.from_numpy(members));group_ids[members]=group
        if len(members)<=k:continue
        distance,_=cKDTree(coordinates[members]).query(coordinates[members],k=list(range(1,k+2)))
        fallback[members]=distance[:,k-1]==distance[:,k]
    return {"indices":indices,"allowed":allowed,"fallback":torch.from_numpy(fallback),"groups":groups,"group_ids":torch.from_numpy(group_ids)}

def exchange(features,graph,heads=8):
    ordinary=point_exchange(features,graph["indices"].to(features.device),graph["allowed"].to(features.device),heads)
    if not bool(graph["fallback"].any()):return ordinary
    means=torch.stack([features[members.to(features.device)].mean(0) for members in graph["groups"]])
    alternative=means[graph["group_ids"].to(features.device)]
    return torch.where(graph["fallback"].to(features.device).unsqueeze(-1),alternative,ordinary)

def controls():
    original=standalone_controls()
    coordinates=np.array([[0.,0.,0.],[1.,.2,0.],[3.,0.,0.],[10.,0.,0.],[11.,.2,0.],[13.,0.,0.]])
    leaves=np.array([0,0,0,1,1,1]);torch.manual_seed(1999)
    x=torch.randn(6,16,dtype=torch.float64,requires_grad=True)
    graph=build_graph(coordinates,leaves)
    assert not bool(graph["fallback"].any())
    assert torch.equal(exchange(x,graph),point_exchange(x,graph["indices"],graph["allowed"]))
    coords=np.zeros((40,3));leaf=np.zeros(40,dtype=np.int64)
    values=torch.sin(torch.arange(640,dtype=torch.float64).reshape(40,16)/7).requires_grad_()
    tied=build_graph(coords,leaf);assert int(tied["fallback"].sum())==40
    actual=exchange(values,tied)
    assert torch.equal(actual,values.mean(0).expand_as(values))
    permutation=torch.arange(39,-1,-1);pg=build_graph(coords[permutation],leaf[permutation])
    permuted=exchange(values[permutation],pg)
    error=float((permuted-actual[permutation]).abs().max().detach());assert error<=1e-12
    gradient=torch.autograd.grad(actual.sum(),values)[0]
    gradient_error=float((gradient-torch.ones_like(gradient)).abs().max());assert gradient_error<=1e-12
    return {"passed":True,"original_six_controls_rerun":original,"untied_branch_exact":True,"tie_fallback_rows":40,
        "tie_permutation_error":error,"analytic_tie_gradient_error":gradient_error,"original_failure_retained":True,
        "new_core_model_revision":False,"HDS_model_revision":False,"native_model_backward":"unmeasured","full_model_resources":"unmeasured","scientific_novelty":"unestablished"}
