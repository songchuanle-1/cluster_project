"""
Cluster attention 模块集合 — posA_l1_residual 版本。

新模块 ResidualAttnRefine: 补上 C2F_ClusterAttn_Lite 的梯度断开——query→cluster
attention 产出不再丢弃，而是残差调制 cluster token。

保留原有 MultiScale_Gather_Refine / MultiScale_Gather / C2F_ClusterAttn_Lite / C2F_ClusterAttn_TrueRoute 兼容旧 config。
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean


def batch2flatten(x, batch_mask):
    return x.view(-1, x.size(-1))[~batch_mask.view(-1)]


def get_batches(x, batch_offsets):
    B = len(batch_offsets) - 1
    max_len = max(batch_offsets[1:] - batch_offsets[:-1])
    if torch.is_tensor(max_len):
        max_len = max_len.item()
    new_feats = torch.zeros(B, max_len, x.shape[1], device=x.device, dtype=x.dtype)
    mask = torch.ones(B, max_len, dtype=torch.bool, device=x.device)
    for i in range(B):
        s, e = batch_offsets[i].item(), batch_offsets[i + 1].item()
        cur = e - s
        new_feats[i, :cur] = x[s:e]
        mask[i, :cur] = False
    return new_feats, mask


def aggregate_cluster(feats, cluster_ids):
    if cluster_ids.numel() == 0:
        return feats
    K = int(cluster_ids.max().item()) + 1
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=K)


class PointCloudPartitioner(nn.Module):
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)

    def partition_points(self, points_pos, fps_pos):
        dist = torch.cdist(points_pos, fps_pos)
        labels = torch.min(dist, dim=-1)[1]
        counts = torch.bincount(labels, minlength=fps_pos.shape[0])
        arange = torch.arange(points_pos.shape[0], device=labels.device)
        _, perm = torch.sort(labels)
        idx_sorted = arange[perm]
        return list(torch.split(idx_sorted, counts.tolist()))

    def cluster_layer(self, pos, fps_num, device):
        fps_num = min(fps_num, pos.size(0))
        fps_seed = FurthestPointSampling.apply(pos.unsqueeze(0), fps_num)
        fps_pos = pos.gather(0, fps_seed.long().squeeze(0).unsqueeze(-1).repeat(1, pos.size(-1)))
        subset_idxs = self.partition_points(pos, fps_pos)
        cid = torch.full((pos.size(0),), -1, dtype=torch.long, device=device)
        for k, idx in enumerate(subset_idxs):
            cid[idx.long()] = k
        center = aggregate_cluster(pos, cid)
        return center, cid

    def forward(self, sp_coords_float, batch_offsets):
        device = sp_coords_float.device
        num_layers = len(self.cluster_layer_nums)
        per_layer_cluster_ids = [[] for _ in range(num_layers)]
        per_layer_coords = [[] for _ in range(num_layers + 1)]
        lens = [(batch_offsets[i + 1] - batch_offsets[i]).item() for i in range(len(batch_offsets) - 1)]
        layer_nums = list(self.cluster_layer_nums)
        layer_nums[0] = min(layer_nums[0], min(lens))
        for b in range(len(batch_offsets) - 1):
            s, e = batch_offsets[b].item(), batch_offsets[b + 1].item()
            coords_b = sp_coords_float[s:e]
            per_layer_coords[0].append(coords_b)
            for lvl in range(num_layers):
                coords_b, cid = self.cluster_layer(coords_b, layer_nums[lvl], device)
                per_layer_cluster_ids[lvl].append(cid)
                per_layer_coords[lvl + 1].append(coords_b)
        child_cluster_maps = [[] for _ in range(num_layers - 1)]
        B = len(per_layer_coords[0])
        for b in range(B):
            for lvl in range(1, num_layers):
                child = per_layer_coords[lvl + 1][b]
                parent = per_layer_coords[lvl][b]
                if child.shape[0] == 0 or parent.shape[0] == 0:
                    child_cluster_maps[lvl - 1].append({})
                    continue
                dist = torch.cdist(child, parent)
                parent_for_child = torch.min(dist, dim=-1)[1]
                mapping = {}
                for cc, pc in enumerate(parent_for_child.tolist()):
                    mapping.setdefault(int(pc), []).append(cc)
                child_cluster_maps[lvl - 1].append(mapping)
        return per_layer_cluster_ids, child_cluster_maps


class SharedClusterBank(nn.Module):
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)

    def get_cluster(self, sp_pos, batch_offsets):
        self.cluster_ids_list, self.child_cluster_maps = self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        device = sp_feats.device
        B = len(batch_offsets) - 1
        cluster_feats_list = []
        current_feats = sp_feats
        for lvl in range(len(self.cluster_layer_nums)):
            ids_list = self.cluster_ids_list[lvl]
            remapped_ids = []
            cum, per_batch_K = 0, []
            for b in range(B):
                ids_b = ids_list[b]
                remapped_ids.append(ids_b + cum)
                Kb = int(ids_b.max().item()) + 1 if ids_b.numel() > 0 else 0
                cum += Kb
                per_batch_K.append(Kb)
            current_feats = aggregate_cluster(current_feats, torch.cat(remapped_ids, dim=0))
            padded_batches, off = [], 0
            for b in range(B):
                Kb = per_batch_K[b]
                cf_b = current_feats[off:off + Kb]
                off += Kb
                padded_batches.append(cf_b)
            max_K = max(cf.shape[0] for cf in padded_batches)
            pad_list = []
            for cf in padded_batches:
                pad = torch.zeros(max_K - cf.shape[0], cf.shape[1], device=device, dtype=cf.dtype) if cf.shape[0] < max_K else None
                pad_list.append(torch.cat([cf, pad], dim=0) if pad is not None else cf)
            cluster_feats_list.append(torch.stack(pad_list, dim=0))
        return cluster_feats_list


class ClusterTokenRefine(nn.Module):
    """共享 1 层 MHA + FFN"""
    def __init__(self, d_model=256, nhead=8, dropout=0.0):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 4), nn.GELU(),
            nn.Dropout(dropout), nn.Linear(d_model * 4, d_model))
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, cluster_feats, padding_mask=None):
        x = cluster_feats
        a, _ = self.self_attn(x, x, x, key_padding_mask=padding_mask)
        x = self.norm1(x + self.dropout(a))
        x = self.norm2(x + self.dropout(self.ffn(x)))
        return x


class MultiScale_Gather_Refine(nn.Module):
    """无 routing + cluster token self-attention refine + sigmoid gate + distance cue"""
    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None, dropout=0.0, **kwargs):
        super().__init__()
        if cluster_layer_nums is None: cluster_layer_nums = [256, 64, 8]
        self.num_scales = len(cluster_layer_nums)
        self.refine = ClusterTokenRefine(d_model, nhead, dropout)
        self.gate_fc = nn.Sequential(
            nn.Linear(d_model + self.num_scales, d_model // 4),
            nn.ReLU(), nn.Linear(d_model // 4, self.num_scales))
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def _dist(self, pt, cf_list, cid_list, mask):
        B, N, C = pt.shape
        S = self.num_scales
        d = torch.zeros(B, N, S, device=pt.device, dtype=pt.dtype)
        for l in range(S):
            for b in range(B):
                ids = cid_list[l][b].long().clamp(0, cf_list[l].shape[1] - 1)
                nv = ids.shape[0]
                d[b, :nv, l] = (pt[b, :nv] - cf_list[l][b, ids]).norm(dim=-1)
        return d

    def _to_pts(self, pt, cf_list, cid_list, mask):
        B, N, C = pt.shape
        S = self.num_scales
        m = []
        for l in range(S):
            fm = torch.zeros(B, N, C, device=pt.device, dtype=pt.dtype)
            for b in range(B):
                ids = cid_list[l][b].long().clamp(0, cf_list[l].shape[1] - 1)
                fm[b, :ids.shape[0]] = cf_list[l][b, ids]
            m.append(fm)
        dist = self._dist(pt, cf_list, cid_list, mask)
        gate = torch.sigmoid(self.gate_fc(torch.cat([pt, dist.masked_fill(mask.unsqueeze(-1), 0)], dim=-1)))
        stk = torch.stack(m, dim=-1)
        out = (stk * gate.unsqueeze(-2)).sum(dim=-1)
        return self.point_out_proj(self.dropout(out)).masked_fill(mask.unsqueeze(-1), 0)

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        refined = []
        for cf in cluster_feats_list:
            vld = (cf.abs().sum(dim=-1) > 1e-8)
            r = self.refine(cf, padding_mask=~vld)
            refined.append(cf + r)
        fm = self._to_pts(point_feats, refined, cluster_ids_list, point_mask)
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': fm}


# ============================================================================
# ★ NEW: ResidualAttnRefine — 让 Q/K/V 首次参与梯度
# ============================================================================
class ResidualAttnRefine(nn.Module):
    """
    补上 C2F_ClusterAttn_Lite 的梯度断开:
      query→cluster attention 输出 → 残差调制 cluster token → gather 回点

    与 B1 的区别:
      - B1: Q/K/V 全量计算但丢弃,点写回用原始 scatter_mean token
      - 新: Q/K/V 产出 context → 残差调制 cluster token
            cluster_feat = cluster_feat + sigmoid(gate) * proj(context_aggregated)
    """
    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None,
                 per_layer_topk_list=None, dropout=0.0, **kwargs):
        super().__init__()
        if cluster_layer_nums is None: cluster_layer_nums = [256, 64, 8]
        if per_layer_topk_list is None: per_layer_topk_list = [4, 6, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.per_layer_topk_list = list(per_layer_topk_list)
        self.num_scales = len(cluster_layer_nums)
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        self.scale = self.head_dim ** -0.5

        self.query_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)

        self.context_proj = nn.ModuleList([
            nn.Sequential(nn.Linear(d_model, d_model), nn.LayerNorm(d_model))
            for _ in range(self.num_scales)])
        self.residual_gate = nn.Parameter(torch.tensor(0.1))

        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def _scale_attn(self, query_feats, cluster_feats, candidate_mask=None):
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]
        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.v_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        s = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.scale
        if candidate_mask is not None:
            s = s + (~candidate_mask).unsqueeze(1).to(s.dtype) * (-1e9)
        ctx = torch.einsum("bhqm,bhmd->bhqd", torch.softmax(s, dim=-1), v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)
        return ctx, s.mean(dim=1)

    def _child_mask(self, parent_indices, child_mapping, num_children, B, Q, device):
        mask = torch.zeros(B, Q, num_children, dtype=torch.bool, device=device)
        for bb in range(B):
            mapping = child_mapping[bb]
            for qq in range(Q):
                for pid in parent_indices[bb, qq].tolist():
                    for cc in mapping.get(int(pid), []):
                        if cc < num_children: mask[bb, qq, int(cc)] = True
        return mask

    def _cluster_to_points(self, point_feats, cluster_feats_list, cluster_ids_list, point_mask):
        B, N, C = point_feats.shape
        scale_msgs = []
        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]
            msg = torch.zeros(B, N, C, device=point_feats.device, dtype=point_feats.dtype)
            for b in range(B):
                ids_b = cluster_ids_list[lvl][b].long().clamp(0, cf.shape[1] - 1)
                msg[b, :ids_b.shape[0]] = cf[b, ids_b]
            scale_msgs.append(msg)
        stack = torch.stack(scale_msgs, dim=-1)
        gm = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)
        lw = torch.softmax(self.level_gate(torch.cat([point_feats, gm], dim=-1)), dim=-1)
        fused = (stack * lw.unsqueeze(-2)).sum(dim=-1)
        return self.point_out_proj(self.dropout(fused)).masked_fill(point_mask.unsqueeze(-1), 0)

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        B, Q, _ = query.shape

        # C2F routing + 保存每层 context
        prev_indices = None
        qctxs = {}
        for lvl in reversed(range(self.num_scales)):
            cf = cluster_feats_list[lvl]
            topk = min(self.per_layer_topk_list[lvl], cf.shape[1])
            if lvl == self.num_scales - 1:
                qctx, scores = self._scale_attn(query, cf)
                prev_indices = scores.topk(topk, dim=-1).indices
            else:
                cmask = self._child_mask(prev_indices, child_cluster_maps[lvl], cf.shape[1], B, Q, cf.device)
                qctx, scores = self._scale_attn(query, cf, candidate_mask=cmask if cmask.any() else None)
                ms = scores.masked_fill(~cmask, -1e9) if cmask.any() else scores
                prev_indices = ms.topk(topk, dim=-1).indices
            qctxs[lvl] = qctx

        # ★ 残差调制: qctx → cluster token
        gate = torch.sigmoid(self.residual_gate)
        refined = []
        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]
            # qctx 沿 Q 维取均值作为 cluster 调制源
            ctx_mean = qctxs[lvl].mean(dim=1, keepdim=True)  # [B, 1, C]
            mod = gate * self.context_proj[lvl](ctx_mean.expand_as(cf))
            refined.append(cf + mod)

        fm = self._cluster_to_points(point_feats, refined, cluster_ids_list, point_mask)
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': fm}


# ============================================================================
# 从 refine 包导入旧类 (兼容旧 config 的 cluster_mode=legacy/noroute/true_route)
# ============================================================================
from framework.model.Quard_model.model_base1_quard2_c2f_enc_lite_posA_l1_refine.hier_postprocess import (
    C2F_ClusterAttn_Lite,
    MultiScale_Gather,
    C2F_ClusterAttn_TrueRoute,
)
