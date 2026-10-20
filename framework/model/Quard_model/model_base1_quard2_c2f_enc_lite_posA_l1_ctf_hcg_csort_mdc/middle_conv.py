"""Middle-only fixed geometric directional convolution for M205-MDC."""
import math
import torch
from torch import nn


class MiddleDirectionalConvolution(nn.Module):
    """Self + nearest donor in each of six xyz sectors; no point-level graph.

    Dominant-axis ties use x/y/z order; distance ties use donor token order.
    Zero displacement, self and padding cannot supply a directional donor.
    Directional edges may cross coarse parents. Coordinates are not learned.
    """
    def __init__(self, channels):
        super().__init__()
        self.kernel = nn.Parameter(torch.empty(7, channels))
        self.bias = nn.Parameter(torch.zeros(channels))
        nn.init.uniform_(self.kernel, -1 / math.sqrt(7), 1 / math.sqrt(7))
        self.pointwise = nn.Linear(channels, channels)
        self.activation = nn.GELU()

    def forward(self, features, positions, parent_ids, valid_masks):
        if positions is None or len(positions) != features.shape[0]:
            raise RuntimeError('Current-batch middle centroids are required')
        outputs = []
        for b in range(features.shape[0]):
            count = parent_ids[b].numel()
            xyz = positions[b]
            if xyz.shape != (count, 3):
                raise RuntimeError('Middle centroid/membership size mismatch')
            values = features[b, :count]
            delta = xyz.unsqueeze(0) - xyz.unsqueeze(1)  # receiver i, donor j
            axis = delta.abs().argmax(dim=-1)
            sign = delta.gather(-1, axis.unsqueeze(-1)).squeeze(-1).gt(0)
            sector = 2 * axis + sign.long()
            distance = delta.square().sum(dim=-1)
            occupied = valid_masks[b]
            valid = distance.gt(0) & occupied.unsqueeze(0) & occupied.unsqueeze(1)
            mixed = values * self.kernel[0]
            for direction in range(6):
                candidates = distance.masked_fill(~(valid & sector.eq(direction)), float('inf'))
                nearest_distance, donor = candidates.min(dim=-1)
                contribution = values[donor] * self.kernel[direction + 1]
                mixed = mixed + contribution.masked_fill(~nearest_distance.isfinite().unsqueeze(-1), 0)
            refined = self.activation(self.pointwise(mixed + self.bias))
            refined = refined.masked_fill(~occupied.unsqueeze(-1), 0)
            padding = features.new_zeros(features.shape[1] - count, features.shape[2])
            outputs.append(torch.cat([refined, padding], dim=0))
        return torch.stack(outputs, dim=0)
