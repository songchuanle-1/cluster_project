"""Receiver-conditioned vector messages on inherited fine-leaf support.

Actual tied rows retain the raw whole-leaf mean. The donor_cut diagnostic
returns raw self on those rows and cuts every nonself input dependency.
Efficacy and novelty are UNKNOWN; no environment/config selects the control.
"""
import math

import numpy as np
from scipy.spatial import cKDTree
import torch
from torch import nn
from torch.nn import functional as F


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


def _inputs(features, graph, wr, wd, w2, b1, b2):
    if features.ndim != 2 or wr.ndim != 3:
        raise ValueError('RVE expects [N,C] features and [H,D,D] weights')
    heads, dim, dim_in = wr.shape
    if heads <= 0 or dim != dim_in or features.shape[1] != heads * dim:
        raise ValueError('RVE feature/head dimensions disagree')
    if wd.shape != wr.shape or w2.shape != wr.shape:
        raise ValueError('RVE headwise matrices must share [H,D,D] shape')
    if b1.shape != (heads, dim) or b2.shape != (heads, dim):
        raise ValueError('RVE biases must have [H,D] shape')
    indices = graph['indices'].to(features.device)
    allowed = graph['allowed'].to(features.device)
    if indices.ndim != 2 or indices.shape != allowed.shape or indices.shape[0] != features.shape[0]:
        raise ValueError('RVE inherited support shape disagrees')
    x = features.reshape(features.shape[0], heads, dim)
    count = allowed.sum(1).clamp_min(1).to(features.dtype).reshape(-1, 1, 1)
    return x, indices, allowed, count


def _fallback(output, features, graph, donor_cut):
    if not bool(graph['fallback'].any()):
        return output
    if donor_cut:
        fallback_value = features
    else:
        # Same raw leaf-mean arithmetic as FLE revision1; no projection here.
        groups = graph['group_ids'].to(features.device)
        count = torch.bincount(groups).to(features.dtype).unsqueeze(-1)
        means = features.new_zeros(len(count), features.shape[1]).index_add(
            0, groups, features) / count
        fallback_value = means[groups]
    return torch.where(
        graph['fallback'].to(features.device).unsqueeze(-1),
        fallback_value, output)


def exchange_reference(features, graph, wr, wd, w2, b1, b2, *, donor_cut=False):
    """Literal per-edge formula; same parameters as exchange_optimized."""
    x, indices, allowed, count = _inputs(features, graph, wr, wd, w2, b1, b2)
    receiver = torch.einsum('nhd,hod->nho', x, wr).unsqueeze(1)
    if donor_cut:
        affine = receiver.expand(-1, indices.shape[1], -1, -1) + b1
    else:
        relative = x[indices] - x.unsqueeze(1)
        affine = receiver + torch.einsum('nkhd,hod->nkho', relative, wd) + b1
    edge_value = torch.einsum('nkhd,hod->nkho', F.gelu(affine), w2) + b2
    edge_value = edge_value.masked_fill(~allowed[:, :, None, None], 0)
    output = (edge_value.sum(1) / count).reshape_as(features)
    return _fallback(output, features, graph, donor_cut)


def exchange_optimized(features, graph, wr, wd, w2, b1, b2, *, donor_cut=False):
    """Precompute endpoints; GELU remains per edge, second affine follows mean."""
    x, indices, allowed, count = _inputs(features, graph, wr, wd, w2, b1, b2)
    if donor_cut:
        receiver = torch.einsum('nhd,hod->nho', x, wr)
        affine = receiver.unsqueeze(1).expand(-1, indices.shape[1], -1, -1) + b1
    else:
        receiver = torch.einsum('nhd,hod->nho', x, wr - wd)
        donor = torch.einsum('nhd,hod->nho', x, wd)
        affine = receiver.unsqueeze(1) + donor[indices] + b1
    hidden = F.gelu(affine).masked_fill(~allowed[:, :, None, None], 0)
    mean_hidden = hidden.sum(1) / count
    output = (torch.einsum('nhd,hod->nho', mean_hidden, w2) + b2).reshape_as(features)
    return _fallback(output, features, graph, donor_cut)


class FineLeafReceiverVectorExchange(nn.Module):
    def __init__(self, channels=256, k=32, heads=8):
        super().__init__()
        if channels <= 0 or heads <= 0 or channels % heads:
            raise ValueError('RVE requires a positive whole number of inherited heads')
        self.channels = channels
        self.k = k
        self.heads = heads
        dim = channels // heads
        self.wr = nn.Parameter(torch.empty(heads, dim, dim))
        self.wd = nn.Parameter(torch.empty(heads, dim, dim))
        self.w2 = nn.Parameter(torch.empty(heads, dim, dim))
        self.b1 = nn.Parameter(torch.empty(heads, dim))
        self.b2 = nn.Parameter(torch.empty(heads, dim))
        self.reset_parameters()

    def reset_parameters(self):
        # Headwise Linear(D,D) fan-in rule, not a searched initialization scale.
        bound = 1 / math.sqrt(self.channels // self.heads)
        for parameter in (self.wr, self.wd, self.w2, self.b1, self.b2):
            nn.init.uniform_(parameter, -bound, bound)

    def _forward(self, features, padding, positions, fine_ids, operator, donor_cut):
        if features.shape[-1] != self.channels:
            raise ValueError('RVE configured channel count disagrees')
        output = torch.zeros_like(features)
        for batch, ids in enumerate(fine_ids):
            count = len(ids)
            if int((~padding[batch]).sum()) != count:
                raise ValueError('Fine membership does not match valid points')
            graph = build_graph(
                positions[batch, :count].detach().cpu().numpy(),
                ids.detach().cpu().numpy(), self.k)
            output[batch, :count] = operator(
                features[batch, :count], graph,
                self.wr, self.wd, self.w2, self.b1, self.b2,
                donor_cut=donor_cut)
        return output.masked_fill(padding.unsqueeze(-1), 0)

    def forward(self, features, padding, positions, fine_ids):
        return self._forward(
            features, padding, positions, fine_ids, exchange_optimized, False)

    def forward_reference(self, features, padding, positions, fine_ids, *, donor_cut=False):
        return self._forward(
            features, padding, positions, fine_ids, exchange_reference, donor_cut)

    def forward_own_only(self, features, padding, positions, fine_ids):
        return self._forward(
            features, padding, positions, fine_ids, exchange_optimized, True)
