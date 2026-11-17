"""M223 FCB: scene-local true-fine x true-coarse vector-message graph."""
import torch
import torch.nn as nn


def _original_ids(values, limit):
    values = list(values)
    if any(type(i) is not int or i < 0 or i >= limit for i in values):
        raise ValueError('Integer original bank IDs in range required')
    return values


def build_fine_coarse_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    """True roots are composed from actual point-supported fine paths, not padding."""
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    k0, k1, k2 = bank_sizes
    points = _original_ids(point_ids, k0)
    f2m = _original_ids(fine_to_middle, k1)
    m2c = _original_ids(middle_to_coarse, k2)
    if len(f2m) > k0 or len(m2c) > k1:
        raise ValueError('Membership exceeds original child bank')
    fine = sorted(set(points))
    if any(i >= len(f2m) for i in fine):
        raise ValueError('Supported fine row lacks original parent')
    middle = sorted({f2m[i] for i in fine})
    if any(j >= len(m2c) for j in middle):
        raise ValueError('Supported middle row lacks original parent')
    coarse = sorted({m2c[j] for j in middle})
    middle_positions = {j: pos for pos, j in enumerate(middle)}
    fine_parents = [middle_positions[f2m[i]] for i in fine]
    middle_counts = [0] * len(middle)
    for parent in fine_parents: middle_counts[parent] += 1
    pair_fine = [f for f in range(len(fine)) for _ in coarse]
    pair_coarse = [c for _ in fine for c in range(len(coarse))]
    return {'fine_ids': fine, 'middle_ids': middle, 'coarse_ids': coarse,
            'fine_parent_positions': fine_parents, 'middle_fine_counts': middle_counts,
            'pair_fine_positions': pair_fine, 'pair_coarse_positions': pair_coarse,
            'fine_pair_counts': [len(coarse)] * len(fine),
            'coarse_pair_counts': [len(fine)] * len(coarse),
            'pair_count': len(pair_fine), 'point_count': len(points)}


def prepare_fine_coarse_plans(levels, cluster_ids_list):
    if len(levels) != 3 or len(cluster_ids_list) != 3 or any(x.ndim != 3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch = int(levels[0].shape[0]); channels = int(levels[0].shape[2])
    if any(int(x.shape[0]) != batch or int(x.shape[2]) != channels or
           x.device != levels[0].device or x.dtype != levels[0].dtype for x in levels):
        raise ValueError('Bank batch/channel/device/dtype mismatch')
    if any(len(values) != batch for values in cluster_ids_list):
        raise ValueError('Membership batch mismatch')
    widths = [int(x.shape[1]) for x in levels]
    return [build_fine_coarse_plan(*(values[b].detach().cpu().tolist()
                                    for values in cluster_ids_list), widths)
            for b in range(batch)]


def equal_message_means(messages, parent_positions, counts):
    """Private fixed vector-message means; original raw pooling is untouched."""
    index = torch.tensor(parent_positions, device=messages.device, dtype=torch.long)
    summed = messages.new_zeros((len(counts), messages.shape[1])).index_add(0, index, messages)
    return summed / messages.new_tensor(counts).unsqueeze(-1)


class FineCoarseBipartiteComposition(nn.Module):
    def __init__(self, channels):
        super().__init__()
        if type(channels) is not int or channels <= 0:
            raise ValueError('Positive integer channels required')
        self.channels = channels
        self.pair_map = nn.Linear(2 * channels, channels)
        self.middle_map = nn.Linear(2 * channels, channels)
        self.activation = nn.GELU()

    def forward(self, normalized, cluster_ids_list):
        plans = prepare_fine_coarse_plans(normalized, cluster_ids_list)
        if any(int(x.shape[2]) != self.channels for x in normalized):
            raise ValueError('FCB channels changed')
        batch = int(normalized[0].shape[0]); c = self.channels
        widths = [int(x.shape[1]) for x in normalized]
        flat = [x.reshape(batch * widths[level], c) for level, x in enumerate(normalized)]
        ids = [[], [], []]; pair_fine=[];pair_coarse=[];fine_parents=[]
        fine_counts=[];coarse_counts=[];middle_counts=[]
        for b, plan in enumerate(plans):
            fo, mo, co = (len(values) for values in ids)
            for level, key in enumerate(('fine_ids', 'middle_ids', 'coarse_ids')):
                ids[level].extend(b * widths[level] + i for i in plan[key])
            pair_fine.extend(fo + i for i in plan['pair_fine_positions'])
            pair_coarse.extend(co + i for i in plan['pair_coarse_positions'])
            fine_parents.extend(mo + i for i in plan['fine_parent_positions'])
            fine_counts.extend(plan['fine_pair_counts']);coarse_counts.extend(plan['coarse_pair_counts'])
            middle_counts.extend(plan['middle_fine_counts'])
        delta = [x.new_zeros(x.shape) for x in flat]
        if not ids[0]:
            return [x.reshape(normalized[level].shape) for level, x in enumerate(delta)]
        device = normalized[0].device
        index = [torch.tensor(values, device=device, dtype=torch.long) for values in ids]
        z = [flat[level].index_select(0, index[level]) for level in range(3)]
        fi = torch.tensor(pair_fine, device=device, dtype=torch.long)
        ci = torch.tensor(pair_coarse, device=device, dtype=torch.long)
        q = self.activation(self.pair_map(torch.cat([z[0].index_select(0, fi),
                                                    z[2].index_select(0, ci)], dim=-1)))
        fine_delta = equal_message_means(q, pair_fine, fine_counts)
        coarse_delta = equal_message_means(q, pair_coarse, coarse_counts)
        middle_context = equal_message_means(fine_delta, fine_parents, middle_counts)
        middle_delta = self.activation(self.middle_map(torch.cat([z[1], middle_context], dim=-1)))
        for level, values in enumerate((fine_delta, middle_delta, coarse_delta)):
            delta[level] = delta[level].index_copy(0, index[level], values)
        return [x.reshape(normalized[level].shape) for level, x in enumerate(delta)]
