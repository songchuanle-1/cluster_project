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


class GeometryBalancedClusterRouting(nn.Module):
    """Fixed-budget coarse-to-fine routing over geometric clusters.

    Modes:
      gbcr_balanced: content-routed fixed candidate budgets.
      gbcr_local: balanced routing with the query's own region preserved.
      gbcr_pointgate: gbcr_local plus point-specific residual gating.
    """

    VALID_MODES = {'gbcr_balanced', 'gbcr_local', 'gbcr_pointgate'}

    def __init__(
        self,
        d_model=256,
        nhead=8,
        cluster_layer_nums=None,
        per_layer_topk_list=None,
        dropout=0.0,
        cluster_mode='gbcr_balanced',
        lightweight_level=0,
        c2f_beta=1.0,
        relevance_temperature=1.0,
    ):
        super().__init__()
        del nhead, lightweight_level, c2f_beta, relevance_temperature
        if cluster_mode not in self.VALID_MODES:
            raise ValueError(f'Unsupported GBC-Routing mode: {cluster_mode}')
        self.cluster_mode = cluster_mode
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])

        # Coarse-to-fine order in config: [256, 64, 8].
        self.topk_schedule = list(per_layer_topk_list or [8, 4, 3])
        if len(self.topk_schedule) != 3:
            raise ValueError('per_layer_topk_list must be [256, 64, 8]')

        self.candidate_budgets = {1: 16, 0: 24}  # 64-level, 256-level
        self.preserve_local = cluster_mode in {'gbcr_local', 'gbcr_pointgate'}
        self.route_chunk_size = 128

        initial_temperature = math.log(math.expm1(0.5))
        self.temperature_raw = nn.Parameter(
            torch.full((3,), initial_temperature))
        self.level_logits = nn.Parameter(torch.zeros(3))
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.point_gate = (nn.Linear(d_model, 1)
                           if cluster_mode == 'gbcr_pointgate' else None)

    def _temperature(self, level):
        return F.softplus(self.temperature_raw[level]) + 1e-4

    @staticmethod
    def _normalize(feats):
        return F.normalize(feats, dim=-1, eps=1e-6)

    @staticmethod
    def _children_table(child_parent_ids):
        """Compact parent-to-children table used only at cluster levels."""
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

    @staticmethod
    def _preserve_own_parent(selected_parents, own_parent):
        """Ensure the local parent is among routed regions without growing k."""
        selected = selected_parents.clone()
        contains_local = (selected == own_parent.unsqueeze(-1)).any(dim=-1)
        selected[~contains_local, -1] = own_parent[~contains_local]
        return selected

    def _coarse_attention(self, feats):
        normalized = self._normalize(feats)
        scores = torch.matmul(normalized, normalized.transpose(0, 1))
        scores = scores / self._temperature(2)
        weights = torch.softmax(scores, dim=-1)
        context = torch.matmul(weights, feats)
        topk = min(self.topk_schedule[2], feats.size(0))
        route = torch.topk(scores.detach(), k=topk, dim=-1).indices
        return context, route

    def _balanced_sparse_attention(self, query_feats, candidate_feats,
                                   selected_parents, child_parent_ids,
                                   own_parent_ids, level):
        """Select a fixed candidate budget, then apply differentiable attention."""
        if self.preserve_local:
            selected_parents = self._preserve_own_parent(
                selected_parents, own_parent_ids)

        child_table, child_valid, child_counts = self._children_table(
            child_parent_ids)
        valid_counts = child_counts[selected_parents].sum(dim=-1)
        candidate_budget = min(
            self.candidate_budgets[level],
            child_table.size(1) * selected_parents.size(1))
        route_topk = min(
            self.topk_schedule[level], candidate_budget,
            int(valid_counts.min().item()))

        normalized_queries = self._normalize(query_feats).detach()
        normalized_keys = self._normalize(candidate_feats).detach()
        context_chunks = []
        route_chunks = []

        for start in range(0, query_feats.size(0), self.route_chunk_size):
            end = min(start + self.route_chunk_size, query_feats.size(0))
            parent_chunk = selected_parents[start:end]
            candidate_indices = child_table[parent_chunk].flatten(1)
            candidate_valid = child_valid[parent_chunk].flatten(1)

            with torch.no_grad():
                candidate_keys = normalized_keys[candidate_indices]
                route_scores = torch.einsum(
                    'qd,qkd->qk', normalized_queries[start:end],
                    candidate_keys)
                route_scores.masked_fill_(
                    ~candidate_valid, float('-inf'))

                # Local-preserving routing always keeps the query token itself.
                if self.preserve_local:
                    query_indices = torch.arange(
                        start, end, device=query_feats.device).unsqueeze(-1)
                    route_scores.masked_fill_(
                        candidate_indices == query_indices, float('inf'))

                _, budget_inner = torch.topk(
                    route_scores, k=candidate_budget, dim=-1)
                selected_indices = torch.gather(
                    candidate_indices, 1, budget_inner)
                selected_valid = torch.gather(
                    candidate_valid, 1, budget_inner)

            selected_values = candidate_feats[selected_indices]
            query = self._normalize(query_feats[start:end])
            keys = self._normalize(selected_values)
            scores = torch.einsum('qd,qkd->qk', query, keys)
            scores = scores / self._temperature(level)
            scores = scores.masked_fill(~selected_valid, float('-inf'))
            weights = torch.softmax(scores, dim=-1)
            context = torch.einsum('qk,qkc->qc', weights, selected_values)

            with torch.no_grad():
                route_inner = torch.topk(
                    scores.detach(), k=route_topk, dim=-1).indices
                route = torch.gather(
                    selected_indices, 1, route_inner)

            context_chunks.append(context)
            route_chunks.append(route)

        return torch.cat(context_chunks, dim=0), torch.cat(route_chunks, dim=0)

    def _forward_scene(self, point_feats, f256, f64, f8,
                       point_to_256, child256_to_64, child64_to_8):
        # 8-level global routing.
        context8, route8 = self._coarse_attention(f8)

        # 8 -> 64: top-k parent regions are expanded, then capped at B64=16.
        selected8 = route8[child64_to_8.long()]
        context64, route64 = self._balanced_sparse_attention(
            f64, f64, selected8, child64_to_8,
            own_parent_ids=child64_to_8,
            level=1)

        # 64 -> 256: routed regions are expanded, then capped at B256=24.
        selected64 = route64[child256_to_64.long()]
        context256, _ = self._balanced_sparse_attention(
            f256, f256, selected64, child256_to_64,
            own_parent_ids=child256_to_64,
            level=0)

        point_to_64 = child256_to_64[point_to_256.long()]
        point_to_8 = child64_to_8[point_to_64.long()]
        messages = [
            context256[point_to_256.long()],
            context64[point_to_64.long()],
            context8[point_to_8.long()],
        ]
        weights = torch.softmax(self.level_logits, dim=0)
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

        difference = self.message_norm(self.dropout(fused) - point_feats)
        if self.point_gate is not None:
            difference = torch.sigmoid(self.point_gate(difference)) * difference
        return difference.masked_fill(point_mask.unsqueeze(-1), 0)


Cluster_Attn = GeometryBalancedClusterRouting
