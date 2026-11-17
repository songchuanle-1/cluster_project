"""Native conditional distribution embedding on the unchanged hierarchy.

The first shared value transformation acts on each valid native point before
its original fine-leaf mean. Original bank aggregation, support memberships
and HCG delivery remain outside this private analysis/synthesis graph.
Efficacy, population bottlenecks and novelty have not been established.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


def build_support_plan(ids0, ids1, ids2, valid_count, widths):
    if len(widths) != 3 or len(ids0) != valid_count:
        raise ValueError('NDE needs three scales and one fine ID per valid point')
    if any(isinstance(x, bool) or not isinstance(x, int) for x in ids0):
        raise ValueError('fine membership IDs must be integers')
    if any(x < 0 or x >= widths[0] for x in ids0):
        raise ValueError('valid point has invalid fine membership')
    fine = sorted(set(ids0))
    if any(x >= len(ids1) for x in fine):
        raise ValueError('missing original fine-to-middle membership')
    mid_values = [ids1[x] for x in fine]
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0
           or x >= widths[1] for x in mid_values):
        raise ValueError('supported fine node has invalid middle membership')
    middle = sorted(set(mid_values))
    if any(x >= len(ids2) for x in middle):
        raise ValueError('missing original middle-to-coarse membership')
    coarse_values = [ids2[x] for x in middle]
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0
           or x >= widths[2] for x in coarse_values):
        raise ValueError('supported middle node has invalid coarse membership')
    coarse = sorted(set(coarse_values))
    fpos = {value: i for i, value in enumerate(fine)}
    mpos = {value: i for i, value in enumerate(middle)}
    cpos = {value: i for i, value in enumerate(coarse)}
    return {
        'nodes': [fine, middle, coarse],
        'point_to_fine': [fpos[x] for x in ids0],
        'fine_to_middle': [mpos[x] for x in mid_values],
        'middle_to_coarse': [cpos[x] for x in coarse_values],
    }


def _group_mean(values, labels, count):
    total = values.new_zeros((count, values.shape[-1])).index_add(0, labels, values)
    mass = values.new_zeros((count, 1)).index_add(
        0, labels, values.new_ones((values.shape[0], 1)))
    return total / mass.clamp_min(1)


class _ConditionalAnalysis(nn.Sequential):
    """Same affine parameters; reuse the parent half before child gathering."""

    def forward(self, values, parent, labels):
        first = self[0]
        channels = values.shape[-1]
        value_affine = F.linear(values, first.weight[:, :channels], first.bias)
        parent_affine = F.linear(parent, first.weight[:, channels:], None)
        hidden = value_affine + parent_affine.index_select(0, labels)
        return self[2](self[1](hidden))


class HierarchicalDistributionEmbedding(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.analysis = _ConditionalAnalysis(
            nn.Linear(2 * channels, channels), nn.GELU(),
            nn.Linear(channels, channels))
        self.synthesis = nn.Sequential(
            nn.Linear(2 * channels, channels), nn.GELU(),
            nn.Linear(channels, channels))

    def forward(self, points, point_mask, normalized, cluster_ids_list):
        if len(normalized) != 3 or len(cluster_ids_list) != 3:
            raise ValueError('NDE requires the original three hierarchy scales')
        if points.ndim != 3 or point_mask.shape != points.shape[:2]:
            raise ValueError('NDE requires the original padded native point mask')
        batch_count, _, channels = points.shape
        if channels != self.channels:
            raise ValueError('NDE channel mismatch')
        if any(bank.ndim != 3 or bank.shape[0] != batch_count
               or bank.shape[-1] != channels for bank in normalized):
            raise ValueError('NDE normalized bank shapes disagree')
        widths = [bank.shape[1] for bank in normalized]
        output = [[], [], []]
        for batch in range(batch_count):
            valid = points[batch][~point_mask[batch]]
            plan = build_support_plan(
                *[cluster_ids_list[level][batch].tolist() for level in range(3)],
                valid.shape[0], widths)
            counts = [len(ids) for ids in plan['nodes']]
            if counts[0] == 0:
                for level in range(3):
                    output[level].append(normalized[level][batch].new_zeros(
                        (widths[level], channels)))
                continue
            ids = [torch.tensor(x, device=points.device, dtype=torch.long)
                   for x in plan['nodes']]
            p0 = torch.tensor(plan['point_to_fine'], device=points.device, dtype=torch.long)
            p1 = torch.tensor(plan['fine_to_middle'], device=points.device, dtype=torch.long)
            p2 = torch.tensor(plan['middle_to_coarse'], device=points.device, dtype=torch.long)
            selected = [normalized[level][batch].index_select(0, ids[level])
                        for level in range(3)]
            fine_state = _group_mean(self.analysis(valid, selected[0], p0), p0, counts[0])
            middle_state = _group_mean(self.analysis(fine_state, selected[1], p1), p1, counts[1])
            coarse_state = _group_mean(self.analysis(middle_state, selected[2], p2), p2, counts[2])
            coarse_delta = self.synthesis(torch.cat(
                (coarse_state, torch.zeros_like(coarse_state)), dim=-1))
            middle_delta = self.synthesis(torch.cat(
                (middle_state, coarse_delta.index_select(0, p2)), dim=-1))
            fine_delta = self.synthesis(torch.cat(
                (fine_state, middle_delta.index_select(0, p1)), dim=-1))
            for level, delta in enumerate((fine_delta, middle_delta, coarse_delta)):
                empty = normalized[level][batch].new_zeros((widths[level], channels))
                output[level].append(empty.index_copy(0, ids[level], delta))
        return [torch.stack(items, dim=0) for items in output]
