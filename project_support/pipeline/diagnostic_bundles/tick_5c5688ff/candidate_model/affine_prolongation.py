"""Geometry-subspace child detail with coarse-to-fine semantic intercepts."""
import torch
from torch import nn


class HierarchicalAffineProlongation(nn.Module):
    """Replace middle/fine intercepts with their already updated parent.

    Coordinates and geometric inverses are detached, but all feature products
    remain in autograd. No learned parameter, child residual or NxN projector.
    Native occupied masks exclude padding and IDs with no actual point support.
    """
    def forward(self, fine, middle, coarse, positions, occupied, ids_list):
        features = (fine, middle, coarse)
        fine_outputs, middle_outputs = [], []
        for b in range(fine.shape[0]):
            original = [features[level][b, :positions[level][b].shape[0]] for level in range(3)]
            updated = list(original)
            for level in (1, 0):
                child = original[level]
                parent = updated[level + 1]
                parent_ids = ids_list[level + 1][b].long()
                active = occupied[level][b]
                xyz = positions[level][b].detach().float()
                count = xyz.new_zeros(parent.shape[0])
                count.index_add_(0, parent_ids, active.to(xyz.dtype))
                centers = xyz.new_zeros(parent.shape[0], 3)
                centers.index_add_(0, parent_ids, xyz * active.unsqueeze(-1))
                centers = centers / count.clamp_min(1).unsqueeze(-1)
                delta = (xyz - centers[parent_ids]) * active.unsqueeze(-1)
                gram = xyz.new_zeros(parent.shape[0], 3, 3)
                gram.index_add_(0, parent_ids, delta.unsqueeze(-1) * delta.unsqueeze(-2))
                inverse = torch.linalg.pinv(gram, hermitian=True).detach()
                # Do not detach RHS, slope or detail: these carry child feature gradients.
                rhs = child.new_zeros(parent.shape[0], 3, child.shape[-1])
                rhs.index_add_(0, parent_ids, delta.unsqueeze(-1) * child.unsqueeze(-2))
                slopes = torch.matmul(inverse, rhs)
                detail = torch.einsum('ni,nic->nc', delta, slopes[parent_ids])
                updated[level] = (parent[parent_ids] + detail).masked_fill(~active.unsqueeze(-1), 0)
            fine_padding = fine.new_zeros(fine.shape[1] - updated[0].shape[0], fine.shape[2])
            middle_padding = middle.new_zeros(middle.shape[1] - updated[1].shape[0], middle.shape[2])
            fine_outputs.append(torch.cat([updated[0], fine_padding], dim=0))
            middle_outputs.append(torch.cat([updated[1], middle_padding], dim=0))
        return torch.stack(fine_outputs), torch.stack(middle_outputs)
