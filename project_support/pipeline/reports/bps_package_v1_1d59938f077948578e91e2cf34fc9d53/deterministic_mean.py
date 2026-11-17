"""Ordered mean reduction; no learned field or supervision change."""
import torch


def scatter_mean(src, index, dim=0, out=None, dim_size=None):
    if dim != 0 or out is not None or index.ndim != 1:
        raise ValueError("Ordered mean requires a one-dimensional dim-0 index")
    size = int(index.max()) + 1 if dim_size is None else dim_size
    order = torch.argsort(index, stable=True)
    counts = torch.bincount(index, minlength=size)
    means = torch.segment_reduce(src[order], "mean", lengths=counts)
    populated = counts.reshape((-1,) + (1,) * (src.ndim - 1)) > 0
    return torch.where(populated, means, torch.zeros_like(means))
