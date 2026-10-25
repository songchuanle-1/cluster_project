"""M213 BFC: shared two-output nonlinear butterfly over original parent siblings.

Detached geometry only constructs a private plan. No fake padded token is a
pair participant; feature states stay on their original differentiable graph.
"""
import math

import torch
from torch import nn


def build_butterfly_plan(centers, parent_ids, supported, max_middle_tokens):
    """Build production simultaneous rounds using only stdlib scalar metadata.

    Per parent use bits ascending then descending without repeating the peak.
    A round is a disjoint matching: both output states consume its OLD states.
    Groups may have different bit sequences; equal round indices are parallel
    across independent original parents. Original token IDs are never relabeled.
    """
    k = len(parent_ids)
    if (type(max_middle_tokens) is not int or max_middle_tokens < 0 or
            not (len(centers) == len(supported) == k <= max_middle_tokens)):
        raise ValueError('BFC geometry/support/original prefix mismatch')
    for point, parent, active in zip(centers, parent_ids, supported):
        if len(point) != 3 or not all(type(v) in (int, float) and math.isfinite(v) for v in point):
            raise ValueError('BFC requires finite original 3D middle centers')
        if type(parent) is not int or parent < 0 or type(active) is not bool:
            raise ValueError('BFC invalid original parent IDs or true-support mask')
    members = {}
    for token, (parent, active) in enumerate(zip(parent_ids, supported)):
        if active:
            members.setdefault(parent, []).append(token)
    groups = []
    singleton_ids = []
    rounds = []
    for parent in sorted(members):
        order = tuple(sorted(members[parent], key=lambda token: (*centers[token], token)))
        n = len(order)
        m = (n - 1).bit_length()
        bits = tuple(range(m)) + tuple(range(m - 2, -1, -1))
        groups.append({'parent': parent, 'order': order, 'bits': bits})
        if n == 1:
            singleton_ids.append(order[0])
        for round_index, bit in enumerate(bits):
            while len(rounds) <= round_index:
                rounds.append([])
            for rank in range(n):
                partner = rank ^ (1 << bit)
                if rank < partner < n:
                    rounds[round_index].append((parent, bit, order[rank], order[partner]))
    return {'groups': tuple(groups), 'rounds': tuple(tuple(pairs) for pairs in rounds),
            'singleton_ids': tuple(singleton_ids)}


class ParentButterflyTokenComposition(nn.Module):
    """One shared 2C->2C map plus original GELU, retaining n C states per group."""

    def __init__(self, channels, max_middle_tokens):
        super().__init__()
        self.channels = channels
        self.max_middle_tokens = max_middle_tokens
        self.mix = nn.Linear(2 * channels, 2 * channels)
        self.activation = nn.GELU()

    def forward(self, features, positions, parent_ids, supported):
        if features.ndim != 3 or features.shape[-1] != self.channels:
            raise ValueError('BFC expects [batch,middle_slots,channels]')
        batch, slots, _ = features.shape
        if (positions is None or parent_ids is None or supported is None or
                not (len(positions) == len(parent_ids) == len(supported) == batch)):
            raise RuntimeError('BFC current-forward geometry/support cache missing')
        outputs = []
        for b in range(batch):
            coords, parents, valid = positions[b], parent_ids[b], supported[b]
            k = parents.numel()
            if (parents.ndim != 1 or parents.dtype != torch.long or
                    coords.shape != (k, 3) or valid.shape != (k,) or
                    valid.dtype != torch.bool or coords.requires_grad or k > slots or
                    any(t.device != features.device for t in (coords, parents, valid))):
                raise RuntimeError('BFC cache shape/device/detached-geometry mismatch')
            plan = build_butterfly_plan(coords.detach().cpu().tolist(),
                                       parents.detach().cpu().tolist(),
                                       valid.detach().cpu().tolist(),
                                       self.max_middle_tokens)
            state = features[b]
            for pairs in plan['rounds']:
                left = torch.tensor([pair[2] for pair in pairs], dtype=torch.long, device=features.device)
                right = torch.tensor([pair[3] for pair in pairs], dtype=torch.long, device=features.device)
                # Every pair in this round reads the same OLD state. Only after
                # both halves are generated do functional scatters form next state.
                pair_input = torch.cat((state.index_select(0, left),
                                        state.index_select(0, right)), dim=-1)
                mixed = self.activation(self.mix(pair_input))
                state = state.index_copy(0, left, mixed[:, :self.channels])
                state = state.index_copy(0, right, mixed[:, self.channels:])
            if plan['singleton_ids']:
                singletons = torch.tensor(plan['singleton_ids'], dtype=torch.long, device=features.device)
                own = features[b].index_select(0, singletons)
                # Private zero input is only this singleton's boundary. It never
                # appears in raw IDs, other groups, CSORT, or HCG as an extra row.
                single_delta = self.activation(self.mix(torch.cat((own, torch.zeros_like(own)), dim=-1)))[:, :self.channels]
                state = state.index_copy(0, singletons, single_delta)
            active_ids = tuple(token for group in plan['groups'] for token in group['order'])
            output = features.new_zeros((slots, self.channels))
            if active_ids:
                index = torch.tensor(active_ids, dtype=torch.long, device=features.device)
                output = output.index_copy(0, index, state.index_select(0, index))
            outputs.append(output)
        # Unsupported internal slots and batch padding have zero update; CTF
        # retains the original cf skip. No new residual path is added here.
        return torch.stack(outputs, dim=0) if outputs else torch.zeros_like(features)
