"""Supported coarse-root directed messages and original-ancestor synthesis."""
import torch
from torch import nn


def build_root_exchange_plan(point_to_fine, fine_to_middle, middle_to_coarse, widths):
    """Pure original-ID membership plan; no feature-dependent selection/weights.

    Work rows are (receiver coarse ID, sender coarse ID). A singleton has one
    private None sender, never a fake original token. Prefix/padding and true
    point support are distinct. All fine/middle ancestors follow original IDs.
    """
    if not all(isinstance(x, (list, tuple)) for x in (point_to_fine, fine_to_middle, middle_to_coarse, widths)):
        raise ValueError('CRE membership metadata must be sequences')
    if len(widths) != 3 or any(type(w) is not int or w < 0 for w in widths):
        raise ValueError('CRE expects three nonnegative token widths')
    for sequence in (point_to_fine, fine_to_middle, middle_to_coarse):
        if any(type(value) is not int or value < 0 for value in sequence):
            raise ValueError('CRE original IDs must be nonnegative integers')
    if len(fine_to_middle) > widths[0] or len(middle_to_coarse) > widths[1]:
        raise ValueError('CRE original child prefixes exceed padded bank widths')
    if any(i >= len(fine_to_middle) for i in point_to_fine):
        raise ValueError('CRE point-to-fine original ID is out of range')
    if any(i >= len(middle_to_coarse) for i in fine_to_middle):
        raise ValueError('CRE fine-to-middle original ID is out of range')
    if any(i >= widths[2] for i in middle_to_coarse):
        raise ValueError('CRE middle-to-coarse original ID is out of range')
    fine = sorted(set(point_to_fine))
    middle = sorted({fine_to_middle[i] for i in fine})
    roots = sorted({middle_to_coarse[i] for i in middle})
    work_rows = []
    root_groups = []
    for receiver in roots:
        donors = [sender for sender in roots if sender != receiver]
        if not donors:
            donors = [None]
        indices = []
        for sender in donors:
            indices.append(len(work_rows))
            work_rows.append((receiver, sender))
        root_groups.append({'root_id': receiver, 'message_row_ids': indices})
    return {
        'fine_ids': fine, 'middle_ids': middle, 'coarse_roots': roots,
        'fine_rows': [(i, middle_to_coarse[fine_to_middle[i]]) for i in fine],
        'middle_rows': [(i, middle_to_coarse[i]) for i in middle],
        'work_rows': work_rows, 'root_groups': root_groups,
        'real_directed_edge_count': len(roots) * max(len(roots) - 1, 0),
        'singleton_private_zero_rows': int(len(roots) == 1),
        'fine_prefix': len(fine_to_middle), 'middle_prefix': len(middle_to_coarse),
        'widths': list(widths),
    }


def equal_root_message_means(messages, groups):
    """Fixed equal mean of actual edge outputs; no learned pool score or count weight."""
    if not groups:
        return messages.new_zeros((0, messages.shape[-1]))
    values = []
    for indices in groups:
        if not indices:
            raise ValueError('CRE active root has no real/private message row')
        index = torch.tensor(indices, device=messages.device, dtype=torch.long)
        values.append(messages.index_select(0, index).mean(dim=0))
    return torch.stack(values, dim=0)


class CoarseRootDirectedExchange(nn.Module):
    """Three shared 2C-to-C maps; cross-root coarse then fine/middle synthesis."""
    def __init__(self, d_model, capacities):
        super().__init__()
        if type(d_model) is not int or d_model <= 0:
            raise ValueError('CRE channel width must be a positive integer')
        if not isinstance(capacities, (list, tuple)) or len(capacities) != 3 or any(type(k) is not int or k <= 0 for k in capacities):
            raise ValueError('CRE requires original three positive hierarchy capacities')
        self.d_model = d_model
        self.capacities = tuple(capacities)
        self.coarse_edge = nn.Linear(2 * d_model, d_model)
        self.fine_decode = nn.Linear(2 * d_model, d_model)
        self.middle_decode = nn.Linear(2 * d_model, d_model)
        self.activation = nn.GELU()

    def forward(self, normalized, cluster_ids_list):
        if not isinstance(normalized, (list, tuple)) or len(normalized) != 3:
            raise ValueError('CRE expects original fine/middle/coarse normalized banks')
        if any(x.ndim != 3 or x.shape[-1] != self.d_model for x in normalized):
            raise ValueError('CRE feature banks must have shape [B,K,C]')
        batch_size = int(normalized[0].shape[0])
        widths = [int(x.shape[1]) for x in normalized]
        if any(x.shape[0] != batch_size or x.device != normalized[0].device or x.dtype != normalized[0].dtype for x in normalized):
            raise ValueError('CRE bank batches/device/dtype differ')
        if any(width > cap for width, cap in zip(widths, self.capacities)):
            raise ValueError('CRE bank width exceeds unchanged native hierarchy capacity')
        if not isinstance(cluster_ids_list, (list, tuple)) or len(cluster_ids_list) != 3 or any(not isinstance(level, (list, tuple)) or len(level) != batch_size for level in cluster_ids_list):
            raise ValueError('CRE original hierarchy-ID batch shape differs')
        plans = []
        receivers, senders, root_ids, groups = [], [], [], []
        fine_rows, middle_rows = [], []
        for batch in range(batch_size):
            ids = [level[batch] for level in cluster_ids_list]
            if any(value.ndim != 1 for value in ids):
                raise ValueError('CRE original hierarchy IDs must be one-dimensional')
            plan = build_root_exchange_plan(*(value.detach().cpu().tolist() for value in ids), widths)
            plans.append(plan)
            offset = len(receivers)
            for receiver, sender in plan['work_rows']:
                receivers.append(batch * widths[2] + receiver)
                senders.append(None if sender is None else batch * widths[2] + sender)
            for group in plan['root_groups']:
                root_ids.append(batch * widths[2] + group['root_id'])
                groups.append([offset + i for i in group['message_row_ids']])
            fine_rows.extend((batch * widths[0] + child, batch * widths[2] + parent) for child, parent in plan['fine_rows'])
            middle_rows.extend((batch * widths[1] + child, batch * widths[2] + parent) for child, parent in plan['middle_rows'])
        deltas = [value.new_zeros(value.shape) for value in normalized]
        if not receivers:
            return deltas
        coarse = normalized[2].reshape(batch_size * widths[2], self.d_model)
        receiver_index = torch.tensor(receivers, device=coarse.device, dtype=torch.long)
        receiver_values = coarse.index_select(0, receiver_index)
        sender_values = coarse.new_zeros(receiver_values.shape)
        real_rows = [i for i, sender in enumerate(senders) if sender is not None]
        if real_rows:
            row_index = torch.tensor(real_rows, device=coarse.device, dtype=torch.long)
            sender_index = torch.tensor([senders[i] for i in real_rows], device=coarse.device, dtype=torch.long)
            sender_values = sender_values.index_copy(0, row_index, coarse.index_select(0, sender_index))
        messages = self.activation(self.coarse_edge(torch.cat((receiver_values, sender_values), dim=-1)))
        means = equal_root_message_means(messages, groups)
        root_index = torch.tensor(root_ids, device=coarse.device, dtype=torch.long)
        root_context = coarse.new_zeros(coarse.shape).index_copy(0, root_index, means)
        deltas[2] = root_context.reshape(normalized[2].shape)
        for level, rows, decode in ((0, fine_rows, self.fine_decode), (1, middle_rows, self.middle_decode)):
            if not rows:
                continue
            features = normalized[level].reshape(batch_size * widths[level], self.d_model)
            child_index = torch.tensor([child for child, parent in rows], device=features.device, dtype=torch.long)
            parent_index = torch.tensor([parent for child, parent in rows], device=features.device, dtype=torch.long)
            value = self.activation(decode(torch.cat((features.index_select(0, child_index), root_context.index_select(0, parent_index)), dim=-1)))
            deltas[level] = features.new_zeros(features.shape).index_copy(0, child_index, value).reshape(normalized[level].shape)
        return deltas
