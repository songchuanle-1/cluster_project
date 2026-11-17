"""Native fine-leaf geometric simplex factors; task efficacy/novelty unknown.

No neighbor-count parameter, attention, residual or gate is introduced. Geometry
is detached; every feature-to-factor-to-vertex edge remains differentiable.
"""
import math
import torch
from torch import nn
from torch.nn import functional as F


def canonical_factors(simplices, members):
    """Pure topology canonicalization, including all uncovered native vertices."""
    members = tuple(sorted(set(int(v) for v in members)))
    support = set(members)
    factors = set()
    for simplex in simplices:
        factor = tuple(sorted(set(int(v) for v in simplex)))
        if factor and set(factor) <= support:
            factors.add(factor)
    covered = {v for factor in factors for v in factor}
    for vertex in support - covered:
        factors.add((vertex,))
    return sorted(factors)


def incidence_lists(factors, count):
    """Return COO incidence with positive degree for every valid vertex."""
    vertices, factor_ids = [], []
    for factor_id, factor in enumerate(factors):
        for vertex in factor:
            if vertex < 0 or vertex >= count:
                raise ValueError("Simplex vertex outside native scene")
            vertices.append(vertex)
            factor_ids.append(factor_id)
    if set(vertices) != set(range(count)):
        raise ValueError("Simplex incidence does not cover every valid point")
    return vertices, factor_ids


def build_graph(coordinates, leaves):
    """Rank-adaptive Delaunay factors confined to each original fine leaf.

    Full rank uses tetrahedra, rank two triangles, rank one adjacent segments.
    Duplicate geometric positions share every containing factor. No coordinate
    jitter is permitted. A Qhull failure uses one explicit whole-leaf factor.
    """
    import numpy as np
    from scipy.spatial import Delaunay, QhullError
    xyz = np.asarray(coordinates, dtype=np.float64)
    leaves = np.asarray(leaves, dtype=np.int64)
    count = len(leaves)
    if xyz.shape != (count, 3) or count == 0 or not np.isfinite(xyz).all():
        raise ValueError("Expected finite nonempty native point geometry")
    all_factors, fallbacks, ranks = [], 0, []
    for leaf in np.unique(leaves):
        members = np.flatnonzero(leaves == leaf)
        unique, inverse = np.unique(xyz[members], axis=0, return_inverse=True)
        centered = unique - unique.mean(axis=0, keepdims=True)
        rank = int(np.linalg.matrix_rank(centered))
        ranks.append(rank)
        if rank == 0:
            local = [tuple(range(len(unique)))]
        else:
            # SVD is a coordinate basis change only, with no feature dependency.
            _, _, basis = np.linalg.svd(centered, full_matrices=False)
            projected = centered @ basis[:rank].T
            if rank == 1:
                order = np.argsort(projected[:, 0], kind="stable")
                local = [(int(order[i]), int(order[i + 1]))
                         for i in range(len(order) - 1)]
            elif len(unique) == rank + 1:
                local = [tuple(range(len(unique)))]
            else:
                try:
                    local = Delaunay(projected).simplices.tolist()
                except QhullError:
                    local = [tuple(range(len(unique)))]
                    fallbacks += 1
        expanded = []
        for simplex in local:
            expanded.append(members[np.isin(inverse, simplex)].tolist())
        all_factors.extend(canonical_factors(expanded, members.tolist()))
    all_factors = sorted(all_factors)
    vertices, factor_ids = incidence_lists(all_factors, count)
    return {"vertices": torch.tensor(vertices, dtype=torch.long),
            "factor_ids": torch.tensor(factor_ids, dtype=torch.long),
            "factor_count": len(all_factors), "point_count": count,
            "summary": {"factors": len(all_factors), "incidences": len(vertices),
                        "qhull_fallback_leaves": fallbacks, "affine_ranks": ranks}}


def simplex_exchange(features, graph, module, *, own_only=False, reference=False):
    """Headwise nonlinear factor analysis then receiver-incidence synthesis."""
    n, channels = features.shape
    if n != graph["point_count"] or channels != module.channels:
        raise ValueError("Simplex graph/features disagree")
    x = features.reshape(n, module.heads, channels // module.heads)
    vertices = graph["vertices"].to(features.device)
    factor_ids = graph["factor_ids"].to(features.device)
    embedded = F.gelu(torch.einsum("nhd,hod->nho", x, module.point_weight)
                      + module.point_bias)
    factor_count = graph["factor_count"]
    if reference:
        factor_values = torch.stack([
            embedded[vertices[factor_ids == factor]].mean(0)
            for factor in range(factor_count)])
    else:
        degree = torch.bincount(factor_ids, minlength=factor_count).to(features.dtype)
        factor_values = features.new_zeros(factor_count, module.heads,
                                          channels // module.heads).index_add(
                                              0, factor_ids, embedded[vertices])
        factor_values = factor_values / degree[:, None, None]
    projected_factor = torch.einsum("nhd,hod->nho", factor_values, module.factor_weight)
    if own_only:
        # Same incidence/weights, cuts every nonself feature dependency.
        incidence_factor = torch.einsum("nhd,hod->nho", embedded,
                                       module.factor_weight)[vertices]
    else:
        incidence_factor = projected_factor[factor_ids]
    receiver = torch.einsum("nhd,hod->nho", x, module.receiver_weight)
    messages = F.gelu(receiver[vertices] + incidence_factor + module.message_bias)
    if reference:
        result = torch.stack([messages[vertices == vertex].mean(0)
                              for vertex in range(n)])
    else:
        vertex_degree = torch.bincount(vertices, minlength=n).to(features.dtype)
        result = features.new_zeros(n, module.heads, channels // module.heads).index_add(
            0, vertices, messages) / vertex_degree[:, None, None]
    return (torch.einsum("nhd,hod->nho", result, module.output_weight)
            + module.output_bias).reshape_as(features)


class FineLeafSimplexIncidence(nn.Module):
    def __init__(self, channels=256, heads=8):
        super().__init__()
        if channels <= 0 or heads <= 0 or channels % heads:
            raise ValueError("Whole inherited attention heads required")
        self.channels, self.heads = channels, heads
        dim = channels // heads
        for name in ("point_weight", "factor_weight", "receiver_weight", "output_weight"):
            setattr(self, name, nn.Parameter(torch.empty(heads, dim, dim)))
        for name in ("point_bias", "message_bias", "output_bias"):
            setattr(self, name, nn.Parameter(torch.empty(heads, dim)))
        bound = 1 / math.sqrt(dim)
        for parameter in self.parameters():
            nn.init.uniform_(parameter, -bound, bound)
        self.last_graph_summary = None

    def _forward(self, features, padding, positions, fine_ids, own_only, reference):
        output = torch.zeros_like(features)
        summaries = []
        for batch, ids in enumerate(fine_ids):
            count = len(ids)
            if int((~padding[batch]).sum()) != count:
                raise ValueError("Native fine membership/valid points disagree")
            graph = build_graph(positions[batch, :count].detach().cpu().numpy(),
                                ids.detach().cpu().numpy())
            output[batch, :count] = simplex_exchange(
                features[batch, :count], graph, self,
                own_only=own_only, reference=reference)
            summaries.append(graph["summary"])
        self.last_graph_summary = summaries
        return output.masked_fill(padding.unsqueeze(-1), 0)

    def forward(self, features, padding, positions, fine_ids):
        return self._forward(features, padding, positions, fine_ids, False, False)

    def forward_reference(self, features, padding, positions, fine_ids, *, own_only=False):
        return self._forward(features, padding, positions, fine_ids, own_only, True)

    def forward_own_only(self, features, padding, positions, fine_ids):
        return self._forward(features, padding, positions, fine_ids, True, False)
