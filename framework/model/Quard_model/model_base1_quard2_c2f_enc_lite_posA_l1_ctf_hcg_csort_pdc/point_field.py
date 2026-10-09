"""A query-conditioned detail field in the null space of SP mean pooling."""
import torch
import torch.nn as nn


def scatter_mean(src, index, dim=0, out=None, dim_size=None):
    """Preserve the mean operator without unordered CUDA atomic additions."""
    if dim != 0 or out is not None or index.ndim != 1:
        raise ValueError("Point detail pooling requires a one-dimensional dim-0 index")
    size = int(index.max()) + 1 if dim_size is None else dim_size
    order = torch.argsort(index, stable=True)
    counts = torch.bincount(index, minlength=size)
    means = torch.segment_reduce(src[order], "mean", lengths=counts)
    populated = counts.reshape((-1,) + (1,) * (src.ndim - 1)) > 0
    return torch.where(populated, means, torch.zeros_like(means))


class PointDetailField(nn.Module):
    def __init__(self, query_dim, point_dim):
        super().__init__()
        self.coefficients = nn.Sequential(
            nn.Linear(query_dim, point_dim), nn.ReLU(),
            nn.Linear(point_dim, point_dim),
        )

    @staticmethod
    def center(points, superpoints):
        return points - scatter_mean(points, superpoints, dim=0)[superpoints]

    def forward(self, query, coarse_logits, detail, superpoints):
        coefficients = self.coefficients(query)
        return coarse_logits[:, superpoints] + coefficients @ detail.transpose(0, 1)
