"""Native joint position/feature scatter on unchanged true ancestry.

Position-feature moments, unlike feature variance, preserve signed spatial
association inside native fine leaves. No query, learned routing, attention,
inverse geometry fit, new pooling weights or new coordinate normalization.
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
    mass = values.new_zeros((count, 1)).index_add(
        0, labels, values.new_ones((values.shape[0], 1)))
    return total / mass.clamp_min(1)


def _centered_cross(position, feature, position_center, feature_center, labels, count):
    """Equal-population mean of signed outer products, flattened as 3C."""
    dx = position - position_center.index_select(0, labels)
    df = feature - feature_center.index_select(0, labels)
    cross = (dx.unsqueeze(-1) * df.unsqueeze(-2)).flatten(start_dim=1)
    return _group_mean(cross, labels, count)


def cross_scatter_components(points, positions, p0, p1, p2, n0, n1, n2):
    """Native-point fine moments, then equal-supported-child covariance law.

    Coordinate centers follow the SAME private equal-child measure as feature
    centers. Raw M95 upper semantic banks are never substituted for centers.
    """
    f0 = _group_mean(points, p0, n0)
    x0 = _group_mean(positions, p0, n0)
    j0 = _centered_cross(positions, points, x0, f0, p0, n0)
    f1 = _group_mean(f0, p1, n1)
    x1 = _group_mean(x0, p1, n1)
    w1 = _group_mean(j0, p1, n1)
    b1 = _centered_cross(x0, f0, x1, f1, p1, n1)
    total1 = w1 + b1
    f2 = _group_mean(f1, p2, n2)
    x2 = _group_mean(x1, p2, n2)
    w2 = _group_mean(total1, p2, n2)
    b2 = _centered_cross(x1, f1, x2, f2, p2, n2)
    return j0, w1, b1, w2, b2


def pack_cross_rows(normalized, stats, p1, p2):
    j0, w1, b1, w2, b2 = stats
    ancestor_between = b2.index_select(0, p2)
    fine = torch.cat((normalized[0], j0, b1.index_select(0, p1),
                      ancestor_between.index_select(0, p1)), dim=-1)
    middle = torch.cat((normalized[1], w1, b1, ancestor_between), dim=-1)
    coarse = torch.cat((normalized[2], w2, b2, torch.zeros_like(b2)), dim=-1)
    return [fine, middle, coarse]


class HierarchicalPositionFeatureScatter(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.factor = nn.Sequential(
            nn.Linear(10 * channels, channels), nn.GELU(),
            nn.Linear(channels, channels))

    def forward(self, points, positions, point_mask, normalized, cluster_ids_list):
        if len(normalized) != 3 or len(cluster_ids_list) != 3:
            raise ValueError('PSC requires the original three hierarchy scales')
        if positions is None or positions.shape[:2] != points.shape[:2] or positions.shape[-1] != 3:
            raise ValueError('PSC requires the original padded native point coordinates')
        batch_count, _, channels = points.shape
        if channels != self.channels:
            raise ValueError('PSC channel mismatch')
        widths = [bank.shape[1] for bank in normalized]
        result = [[], [], []]
        for batch in range(batch_count):
            valid = points[batch][~point_mask[batch]]
            coords = positions[batch][~point_mask[batch]].to(dtype=valid.dtype)
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
            stats = cross_scatter_components(valid, coords, p0, p1, p2, *counts)
            selected = [normalized[level][batch].index_select(0, node_ids[level])
                        for level in range(3)]
            packed = pack_cross_rows(selected, stats, p1, p2)
            changes = self.factor(torch.cat(packed, dim=0)).split(counts, dim=0)
            for level in range(3):
                empty = normalized[level][batch].new_zeros((widths[level], channels))
                result[level].append(empty.index_copy(0, node_ids[level], changes[level]))
        return [torch.stack(items, dim=0) for items in result]
