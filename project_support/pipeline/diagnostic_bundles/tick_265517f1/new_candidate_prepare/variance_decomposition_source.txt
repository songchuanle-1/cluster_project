"""Hierarchical variance decomposition on original true-supported memberships.

Private equal-child moments distinguish within-leaf variation from variation
of child means. Raw M95 semantic banks, membership, HCG and CSORT stay outside
this core. No query, learned pooling weights, channel attention or new routing.
"""
import torch
import torch.nn as nn


def build_support_plan(ids0, ids1, ids2, valid_count, widths):
    """Compress only nodes reached by actual valid points; retain original IDs."""
    if len(widths) != 3 or len(ids0) != valid_count:
        raise ValueError('HVD needs three scales and one fine ID per valid point')
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
    fine_pos = {value: i for i, value in enumerate(fine)}
    middle_pos = {value: i for i, value in enumerate(middle)}
    coarse_pos = {value: i for i, value in enumerate(coarse)}
    return {
        'nodes': [fine, middle, coarse],
        'point_to_fine': [fine_pos[x] for x in ids0],
        'fine_to_middle': [middle_pos[x] for x in mid_values],
        'middle_to_coarse': [coarse_pos[x] for x in coarse_values],
    }


def _group_mean(values, labels, count):
    total = values.new_zeros((count, values.shape[-1])).index_add(0, labels, values)
    ones = values.new_ones((values.shape[0], 1))
    mass = values.new_zeros((count, 1)).index_add(0, labels, ones)
    return total / mass.clamp_min(1)


def moment_components(points, point_to_fine, fine_to_middle, middle_to_coarse,
                      fine_count, middle_count, coarse_count):
    """Real-arithmetic total-variance decomposition with equal true-child means.

    Fine moments use equal actual points. Each higher level then assigns equal
    mass to each true-supported child, independently of child point population.
    All private centers are recomputed from these exact moment semantics; raw
    M95 upper banks are never substituted for these private centers.
    """
    fine_mean = _group_mean(points, point_to_fine, fine_count)
    fine_var = _group_mean(
        (points - fine_mean.index_select(0, point_to_fine)).square(),
        point_to_fine, fine_count)
    middle_mean = _group_mean(fine_mean, fine_to_middle, middle_count)
    middle_within = _group_mean(fine_var, fine_to_middle, middle_count)
    middle_between = _group_mean(
        (fine_mean - middle_mean.index_select(0, fine_to_middle)).square(),
        fine_to_middle, middle_count)
    middle_var = middle_within + middle_between
    coarse_mean = _group_mean(middle_mean, middle_to_coarse, coarse_count)
    coarse_within = _group_mean(middle_var, middle_to_coarse, coarse_count)
    coarse_between = _group_mean(
        (middle_mean - coarse_mean.index_select(0, middle_to_coarse)).square(),
        middle_to_coarse, coarse_count)
    return fine_var, middle_within, middle_between, coarse_within, coarse_between


def pack_moment_rows(normalized, stats, fine_to_middle, middle_to_coarse):
    fine_var, middle_within, middle_between, coarse_within, coarse_between = stats
    coarse_for_middle = coarse_between.index_select(0, middle_to_coarse)
    fine_rows = torch.cat((
        normalized[0], fine_var,
        middle_between.index_select(0, fine_to_middle),
        coarse_for_middle.index_select(0, fine_to_middle)), dim=-1)
    middle_rows = torch.cat((
        normalized[1], middle_within, middle_between, coarse_for_middle), dim=-1)
    coarse_rows = torch.cat((
        normalized[2], coarse_within, coarse_between,
        torch.zeros_like(coarse_between)), dim=-1)
    return [fine_rows, middle_rows, coarse_rows]


class HierarchicalVarianceDecomposition(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.factor = nn.Sequential(
            nn.Linear(4 * channels, channels),
            nn.GELU(),
            nn.Linear(channels, channels))

    def forward(self, points, point_mask, normalized, cluster_ids_list):
        if len(normalized) != 3 or len(cluster_ids_list) != 3:
            raise ValueError('HVD requires the original three-scale hierarchy')
        batch_count, _, channels = points.shape
        if channels != self.channels:
            raise ValueError('HVD channel mismatch')
        widths = [bank.shape[1] for bank in normalized]
        result = [[], [], []]
        for batch in range(batch_count):
            valid = points[batch][~point_mask[batch]]
            plan = build_support_plan(
                *[cluster_ids_list[level][batch].tolist() for level in range(3)],
                valid.shape[0], widths)
            node_ids = [torch.tensor(ids, device=points.device, dtype=torch.long)
                        for ids in plan['nodes']]
            counts = [len(ids) for ids in plan['nodes']]
            if counts[0] == 0:
                for level in range(3):
                    result[level].append(normalized[level][batch].new_zeros(
                        (widths[level], channels)))
                continue
            p0 = torch.tensor(plan['point_to_fine'], device=points.device, dtype=torch.long)
            p1 = torch.tensor(plan['fine_to_middle'], device=points.device, dtype=torch.long)
            p2 = torch.tensor(plan['middle_to_coarse'], device=points.device, dtype=torch.long)
            stats = moment_components(valid, p0, p1, p2, *counts)
            selected = [normalized[level][batch].index_select(0, node_ids[level])
                        for level in range(3)]
            packed = pack_moment_rows(selected, stats, p1, p2)
            changes = self.factor(torch.cat(packed, dim=0)).split(counts, dim=0)
            for level in range(3):
                empty = normalized[level][batch].new_zeros((widths[level], channels))
                result[level].append(empty.index_copy(0, node_ids[level], changes[level]))
        return [torch.stack(items, dim=0) for items in result]
