"""Coarse-derived grouped channel attention on fine token values, M206-CGCA."""
import math
import torch
from torch import nn
from torch.nn import functional as F


class CoarseConditionedChannelAttention(nn.Module):
    """Mix channels within each fine token using coarse scene channel affinity.

    No spatial value donor exchange, learned gate, projection or new residual.
    The inherited decoder head count determines channel groups.
    """
    def __init__(self, channels, heads):
        super().__init__()
        if channels % heads:
            raise ValueError('Channel count must divide inherited attention heads')
        self.channels = channels
        self.heads = heads
        self.width = channels // heads

    def forward(self, fine, coarse, fine_to_middle, middle_to_coarse):
        batches = []
        for b in range(fine.shape[0]):
            nf = fine_to_middle[b].numel()
            coarse_ids = torch.unique(middle_to_coarse[b].long(), sorted=True)
            nc = coarse_ids.numel()
            context = F.layer_norm(coarse[b, coarse_ids], (self.channels,))
            z = context.reshape(nc, self.heads, self.width).permute(1, 0, 2)
            affinity = torch.softmax(torch.matmul(z.transpose(-2, -1), z) / math.sqrt(nc), dim=-1)
            values = fine[b, :nf].reshape(nf, self.heads, self.width).permute(1, 0, 2)
            mixed = torch.matmul(values, affinity.transpose(-2, -1))
            mixed = mixed.permute(1, 0, 2).reshape(nf, self.channels)
            padding = fine.new_zeros(fine.shape[1] - nf, self.channels)
            batches.append(torch.cat([mixed, padding], dim=0))
        return torch.stack(batches, dim=0)
