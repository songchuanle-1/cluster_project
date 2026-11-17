"""M227 LFT: nonlinear lifting of true hierarchy banks around original FFNs."""
import torch
import torch.nn as nn


def build_lifting_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    def ids(values, limit):
        values = list(values)
        if any(type(i) is not int or i < 0 or i >= limit for i in values):
            raise ValueError('Integer original hierarchy IDs in range required')
        return values
    k0, k1, k2 = bank_sizes
    points = ids(point_ids, k0)
    fm = ids(fine_to_middle, k1)
    mc = ids(middle_to_coarse, k2)
    if len(fm) > k0 or len(mc) > k1:
        raise ValueError('Membership exceeds original child bank')
    fine = sorted(set(points))
    if any(i >= len(fm) for i in fine):
        raise ValueError('Supported fine row lacks original parent')
    middle = sorted({fm[i] for i in fine})
    if any(j >= len(mc) for j in middle):
        raise ValueError('Supported middle row lacks original parent')
    coarse = sorted({mc[j] for j in middle})
    fp = [middle.index(fm[i]) for i in fine]
    mp = [coarse.index(mc[j]) for j in middle]
    return {'fine_ids': fine, 'middle_ids': middle, 'coarse_ids': coarse,
            'fine_parent_positions': fp, 'middle_parent_positions': mp,
            'middle_fine_counts': [fp.count(j) for j in range(len(middle))],
            'coarse_middle_counts': [mp.count(j) for j in range(len(coarse))],
            'point_count': len(points)}


def prepare_lifting_plans(levels, cluster_ids_list):
    if len(levels) != 3 or len(cluster_ids_list) != 3 or any(x.ndim != 3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch = int(levels[0].shape[0])
    channels = int(levels[0].shape[2])
    widths = [int(x.shape[1]) for x in levels]
    if any(int(x.shape[0]) != batch or int(x.shape[2]) != channels or
           x.device != levels[0].device or x.dtype != levels[0].dtype for x in levels):
        raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(values) != batch for values in cluster_ids_list):
        raise ValueError('Membership batch mismatch')
    return [build_lifting_plan(*(values[b].detach().cpu().tolist() for values in cluster_ids_list), widths)
            for b in range(batch)]


def mean_by_parent(messages, parent_positions, counts):
    """Private equal true-child mean; supported parent counts are positive."""
    index = torch.tensor(parent_positions, device=messages.device, dtype=torch.long)
    summed = messages.new_zeros((len(counts), int(messages.shape[1]))).index_add(0, index, messages)
    return summed / messages.new_tensor(counts).unsqueeze(-1)


class NonlinearLiftingComposition(nn.Module):
    def __init__(self, channels):
        super().__init__()
        if type(channels) is not int or channels <= 0:
            raise ValueError('Positive integer channels required')
        self.channels = channels
        self.predict_fine = nn.Linear(channels, channels)
        self.update_middle = nn.Linear(channels, channels)
        self.predict_middle = nn.Linear(channels, channels)
        self.update_coarse = nn.Linear(channels, channels)
        self.activation = nn.GELU()

    def forward(self, normalized, cluster_ids_list, ffns):
        plans = prepare_lifting_plans(normalized, cluster_ids_list)
        if len(ffns) != 3 or any(int(x.shape[2]) != self.channels for x in normalized):
            raise ValueError('Original three FFNs and unchanged channels required')
        batch = int(normalized[0].shape[0])
        widths = [int(x.shape[1]) for x in normalized]
        flat = [x.reshape(batch * widths[level], self.channels) for level, x in enumerate(normalized)]
        output = [x.new_zeros(x.shape) for x in flat]
        destinations = [[], [], []]
        fine_parents, middle_parents, fine_counts, middle_counts = [], [], [], []
        middle_offset = coarse_offset = 0
        for b, plan in enumerate(plans):
            for level, key in enumerate(('fine_ids', 'middle_ids', 'coarse_ids')):
                destinations[level].extend(b * widths[level] + i for i in plan[key])
            fine_parents.extend(middle_offset + p for p in plan['fine_parent_positions'])
            middle_parents.extend(coarse_offset + p for p in plan['middle_parent_positions'])
            fine_counts.extend(plan['middle_fine_counts'])
            middle_counts.extend(plan['coarse_middle_counts'])
            middle_offset += len(plan['middle_ids'])
            coarse_offset += len(plan['coarse_ids'])
        if not destinations[0]:
            return [x.reshape(normalized[level].shape) for level, x in enumerate(output)]
        index = [torch.tensor(values, device=normalized[0].device, dtype=torch.long) for values in destinations]
        fine, middle, coarse = [flat[level].index_select(0, index[level]) for level in range(3)]
        fp = torch.tensor(fine_parents, device=fine.device, dtype=torch.long)
        mp = torch.tensor(middle_parents, device=fine.device, dtype=torch.long)

        predicted_fine = self.activation(self.predict_fine(middle))
        detail_fine = fine - predicted_fine.index_select(0, fp)
        lifted_middle = middle + self.activation(self.update_middle(mean_by_parent(detail_fine, fine_parents, fine_counts)))
        predicted_middle = self.activation(self.predict_middle(coarse))
        detail_middle = lifted_middle - predicted_middle.index_select(0, mp)
        lifted_coarse = coarse + self.activation(self.update_coarse(mean_by_parent(detail_middle, middle_parents, middle_counts)))

        # Original modules remain registered only under the caller's cluster_ffn.
        fine_core = ffns[0](detail_fine)
        middle_core = ffns[1](detail_middle)
        coarse_core = ffns[2](lifted_coarse)

        coarse_out = coarse_core - self.activation(self.update_coarse(mean_by_parent(middle_core, middle_parents, middle_counts)))
        lifted_middle_out = middle_core + self.activation(self.predict_middle(coarse_out)).index_select(0, mp)
        middle_out = lifted_middle_out - self.activation(self.update_middle(mean_by_parent(fine_core, fine_parents, fine_counts)))
        fine_out = fine_core + self.activation(self.predict_fine(middle_out)).index_select(0, fp)
        for level, value in enumerate((fine_out, middle_out, coarse_out)):
            output[level] = output[level].index_copy(0, index[level], value)
        return [x.reshape(normalized[level].shape) for level, x in enumerate(output)]
