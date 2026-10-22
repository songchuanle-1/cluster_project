"""M209 PSBR: parent-segmented, geometry-ordered bidirectional token state.

This module replaces the middle residual FFN. It introduces no residual, gate,
Q/K/V, learned scale, cross-parent state, or change to the raw hierarchy banks.
Geometry/support are detached side caches of the current native partition.
"""

import torch
import torch.nn as nn


class ParentSegmentedBidirectionalRecurrence(nn.Module):
    """Shared Wx/Wh in both directions, then one fixed concatenation projection."""

    def __init__(self, d_model):
        super().__init__()
        self.d_model = d_model
        self.Wx = nn.Linear(d_model, d_model, bias=True)
        self.Wh = nn.Linear(d_model, d_model, bias=False)
        self.Wo = nn.Linear(2 * d_model, d_model, bias=True)

    def forward(self, middle, middle_positions, middle_parent_ids, middle_valid):
        if middle.ndim != 3 or middle.shape[-1] != self.d_model:
            raise ValueError('PSBR expects middle features [B,K,C]')
        B, padded_K, C = middle.shape
        caches = (middle_positions, middle_parent_ids, middle_valid)
        if B == 0 or any(cache is None or len(cache) != B for cache in caches):
            raise RuntimeError('PSBR current geometry/support cache is missing')
        batch_outputs = []
        for b in range(B):
            positions = middle_positions[b]
            parents = middle_parent_ids[b]
            valid = middle_valid[b]
            K = parents.numel()
            if parents.ndim != 1 or parents.dtype != torch.long:
                raise RuntimeError('PSBR parent IDs must be original int64 vector')
            if K > padded_K or positions.shape != (K, 3) or valid.shape != (K,):
                raise RuntimeError('PSBR cache lengths do not match middle prefix')
            if valid.dtype != torch.bool or positions.requires_grad:
                raise RuntimeError('PSBR requires boolean support and detached geometry')
            if any(t.device != middle.device for t in (positions, parents, valid)):
                raise RuntimeError('PSBR geometry/support device mismatch')
            if not torch.isfinite(positions).all():
                raise RuntimeError('PSBR geometry must be finite')
            if K and int(parents.min().item()) < 0:
                raise RuntimeError('PSBR original parent IDs must be nonnegative')

            # Sorting uses only actual detached geometry and original token ID.
            # Internal unsupported slots and batch tail padding never enter a chain.
            centers = positions.detach().cpu().tolist()
            parent_values = parents.detach().cpu().tolist()
            supported = torch.nonzero(valid, as_tuple=False).flatten().cpu().tolist()
            groups = {}
            for j in supported:
                groups.setdefault(parent_values[j], []).append(j)
            output = middle.new_zeros((padded_K, C))
            for parent in sorted(groups):
                ordered = sorted(groups[parent], key=lambda j: (
                    centers[j][0], centers[j][1], centers[j][2], j))
                original_ids = torch.tensor(ordered, device=middle.device, dtype=torch.long)
                # One input projection shared by both directions.
                projected = self.Wx(middle[b].index_select(0, original_ids))
                forward_states = []
                state = projected.new_zeros((C,))
                for i in range(len(ordered)):
                    state = torch.tanh(projected[i] + self.Wh(state))
                    forward_states.append(state)
                backward_states = [None] * len(ordered)
                state = projected.new_zeros((C,))
                for i in range(len(ordered) - 1, -1, -1):
                    state = torch.tanh(projected[i] + self.Wh(state))
                    backward_states[i] = state
                paired = torch.cat((torch.stack(forward_states, dim=0),
                                    torch.stack(backward_states, dim=0)), dim=-1)
                # Inverse write to ORIGINAL IDs; there is no middle residual.
                output = output.index_copy(0, original_ids, self.Wo(paired))
            batch_outputs.append(output)
        return torch.stack(batch_outputs, dim=0)
