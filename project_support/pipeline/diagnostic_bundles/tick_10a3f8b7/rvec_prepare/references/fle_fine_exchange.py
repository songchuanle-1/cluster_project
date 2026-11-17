"""Recipient-specific bounded exchange within geometric fine leaves."""

import math

import numpy as np
from scipy.spatial import cKDTree
import torch
from torch import nn


def build_graph(coordinates, leaves, k=32):
    coordinates = np.asarray(coordinates, dtype=np.float64)
    leaves = np.asarray(leaves, dtype=np.int64)
    n = len(leaves)
    if coordinates.shape != (n, 3) or n == 0 or k <= 0:
        raise ValueError("Expected nonempty finite point geometry and positive k")
    if not np.isfinite(coordinates).all():
        raise ValueError("Nonfinite point geometry")
    indices = np.repeat(np.arange(n)[:, None], k, axis=1)
    allowed = np.zeros((n, k), dtype=bool)
    fallback = np.zeros(n, dtype=bool)
    group_ids = np.empty(n, dtype=np.int64)
    for group, leaf in enumerate(np.unique(leaves)):
        members = np.flatnonzero(leaves == leaf)
        group_ids[members] = group
        degree = min(k, len(members))
        distance, local = cKDTree(coordinates[members]).query(
            coordinates[members],
            k=list(range(1, min(k + 1, len(members)) + 1)),
        )
        indices[members, :degree] = members[local[:, :degree]]
        allowed[members, :degree] = True
        if len(members) > k:
            fallback[members] = distance[:, k - 1] == distance[:, k]
    return {
        "indices": torch.from_numpy(indices),
        "allowed": torch.from_numpy(allowed),
        "fallback": torch.from_numpy(fallback),
        "group_ids": torch.from_numpy(group_ids),
    }


def exchange(features, graph, heads=8):
    n, channels = features.shape
    if channels % heads:
        raise ValueError("Channels must be divisible by heads")
    dim = channels // heads
    indices = graph["indices"].to(features.device)
    allowed = graph["allowed"].to(features.device)
    gathered = features[indices].reshape(n, indices.shape[1], heads, dim)
    query = features.reshape(n, 1, heads, dim)
    scores = (query * gathered).sum(-1) / math.sqrt(dim)
    scores = scores.masked_fill(~allowed.unsqueeze(-1), -torch.inf)
    ordinary = (scores.softmax(1).unsqueeze(-1) * gathered).sum(1)
    ordinary = ordinary.reshape(n, channels)
    if not bool(graph["fallback"].any()):
        return ordinary
    # Exact cutoff ties cannot select point identities in a stable order.
    groups = graph["group_ids"].to(features.device)
    count = torch.bincount(groups).to(features.dtype).unsqueeze(-1)
    means = features.new_zeros(len(count), channels).index_add(
        0, groups, features) / count
    return torch.where(
        graph["fallback"].to(features.device).unsqueeze(-1),
        means[groups], ordinary)


class FineLeafExchange(nn.Module):
    def __init__(self, k=32, heads=8):
        super().__init__()
        self.k = k
        self.heads = heads

    def forward(self, features, padding, positions, fine_ids):
        output = torch.zeros_like(features)
        for b, ids in enumerate(fine_ids):
            n = len(ids)
            if int((~padding[b]).sum()) != n:
                raise ValueError("Fine membership does not match valid points")
            graph = build_graph(
                positions[b, :n].detach().cpu().numpy(),
                ids.detach().cpu().numpy(), self.k)
            output[b, :n] = exchange(features[b, :n], graph, self.heads)
        return output.masked_fill(padding.unsqueeze(-1), 0)
