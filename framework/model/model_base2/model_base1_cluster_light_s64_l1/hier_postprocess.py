"""Correct and differentiable hierarchical cluster context modules."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean


def aggregate_cluster(feats, cluster_ids):
    if cluster_ids.numel() == 0:
        return feats
    num_clusters = int(cluster_ids.max().item()) + 1
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=num_clusters)


class PointCloudPartitioner(nn.Module):
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])

    @staticmethod
    def cluster_layer(pos, cluster_num):
        cluster_num = min(cluster_num, pos.size(0))
        seeds = FurthestPointSampling.apply(pos.unsqueeze(0), cluster_num).long().squeeze(0)
        centers = pos[seeds]
        cluster_ids = torch.cdist(pos, centers).argmin(dim=-1)
        return aggregate_cluster(pos, cluster_ids), cluster_ids

    def forward(self, sp_coords, batch_offsets):
        batch_level_ids = [[] for _ in self.cluster_layer_nums]

        for batch_idx in range(len(batch_offsets) - 1):
            start = batch_offsets[batch_idx].item()
            end = batch_offsets[batch_idx + 1].item()
            current_pos = sp_coords[start:end]
            for level, cluster_num in enumerate(self.cluster_layer_nums):
                current_pos, cluster_ids = self.cluster_layer(current_pos, cluster_num)
                batch_level_ids[level].append(cluster_ids)

        point_level_ids = [[] for _ in self.cluster_layer_nums]
        child_to_parent = [[] for _ in range(len(self.cluster_layer_nums) - 1)]
        for batch_idx in range(len(batch_offsets) - 1):
            composed = batch_level_ids[0][batch_idx]
            point_level_ids[0].append(composed)
            for level in range(1, len(self.cluster_layer_nums)):
                parent_ids = batch_level_ids[level][batch_idx]
                child_to_parent[level - 1].append(parent_ids)
                composed = parent_ids[composed]
                point_level_ids[level].append(composed)

        return batch_level_ids, point_level_ids, child_to_parent


class SharedClusterBank(nn.Module):
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        self.partitioner = PointCloudPartitioner(self.cluster_layer_nums)

    def get_cluster(self, sp_pos, batch_offsets):
        outputs = self.partitioner(sp_pos, batch_offsets)
        self.level_ids, self.point_level_ids, self.child_to_parent = outputs

    def build_cluster_feats(self, sp_feats, batch_offsets):
        batch_size = len(batch_offsets) - 1
        current_feats = [
            sp_feats[batch_offsets[b].item():batch_offsets[b + 1].item()]
            for b in range(batch_size)
        ]
        cluster_feats_list = []

        for level, ids_per_batch in enumerate(self.level_ids):
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


class HierarchicalClusterRefinement(nn.Module):
    """Broadcast hierarchical context with optional language relevance."""

    def __init__(
        self,
        d_model=256,
        nhead=8,
        cluster_layer_nums=None,
        per_layer_topk_list=None,
        dropout=0.0,
        cluster_mode='context',
        lightweight_level=0,
        c2f_beta=1.0,
        relevance_temperature=1.0,
    ):
        super().__init__()
        del nhead, per_layer_topk_list
        self.cluster_layer_nums = list(cluster_layer_nums or [256, 64, 8])
        self.num_scales = len(self.cluster_layer_nums)
        self.cluster_mode = cluster_mode
        self.lightweight_level = int(lightweight_level)
        self.c2f_beta = c2f_beta
        self.relevance_temperature = relevance_temperature

        self.is_lightweight = (cluster_mode.startswith('light_') or
                               cluster_mode.startswith('hier_'))
        if self.is_lightweight:
            learned_fusion = cluster_mode in (
                'light_parallel_learned', 'light_parallel_diff',
                'light_c2f_scalar', 'hier_fusion')
            if learned_fusion:
                self.level_logits = nn.Parameter(torch.zeros(self.num_scales))
            else:
                self.register_buffer('level_logits', torch.zeros(self.num_scales))

            scalar_modes = (
                'light_c2f_scalar', 'hier_add', 'hier_diff', 'hier_fusion')
            if cluster_mode in scalar_modes:
                self.c2f_scales = nn.Parameter(
                    torch.zeros(self.num_scales - 1))
            elif cluster_mode == 'hier_channel':
                self.c2f_channel_scales = nn.Parameter(
                    torch.zeros(self.num_scales - 1, d_model))
            elif cluster_mode == 'hier_content':
                self.content_scale = nn.Parameter(
                    torch.zeros(self.num_scales - 1))
                self.content_bias = nn.Parameter(
                    torch.full((self.num_scales - 1,), -4.0))
        else:
            self.lang_proj = nn.Linear(d_model, d_model)
            self.cluster_proj = nn.Linear(d_model, d_model)
            self.value_proj = nn.Linear(d_model, d_model)
            self.level_gate = nn.Linear(d_model * 3, self.num_scales)
            self.point_out_proj = nn.Linear(d_model, d_model)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    @staticmethod
    def _gather_to_points(values, point_ids_per_batch, point_feats):
        batch_size, num_points, channels = point_feats.shape
        message = point_feats.new_zeros(batch_size, num_points, channels)
        for batch_idx, point_ids in enumerate(point_ids_per_batch):
            count = point_ids.numel()
            message[batch_idx, :count] = values[batch_idx, point_ids.long()]
        return message

    def _propagate_c2f(self, cluster_feats_list, cluster_bank):
        refined = list(cluster_feats_list)
        for level in reversed(range(self.num_scales - 1)):
            child_source = refined[level]
            child = child_source.clone()
            parent = refined[level + 1]
            for batch_idx, child_to_parent in enumerate(
                    cluster_bank.child_to_parent[level]):
                child_count = child_to_parent.numel()
                local = child_source[batch_idx, :child_count]
                parent_up = parent[batch_idx, child_to_parent.long()]

                if self.cluster_mode == 'hier_channel':
                    update = self.c2f_channel_scales[level] * parent_up
                elif self.cluster_mode == 'hier_content':
                    similarity = F.cosine_similarity(
                        local, parent_up, dim=-1, eps=1e-6)
                    gate = torch.sigmoid(
                        self.content_scale[level] * similarity
                        + self.content_bias[level])
                    update = gate.unsqueeze(-1) * parent_up
                else:
                    update = self.c2f_scales[level] * parent_up

                child[batch_idx, :child_count] = local + update
            refined[level] = child
        return refined

    def _forward_lightweight(self, point_feats, point_mask,
                             cluster_feats_list, cluster_bank):
        mode = self.cluster_mode
        uses_hierarchy = (mode == 'light_c2f_scalar' or
                          mode.startswith('hier_'))
        values = (self._propagate_c2f(cluster_feats_list, cluster_bank)
                  if uses_hierarchy else cluster_feats_list)
        scale_messages = [
            self._gather_to_points(
                values[level], cluster_bank.point_level_ids[level], point_feats)
            for level in range(self.num_scales)
        ]

        if mode == 'light_single':
            if not 0 <= self.lightweight_level < self.num_scales:
                raise ValueError('lightweight_level is outside cluster scales')
            message = scale_messages[self.lightweight_level]
        elif mode in ('hier_add', 'hier_diff', 'hier_channel',
                      'hier_content'):
            message = scale_messages[0]
        else:
            if mode == 'light_parallel_fixed':
                weights = point_feats.new_full(
                    (self.num_scales,), 1.0 / self.num_scales)
            else:
                weights = torch.softmax(self.level_logits, dim=0)
            message = sum(
                weights[level] * scale_messages[level]
                for level in range(self.num_scales))

        if mode in ('light_parallel_diff', 'light_c2f_scalar',
                    'hier_diff', 'hier_fusion', 'hier_channel',
                    'hier_content'):
            message = message - point_feats
        message = self.message_norm(message)
        return message.masked_fill(point_mask.unsqueeze(-1), 0)

    @staticmethod
    def masked_language_pool(lang_feats, lang_mask):
        valid = (~lang_mask).unsqueeze(-1).to(lang_feats.dtype)
        return (lang_feats * valid).sum(dim=1) / valid.sum(dim=1).clamp_min(1.0)

    def _language_relevance(self, lang_summary, cluster_feats_list, bank):
        query = F.normalize(self.lang_proj(lang_summary), dim=-1)
        relevances = [None] * self.num_scales
        parent_probs = None

        for level in reversed(range(self.num_scales)):
            keys = F.normalize(self.cluster_proj(cluster_feats_list[level]), dim=-1)
            logits = torch.einsum('bd,bkd->bk', query, keys)
            logits = logits / max(float(self.relevance_temperature), 1e-6)

            if self.cluster_mode == 'language_soft_c2f' and parent_probs is not None:
                for batch_idx, child_parent_ids in enumerate(bank.child_to_parent[level]):
                    child_count = child_parent_ids.numel()
                    parent_prior = parent_probs[batch_idx, child_parent_ids.long()]
                    logits[batch_idx, :child_count] += self.c2f_beta * torch.log(
                        parent_prior.clamp_min(1e-6)
                    )

            probs = torch.sigmoid(logits)
            relevances[level] = probs
            parent_probs = probs

        return relevances

    def forward(self, point_feats, lang_feats, lang_mask, point_mask,
                cluster_feats_list, cluster_bank):
        if self.is_lightweight:
            return self._forward_lightweight(
                point_feats, point_mask, cluster_feats_list, cluster_bank)

        batch_size, num_points, channels = point_feats.shape
        lang_summary = self.masked_language_pool(lang_feats, lang_mask)

        if self.cluster_mode == 'context':
            relevances = [
                torch.ones(feats.shape[:2], device=feats.device, dtype=feats.dtype)
                for feats in cluster_feats_list
            ]
        elif self.cluster_mode in ('language_soft', 'language_soft_c2f'):
            relevances = self._language_relevance(
                lang_summary, cluster_feats_list, cluster_bank
            )
        else:
            raise ValueError(f'Unsupported cluster_mode: {self.cluster_mode}')

        scale_messages = []
        for level, cluster_feats in enumerate(cluster_feats_list):
            values = self.value_proj(cluster_feats)
            weighted_values = values * relevances[level].unsqueeze(-1)
            point_message = point_feats.new_zeros(batch_size, num_points, channels)
            for batch_idx, point_ids in enumerate(cluster_bank.point_level_ids[level]):
                point_count = point_ids.numel()
                point_message[batch_idx, :point_count] = weighted_values[
                    batch_idx, point_ids.long()
                ]
            scale_messages.append(point_message)

        valid = (~point_mask).unsqueeze(-1).to(point_feats.dtype)
        global_mean = (point_feats * valid).sum(dim=1, keepdim=True)
        global_mean = global_mean / valid.sum(dim=1, keepdim=True).clamp_min(1.0)
        global_mean = global_mean.expand_as(point_feats)
        lang_per_point = lang_summary.unsqueeze(1).expand(-1, num_points, -1)
        gate_input = torch.cat([point_feats, global_mean, lang_per_point], dim=-1)
        level_weights = torch.softmax(self.level_gate(gate_input), dim=-1)

        stacked = torch.stack(scale_messages, dim=-1)
        message = (stacked * level_weights.unsqueeze(-2)).sum(dim=-1)
        message = self.point_out_proj(self.dropout(message))
        message = self.message_norm(message)
        return message.masked_fill(point_mask.unsqueeze(-1), 0)


Cluster_Attn = HierarchicalClusterRefinement
