"""M212 BCR: exclusive sibling-prefix/suffix states, not inclusive PSBR readout.

Only detached original geometry/support determine the private chain plan.
Feature tensors remain on their native graph; original hierarchy IDs are kept.
"""
import math

import torch
from torch import nn


def build_complement_plan(centers, parent_ids, supported, max_middle_tokens):
    """Production chain plan, also directly testable using only stdlib scalars.

    Every step is (destination_original_ID, source_original_ID); its recurrent
    input is the same direction's already-computed context at the source ID.
    There are exactly 2(n-1) consumed state steps for each nonempty parent.
    """
    k = len(parent_ids)
    if not (len(centers) == len(supported) == k <= max_middle_tokens):
        raise ValueError('BCR geometry/support/original parent prefix mismatch')
    for point, parent, active in zip(centers, parent_ids, supported):
        if len(point) != 3 or not all(math.isfinite(v) for v in point):
            raise ValueError('BCR requires finite original 3D middle centers')
        if type(parent) is not int or parent < 0 or type(active) is not bool:
            raise ValueError('BCR invalid original parent IDs or true-support mask')
    groups = {}
    for token, (parent, active) in enumerate(zip(parent_ids, supported)):
        if active:
            groups.setdefault(parent, []).append(token)
    plan = []
    for parent in sorted(groups):
        order = tuple(sorted(groups[parent], key=lambda i: (*centers[i], i)))
        left_steps = tuple((order[i], order[i - 1]) for i in range(1, len(order)))
        right_steps = tuple((order[i], order[i + 1]) for i in range(len(order) - 2, -1, -1))
        plan.append({'parent': parent, 'order': order,
                     'left_steps': left_steps, 'right_steps': right_steps})
    return plan


class ParentBidirectionalComplementRecurrence(nn.Module):
    """One shared scan, original GELU, one own/left/right linear readout."""

    def __init__(self, channels, max_middle_tokens):
        super().__init__()
        self.channels = channels
        self.max_middle_tokens = max_middle_tokens
        self.scan = nn.Linear(2 * channels, channels)
        self.readout = nn.Linear(3 * channels, channels)
        self.activation = nn.GELU()

    def forward(self, features, positions, parent_ids, supported):
        if features.ndim != 3 or features.shape[-1] != self.channels:
            raise ValueError('BCR expects [batch,middle_slots,channels]')
        batch, slots, _ = features.shape
        if (positions is None or parent_ids is None or supported is None or
                not (len(positions) == len(parent_ids) == len(supported) == batch)):
            raise RuntimeError('BCR current-forward geometry/support cache missing')
        outputs = []
        for b in range(batch):
            coords, parents, valid = positions[b], parent_ids[b], supported[b]
            k = parents.numel()
            if (parents.ndim != 1 or parents.dtype != torch.long or
                    coords.shape != (k, 3) or valid.shape != (k,) or
                    valid.dtype != torch.bool or coords.requires_grad or k > slots or
                    any(t.device != features.device for t in (coords, parents, valid))):
                raise RuntimeError('BCR cache shape/device/detached-geometry mismatch')
            plan = build_complement_plan(coords.detach().cpu().tolist(),
                                         parents.detach().cpu().tolist(),
                                         valid.detach().cpu().tolist(),
                                         self.max_middle_tokens)
            output = features.new_zeros((slots, self.channels))
            for group in plan:
                order = group['order']
                # Direction/batch/parent resets; these are fixed zero boundaries.
                left = {order[0]: features.new_zeros(self.channels)}
                right = {order[-1]: features.new_zeros(self.channels)}
                for destination, source in group['left_steps']:
                    left[destination] = self.activation(self.scan(torch.cat(
                        (features[b, source], left[source]), dim=-1)))
                for destination, source in group['right_steps']:
                    right[destination] = self.activation(self.scan(torch.cat(
                        (features[b, source], right[source]), dim=-1)))
                original_ids = torch.tensor(order, dtype=torch.long, device=features.device)
                own = features[b].index_select(0, original_ids)
                delta = self.readout(torch.cat((own,
                    torch.stack([left[token] for token in order]),
                    torch.stack([right[token] for token in order])), dim=-1))
                output = output.index_copy(0, original_ids, delta)
            outputs.append(output)
        # Unsupported internal slots and batch padding have zero update. The
        # unchanged outer cf skip is applied by CTF; no extra residual is here.
        return torch.stack(outputs, dim=0) if outputs else torch.zeros_like(features)
