"""M214 CTS: overlapping cyclic triadic updates inside original parent groups.

A fixed geometric order and minimum ternary coverage depth determine the plan.
Only private work slots can be zero; no fake hierarchy token/point is created.
"""
import math

import torch
from torch import nn


def build_triadic_plan(centers, parent_ids, supported, max_middle_tokens):
    """Production plan, directly executable with stdlib scalar metadata.

    Each row is(parent, offset, own_original_ID, plus_ID_or_None, minus_ID_or_None).
    Only first occurrences of real IDs are retained in own,+,- slot order.
    All receivers in one round consume the same OLD stage before any writeback.
    """
    k = len(parent_ids)
    if (type(max_middle_tokens) is not int or max_middle_tokens < 0 or
            not (len(centers) == len(supported) == k <= max_middle_tokens)):
        raise ValueError('CTS geometry/support/original prefix mismatch')
    for point, parent, active in zip(centers, parent_ids, supported):
        if len(point) != 3 or not all(type(v) in (int, float) and math.isfinite(v) for v in point):
            raise ValueError('CTS requires finite original 3D middle centers')
        if type(parent) is not int or parent < 0 or type(active) is not bool:
            raise ValueError('CTS invalid original parent IDs or true-support mask')
    members = {}
    for token, (parent, active) in enumerate(zip(parent_ids, supported)):
        if active:
            members.setdefault(parent, []).append(token)
    groups = []
    singletons = []
    rounds = []
    for parent in sorted(members):
        order = tuple(sorted(members[parent], key=lambda token: (*centers[token], token)))
        n = len(order)
        offsets = []
        offset = 1
        while offset < n:
            offsets.append(offset)
            offset *= 3
        groups.append({'parent': parent, 'order': order, 'offsets': tuple(offsets)})
        if n == 1:
            singletons.append(order[0])
        for r, offset in enumerate(offsets):
            while len(rounds) <= r:
                rounds.append([])
            for rank, own in enumerate(order):
                plus = order[(rank + offset) % n]
                minus = order[(rank - offset) % n]
                used = {own}
                if plus in used:
                    plus = None
                else:
                    used.add(plus)
                if minus in used:
                    minus = None
                rounds[r].append((parent, offset, own, plus, minus))
    return {'groups': tuple(groups), 'rounds': tuple(tuple(rows) for rows in rounds),
            'singleton_ids': tuple(singletons)}


class ParentCyclicTriadicStateComposition(nn.Module):
    """One shared 3C->C Linear and original GELU; synchronous overlapping rows."""

    def __init__(self, channels, max_middle_tokens):
        super().__init__()
        self.channels = channels
        self.max_middle_tokens = max_middle_tokens
        self.mix = nn.Linear(3 * channels, channels)
        self.activation = nn.GELU()

    def forward(self, features, positions, parent_ids, supported):
        if features.ndim != 3 or features.shape[-1] != self.channels:
            raise ValueError('CTS expects [batch,middle_slots,channels]')
        batch, slots, _ = features.shape
        if (positions is None or parent_ids is None or supported is None or
                not (len(positions) == len(parent_ids) == len(supported) == batch)):
            raise RuntimeError('CTS current-forward geometry/support cache missing')
        outputs = []
        for b in range(batch):
            coords, parents, valid = positions[b], parent_ids[b], supported[b]
            k = parents.numel()
            if (parents.ndim != 1 or parents.dtype != torch.long or
                    coords.shape != (k, 3) or valid.shape != (k,) or
                    valid.dtype != torch.bool or coords.requires_grad or k > slots or
                    any(t.device != features.device for t in (coords, parents, valid))):
                raise RuntimeError('CTS cache shape/device/detached-geometry mismatch')
            plan = build_triadic_plan(coords.detach().cpu().tolist(),
                                      parents.detach().cpu().tolist(),
                                      valid.detach().cpu().tolist(),
                                      self.max_middle_tokens)
            state = features[b]
            for rows in plan['rounds']:
                own_ids = torch.tensor([row[2] for row in rows], dtype=torch.long, device=features.device)
                fields = [state.index_select(0, own_ids)]
                for slot in (3, 4):
                    # Missing/aliased donor is an actual private zero work slot,
                    # never an index pointing to a real token with ID0.
                    field = features.new_zeros((len(rows), self.channels))
                    recipients = [i for i, row in enumerate(rows) if row[slot] is not None]
                    if recipients:
                        out_ids = torch.tensor(recipients, dtype=torch.long, device=features.device)
                        in_ids = torch.tensor([rows[i][slot] for i in recipients], dtype=torch.long, device=features.device)
                        field = field.index_copy(0, out_ids, state.index_select(0, in_ids))
                    fields.append(field)
                # Every own/+/- gather above uses OLD state. A single functional
                # scatter updates all receivers only after the original map/GELU.
                mixed = self.activation(self.mix(torch.cat(fields, dim=-1)))
                state = state.index_copy(0, own_ids, mixed)
            if plan['singleton_ids']:
                ids = torch.tensor(plan['singleton_ids'], dtype=torch.long, device=features.device)
                own = features[b].index_select(0, ids)
                singleton = self.activation(self.mix(torch.cat((own, torch.zeros_like(own), torch.zeros_like(own)), dim=-1)))
                state = state.index_copy(0, ids, singleton)
            active_ids = tuple(token for group in plan['groups'] for token in group['order'])
            output = features.new_zeros((slots, self.channels))
            if active_ids:
                ids = torch.tensor(active_ids, dtype=torch.long, device=features.device)
                output = output.index_copy(0, ids, state.index_select(0, ids))
            outputs.append(output)
        # Unsupported/padded slots get delta0. The original CTF cf skip is outside
        # this module, with no extra residual, learned gate or injection here.
        return torch.stack(outputs, dim=0) if outputs else torch.zeros_like(features)
