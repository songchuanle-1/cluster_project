"""Lightweight parameter-free hierarchical cluster attention.

The module builds N -> 256 -> 64 -> 8 geometric clusters, refines cluster
features from coarse to fine, and writes the result back to inst_feats only.
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
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        if len(self.cluster_layer_nums) != 3:
            raise ValueError('HCA expects exactly three cluster levels')

    @staticmethod
    def cluster_layer(pos, cluster_num):
        cluster_num = min(cluster_num, pos.size(0))
        seeds = FurthestPointSampling.apply(
            pos.unsqueeze(0), cluster_num).long().squeeze(0)
        centers = pos[seeds]
        cluster_ids = torch.cdist(pos, centers).argmin(dim=-1)
        return aggregate_cluster(pos, cluster_ids), cluster_ids

    def forward(self, sp_coords, batch_offsets):
        # level_ids: point->256, 256->64, 64->8 for every batch.
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
        child_to_parent = [[] for _ in range(len(self.cluster_layer_nums) - 1)]
        for batch_idx in range(len(batch_offsets) - 1):
            composed = level_ids[0][batch_idx]
            point_level_ids[0].append(composed)
            for level in range(1, len(self.cluster_layer_nums)):
                parent_ids = level_ids[level][batch_idx]
                child_to_parent[level - 1].append(parent_ids)
                composed = parent_ids[composed]
                point_level_ids[level].append(composed)

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


class HierarchicalClusterAttention(nn.Module):
    """Content-adaptive 8 -> 64 -> 256 cluster refinement.

    Modes:
      hca_coarse: attention at 8; parent broadcast at 64 and 256.
      hca_parent: child attends to [self, refined parent].
      hca_sibling: child attends to [refined parent, same-parent siblings].
    """

    VALID_MODES = {'hca_coarse', 'hca_parent', 'hca_sibling'}

    def __init__(
        self,
        d_model=256,
        nhead=8,
        cluster_layer_nums=None,
        per_layer_topk_list=None,
        dropout=0.0,
        cluster_mode='hca_sibling',
        lightweight_level=0,
        c2f_beta=1.0,
        relevance_temperature=1.0,
    ):
        super().__init__()
        del nhead, per_layer_topk_list, lightweight_level
        del c2f_beta, relevance_temperature
        if cluster_mode not in self.VALID_MODES:
            raise ValueError(f'Unsupported HCA mode: {cluster_mode}')
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        self.cluster_mode = cluster_mode

        # softplus(-1.5078) is approximately 0.2.
        initial_temperature = math.log(math.expm1(0.2))
        self.temperature_raw = nn.Parameter(
            torch.full((3,), initial_temperature))
        self.level_scales = nn.Parameter(torch.full((3,), 0.1))
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def _temperature(self, level):
        return F.softplus(self.temperature_raw[level]) + 1e-4

    def _attend(self, query, keys, values, level):
        query = F.normalize(query, dim=-1, eps=1e-6)
        keys = F.normalize(keys, dim=-1, eps=1e-6)
        scores = torch.matmul(query, keys.transpose(-1, -2))
        weights = torch.softmax(scores / self._temperature(level), dim=-1)
        return torch.matmul(weights, values)

    def _refine_coarse(self, coarse_feats, cluster_bank):
        refined = coarse_feats.clone()
        for batch_idx, parent_ids in enumerate(
                cluster_bank.child_to_parent[1]):
            coarse_count = (int(parent_ids.max().item()) + 1
                            if parent_ids.numel() else 0)
            if coarse_count == 0:
                continue
            local = coarse_feats[batch_idx, :coarse_count]
            message = self._attend(local, local, local, level=2)
            refined[batch_idx, :coarse_count] = (
                local + self.level_scales[2] * self.dropout(message))
        return refined

    def _refine_children(self, local_feats, parent_feats,
                         child_parent_ids, level):
        child_count = child_parent_ids.numel()
        local = local_feats[:child_count]
        parent_up = parent_feats[child_parent_ids.long()]

        if self.cluster_mode == 'hca_coarse':
            message = parent_up
        elif self.cluster_mode == 'hca_parent':
            messages = []
            for child_idx in range(child_count):
                candidates = torch.stack(
                    [local[child_idx], parent_up[child_idx]], dim=0)
                message = self._attend(
                    local[child_idx:child_idx + 1],
                    candidates, candidates, level=level)
                messages.append(message.squeeze(0))
            message = torch.stack(messages, dim=0)
        else:
            messages = []
            for child_idx in range(child_count):
                parent_id = child_parent_ids[child_idx]
                sibling_mask = child_parent_ids == parent_id
                candidates = torch.cat(
                    [parent_up[child_idx:child_idx + 1], local[sibling_mask]],
                    dim=0)
                message = self._attend(
                    local[child_idx:child_idx + 1],
                    candidates, candidates, level=level)
                messages.append(message.squeeze(0))
            message = torch.stack(messages, dim=0)

        return local + self.level_scales[level] * self.dropout(message)

    def _coarse_to_fine(self, cluster_feats_list, cluster_bank):
        refined = list(cluster_feats_list)
        refined[2] = self._refine_coarse(
            cluster_feats_list[2], cluster_bank)

        # level 1: 8 -> 64; level 0: refined 64 -> 256.
        for level in (1, 0):
            child_source = cluster_feats_list[level]
            child_refined = child_source.clone()
            parent_refined = refined[level + 1]
            for batch_idx, child_parent_ids in enumerate(
                    cluster_bank.child_to_parent[level]):
                parent_count = (int(child_parent_ids.max().item()) + 1
                                if child_parent_ids.numel() else 0)
                updated = self._refine_children(
                    child_source[batch_idx],
                    parent_refined[batch_idx, :parent_count],
                    child_parent_ids,
                    level)
                child_refined[batch_idx, :updated.size(0)] = updated
            refined[level] = child_refined
        return refined

    @staticmethod
    def _gather_finest(finest_feats, point_ids_per_batch, point_feats):
        batch_size, num_points, channels = point_feats.shape
        context = point_feats.new_zeros(batch_size, num_points, channels)
        for batch_idx, point_ids in enumerate(point_ids_per_batch):
            point_count = point_ids.numel()
            context[batch_idx, :point_count] = \
                finest_feats[batch_idx, point_ids.long()]
        return context

    def forward(self, point_feats, lang_feats, lang_mask, point_mask,
                cluster_feats_list, cluster_bank):
        del lang_feats, lang_mask
        refined = self._coarse_to_fine(cluster_feats_list, cluster_bank)
        context = self._gather_finest(
            refined[0], cluster_bank.point_level_ids[0], point_feats)
        message = self.message_norm(context - point_feats)
        return message.masked_fill(point_mask.unsqueeze(-1), 0)


Cluster_Attn = HierarchicalClusterAttention
