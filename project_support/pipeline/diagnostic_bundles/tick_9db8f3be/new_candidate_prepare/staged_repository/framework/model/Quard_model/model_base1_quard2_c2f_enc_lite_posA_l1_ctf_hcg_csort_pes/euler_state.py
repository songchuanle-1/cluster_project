"""M221: persistent node states on the original supported hierarchy forest.

The two deterministic closed walks use original ID child order, then its reverse.
They are order sensitive; the second walk continues the first walk's states.
"""
import torch
import torch.nn as nn


def build_euler_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    """Build actual directed events only; never add a padding or empty-root event."""
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    k0, k1, k2 = bank_sizes
    def ids(values, limit):
        values = list(values)
        if any(type(i) is not int or i < 0 or i >= limit for i in values):
            raise ValueError('Invalid original hierarchy IDs')
        return values
    points = ids(point_ids, k0)
    f2m = ids(fine_to_middle, k1)
    m2c = ids(middle_to_coarse, k2)
    if len(f2m) > k0 or len(m2c) > k1:
        raise ValueError('Membership exceeds original bank')
    fine = sorted(set(points))
    if any(i >= len(f2m) for i in fine):
        raise ValueError('Supported fine row lacks parent')
    middle = sorted({f2m[i] for i in fine})
    if any(j >= len(m2c) for j in middle):
        raise ValueError('Supported middle row lacks parent')
    coarse = sorted({m2c[j] for j in middle})
    node_keys = [(level, i) for level, values in enumerate((fine, middle, coarse)) for i in values]
    position = {key: i for i, key in enumerate(node_keys)}
    fine_children = {j: [] for j in middle}
    middle_children = {k: [] for k in coarse}
    for i in fine:
        fine_children[f2m[i]].append(i)
    for j in middle:
        middle_children[m2c[j]].append(j)
    components = []
    for k in coarse:
        root = position[(2, k)]
        walk = [root]
        for j in middle_children[k]:
            parent = position[(1, j)]
            walk.append(parent)
            for i in fine_children[j]:
                walk.extend((position[(0, i)], parent))
            walk.append(root)
        forward = list(zip(walk[:-1], walk[1:]))
        reverse_walk = list(reversed(walk))
        backward = list(zip(reverse_walk[:-1], reverse_walk[1:]))
        edges = len(middle_children[k]) + sum(len(fine_children[j]) for j in middle_children[k])
        components.append({'root_id': k, 'walk': walk, 'forward_events': forward,
                           'backward_events': backward, 'events': forward + backward,
                           'edge_count': edges})
    return {'fine_ids': fine, 'middle_ids': middle, 'coarse_ids': coarse,
            'node_keys': node_keys, 'components': components,
            'edge_count': len(fine) + len(middle), 'point_count': len(points)}


def prepare_euler_plans(levels, cluster_ids_list):
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
    return [build_euler_plan(*(values[b].detach().cpu().tolist() for values in cluster_ids_list), widths)
            for b in range(batch)]


def build_event_rounds(plans):
    """Batch one true event per independent component, excluding finished components."""
    components = []
    offset = 0
    for plan in plans:
        for component in plan['components']:
            components.append([(offset + sender, offset + receiver)
                               for sender, receiver in component['events']])
        offset += len(plan['node_keys'])
    return [[events[r] for events in components if r < len(events)]
            for r in range(max((len(events) for events in components), default=0))]


class PalindromicEulerStateComposition(nn.Module):
    def __init__(self, channels):
        super().__init__()
        if type(channels) is not int or channels <= 0:
            raise ValueError('Positive integer channels required')
        self.channels = channels
        self.cell = nn.Linear(2 * channels, channels)
        self.activation = nn.GELU()

    def forward(self, normalized, cluster_ids_list):
        plans = prepare_euler_plans(normalized, cluster_ids_list)
        if any(int(x.shape[2]) != self.channels for x in normalized):
            raise ValueError('Channels changed')
        batch = int(normalized[0].shape[0])
        widths = [int(x.shape[1]) for x in normalized]
        flat = [x.reshape(batch * widths[level], self.channels)
                for level, x in enumerate(normalized)]
        output = [x.new_zeros(x.shape) for x in flat]
        # Replacing Python references preserves old Tensor nodes in the autograd DAG.
        # No Tensor feature is detached or mutated in place; no full bank is copied per event.
        states = []
        destinations = [[], [], []]
        state_positions = [[], [], []]
        for b, plan in enumerate(plans):
            for level, original_id in plan['node_keys']:
                state_positions[level].append(len(states))
                destinations[level].append(b * widths[level] + original_id)
                states.append(flat[level][b * widths[level] + original_id])
        for events in build_event_rounds(plans):
            # All active components read their current states before any receiver is replaced.
            receiver = torch.stack([states[v] for u, v in events], dim=0)
            sender = torch.stack([states[u] for u, v in events], dim=0)
            updated = self.activation(self.cell(torch.cat([receiver, sender], dim=-1)))
            for row, (u, v) in enumerate(events):
                states[v] = updated[row]
        for level in range(3):
            if destinations[level]:
                index = torch.tensor(destinations[level], device=normalized[0].device, dtype=torch.long)
                values = torch.stack([states[i] for i in state_positions[level]], dim=0)
                output[level] = output[level].index_copy(0, index, values)
        return [x.reshape(normalized[level].shape) for level, x in enumerate(output)]
