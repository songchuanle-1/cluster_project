"""M229 MIC: shared Boolean-lattice ancestry interaction, eight subset vertices."""
import torch
import torch.nn as nn


def _ids(values, limit, label):
    out = list(values)
    if any(type(i) is not int or i < 0 or i >= limit for i in out):
        raise ValueError(label + ' must be integer original bank IDs in range')
    return out


def build_mobius_path_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    """One path per true fine ID; upper means weight paths, not points or middles."""
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    k0, k1, k2 = bank_sizes
    points = _ids(point_ids, k0, 'point_ids')
    f2m = _ids(fine_to_middle, k1, 'fine_to_middle')
    m2c = _ids(middle_to_coarse, k2, 'middle_to_coarse')
    if len(f2m) > k0 or len(m2c) > k1:
        raise ValueError('Membership exceeds original bank')
    fine = sorted(set(points))
    if any(i >= len(f2m) for i in fine):
        raise ValueError('Supported fine row lacks parent')
    middle_for_paths = [f2m[i] for i in fine]
    if any(j >= len(m2c) for j in middle_for_paths):
        raise ValueError('Supported middle row lacks parent')
    coarse_for_paths = [m2c[j] for j in middle_for_paths]
    middle = sorted(set(middle_for_paths))
    coarse = sorted(set(coarse_for_paths))
    mid_positions = {j: pos for pos, j in enumerate(middle)}
    coarse_positions = {k: pos for pos, k in enumerate(coarse)}
    mp = [mid_positions[j] for j in middle_for_paths]
    cp = [coarse_positions[k] for k in coarse_for_paths]
    mc = [0] * len(middle)
    cc = [0] * len(coarse)
    for j in mp: mc[j] += 1
    for k in cp: cc[k] += 1
    return {'fine_ids': fine, 'middle_for_paths': middle_for_paths,
            'coarse_for_paths': coarse_for_paths, 'middle_ids': middle,
            'coarse_ids': coarse, 'middle_parent_positions': mp,
            'coarse_parent_positions': cp, 'middle_path_counts': mc,
            'coarse_path_counts': cc, 'path_count': len(fine), 'point_count': len(points)}


def prepare_mobius_path_plans(levels, cluster_ids_list):
    if len(levels) != 3 or len(cluster_ids_list) != 3 or any(x.ndim != 3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch = int(levels[0].shape[0])
    channels = int(levels[0].shape[2])
    if any(int(x.shape[0]) != batch or int(x.shape[2]) != channels or
           x.device != levels[0].device or x.dtype != levels[0].dtype for x in levels):
        raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(values) != batch for values in cluster_ids_list):
        raise ValueError('Membership batch mismatch')
    widths = [int(x.shape[1]) for x in levels]
    return [build_mobius_path_plan(*(values[b].detach().cpu().tolist()
                                     for values in cluster_ids_list), widths)
            for b in range(batch)]


def mean_mobius_paths(messages, parent_positions, counts):
    """Fixed private equal mean; never recompute or change the original raw banks."""
    index = torch.tensor(parent_positions, device=messages.device, dtype=torch.long)
    summed = messages.new_zeros((len(counts), messages.shape[1])).index_add(0, index, messages)
    return summed / messages.new_tensor(counts).unsqueeze(-1)


class AncestryMobiusInteraction(nn.Module):
    def __init__(self, channels):
        super().__init__()
        if type(channels) is not int or channels <= 0:
            raise ValueError('Positive integer channels required')
        self.channels = channels
        self.cell = nn.Linear(channels, channels)
        self.activation = nn.GELU()

    def forward(self, normalized, cluster_ids_list):
        plans = prepare_mobius_path_plans(normalized, cluster_ids_list)
        if any(int(x.shape[2]) != self.channels for x in normalized):
            raise ValueError('MIC channels changed')
        batch = int(normalized[0].shape[0])
        widths = [int(x.shape[1]) for x in normalized]
        flat = [x.reshape(batch * widths[level], self.channels)
                for level, x in enumerate(normalized)]
        fine_index=[];middle_input=[];coarse_input=[]
        middle_index=[];coarse_index=[];mp=[];cp=[];mc=[];cc=[]
        for b, plan in enumerate(plans):
            mo, co = len(middle_index), len(coarse_index)
            fine_index.extend(b * widths[0] + i for i in plan['fine_ids'])
            middle_input.extend(b * widths[1] + j for j in plan['middle_for_paths'])
            coarse_input.extend(b * widths[2] + k for k in plan['coarse_for_paths'])
            middle_index.extend(b * widths[1] + j for j in plan['middle_ids'])
            coarse_index.extend(b * widths[2] + k for k in plan['coarse_ids'])
            mp.extend(mo + j for j in plan['middle_parent_positions'])
            cp.extend(co + k for k in plan['coarse_parent_positions'])
            mc.extend(plan['middle_path_counts']);cc.extend(plan['coarse_path_counts'])
        delta = [x.new_zeros(x.shape) for x in flat]
        if not fine_index:
            return [x.reshape(normalized[level].shape) for level, x in enumerate(delta)]
        device = normalized[0].device
        index = [torch.tensor(values, device=device, dtype=torch.long)
                 for values in (fine_index, middle_input, coarse_input)]
        a, b, c = [flat[level].index_select(0, index[level]) for level in range(3)]
        # One shared map/GELU call for all eight subset vertices.
        n = len(fine_index)
        zero = a.new_zeros(a.shape)
        subset_inputs = torch.cat([a+b+c, a+b, a+c, b+c, a, b, c, zero], dim=0)
        subset_outputs = self.activation(self.cell(subset_inputs))
        contrast = (subset_outputs[:n] - subset_outputs[n:2*n]
                    - subset_outputs[2*n:3*n] - subset_outputs[3*n:4*n]
                    + subset_outputs[4*n:5*n] + subset_outputs[5*n:6*n]
                    + subset_outputs[6*n:7*n] - subset_outputs[7*n:8*n])
        middle_delta = mean_mobius_paths(contrast, mp, mc)
        coarse_delta = mean_mobius_paths(contrast, cp, cc)
        delta[0] = delta[0].index_copy(0, index[0], contrast)
        delta[1] = delta[1].index_copy(0, torch.tensor(middle_index, device=device, dtype=torch.long), middle_delta)
        delta[2] = delta[2].index_copy(0, torch.tensor(coarse_index, device=device, dtype=torch.long), coarse_delta)
        return [x.reshape(normalized[level].shape) for level, x in enumerate(delta)]
