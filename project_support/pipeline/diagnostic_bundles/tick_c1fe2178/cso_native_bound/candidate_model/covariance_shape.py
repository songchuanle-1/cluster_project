"""Fine-leaf full channel-covariance shape, not donor/receiver exchange.

One preregistered rank-eight matrix representation. A fixed six-step
Newton-Schulz square root couples the covariance entries after aggregation.
Original native memberships, middle/coarse context and mask path stay native.
"""
import torch
from torch import nn
from torch.nn import functional as F


def matrix_square_root(covariance):
    """Differentiable polynomial approximation; no eigensystem/backward pole."""
    rank = covariance.shape[-1]
    eye = torch.eye(rank, device=covariance.device, dtype=covariance.dtype)
    eye = eye.expand(covariance.shape[0], rank, rank)
    # Numeric floor, not a selected training hyperparameter.
    epsilon = torch.finfo(covariance.dtype).eps
    positive = covariance + epsilon * eye
    trace = positive.diagonal(dim1=-2, dim2=-1).sum(-1).clamp_min(epsilon)
    y = positive / trace[:, None, None]
    z = eye
    for _ in range(6):
        correction = 0.5 * (3.0 * eye - z.bmm(y))
        y = y.bmm(correction)
        z = correction.bmm(z)
    return y * trace.sqrt()[:, None, None]


def covariance_statistics(projected, groups, number):
    """Population covariance, preserving all cross-channel coactivation."""
    rank = projected.shape[-1]
    counts = torch.bincount(groups, minlength=number).to(projected.dtype)
    means = projected.new_zeros(number, rank).index_add(0, groups, projected)
    means = means / counts.clamp_min(1)[:, None]
    centered = projected - means[groups]
    products = centered[:, :, None] * centered[:, None, :]
    covariance = projected.new_zeros(number, rank * rank).index_add(
        0, groups, products.reshape(-1, rank * rank))
    covariance = covariance.reshape(number, rank, rank) / counts.clamp_min(1)[:, None, None]
    return means, covariance, counts


class FineLeafCovarianceShape(nn.Module):
    """Shared leaf descriptor broadcast along original point->leaf incidence.

    No spatial edges, attention weights, receiver-conditioned donor values,
    extra residual/gate, query update or extra encoder-layer injection.
    """
    def __init__(self, channels=256):
        super().__init__()
        self.channels = channels
        self.rank = 8
        self.input_norm = nn.LayerNorm(channels)
        self.project = nn.Linear(channels, self.rank, bias=False)
        triangle = torch.triu_indices(self.rank, self.rank)
        self.register_buffer("triangle", triangle, persistent=False)
        width = self.rank + self.rank * (self.rank + 1) // 2
        self.readout = nn.Sequential(
            nn.Linear(width, channels // 2), nn.GELU(),
            nn.Linear(channels // 2, channels), nn.LayerNorm(channels))
        self.last_observation = None

    def _forward(self, point_feats, point_mask, point_positions, fine_ids,
                 reference=False, diagonal_only=False):
        if point_feats.ndim != 3 or point_feats.shape[-1] != self.channels:
            raise ValueError("Expected native padded [B,N,C] features")
        if point_mask.shape != point_feats.shape[:2] or len(fine_ids) != point_feats.shape[0]:
            raise ValueError("Native fine-membership batch mismatch")
        output = torch.zeros_like(point_feats)
        observed_points = observed_leaves = 0
        for batch in range(point_feats.shape[0]):
            valid = ~point_mask[batch]
            x = point_feats[batch, valid]
            ids = fine_ids[batch].to(device=x.device, dtype=torch.long)
            if ids.numel() != x.shape[0] or not ids.numel() or bool((ids < 0).any()):
                raise ValueError("Expected exact original nonempty valid fine incidence")
            number = int(ids.max().item()) + 1
            z = self.project(self.input_norm(x))
            if reference:
                means, covariance, counts = [], [], []
                for leaf_id in range(number):
                    members = z[ids == leaf_id]
                    count = len(members)
                    mean = members.mean(0) if count else z.new_zeros(self.rank)
                    centered = members - mean
                    cov = centered.T.matmul(centered) / max(count, 1)
                    means.append(mean)
                    covariance.append(cov)
                    counts.append(count)
                means, covariance = torch.stack(means), torch.stack(covariance)
                counts = z.new_tensor(counts)
            else:
                means, covariance, counts = covariance_statistics(z, ids, number)
            if diagonal_only:
                covariance = torch.diag_embed(covariance.diagonal(dim1=-2, dim2=-1))
            root = matrix_square_root(covariance)
            # sqrt(2) is the standard symmetric-vectorization isometry for
            # off-diagonal entries, not an adjustable gain.
            triangle = root[:, self.triangle[0], self.triangle[1]]
            off_diagonal = self.triangle[0] != self.triangle[1]
            weights = torch.where(off_diagonal, triangle.new_tensor(2.0).sqrt(),
                                  triangle.new_tensor(1.0))
            descriptor = torch.cat([means, triangle * weights], dim=-1)
            leaf = self.readout(descriptor)
            leaf = leaf.masked_fill((counts == 0)[:, None], 0)
            output[batch, valid] = leaf[ids]
            observed_points += x.shape[0]
            observed_leaves += int((counts > 0).sum().item())
        self.last_observation = {
            "kind": "native_fine_leaf_full_channel_covariance_square_root",
            "points": observed_points, "occupied_leaves": observed_leaves,
            "rank": self.rank, "matrix_iterations": 6,
            "receiver_donor_edges": 0, "uses_positions": False,
            "reference_control": reference, "diagonal_only_control": diagonal_only,
        }
        return output

    def forward(self, point_feats, point_mask, point_positions, fine_ids):
        return self._forward(point_feats, point_mask, point_positions, fine_ids)

    def forward_reference(self, point_feats, point_mask, point_positions, fine_ids,
                          *, diagonal_only=False):
        return self._forward(point_feats, point_mask, point_positions, fine_ids,
                             reference=True, diagonal_only=diagonal_only)

    def forward_diagonal_only(self, point_feats, point_mask, point_positions, fine_ids):
        return self._forward(point_feats, point_mask, point_positions, fine_ids, diagonal_only=True)
