"""A query-conditioned detail field in the null space of SP mean pooling."""
import torch
import torch.nn as nn
from torch_scatter import scatter_mean


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
