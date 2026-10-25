"""M215 BEC: bipartite edge analysis and synthesis across the unchanged hierarchy.

Private edge-message means never replace the original raw bank construction.
Only metadata uses CPU lists; all feature paths retain native autograd.
"""
import torch
from torch import nn


def build_bipartite_plan(point_to_fine, fine_to_middle, middle_to_coarse, widths):
    """Actual production original-ID plan; executable on stdlib integer metadata.

    True support starts at real points; no occupancy is inferred from features.
    Means have one equal contribution per true-supported child token, not point.
    """
    if (not isinstance(widths, (list, tuple)) or len(widths) != 3 or
            any(type(v) is not int or v < 0 for v in widths)):
        raise ValueError('BEC requires three nonnegative padded bank widths')
    levels = (point_to_fine, fine_to_middle, middle_to_coarse)
    if any(not isinstance(v, (list, tuple)) for v in levels):
        raise ValueError('BEC requires original integer ID lists')
    if any(type(i) is not int or i < 0 for values in levels for i in values):
        raise ValueError('BEC original IDs must be nonnegative integers')
    k0, k1 = len(fine_to_middle), len(middle_to_coarse)
    if (k0 > widths[0] or k1 > widths[1] or
            any(i >= k0 for i in point_to_fine) or
            any(i >= k1 for i in fine_to_middle) or
            any(i >= widths[2] for i in middle_to_coarse)):
        raise ValueError('BEC original ID/prefix/padded bank mismatch')
    fine_mask = [False] * k0
    for token in point_to_fine:
        fine_mask[token] = True
    fine = tuple(i for i, active in enumerate(fine_mask) if active)
    middle_mask = [False] * k1
    for token in fine:
        middle_mask[fine_to_middle[token]] = True
    middle = tuple(i for i, active in enumerate(middle_mask) if active)
    coarse_mask = [False] * widths[2]
    for token in middle:
        coarse_mask[middle_to_coarse[token]] = True
    coarse = tuple(i for i, active in enumerate(coarse_mask) if active)
    fine_edges = tuple((i, fine_to_middle[i]) for i in fine)
    middle_edges = tuple((i, middle_to_coarse[i]) for i in middle)
    # One append per actual edge, preserving original parent/child-row order.
    fine_rows = {parent: [] for parent in middle}
    for row, (_, parent) in enumerate(fine_edges):
        fine_rows[parent].append(row)
    middle_rows = {parent: [] for parent in coarse}
    for row, (_, parent) in enumerate(middle_edges):
        middle_rows[parent].append(row)
    fine_groups = tuple((parent, tuple(fine_rows[parent])) for parent in middle)
    middle_groups = tuple((parent, tuple(middle_rows[parent])) for parent in coarse)
    return {'fine_ids': fine, 'middle_ids': middle, 'coarse_ids': coarse,
            'fine_edges': fine_edges, 'middle_edges': middle_edges,
            'fine_parent_ids': tuple(p for _, p in fine_edges),
            'middle_parent_ids': tuple(p for _, p in middle_edges),
            'fine_mean_groups': fine_groups, 'middle_mean_groups': middle_groups,
            'prefixes': (k0, k1, max(middle_to_coarse) + 1 if middle_to_coarse else 0),
            'widths': tuple(widths)}


class CrossLevelBipartiteEdgeComposition(nn.Module):
    """Two upward split maps, original coarse transform, two downward maps."""

    def __init__(self, channels):
        super().__init__()
        self.channels = channels
        self.up_fine = nn.Linear(2 * channels, 2 * channels)
        self.up_middle = nn.Linear(2 * channels, 2 * channels)
        self.down_middle = nn.Linear(2 * channels, channels)
        self.down_fine = nn.Linear(2 * channels, channels)
        self.activation = nn.GELU()

    def _mean_messages(self, messages, groups, width):
        """Equal true-child-row means from actual upward branch outputs."""
        result = messages.new_zeros((width, self.channels))
        if groups:
            rows = []
            for _, children in groups:
                ids = torch.tensor(children, dtype=torch.long, device=messages.device)
                rows.append(messages.index_select(0, ids).mean(dim=0))
            parents = torch.tensor([parent for parent, _ in groups], dtype=torch.long, device=messages.device)
            result = result.index_copy(0, parents, torch.stack(rows, dim=0))
        return result

    def forward(self, fine, middle, coarse, cluster_ids_list, coarse_transform):
        banks = (fine, middle, coarse)
        if (any(x.ndim != 3 or x.shape[-1] != self.channels for x in banks) or
                any(x.shape[0] != fine.shape[0] or x.device != fine.device or x.dtype != fine.dtype for x in banks) or
                len(cluster_ids_list) != 3 or any(len(level) != fine.shape[0] for level in cluster_ids_list)):
            raise RuntimeError('BEC current bank/ID batch/shape mismatch')
        widths = tuple(int(x.shape[1]) for x in banks)
        plans, kept_fine, kept_middle, coarse_inputs = [], [], [], []
        for b in range(fine.shape[0]):
            ids = [level[b] for level in cluster_ids_list]
            if any(x.ndim != 1 or x.dtype != torch.long or x.device != fine.device for x in ids):
                raise RuntimeError('BEC original IDs must be same-device long vectors')
            plan = build_bipartite_plan(*(x.detach().cpu().tolist() for x in ids), widths)
            plans.append(plan)
            fi = torch.tensor(plan['fine_ids'], dtype=torch.long, device=fine.device)
            mp = torch.tensor(plan['fine_parent_ids'], dtype=torch.long, device=fine.device)
            if plan['fine_ids']:
                upward = self.activation(self.up_fine(torch.cat((fine[b].index_select(0, fi), middle[b].index_select(0, mp)), dim=-1)))
                u0, v0 = upward[:, :self.channels], upward[:, self.channels:]
            else:
                u0 = v0 = fine.new_zeros((0, self.channels))
            kept_fine.append(u0)
            a1 = self._mean_messages(v0, plan['fine_mean_groups'], widths[1])
            mi = torch.tensor(plan['middle_ids'], dtype=torch.long, device=fine.device)
            cp = torch.tensor(plan['middle_parent_ids'], dtype=torch.long, device=fine.device)
            if plan['middle_ids']:
                upward = self.activation(self.up_middle(torch.cat((a1.index_select(0, mi), coarse[b].index_select(0, cp)), dim=-1)))
                u1, v1 = upward[:, :self.channels], upward[:, self.channels:]
            else:
                u1 = v1 = fine.new_zeros((0, self.channels))
            kept_middle.append(u1)
            coarse_inputs.append(self._mean_messages(v1, plan['middle_mean_groups'], widths[2]))
        a2 = torch.stack(coarse_inputs, dim=0) if coarse_inputs else torch.zeros_like(coarse)
        # The original registered coarse LN/FFN is called once for this full bank.
        coarse_delta = coarse_transform(a2)
        if coarse_delta.shape != coarse.shape:
            raise RuntimeError('BEC original coarse transform changed bank shape')
        mask = torch.zeros(coarse.shape[:2], dtype=torch.bool, device=coarse.device)
        for b, plan in enumerate(plans):
            ids = torch.tensor(plan['coarse_ids'], dtype=torch.long, device=coarse.device)
            mask[b] = mask[b].index_fill(0, ids, True)
        # No new unsupported bias token may participate in the down-going graph.
        coarse_delta = coarse_delta.masked_fill(~mask.unsqueeze(-1), 0)
        refined_coarse = coarse + coarse_delta  # The one original coarse cf skip.
        fine_deltas, middle_deltas = [], []
        for b, plan in enumerate(plans):
            mi = torch.tensor(plan['middle_ids'], dtype=torch.long, device=fine.device)
            cp = torch.tensor(plan['middle_parent_ids'], dtype=torch.long, device=fine.device)
            middle_delta = middle.new_zeros((widths[1], self.channels))
            if plan['middle_ids']:
                values = self.activation(self.down_middle(torch.cat((kept_middle[b], refined_coarse[b].index_select(0, cp)), dim=-1)))
                middle_delta = middle_delta.index_copy(0, mi, values)
            middle_deltas.append(middle_delta)
            fi = torch.tensor(plan['fine_ids'], dtype=torch.long, device=fine.device)
            mp = torch.tensor(plan['fine_parent_ids'], dtype=torch.long, device=fine.device)
            fine_delta = fine.new_zeros((widths[0], self.channels))
            if plan['fine_ids']:
                values = self.activation(self.down_fine(torch.cat((kept_fine[b], middle_delta.index_select(0, mp)), dim=-1)))
                fine_delta = fine_delta.index_copy(0, fi, values)
            fine_deltas.append(fine_delta)
        d0 = torch.stack(fine_deltas, dim=0) if fine_deltas else torch.zeros_like(fine)
        d1 = torch.stack(middle_deltas, dim=0) if middle_deltas else torch.zeros_like(middle)
        return d0, d1, refined_coarse
