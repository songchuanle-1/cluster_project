"""Geometry-guided sparse top-k coarse-to-fine cluster attention.

Hierarchy: points -> 256 -> 64 -> 8.
Routing: full attention at 8, then each level only searches descendants of
regions selected by its parent query. The final sparse point attention updates
inst_feats; decoder proposal queries are never used.
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean


def batch2flatten(x, batch_mask):
    return x.view(-1, x.size(-1))[~batch_mask.view(-1)]


def aggregate_cluster(feats, cluster_ids):
    if cluster_ids.numel() == 0:
        return feats
    num_clusters = int(cluster_ids.max().item()) + 1
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=num_clusters)


class PointCloudPartitioner(nn.Module):
    """Build nested geometric assignments: point->256, 256->64, 64->8."""

    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        if len(self.cluster_layer_nums) != 3:
            raise ValueError('TopK-C2F expects three cluster levels')

    @staticmethod
    def cluster_layer(pos, cluster_num):
        cluster_num = min(cluster_num, pos.size(0))
        seeds = FurthestPointSampling.apply(
            pos.unsqueeze(0), cluster_num).long().squeeze(0)
        centers = pos[seeds]
        cluster_ids = torch.cdist(pos, centers).argmin(dim=-1)
        return aggregate_cluster(pos, cluster_ids), cluster_ids

    def forward(self, sp_coords, batch_offsets):
        level_ids = [[] for _ in self.cluster_layer_nums]
        for batch_idx in range(len(batch_offsets) - 1):
            start = batch_offsets[batch_idx].item()
            end = batch_offsets[batch_idx + 1].item()
            current_pos = sp_coords[start:end]
            for level, cluster_num in enumerate(self.cluster_layer_nums):
                current_pos, cluster_ids = self.cluster_layer(
                    current_pos, cluster_num)
                level_ids[level].append(cluster_ids)

        point_level_ids = [[] for _ in self.cluster_layer_nums]
        child_to_parent = [[] for _ in range(2)]
        for batch_idx in range(len(batch_offsets) - 1):
            point_to_level = level_ids[0][batch_idx]
            point_level_ids[0].append(point_to_level)
            for level in range(1, 3):
                parent_ids = level_ids[level][batch_idx]
                child_to_parent[level - 1].append(parent_ids)
                point_to_level = parent_ids[point_to_level]
                point_level_ids[level].append(point_to_level)

        return level_ids, point_level_ids, child_to_parent


class SharedClusterBank(nn.Module):
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        self.partitioner = PointCloudPartitioner(self.cluster_layer_nums)

    def get_cluster(self, sp_pos, batch_offsets):
        self.level_ids, self.point_level_ids, self.child_to_parent = \
            self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        batch_size = len(batch_offsets) - 1
        current_feats = [
            sp_feats[batch_offsets[b].item():batch_offsets[b + 1].item()]
            for b in range(batch_size)
        ]
        cluster_feats_list = []
        for ids_per_batch in self.level_ids:
            current_feats = [
                aggregate_cluster(current_feats[b], ids_per_batch[b])
                for b in range(batch_size)
            ]
            max_clusters = max(feats.size(0) for feats in current_feats)
            padded = [
                F.pad(feats, (0, 0, 0, max_clusters - feats.size(0)))
                for feats in current_feats
            ]
            cluster_feats_list.append(torch.stack(padded, dim=0))
        return cluster_feats_list


class TopKCoarseToFineAttention(nn.Module):
    """Sparse top-k routing that progressively narrows finer-level attention."""

    VALID_MODES = {'topk_c2f_cosine', 'topk_c2f_bottleneck'}

    def __init__(
        self,
        d_model=256,
        nhead=8,
        cluster_layer_nums=None,
        per_layer_topk_list=None,
        dropout=0.0,
        cluster_mode='topk_c2f_cosine',
        lightweight_level=0,
        c2f_beta=1.0,
        relevance_temperature=1.0,
    ):
        super().__init__()
        del nhead, lightweight_level, c2f_beta, relevance_temperature
        if cluster_mode not in self.VALID_MODES:
            raise ValueError(f'Unsupported TopK-C2F mode: {cluster_mode}')
        self.cluster_mode = cluster_mode
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])

        # Order: point, 256, 64, 8. Each value is the selected key budget.
        self.topk_schedule = list(per_layer_topk_list or [16, 8, 4, 4])
        if len(self.topk_schedule) != 4:
            raise ValueError(
                'per_layer_topk_list must be [point, 256, 64, 8]')

        if cluster_mode == 'topk_c2f_bottleneck':
            route_dim = max(16, d_model // 8)
            self.query_proj = nn.Linear(d_model, route_dim)
            self.key_proj = nn.Linear(d_model, route_dim)
        else:
            self.query_proj = None
            self.key_proj = None

        initial_temperature = math.log(math.expm1(0.5))
        self.temperature_raw = nn.Parameter(
            torch.full((4,), initial_temperature))
        self.level_logits = nn.Parameter(torch.zeros(4))
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.route_chunk_size = 128

    def _temperature(self, level):
        return F.softplus(self.temperature_raw[level]) + 1e-4

    def _route_features(self, query, keys):
        if self.query_proj is not None:
            query = self.query_proj(query)
            keys = self.key_proj(keys)
        query = F.normalize(query, dim=-1, eps=1e-6)
        keys = F.normalize(keys, dim=-1, eps=1e-6)
        return query, keys

    @staticmethod
    def _children_table(child_parent_ids):
        """Create a compact parent->children lookup without a dense QxM mask."""
        num_parents = int(child_parent_ids.max().item()) + 1
        counts = torch.bincount(child_parent_ids.long(), minlength=num_parents)
        max_children = max(1, int(counts.max().item()))
        table = torch.zeros(
            num_parents, max_children, dtype=torch.long,
            device=child_parent_ids.device)
        valid = torch.zeros(
            num_parents, max_children, dtype=torch.bool,
            device=child_parent_ids.device)
        order = torch.argsort(child_parent_ids)
        start = 0
        for parent_idx, count in enumerate(counts.tolist()):
            if count:
                table[parent_idx, :count] = order[start:start + count]
                valid[parent_idx, :count] = True
                start += count
        return table, valid

    def _full_attention(self, feats, level):
        query, keys = self._route_features(feats, feats)
        scores = torch.matmul(query, keys.transpose(0, 1))
        scores = scores / self._temperature(level)
        weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(weights, feats)
        topk = min(self.topk_schedule[level], feats.size(0))
        route = torch.topk(scores, k=topk, dim=-1).indices
        return context, route
    def _sparse_attention(self, query_feats, candidate_feats,
                          selected_parents, child_parent_ids, level):
        """Chunked sparse search followed by differentiable top-k attention.

        Candidate scoring used only for discrete routing runs without autograd.
        Scores for the selected keys are then recomputed with gradients. This
        avoids retaining [num_queries, num_candidates, channels] activations.
        """
        child_table, child_valid = self._children_table(child_parent_ids)
        child_counts = child_valid.sum(dim=1)
        valid_counts = child_counts[selected_parents].sum(dim=1)
        layer_topk = min(self.topk_schedule[level],
                         int(valid_counts.min().item()))

        with torch.no_grad():
            route_queries, route_keys = self._route_features(
                query_feats, candidate_feats)

        context_chunks = []
        route_chunks = []
        num_queries = query_feats.size(0)

        for start in range(0, num_queries, self.route_chunk_size):
            end = min(start + self.route_chunk_size, num_queries)
            parent_chunk = selected_parents[start:end]
            candidate_indices = child_table[parent_chunk].flatten(1)
            candidate_valid = child_valid[parent_chunk].flatten(1)

            # Top-k index selection is discrete. Keep the large candidate
            # tensor outside autograd, then recompute only selected scores.
            with torch.no_grad():
                candidate_keys = route_keys[candidate_indices]
                route_scores = torch.einsum(
                    'qd,qkd->qk', route_queries[start:end], candidate_keys)
                route_scores.masked_fill_(
                    ~candidate_valid, float('-inf'))
                inner_indices = torch.topk(
                    route_scores, k=layer_topk, dim=-1).indices
                route = torch.gather(
                    candidate_indices, 1, inner_indices)

            selected_values = candidate_feats[route]
            query, selected_keys = self._route_features(
                query_feats[start:end], selected_values)
            selected_scores = torch.einsum(
                'qd,qkd->qk', query, selected_keys)
            selected_scores = selected_scores / self._temperature(level)
            weights = torch.softmax(selected_scores, dim=-1)
            context = torch.einsum(
                'qk,qkc->qc', weights, selected_values)

            context_chunks.append(context)
            route_chunks.append(route)

        return torch.cat(context_chunks, dim=0), torch.cat(route_chunks, dim=0)

    def _selected_cluster_attention(self, query_feats, cluster_feats,
                                    selected_clusters, level):
        """Attend from points to selected fine cluster tokens in chunks."""
        context_chunks = []
        for start in range(0, query_feats.size(0), self.route_chunk_size):
            end = min(start + self.route_chunk_size, query_feats.size(0))
            route = selected_clusters[start:end]
            selected_values = cluster_feats[route]
            query, selected_keys = self._route_features(
                query_feats[start:end], selected_values)
            scores = torch.einsum('qd,qkd->qk', query, selected_keys)
            scores = scores / self._temperature(level)
            weights = torch.softmax(scores, dim=-1)
            context_chunks.append(torch.einsum(
                'qk,qkc->qc', weights, selected_values))
        return torch.cat(context_chunks, dim=0)

    @staticmethod
    def _gather_to_points(values, point_ids, point_count):
        return values[point_ids[:point_count].long()]

    def _forward_scene(self, point_feats, f256, f64, f8,
                       point_to_256, child256_to_64, child64_to_8):
        # 1) Coarse global search over 8 regions.
        context8, route8 = self._full_attention(f8, level=3)

        # 2) A 64 query inherits its 8-parent route and only searches children
        #    of those selected coarse regions.
        selected8 = route8[child64_to_8.long()]
        context64, route64 = self._sparse_attention(
            f64, f64, selected8, child64_to_8, level=2)

        # 3) A 256 query inherits its 64-parent route and narrows the search.
        selected64 = route64[child256_to_64.long()]
        context256, route256 = self._sparse_attention(
            f256, f256, selected64, child256_to_64, level=1)

        # 4) Map routed cluster messages back to points. The hierarchy
        #    ends at 256 clusters; no point-level attention is materialized.
        point_to_64 = child256_to_64[point_to_256.long()]
        point_to_8 = child64_to_8[point_to_64.long()]
        messages = [
            context256[point_to_256.long()],
            context64[point_to_64.long()],
            context8[point_to_8.long()],
        ]
        weights = torch.softmax(self.level_logits[1:], dim=0)
        return sum(weights[level] * messages[level] for level in range(3))

    def forward(self, point_feats, lang_feats, lang_mask, point_mask,
                cluster_feats_list, cluster_bank):
        del lang_feats, lang_mask
        batch_size, max_points, channels = point_feats.shape
        fused = point_feats.new_zeros(batch_size, max_points, channels)

        for batch_idx in range(batch_size):
            point_to_256 = cluster_bank.level_ids[0][batch_idx]
            child256_to_64 = cluster_bank.child_to_parent[0][batch_idx]
            child64_to_8 = cluster_bank.child_to_parent[1][batch_idx]
            point_count = point_to_256.numel()
            count256 = child256_to_64.numel()
            count64 = child64_to_8.numel()
            count8 = int(child64_to_8.max().item()) + 1

            fused[batch_idx, :point_count] = self._forward_scene(
                point_feats[batch_idx, :point_count],
                cluster_feats_list[0][batch_idx, :count256],
                cluster_feats_list[1][batch_idx, :count64],
                cluster_feats_list[2][batch_idx, :count8],
                point_to_256,
                child256_to_64,
                child64_to_8,
            )

        message = self.message_norm(self.dropout(fused) - point_feats)
        return message.masked_fill(point_mask.unsqueeze(-1), 0)


Cluster_Attn = TopKCoarseToFineAttention
