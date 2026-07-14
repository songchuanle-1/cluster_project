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


class LanguageConditionedC2FRouting(nn.Module):
    """Performance-oriented geometry-balanced coarse-to-fine routing."""

    def __init__(
        self,
        d_model=256,
        nhead=8,
        cluster_layer_nums=None,
        per_layer_topk_list=None,
        dropout=0.0,
        cluster_mode='gbcr_langc2f',
        lightweight_level=0,
        c2f_beta=1.0,
        relevance_temperature=1.0,
    ):
        super().__init__()
        del nhead, lightweight_level, c2f_beta, relevance_temperature
        if cluster_mode != 'gbcr_langc2f':
            raise ValueError(f'Unsupported language C2F mode: {cluster_mode}')
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        self.topk_schedule = list(per_layer_topk_list or [8, 6, 3])
        if len(self.topk_schedule) != 3:
            raise ValueError('per_layer_topk_list must be [256, 64, 8]')

        # level 1 is 64 clusters; level 0 is 256 clusters.
        self.local_budgets = {1: 4, 0: 4}
        self.routed_budgets = {1: 12, 0: 20}
        self.route_chunk_size = 128

        route_dim = max(16, d_model // 8)
        self.query_proj = nn.Linear(d_model, route_dim)
        self.key_proj = nn.Linear(d_model, route_dim)

        initial_temperature = math.log(math.expm1(0.5))
        self.temperature_raw = nn.Parameter(
            torch.full((3,), initial_temperature))
        self.scale_temperature_raw = nn.Parameter(
            torch.tensor(initial_temperature))
        self.scale_bias = nn.Parameter(torch.zeros(3))
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.point_gate = nn.Linear(d_model, 1)
        nn.init.zeros_(self.point_gate.weight)
        nn.init.constant_(self.point_gate.bias, 4.0)
        self.language_route_scale = nn.Parameter(torch.tensor(0.1))
        # Order is [256, 64]; child queries receive parent context.
        self.parent_context_scale = nn.Parameter(torch.full((2,), 0.1))

    def _temperature(self, level):
        return F.softplus(self.temperature_raw[level]) + 1e-4

    def _scale_temperature(self):
        return F.softplus(self.scale_temperature_raw) + 1e-4

    def _route_features(self, query, keys):
        query = F.normalize(self.query_proj(query), dim=-1, eps=1e-6)
        keys = F.normalize(self.key_proj(keys), dim=-1, eps=1e-6)
        return query, keys

    @staticmethod
    def _children_table(child_parent_ids):
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
        return table, valid, counts

    def _coarse_attention(self, feats, language):
        query, keys = self._route_features(feats, feats)
        scores = torch.matmul(query, keys.transpose(0, 1))
        language_query = F.normalize(
            self.query_proj(language.unsqueeze(0)), dim=-1, eps=1e-6)
        language_relevance = torch.matmul(
            language_query, keys.transpose(0, 1)).squeeze(0)
        scores = scores + (
            self.language_route_scale * language_relevance.unsqueeze(0))
        scores = scores / self._temperature(2)
        weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(weights, feats)
        topk = min(self.topk_schedule[2], feats.size(0))
        route = torch.topk(scores.detach(), k=topk, dim=-1).indices
        return context, route

    @staticmethod
    def _select_budget(scores, indices, valid, budget):
        width = min(budget, scores.size(1))
        _, inner = torch.topk(scores, k=width, dim=-1)
        return (torch.gather(indices, 1, inner),
                torch.gather(valid, 1, inner))

    def _quota_sparse_attention(self, query_feats, candidate_feats,
                                routed_parents, child_parent_ids,
                                own_parent_ids, level):
        """Use independent local and routed quotas with a fixed upper bound."""
        child_table, child_valid, child_counts = self._children_table(
            child_parent_ids)
        local_budget = self.local_budgets[level]
        routed_budget = self.routed_budgets[level]

        # Exclude own parent from routed quota; local tokens have a dedicated quota.
        routed_parent_valid = routed_parents != own_parent_ids.unsqueeze(-1)
        min_total_valid = child_counts[own_parent_ids].clamp_max(local_budget)
        routed_counts = (
            child_counts[routed_parents] * routed_parent_valid.long()
        ).sum(dim=-1).clamp_max(routed_budget)
        min_total_valid = int((min_total_valid + routed_counts).min().item())
        route_topk = min(self.topk_schedule[level], min_total_valid)

        with torch.no_grad():
            route_queries, route_keys = self._route_features(
                query_feats, candidate_feats)

        context_chunks = []
        route_chunks = []
        for start in range(0, query_feats.size(0), self.route_chunk_size):
            end = min(start + self.route_chunk_size, query_feats.size(0))
            query_indices = torch.arange(
                start, end, device=query_feats.device).unsqueeze(-1)
            own_chunk = own_parent_ids[start:end]
            routed_chunk = routed_parents[start:end]
            routed_parent_mask = routed_parent_valid[start:end]

            local_indices = child_table[own_chunk]
            local_valid = child_valid[own_chunk]
            routed_indices = child_table[routed_chunk].flatten(1)
            routed_valid = (
                child_valid[routed_chunk]
                & routed_parent_mask.unsqueeze(-1)
            ).flatten(1)

            with torch.no_grad():
                query_route = route_queries[start:end]
                local_scores = torch.einsum(
                    'qd,qkd->qk', query_route, route_keys[local_indices])
                local_scores.masked_fill_(~local_valid, float('-inf'))
                # Always retain the query cluster in the local quota.
                local_scores.masked_fill_(
                    local_indices == query_indices, float('inf'))

                routed_scores = torch.einsum(
                    'qd,qkd->qk', query_route, route_keys[routed_indices])
                routed_scores.masked_fill_(~routed_valid, float('-inf'))

                local_selected, local_selected_valid = self._select_budget(
                    local_scores, local_indices, local_valid, local_budget)
                routed_selected, routed_selected_valid = self._select_budget(
                    routed_scores, routed_indices, routed_valid, routed_budget)
                selected_indices = torch.cat(
                    [local_selected, routed_selected], dim=1)
                selected_valid = torch.cat(
                    [local_selected_valid, routed_selected_valid], dim=1)

            selected_values = candidate_feats[selected_indices]
            query, selected_keys = self._route_features(
                query_feats[start:end], selected_values)
            scores = torch.einsum('qd,qkd->qk', query, selected_keys)
            scores = scores / self._temperature(level)
            scores = scores.masked_fill(~selected_valid, float('-inf'))
            weights = torch.softmax(scores, dim=-1)
            context = torch.einsum('qk,qkc->qc', weights, selected_values)

            with torch.no_grad():
                route_inner = torch.topk(
                    scores.detach(), k=route_topk, dim=-1).indices
                route = torch.gather(selected_indices, 1, route_inner)

            context_chunks.append(context)
            route_chunks.append(route)

        return torch.cat(context_chunks, dim=0), torch.cat(route_chunks, dim=0)

    def _point_adaptive_fusion(self, point_feats, contexts):
        """Choose 256/64/8 context weights independently for every point."""
        # Similarity routes scales without retaining three full [N,C]
        # normalization graphs. Context values remain differentiable.
        with torch.no_grad():
            point_norm = F.normalize(point_feats, dim=-1, eps=1e-6)
            similarities = torch.stack([
                (point_norm * F.normalize(
                    context, dim=-1, eps=1e-6)).sum(-1)
                for context in contexts
            ], dim=-1)
        logits = (similarities + self.scale_bias) / self._scale_temperature()
        weights = torch.softmax(logits, dim=-1)
        return sum(
            weights[:, level:level + 1] * contexts[level]
            for level in range(3)
        )

    def _forward_scene(self, point_feats, f256, f64, f8,
                       point_to_256, child256_to_64, child64_to_8,
                       language):
        context8, route8 = self._coarse_attention(f8, language)

        selected8 = route8[child64_to_8.long()]
        parent_context8 = context8[child64_to_8.long()]
        query64 = f64 + self.parent_context_scale[1] * parent_context8
        context64, route64 = self._quota_sparse_attention(
            query64, f64, selected8, child64_to_8,
            own_parent_ids=child64_to_8, level=1)

        selected64 = route64[child256_to_64.long()]
        parent_context64 = context64[child256_to_64.long()]
        query256 = f256 + self.parent_context_scale[0] * parent_context64
        context256, _ = self._quota_sparse_attention(
            query256, f256, selected64, child256_to_64,
            own_parent_ids=child256_to_64, level=0)

        point_to_64 = child256_to_64[point_to_256.long()]
        point_to_8 = child64_to_8[point_to_64.long()]
        contexts = [
            context256[point_to_256.long()],
            context64[point_to_64.long()],
            context8[point_to_8.long()],
        ]
        return self._point_adaptive_fusion(point_feats, contexts)

    def forward(self, point_feats, lang_feats, lang_mask, point_mask,
                cluster_feats_list, cluster_bank):
        batch_size, max_points, channels = point_feats.shape
        fused = point_feats.new_zeros(batch_size, max_points, channels)
        valid_tokens = (~lang_mask).unsqueeze(-1).to(lang_feats.dtype)
        language = (lang_feats * valid_tokens).sum(dim=1)
        language = language / valid_tokens.sum(dim=1).clamp_min(1.0)

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
                point_to_256, child256_to_64, child64_to_8,
                language[batch_idx])

        difference = self.message_norm(self.dropout(fused) - point_feats)
        point_weight = torch.sigmoid(self.point_gate(difference))
        difference = point_weight * difference
        return difference.masked_fill(point_mask.unsqueeze(-1), 0)


Cluster_Attn = LanguageConditionedC2FRouting
