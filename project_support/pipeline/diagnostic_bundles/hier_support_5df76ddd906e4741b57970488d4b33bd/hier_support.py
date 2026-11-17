"""Isolated conditional readout prototype; not a native training model."""
import math
import torch
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint


def supports(point_leaf, parent1, parent2):
    fine = point_leaf.unique(sorted=True)
    middle = parent1[fine].unique(sorted=True)
    coarse = parent2[middle].unique(sorted=True)
    result = {}
    for leaf in fine.tolist():
        mid = parent1[leaf]
        top = parent2[mid]
        result[leaf] = (
            fine[parent1[fine] == mid],
            middle[(parent2[middle] == top) & (middle != mid)],
            coarse[coarse != top])
    return result


def _attend(q, k, heads):
    if not k.shape[0]:
        return q * 0
    dim = q.shape[-1] // heads
    query = q.reshape(-1, heads, dim).transpose(0, 1).unsqueeze(0)
    key = k.reshape(-1, heads, dim).transpose(0, 1).unsqueeze(0)
    out = F.scaled_dot_product_attention(query, key, key, dropout_p=0.0)
    return out.squeeze(0).transpose(0, 1).reshape_as(q)


def grouped(points, banks, point_leaf, parent1, parent2, weights,
            chunk_size=5, heads=8, checkpoint_chunks=False):
    assert points.shape[1] % heads == 0 and chunk_size > 0
    assert weights.shape == (points.shape[0], 3) and len(banks) == 3
    assert point_leaf.numel() <= points.shape[0]
    tree = supports(point_leaf, parent1, parent2)
    rows, outputs = [], []
    for leaf, selections in tree.items():
        indices = torch.nonzero(point_leaf == leaf, as_tuple=False).flatten()
        keys = tuple(bank.index_select(0, ids) for bank, ids in zip(banks, selections))
        for index in indices.split(chunk_size):
            q = points.index_select(0, index)
            w = weights.index_select(0, index)

            def readout(q, w, *keys):
                value = q * 0
                for level, key in enumerate(keys):
                    value = value + _attend(q, key, heads) * w[:, level:level+1]
                return value

            if checkpoint_chunks:
                value = checkpoint(readout, q, w, *keys, use_reentrant=False,
                                   preserve_rng_state=True)
            else:
                value = readout(q, w, *keys)
            rows.append(index)
            outputs.append(value)
    output = points * 0
    if rows:
        output = output.index_copy(0, torch.cat(rows), torch.cat(outputs))
    return output


def dense_reference(points, banks, point_leaf, parent1, parent2, weights, heads=8):
    count, channels = points.shape
    dim = channels // heads
    valid = point_leaf.numel()
    if not valid:
        return points * 0
    tree = supports(point_leaf, parent1, parent2)
    query = points[:valid].reshape(valid, heads, dim).transpose(0, 1)
    fused = points[:valid] * 0
    for level, bank in enumerate(banks):
        allowed = torch.zeros(valid, bank.shape[0], dtype=torch.bool, device=points.device)
        for leaf, selections in tree.items():
            row = torch.nonzero(point_leaf == leaf, as_tuple=False).flatten()
            col = selections[level]
            if col.numel():
                allowed[row[:, None], col[None, :]] = True
        key = bank.reshape(-1, heads, dim).transpose(0, 1)
        logits = (query @ key.transpose(-1, -2)) / math.sqrt(dim)
        nonempty = allowed.any(dim=-1)
        logits = logits.masked_fill(~allowed.unsqueeze(0), -torch.inf)
        logits = torch.where(nonempty[None, :, None], logits, torch.zeros_like(logits))
        probability = logits.softmax(dim=-1) * allowed.unsqueeze(0)
        value = (probability @ key).transpose(0, 1).reshape(valid, channels)
        fused = fused + value * weights[:valid, level:level+1]
    return torch.cat([fused, points[valid:] * 0], dim=0)


def coverage(point_leaf, parent1, parent2):
    leaves = point_leaf.unique(sorted=True)
    checks = []
    for leaf, selections in supports(point_leaf, parent1, parent2).items():
        counts = torch.zeros_like(leaves)
        for level, ids in enumerate(selections):
            for node in ids:
                ancestors = leaves if level == 0 else parent1[leaves] if level == 1 else parent2[parent1[leaves]]
                counts = counts + (ancestors == node).to(counts.dtype)
        checks.append(bool((counts == 1).all()))
    return all(checks)
