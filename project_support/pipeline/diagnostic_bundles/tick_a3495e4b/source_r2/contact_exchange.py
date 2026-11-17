"""Geometry-only physical contact graph and a cross-leaf feature path."""
import math
import numpy as np
import torch
from .contact_geometry import contacts


def exchange(features, positions, leaves, edge_array, fallback, heads=8, rotate_values=False):
    n, channels = features.shape
    assert channels % heads == 0 and fallback.shape == features.shape
    leaves = np.asarray(leaves, dtype=np.int64)
    positions = np.asarray(positions)
    edges = np.asarray(edge_array, dtype=np.int64).reshape(-1, 2)
    adjacency = [set() for _ in range(n)]
    for a, b in edges:
        if leaves[a] != leaves[b]:
            adjacency[a].add(int(b))
            adjacency[b].add(int(a))
    dimension = channels // heads
    rows, degrees = [], []
    for i, donors in enumerate(adjacency):
        degrees.append(len(donors))
        if not donors:
            rows.append(fallback[i])
            continue
        # Geometry fixes reduction order, independently of superpoint numbering.
        donors = sorted(donors, key=lambda j: tuple(positions[j]))
        coordinates = [tuple(positions[j]) for j in donors]
        if len(coordinates) != len(set(coordinates)):
            raise ValueError('Coincident contact donors: geometric ordering undefined')
        indices = torch.tensor(donors, device=features.device)
        keys = features[indices].reshape(len(donors), heads, dimension)
        values = features[(indices + 1) % n] if rotate_values else features[indices]
        values = values.reshape(len(donors), heads, dimension)
        query = features[i].reshape(1, heads, dimension)
        weights = ((query * keys).sum(-1) / math.sqrt(dimension)).softmax(0)
        rows.append((weights.unsqueeze(-1) * values).sum(0).reshape(channels))
    return torch.stack(rows), degrees


def readback(owner, point_features, banks, identifiers, padding, fine_override=None):
    batch, width, channels = point_features.shape
    composed = []
    for b in range(batch):
        ids = identifiers[0][b].long().clamp(0, banks[0].shape[1] - 1)
        levels = [ids]
        for level in range(1, owner.num_scales):
            parent = identifiers[level][b].long().clamp(0, banks[level].shape[1] - 1)
            levels.append(parent.gather(0, levels[-1]))
        composed.append(levels)
    messages = []
    for level in range(owner.num_scales):
        message = torch.zeros(batch, width, channels, device=point_features.device, dtype=point_features.dtype)
        for b in range(batch):
            ids = composed[b][level]
            count = min(len(ids), width)
            message[b, :count] = (fine_override[b] if level == 0 and fine_override is not None
                                   else banks[level][b, ids[:count]])
        messages.append(message)
    stack = torch.stack(messages, dim=-1)
    global_mean = point_features.mean(1, keepdim=True).expand_as(point_features)
    weights = owner.level_gate(torch.cat((point_features, global_mean), dim=-1)).softmax(-1)
    fused = (stack * weights.unsqueeze(-2)).sum(-1)
    fused = owner.point_out_proj(owner.dropout(fused))
    return fused.masked_fill(padding.unsqueeze(-1), 0)
