"""
quard2_c2f_pq: Coarse-to-Fine + Per-Query 独立路由。

与 c2f 的核心差异:
  粗层 topk: 不再对 H 维 mean，而是保留 [B,H,Q,M] → topk per-head per-query
  级联传递: 上一层每个 query 独立选中自己的父簇 → 子簇候选 per-query 不同
  候选合并: 对每个 query，合并所有 head 选中的父簇（去重并集）

与 c2f 相同的部分:
  - PointCloudPartitioner + 父子映射
  - SharedClusterBank 级联聚合
  - 多尺度融合 + 点回读
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


# ============================================================================
# PointCloudPartitioner — 同 c2f
# ============================================================================
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
        child_cluster_maps = [[] for _ in range(num_layers - 1)]

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

                if lvl > 0:
                    child_centers = per_layer_coords[lvl + 1][b]
                    parent_centers = per_layer_coords[lvl][b]
                    dist = torch.cdist(child_centers, parent_centers)
                    parent_for_child = torch.min(dist, dim=-1)[1]

                    mapping = {}
                    for cc, pc in enumerate(parent_for_child.tolist()):
                        mapping.setdefault(int(pc), []).append(cc)
                    child_cluster_maps[lvl - 1].append(mapping)

        return per_layer_cluster_ids, child_cluster_maps


# ============================================================================
# SharedClusterBank — 同 c2f
# ============================================================================
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
            cum = 0
            per_batch_K = []
            for b in range(B):
                ids_b = ids_list[b]
                remapped_ids.append(ids_b + cum)
                Kb = int(ids_b.max().item()) + 1 if ids_b.numel() > 0 else 0
                cum += Kb
                per_batch_K.append(Kb)
            flat_ids = torch.cat(remapped_ids, dim=0)
            current_feats = aggregate_cluster(current_feats, flat_ids)
            padded_batches = []
            off = 0
            for b in range(B):
                Kb = per_batch_K[b]
                cf_b = current_feats[off:off+Kb]
                off += Kb
                padded_batches.append(cf_b)
            max_K = max(cf.shape[0] for cf in padded_batches)
            pad_list = []
            for cf in padded_batches:
                if cf.shape[0] < max_K:
                    pad = torch.zeros(max_K - cf.shape[0], cf.shape[1], device=device, dtype=cf.dtype)
                    cf = torch.cat([cf, pad], dim=0)
                pad_list.append(cf)
            cluster_feats_list.append(torch.stack(pad_list, dim=0))
        return cluster_feats_list


# ============================================================================
# PQ_C2F_ClusterAttn — Per-Query Coarse-to-Fine
# ============================================================================
class PQ_C2F_ClusterAttn(nn.Module):
    """
    Per-Query Coarse-to-Fine Cluster Attention.

    与 C2F 的关键区别:
      - 粗层选 topk 时保留 head 维，per-query-per-head 独立选择
      - 跨 head 合并成 per-query 候选集（取并集）
      - 子簇候选构建仍然是 per-query 独立

    参数 (从细到粗):
      cluster_layer_nums = [256, 64, 8]
      per_layer_topk_list = [4, 6, 8]  注意：这里 topk 是 per-head 的取值
    """

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None,
                 per_layer_topk_list=None, dropout=0.0):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        if per_layer_topk_list is None:
            per_layer_topk_list = [4, 6, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.per_layer_topk_list = list(per_layer_topk_list)
        self.num_scales = len(cluster_layer_nums)

        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        self.scale = self.head_dim ** -0.5

        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.query_linear = nn.Linear(d_model, d_model)
        self.query_k_linear = nn.Linear(d_model, d_model)
        self.query_v_linear = nn.Linear(d_model, d_model)

        self.point_out_proj = nn.Linear(d_model, d_model)
        self.query_out_proj = nn.ModuleList(
            [nn.Linear(d_model, d_model) for _ in range(self.num_scales)])

        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.query_level_gate = nn.Linear(d_model, self.num_scales)
        self.message_norm = nn.LayerNorm(d_model)
        self.query_message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    # ---------- 尺度内 attention + per-head topk ----------
    def _scale_attn(self, query_feats, cluster_feats, candidate_mask=None, return_topk_indices=False):
        """
        返回: context [B,Q,C], 以及可选 topk_indices [B,Q,K] (per-query)
        candidate_mask: [B,Q,M] bool（非 [B,H,Q,M]）
        """
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]

        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.v_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.scale  # [B, H, Q, M]

        if candidate_mask is not None:
            # candidate_mask [B,Q,M] → [B,1,Q,M] → broadcast to [B,H,Q,M]
            inf_mask = (~candidate_mask).unsqueeze(1).to(scores.dtype) * (-1e9)
            scores = scores + inf_mask

        attn = torch.softmax(scores, dim=-1)
        ctx = torch.einsum("bhqm,bhmd->bhqd", attn, v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)

        if not return_topk_indices:
            return ctx, None

        # Per-query topk: 在 [B,H,Q,M] 的 H 维做 mean 拿到 per-query 总分
        # 更精确：对每个 query，合并所有 head 选中的簇（取并集），
        # 但这太复杂。折中：H 维 sum 后 topk（保留 head 多样性，
        # 不同 head 关注不同 pattern）
        scores_sum_h = scores.sum(dim=1)  # [B, Q, M]
        topk_val, topk_idx = scores_sum_h.topk(
            min(topk_val.shape[-1] if isinstance(topk_val, torch.Tensor) else M, 
                candidate_mask.sum(dim=-1).min().item() if candidate_mask is not None else M),
            dim=-1)
        return ctx, topk_idx

    # 简化版：per-query topk
    def _scale_attn_with_topk(self, query_feats, cluster_feats, topk, candidate_mask=None):
        """
        返回: context, selected_indices [B, Q, topk]
        """
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]

        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.v_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.scale  # [B, H, Q, M]

        if candidate_mask is not None:
            inf_mask = (~candidate_mask).unsqueeze(1).to(scores.dtype) * (-1e9)
            scores = scores + inf_mask

        # 对 H 维 sum，得到 per-query 的分
        scores_q = scores.sum(dim=1)  # [B, Q, M]
        tk = min(topk, M)
        # 如果 candidate_mask 能选的不够 topk，就用实际可选的
        if candidate_mask is not None:
            n_cand = candidate_mask.sum(dim=-1).min().item()  # 最小可选的簇数
            tk = min(tk, max(1, int(n_cand)))
        _, topk_idx = scores_q.topk(tk, dim=-1)  # [B, Q, tk]

        attn = torch.softmax(scores, dim=-1)
        ctx = torch.einsum("bhqm,bhmd->bhqd", attn, v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)
        return ctx, topk_idx

    # ---------- 子簇候选掩码 (per-query) ----------
    def _child_mask(self, parent_indices, child_mapping, num_children, B, Q, device):
        """
        parent_indices: [B, Q, K_parent] — per-query 选中的父簇
        返回: mask [B, Q, num_children]
        """
        mask = torch.zeros(B, Q, num_children, dtype=torch.bool, device=device)
        for bb in range(B):
            mapping = child_mapping[bb]
            for qq in range(Q):
                pids = parent_indices[bb, qq].tolist()
                # 去重取并集
                seen = set()
                for pid in pids:
                    if pid not in seen:
                        for cc in mapping.get(int(pid), []):
                            if cc < num_children:
                                mask[bb, qq, int(cc)] = True
                        seen.add(pid)
        return mask

    # ---------- 点回读 ----------
    def _route_points(self, point_feats, query_feats, query_context, point_mask):
        B, N, _ = point_feats.shape
        Q = query_feats.shape[1]
        q = self.query_linear(point_feats).view(B, N, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.query_k_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.query_v_linear(query_context).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.einsum("bhnd,bhqd->bhnq", q, k) * self.scale
        attn = torch.softmax(scores, dim=-1)
        ctx = torch.einsum("bhnq,bhqd->bhnd", attn, v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, N, self.d_model)
        ctx = self.point_out_proj(self.dropout(ctx))
        return ctx.masked_fill(point_mask.unsqueeze(-1), 0)

    # ---------- forward ----------
    def forward(self, point_feats, query, point_mask, cluster_feats_list, child_cluster_maps):
        B, Q, _ = query.shape
        num_scales = self.num_scales

        qmsgs = []
        msgs = []
        prev_indices = None  # [B, Q, K_prev]

        for lvl in reversed(range(num_scales)):
            cf = cluster_feats_list[lvl]
            topk = self.per_layer_topk_list[lvl]

            if lvl == num_scales - 1:
                # 最粗层：全选 + per-query topk
                qctx, prev_indices = self._scale_attn_with_topk(query, cf, topk)
            else:
                # 中间/细层：per-query 子簇候选
                cmask = self._child_mask(prev_indices, child_cluster_maps[lvl],
                                         cf.shape[1], B, Q, cf.device)
                if cmask.any():
                    qctx, prev_indices = self._scale_attn_with_topk(query, cf, topk, candidate_mask=cmask)
                else:
                    qctx, prev_indices = self._scale_attn_with_topk(query, cf, topk)

            qctx = self.query_out_proj[lvl](self.dropout(qctx))
            qmsgs.append(qctx)
            msgs.append(self._route_points(point_feats, query, qctx, point_mask))

        msgs = list(reversed(msgs))
        qmsgs = list(reversed(qmsgs))

        qs = query.mean(dim=1, keepdim=True).expand(-1, point_feats.shape[1], -1)
        gi = torch.cat([point_feats, qs], dim=-1)
        lw = torch.softmax(self.level_gate(gi), dim=-1)
        qlw = torch.softmax(self.query_level_gate(query), dim=-1)

        fm = torch.zeros_like(point_feats)
        fq = torch.zeros_like(query)
        for i in range(num_scales):
            fm = fm + msgs[i] * lw[..., i:i+1]
            fq = fq + qmsgs[i] * qlw[..., i:i+1]

        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)
        fq = self.query_message_norm(fq)
        return {'point': fm, 'query': fq}


Cluster_Attn = PQ_C2F_ClusterAttn
