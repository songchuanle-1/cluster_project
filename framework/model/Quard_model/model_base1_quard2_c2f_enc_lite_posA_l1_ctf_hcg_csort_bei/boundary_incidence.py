"""Sparse, directed target-boundary likelihood on native matched masks."""
import numpy as np
import torch
import torch.nn.functional as F
from scipy.spatial import cKDTree


def scatter_mean(src, index, dim=0, out=None, dim_size=None):
    if dim != 0 or out is not None or index.ndim != 1:
        raise ValueError("Sorted mean requires a dim-0 vector index")
    size = int(index.max()) + 1 if dim_size is None else dim_size
    order = torch.argsort(index, stable=True)
    counts = torch.bincount(index, minlength=size)
    means = torch.segment_reduce(src[order], "mean", lengths=counts)
    populated = counts.reshape((-1,) + (1,) * (src.ndim - 1)) > 0
    return torch.where(populated, means, torch.zeros_like(means))


def spatial_edges(coords):
    xyz = coords.detach().double().cpu().numpy()
    if len(xyz) < 2:
        return torch.empty((0, 2), dtype=torch.long, device=coords.device)
    _, nearest = cKDTree(xyz).query(xyz, k=2, workers=1)
    other = [next(int(j) for j in row if int(j) != i)
             for i, row in enumerate(nearest)]
    edges = np.unique(np.sort(np.column_stack((np.arange(len(xyz)), other)), axis=1),
                      axis=0)
    return torch.as_tensor(edges, dtype=torch.long, device=coords.device)


def incidence_loss(logits, targets, edges, mode="native"):
    if mode == "bypass" or not len(edges):
        return logits.sum() * 0
    if mode not in ("native", "placebo"):
        raise ValueError("Unknown boundary diagnostic mode")
    u, v = edges.T
    signs = targets[..., u].to(logits.dtype) - targets[..., v].to(logits.dtype)
    selected = signs != 0
    if not bool(selected.any()):
        return logits.sum() * 0
    if mode == "placebo":
        permutation = np.random.default_rng(1999).permutation(logits.shape[-1])
        permutation = torch.as_tensor(permutation, device=logits.device)
        u, v = permutation[u], permutation[v]
    signed_gap = signs * (logits[..., u] - logits[..., v])
    return F.softplus(-signed_gap[selected]).mean()
