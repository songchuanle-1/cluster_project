"""Native spatial-chain energy with hierarchy analysis and synthesis.

The private graph uses unchanged true ancestry and coordinate-only chains
inside each original fine/middle/coarse support group. It changes neither
original memberships nor HCG delivery. Efficacy and novelty are unmeasured.
"""
import math
import torch
import torch.nn as nn


def build_support_plan(ids0, ids1, ids2, valid_count, widths):
    if len(widths) != 3 or len(ids0) != valid_count:
        raise ValueError('NSD needs three scales and one fine ID per valid point')
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


def build_chain_plan(coordinates, labels, count):
    """Coordinate-only adjacent chains; exact ties are merged, never ordered.

    Coordinate-coincident values are averaged before contrasts. This removes
    an input-row tie break and ensures geometry, rather than feature content
    or an arbitrary row permutation, determines every private edge.
    """
    if len(coordinates) != len(labels) or isinstance(count, bool) or count < 0:
        raise ValueError('NSD chain inputs disagree')
    by_parent = [{} for _ in range(count)]
    for i, (xyz, parent) in enumerate(zip(coordinates, labels)):
        if (isinstance(parent, bool) or not isinstance(parent, int)
                or parent < 0 or parent >= count):
            raise ValueError('invalid chain parent')
        if len(xyz) != 3 or any(not math.isfinite(x) for x in xyz):
            raise ValueError('chain requires finite original 3D coordinates')
        by_parent[parent].setdefault(tuple(xyz), []).append(i)
    p_to_group = [-1] * len(labels)
    groups, group_parent, left, right, edge_parent = [], [], [], [], []
    for parent, points_by_xyz in enumerate(by_parent):
        ordered = []
        for xyz in sorted(points_by_xyz):
            group = len(groups)
            rows = points_by_xyz[xyz]
            groups.append(rows)
            group_parent.append(parent)
            ordered.append(group)
            for row in rows:
                p_to_group[row] = group
        for u, v in zip(ordered[:-1], ordered[1:]):
            left.append(u)
            right.append(v)
            edge_parent.append(parent)
    return {
        'point_to_coordinate': p_to_group, 'groups': groups,
        'group_parent': group_parent, 'left': left, 'right': right,
        'edge_parent': edge_parent,
    }


def _group_mean(values, labels, count):
    total = values.new_zeros((count, values.shape[-1])).index_add(0, labels, values)
    mass = values.new_zeros((count, 1)).index_add(
        0, labels, values.new_ones((values.shape[0], 1)))
    return total / mass.clamp_min(1)


def chain_energy(values, coordinates, labels, count):
    """Mean squared adjacent-coordinate-group feature contrast per parent."""
    plan = build_chain_plan(
        coordinates.detach().cpu().tolist(), labels.tolist(), count)
    if not plan['left']:
        return values.new_zeros((count, values.shape[-1]))
    device = values.device
    group = torch.tensor(plan['point_to_coordinate'], device=device, dtype=torch.long)
    means = _group_mean(values, group, len(plan['groups']))
    left = torch.tensor(plan['left'], device=device, dtype=torch.long)
    right = torch.tensor(plan['right'], device=device, dtype=torch.long)
    owner = torch.tensor(plan['edge_parent'], device=device, dtype=torch.long)
    return _group_mean(
        (means.index_select(0, left) - means.index_select(0, right)).square(),
        owner, count)


class HierarchicalSpatialDirichlet(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.analysis = nn.Sequential(
            nn.Linear(3 * channels, channels), nn.GELU(),
            nn.Linear(channels, channels))
        self.synthesis = nn.Sequential(
            nn.Linear(2 * channels, channels), nn.GELU(),
            nn.Linear(channels, channels))

    def forward(self, points, positions, point_mask, normalized, cluster_ids_list):
        if len(normalized) != 3 or len(cluster_ids_list) != 3:
            raise ValueError('NSD requires the original three hierarchy scales')
        if positions is None or positions.shape[:2] != points.shape[:2] or positions.shape[-1] != 3:
            raise ValueError('NSD requires original padded native coordinates')
        batch_count, _, channels = points.shape
        if channels != self.channels:
            raise ValueError('NSD channel mismatch')
        widths = [bank.shape[1] for bank in normalized]
        output = [[], [], []]
        for batch in range(batch_count):
            valid = points[batch][~point_mask[batch]]
            coords = positions[batch][~point_mask[batch]]
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
            f0 = _group_mean(valid, p0, counts[0])
            x0 = _group_mean(coords, p0, counts[0])
            f1 = _group_mean(f0, p1, counts[1])
            x1 = _group_mean(x0, p1, counts[1])
            energies = [
                chain_energy(valid, coords, p0, counts[0]),
                chain_energy(f0, x0, p1, counts[1]),
                chain_energy(f1, x1, p2, counts[2]),
            ]
            selected = [normalized[level][batch].index_select(0, ids[level])
                        for level in range(3)]
            fine_state = self.analysis(torch.cat(
                (selected[0], energies[0], torch.zeros_like(selected[0])), dim=-1))
            middle_state = self.analysis(torch.cat(
                (selected[1], energies[1], _group_mean(fine_state, p1, counts[1])), dim=-1))
            coarse_state = self.analysis(torch.cat(
                (selected[2], energies[2], _group_mean(middle_state, p2, counts[2])), dim=-1))
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
