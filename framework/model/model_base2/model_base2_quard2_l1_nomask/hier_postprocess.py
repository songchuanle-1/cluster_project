"""
quard2: 优化版点云层级聚类与 Cluster_Attn。

优化点（vs quard1）:
  P0: 6 层共享同一 Cluster_Attn 实例（per-layer gate/fuse 在 DEC 侧控制）
  P1: select 阶段不再做独立 Q/K 投影（共享 attend 阶段的 Q/K），消除冗余 Einsum + Linear
  P2: matching_masks 改为双线性偏移：Bilinear(QW_q, PW_p)，做 cluster-guided 偏移校正

流程概要：
 1. PointCloudPartitioner：FPS + 最近邻 → 多尺度「点→簇」划分
 2. SharedClusterBank：缓存划分，按当前点特征聚合 cluster token
 3. Cluster_Attn：query 路由 → 簇注意力 → 点回读 + matching_masks
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean


def batch2flatten(x, batch_mask):
    """[B,N,C] → [total_N,C]，去除 padding 行"""
    return x.view(-1, x.size(-1))[~batch_mask.view(-1)]


def get_batches(x, batch_offsets):
    """[total_N,C] + batch_offsets → [B,N_max,C] + padding mask"""
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
    """feats[N,C], cluster_ids[N] → cluster_mean[K,C]"""
    if cluster_ids.numel() == 0:
        return feats
    K = int(cluster_ids.max().item()) + 1
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=K)


# ---------------------------------------------------------------------------
# PointCloudPartitioner
# ---------------------------------------------------------------------------
class PointCloudPartitioner(nn.Module):
    """FPS 多层几何划分，记录每层每个场景的点->簇映射"""

    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]

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
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]
        device = sp_coords_float.device
        lens = [(batch_offsets[i + 1] - batch_offsets[i]).item() for i in range(len(batch_offsets) - 1)]
        layer_nums = list(self.cluster_layer_nums)
        layer_nums[0] = min(layer_nums[0], min(lens))
        for b in range(len(batch_offsets) - 1):
            s, e = batch_offsets[b].item(), batch_offsets[b + 1].item()
            coords_b = sp_coords_float[s:e]
            for lvl in range(len(layer_nums)):
                coords_b, cid = self.cluster_layer(coords_b, layer_nums[lvl], device)
                self.per_layer_cluster_ids[lvl].append(cid)


# ---------------------------------------------------------------------------
# SharedClusterBank
# ---------------------------------------------------------------------------
class SharedClusterBank(nn.Module):
    """几何划分一次；build_cluster_feats 用当前特征+固定划分聚合 cluster token"""

    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)

    def get_cluster(self, sp_pos, batch_offsets):
        self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        per_layer = [[] for _ in range(len(self.cluster_layer_nums))]
        for b in range(len(batch_offsets) - 1):
            s, e = batch_offsets[b].item(), batch_offsets[b + 1].item()
            feats_b = sp_feats[s:e]
            for lvl in range(len(self.cluster_layer_nums)):
                feats_b = aggregate_cluster(feats_b, self.partitioner.per_layer_cluster_ids[lvl][b])
                per_layer[lvl].append(feats_b)
        return [torch.stack(f) for f in per_layer]


# ---------------------------------------------------------------------------
# Cluster_Attn（优化版）
# ---------------------------------------------------------------------------
class Cluster_Attn(nn.Module):
    """
    多尺度 cluster routing + query-point 消息 + matching_masks.

    与 quard1 差异:
      P0: 参数共享 (DEC 侧只实例化一次, 6 层复用)
      P1: select + attend 共享 query_linear/k_linear (消除冗余投影)
      P2: matching_masks = Bilinear(Q@Wq', P@Wp') 双线性偏移
    """

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None, per_layer_topk_list=None, dropout=0.0):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        if per_layer_topk_list is None:
            per_layer_topk_list = [32, 16, 8]
        assert d_model % nhead == 0
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        self.scale = self.head_dim ** -0.5
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.per_layer_topk_list = list(per_layer_topk_list[:len(self.cluster_layer_nums)])
        if len(self.per_layer_topk_list) < len(self.cluster_layer_nums):
            self.per_layer_topk_list.extend(
                [self.per_layer_topk_list[-1]] * (len(self.cluster_layer_nums) - len(self.per_layer_topk_list))
            )

        # ---- 投影层 (select + attend 共享 query_linear / k_linear) ----
        self.q_linear = nn.Linear(d_model, d_model)       # point q (route)
        self.k_linear = nn.Linear(d_model, d_model)       # shared k (select score + attend key)
        self.v_linear = nn.Linear(d_model, d_model)       # attend value
        self.query_linear = nn.Linear(d_model, d_model)   # query q (select 路由信号 + attend query)
        self.query_k_linear = nn.Linear(d_model, d_model) # query as key (route)
        self.query_v_linear = nn.Linear(d_model, d_model) # query context as value (route)

        self.point_out_proj = nn.Linear(d_model, d_model)
        self.query_out_proj = nn.Linear(d_model, d_model)


        # ---- 多尺度融合 ----
        self.level_gate = nn.Linear(d_model * 2, len(self.cluster_layer_nums))
        self.query_level_gate = nn.Linear(d_model, len(self.cluster_layer_nums))
        self.message_norm = nn.LayerNorm(d_model)
        self.query_message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    # ---------- P1: 合并 select + attend ----------
    def query_attend_clusters(self, query_feats, cluster_feats, topk):
        """
        1) query 对全部簇打分 (共享 k_linear)
        2) top-k select
        3) query 在选中簇 + 全局 token 上做注意力

        返回: (context [B,Q,C], selected [B,Q,K,C])
        """
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]

        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k_all = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        scores = torch.einsum("bhqd,bhmd->bhqm", q, k_all) * self.scale
        mean_scores = scores.mean(dim=1)

        topk = min(topk, M)
        topk_idx = mean_scores.topk(topk, dim=-1).indices
        expanded = cluster_feats.unsqueeze(1).expand(-1, Q, -1, -1)
        selected = expanded.gather(2, topk_idx.unsqueeze(-1).expand(-1, -1, -1, cluster_feats.size(-1)))
        sel_w = mean_scores.gather(-1, topk_idx).unsqueeze(-1)
        selected = selected * (1.0 + sel_w)

        global_tok = cluster_feats.mean(dim=1, keepdim=True).unsqueeze(1).expand(-1, Q, -1, -1)
        selected = torch.cat([selected, global_tok], dim=2)
        K = selected.shape[2]

        k_sel = self.k_linear(selected).view(B, Q, K, self.nhead, self.head_dim).permute(0, 3, 1, 2, 4)
        v_sel = self.v_linear(selected).view(B, Q, K, self.nhead, self.head_dim).permute(0, 3, 1, 2, 4)

        attn_scores = torch.einsum("bhqd,bhqkd->bhqk", q, k_sel) * self.scale
        attn = torch.softmax(attn_scores, dim=-1)
        ctx = torch.einsum("bhqk,bhqkd->bhqd", attn, v_sel)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)
        ctx = self.query_out_proj(self.dropout(ctx))
        return ctx, selected

    # ---------- route: 点通过 query 读回簇信息 ----------
    def route_query_context_to_points(self, point_feats, query_feats, query_context, point_mask):
        B, N, _ = point_feats.shape
        Q = query_feats.shape[1]
        q = self.q_linear(point_feats).view(B, N, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.query_k_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.query_v_linear(query_context).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.einsum("bhnd,bhqd->bhnq", q, k) * self.scale
        attn = torch.softmax(scores, dim=-1)
        ctx = torch.einsum("bhnq,bhqd->bhnd", attn, v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, N, self.d_model)
        ctx = self.point_out_proj(self.dropout(ctx))
        ctx = ctx.masked_fill(point_mask.unsqueeze(-1), 0)
        return ctx


    # ---------- forward ----------
    def forward(self, point_feats, query, point_mask, cluster_feats_list):
        query_summary = query.mean(dim=1, keepdim=True).expand(-1, point_feats.shape[1], -1)
        gate_input = torch.cat([point_feats, query_summary], dim=-1)

        multi_scale_msgs = []
        multi_scale_qmsgs = []
        for cluster_feats, topk in zip(cluster_feats_list, self.per_layer_topk_list):
            query_ctx, _ = self.query_attend_clusters(query, cluster_feats, topk)
            pt_ctx = self.route_query_context_to_points(point_feats, query, query_ctx, point_mask)
            multi_scale_msgs.append(pt_ctx)
            multi_scale_qmsgs.append(query_ctx)

        lw = torch.softmax(self.level_gate(gate_input), dim=-1)
        qlw = torch.softmax(self.query_level_gate(query), dim=-1)

        final_msg = torch.zeros_like(point_feats)
        final_qmsg = torch.zeros_like(query)
        for idx in range(len(multi_scale_msgs)):
            final_msg = final_msg + multi_scale_msgs[idx] * lw[..., idx:idx + 1]
            final_qmsg = final_qmsg + multi_scale_qmsgs[idx] * qlw[..., idx:idx + 1]

        final_msg = self.message_norm(final_msg)
        final_qmsg = self.query_message_norm(final_qmsg)
        final_msg = final_msg.masked_fill(point_mask.unsqueeze(-1), 0)


        return {'point': final_msg, 'query': final_qmsg}
