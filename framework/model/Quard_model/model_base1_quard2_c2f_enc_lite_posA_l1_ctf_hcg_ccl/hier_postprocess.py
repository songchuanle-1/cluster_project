"""
quard2_c2f_enc_lite: 轻量版 Coarse-to-Fine Cluster Attention.

相比 c2f_enc 的三项优化 (P0: A+B+D):
  A. 去掉 _route_points (N×Q 全注意力), 改用 cluster_ids 直接 gather 回读 → O(N)
  B. 不再修改 query (只增强 inst_feats), 避免与 decoder 的 query 更新路径冲突
  D. Cluster Attention 仅在后 N 层使用 (由 dec.py 中 Encoder_layer 控制)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean, scatter_max


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


def aggregate_cluster(feats, cluster_ids, pool_type='mean'):
    if cluster_ids.numel() == 0:
        return feats
    K = int(cluster_ids.max().item()) + 1
    if pool_type == 'max':
        return scatter_max(feats, cluster_ids, dim=0, dim_size=K)[0]
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=K)


# ============================================================================
# PointCloudPartitioner — 同 c2f_enc
# ============================================================================
class PointCloudPartitioner(nn.Module):
    """FPS 多层几何划分，记录每层点→簇映射，并建立父子关系"""

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
        child_cluster_maps = [[] for _ in range(num_layers - 1)]  # lvl→lvl-1 的映射

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
                    # 子簇中心 → 父簇归属（用最近邻）
                    child_centers = per_layer_coords[lvl + 1][b]  # [K_lvl, 3]
                    parent_centers = per_layer_coords[lvl][b]     # [K_lvl-1, 3]
                    dist = torch.cdist(child_centers, parent_centers)
                    parent_for_child = torch.min(dist, dim=-1)[1]  # [K_lvl]

                    mapping = {}
                    for cc, pc in enumerate(parent_for_child.tolist()):
                        mapping.setdefault(int(pc), []).append(cc)
                    child_cluster_maps[lvl - 1].append(mapping)

        return per_layer_cluster_ids, child_cluster_maps


# ============================================================================
# SharedClusterBank — 同 c2f_enc
# ============================================================================
class SharedClusterBank(nn.Module):
    """几何划分一次，用当前特征聚合 cluster token"""

    def __init__(self, cluster_layer_nums=None, cluster_pool_type='mean', d_model=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.cluster_pool_type = cluster_pool_type
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)
        if cluster_pool_type == 'dual':
            assert d_model is not None, "d_model required for dual-branch cluster aggregation"
            self.dual_proj = nn.Sequential(
                nn.Linear(2 * d_model, d_model),
                nn.LayerNorm(d_model),
                nn.ReLU(),
                nn.Linear(d_model, d_model),
            )

    def get_cluster(self, sp_pos, batch_offsets):
        self.cluster_ids_list, self.child_cluster_maps = self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        """级联聚合：lvl0从原始点聚合成256token/batch，lvl1从256聚合成64/batch，lvl2从64聚合成8/batch"""
        device = sp_feats.device
        B = len(batch_offsets) - 1
        cluster_feats_list = []
        current_feats = sp_feats  # [total_N, C]
        for lvl in range(len(self.cluster_layer_nums)):
            ids_list = self.cluster_ids_list[lvl]
            # Per-batch remap: add cumulative offset so ids are globally unique
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
            total_K = cum
            if self.cluster_pool_type == 'dual':
                mean_feats = aggregate_cluster(current_feats, flat_ids, pool_type='mean')  # [total_K, C]
                max_feats = aggregate_cluster(current_feats, flat_ids, pool_type='max')    # [total_K, C]
                current_feats = self.dual_proj(torch.cat([mean_feats, max_feats], dim=-1))  # [total_K, C]
            else:
                current_feats = aggregate_cluster(current_feats, flat_ids, pool_type=self.cluster_pool_type)  # [total_K, C]
            # Split back into per-batch tensors and pad
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
# C2F_ClusterAttn_Lite — 轻量版 Coarse-to-Fine 级联注意力
# ============================================================================
class C2F_ClusterAttn_Lite(nn.Module):
    """
    轻量版 Coarse-to-Fine Cluster Attention.

    相比原版 C2F_ClusterAttn 的改动:
      A. 去掉 _route_points (N×Q 全注意力) → 改用 cluster_ids 直接 gather, O(N)
      B. 不返回 query message, 只增强 inst_feats
      (D 由 dec.py 中 Encoder_layer 控制: 仅在后 N 层启用)

    执行顺序 (从粗到细):
      最粗 (8簇, topk=8):  全选, full attention
      中间 (64簇, topk=6): 只看粗层选中簇的子簇
      最细 (256簇, topk=4): 只看中间层选中簇的子簇
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

        # ── query → cluster attention 投影 ──
        self.query_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)

        # ── point message 输出 ──
        self.point_out_proj = nn.Linear(d_model, d_model)

        # ── 多尺度融合 gate (per-point, 基于 [local_feat, global_mean]) ──
        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    # ---------- 尺度内 attention (不变) ----------
    def _scale_attn(self, query_feats, cluster_feats, candidate_mask=None):
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]

        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.v_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.scale
        if candidate_mask is not None:
            scores = scores + (~candidate_mask).unsqueeze(1).to(scores.dtype) * (-1e9)

        mean_scores = scores.mean(dim=1)
        attn = torch.softmax(scores, dim=-1)
        ctx = torch.einsum("bhqm,bhmd->bhqd", attn, v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)
        return ctx, mean_scores

    # ---------- 子簇候选掩码 (不变) ----------
    def _child_mask(self, parent_indices, child_mapping, num_children, B, Q, device):
        """parent_indices: [B,Q,K_parent] → mask: [B,Q,M_child]"""
        mask = torch.zeros(B, Q, num_children, dtype=torch.bool, device=device)
        for bb in range(B):
            mapping = child_mapping[bb]
            for qq in range(Q):
                for pid in parent_indices[bb, qq].tolist():
                    for cc in mapping.get(int(pid), []):
                        if cc < num_children:
                            mask[bb, qq, int(cc)] = True
        return mask

    # ---------- 轻量 cluster → point 回读 (新增, 替代 _route_points) ----------
    def _cluster_to_points(self, point_feats, cluster_feats_list,
                           cluster_ids_list, point_mask):
        """
        每个点通过 cluster_ids 直接 gather 所属 cluster token 的特征 → O(N).
        然后多尺度融合 (per-point learned gate).

        Args:
            point_feats: [B, N, C]  padded 的 inst_feats
            cluster_feats_list: list of [B, K_lvl, C]  各级 cluster tokens
            cluster_ids_list: list of list([N_b])  各级每个点所属的 cluster id
            point_mask: [B, N]  True = padding
        Returns:
            [B, N, C]  增强后的 point message
        """
        B, N, C = point_feats.shape
        scale_msgs = []

        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]  # [B, K_lvl, C]
            msg = torch.zeros(B, N, C, device=point_feats.device, dtype=point_feats.dtype)
            for b in range(B):
                ids_b = cluster_ids_list[lvl][b].long()  # [N_b]
                n_valid = ids_b.shape[0]
                # clamp 防止越界 (padding 位置可能含无效 id)
                ids_b = ids_b.clamp(min=0, max=cf.shape[1] - 1)
                msg[b, :n_valid] = cf[b, ids_b]  # [N_b, C]
            scale_msgs.append(msg)

        # 多尺度融合: per-point learned gate
        stack = torch.stack(scale_msgs, dim=-1)  # [B, N, C, S]
        global_mean = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)
        gate_in = torch.cat([point_feats, global_mean], dim=-1)  # [B, N, 2C]
        lw = torch.softmax(self.level_gate(gate_in), dim=-1)  # [B, N, S]

        fused = (stack * lw.unsqueeze(-2)).sum(dim=-1)  # [B, N, C]
        fused = self.point_out_proj(self.dropout(fused))
        return fused.masked_fill(point_mask.unsqueeze(-1), 0)

    # ---------- forward ----------
    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        """
        Args:
            point_feats: [B, N, C]  padded inst_feats
            query: [B, Q, C]  (仅用于 C2F 路由, 不修改)
            point_mask: [B, N]  True = padding
            cluster_feats_list: list of [B, K_lvl, C]
            child_cluster_maps: list of list(dict)  父子映射
            cluster_ids_list: list of list([N_b])  每级每个点的 cluster id
        Returns:
            {'point': fm}  仅返回 point message
        """
        B, Q, _ = query.shape
        num_scales = self.num_scales

        prev_indices = None

        for lvl in reversed(range(num_scales)):
            cf = cluster_feats_list[lvl]
            topk = min(self.per_layer_topk_list[lvl], cf.shape[1])

            if lvl == num_scales - 1:
                # 最粗层：全选
                _qctx, scores = self._scale_attn(query, cf)
                prev_indices = scores.topk(topk, dim=-1).indices
            else:
                # 细层：子簇候选
                cmask = self._child_mask(prev_indices, child_cluster_maps[lvl],
                                         cf.shape[1], B, Q, cf.device)
                if cmask.any():
                    _qctx, scores = self._scale_attn(query, cf, candidate_mask=cmask)
                    ms = scores.masked_fill(~cmask, -1e9)
                else:
                    _qctx, scores = self._scale_attn(query, cf)
                    ms = scores
                prev_indices = ms.topk(topk, dim=-1).indices

        # C2F 路由完成后, 一次性将聚合好的多尺度 cluster tokens 映射回原始点
        fm = self._cluster_to_points(point_feats, cluster_feats_list,
                                     cluster_ids_list, point_mask)
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)

        return {'point': fm}


class MultiScale_Gather(nn.Module):
    """Pure multi-scale cluster-to-point gather without query routing."""

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None,
                 per_layer_topk_list=None, dropout=0.0):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.num_scales = len(cluster_layer_nums)
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def _cluster_to_points(self, point_feats, cluster_feats_list,
                           cluster_ids_list, point_mask):
        B, N, C = point_feats.shape
        scale_messages = []

        for level in range(self.num_scales):
            cluster_feats = cluster_feats_list[level]
            message = torch.zeros_like(point_feats)
            for b in range(B):
                point_cluster_ids = cluster_ids_list[level][b].long()
                num_valid = point_cluster_ids.shape[0]
                point_cluster_ids = point_cluster_ids.clamp(
                    min=0, max=cluster_feats.shape[1] - 1)
                message[b, :num_valid] = cluster_feats[
                    b, point_cluster_ids]
            scale_messages.append(message)

        stacked = torch.stack(scale_messages, dim=-1)
        global_mean = point_feats.mean(
            dim=1, keepdim=True).expand_as(point_feats)
        level_weights = torch.softmax(
            self.level_gate(torch.cat([point_feats, global_mean], dim=-1)),
            dim=-1)
        fused = (stacked * level_weights.unsqueeze(-2)).sum(dim=-1)
        fused = self.point_out_proj(self.dropout(fused))
        return fused.masked_fill(point_mask.unsqueeze(-1), 0)

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        point_message = self._cluster_to_points(
            point_feats, cluster_feats_list,
            cluster_ids_list, point_mask)
        point_message = self.message_norm(point_message)
        point_message = point_message.masked_fill(
            point_mask.unsqueeze(-1), 0)
        return {'point': point_message}


class C2F_ClusterAttn_TrueRoute(C2F_ClusterAttn_Lite):
    """Coarse-to-fine routing whose selected paths affect point messages.

    The legacy Lite module computes top-k routes but discards them before its
    cluster-to-point readback.  This version uses the final fine-level routes
    to aggregate query contexts into routed fine-cluster tokens, then replaces
    the fine scale in the normal multi-scale point readback.  Unselected fine
    clusters retain their original token, avoiding empty messages.
    """

    @staticmethod
    def _queries_to_routed_clusters(cluster_feats, query_context,
                                    route_indices, route_scores):
        B, M, C = cluster_feats.shape
        routed = cluster_feats.clone()
        route_weights = torch.softmax(route_scores, dim=-1)

        for b in range(B):
            flat_indices = route_indices[b].reshape(-1)
            contributions = (
                query_context[b].unsqueeze(1)
                * route_weights[b].unsqueeze(-1)
            ).reshape(-1, C)
            flat_weights = route_weights[b].reshape(-1, 1)

            context_sum = cluster_feats.new_zeros(M, C)
            weight_sum = cluster_feats.new_zeros(M, 1)
            context_sum.index_add_(0, flat_indices, contributions)
            weight_sum.index_add_(0, flat_indices, flat_weights)

            selected = weight_sum.squeeze(-1) > 0
            routed[b, selected] = (
                context_sum[selected] / weight_sum[selected].clamp_min(1e-6))

        return routed

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        B, Q, _ = query.shape
        num_scales = self.num_scales
        prev_indices = None
        fine_query_context = None
        fine_route_indices = None
        fine_route_scores = None

        for lvl in reversed(range(num_scales)):
            cf = cluster_feats_list[lvl]
            topk = min(self.per_layer_topk_list[lvl], cf.shape[1])

            if lvl == num_scales - 1:
                query_context, scores = self._scale_attn(query, cf)
                masked_scores = scores
            else:
                candidate_mask = self._child_mask(
                    prev_indices, child_cluster_maps[lvl],
                    cf.shape[1], B, Q, cf.device)
                if candidate_mask.any():
                    query_context, scores = self._scale_attn(
                        query, cf, candidate_mask=candidate_mask)
                    masked_scores = scores.masked_fill(
                        ~candidate_mask, -1e9)
                else:
                    query_context, scores = self._scale_attn(query, cf)
                    masked_scores = scores

            prev_indices = masked_scores.topk(topk, dim=-1).indices

            if lvl == 0:
                fine_query_context = query_context
                fine_route_indices = prev_indices
                fine_route_scores = torch.gather(
                    masked_scores, -1, fine_route_indices)

        routed_cluster_feats = list(cluster_feats_list)
        routed_cluster_feats[0] = self._queries_to_routed_clusters(
            cluster_feats_list[0], fine_query_context,
            fine_route_indices, fine_route_scores)

        point_message = self._cluster_to_points(
            point_feats, routed_cluster_feats,
            cluster_ids_list, point_mask)
        point_message = self.message_norm(point_message)
        point_message = point_message.masked_fill(
            point_mask.unsqueeze(-1), 0)
        return {'point': point_message}


Cluster_Attn = C2F_ClusterAttn_Lite


class C2F_ClusterAttn_DRP(C2F_ClusterAttn_Lite):
    """M32 Delete Routing Path: champion Lite 的 top-k C2F 路由被证实是装饰性
    (路由索引 prev_indices 从不用于 _cluster_to_points), 但转发了 query→cluster
    attention 计算中的 6 个 QKV 投影与 3 层 softmax。本变体去掉整个路由计算,
    只保留 _cluster_to_points 的 context 回写。测试: 去掉路由死代码后 mIoU 是否不变.
    FLOPs 节省: 去掉 QKV 投影 + _scale_attn + child_mask + topk 循环.
    """

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        # 跳过全部 routing: 直接做 multi-scale context 回写
        point_message = self._cluster_to_points(
            point_feats, cluster_feats_list, cluster_ids_list, point_mask)
        point_message = self.message_norm(point_message)
        point_message = point_message.masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': point_message}


class C2F_ClusterAttn_CTF(C2F_ClusterAttn_Lite):
    """M41 Cluster Token Feed-Forward: per-scale FFN refinement of cluster tokens.

    DRP (0.5012) 证明 routing 是死代码。CTF 在此基础上测试: cluster token 自身
    是否需要 non-linear refinement 才能提供更好的 context?

    每级 cluster token 在 readback 前经过:
      token = token + FFN(LayerNorm(token))
      FFN = Linear(d→4d) → GELU → Linear(4d→d)

    C2C (队列中) 测试 token 交互 (self-attention between tokens);
    CTF 测试 token 自身 refinement (per-token FFN, no interaction).
    两者互补: C2C=interaction, CTF=refinement.

    假设: mean-pool 聚合丢失了非线性特征交互, per-token FFN 恢复表达能力,
    提升 readback context 质量, 突破 0.5012 天花板.
    """

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None,
                 per_layer_topk_list=None, dropout=0.0):
        super().__init__(d_model=d_model, nhead=nhead,
                         cluster_layer_nums=cluster_layer_nums,
                         per_layer_topk_list=per_layer_topk_list,
                         dropout=dropout)
        num_scales = len(cluster_layer_nums) if cluster_layer_nums else 3

        # Per-scale FFN: 2-layer MLP with GELU
        self.cluster_ffn = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model, d_model * 4),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(d_model * 4, d_model),
                nn.Dropout(dropout),
            ) for _ in range(num_scales)
        ])
        # Per-scale LayerNorm (pre-norm style)
        self.cluster_ffn_norm = nn.ModuleList([
            nn.LayerNorm(d_model) for _ in range(num_scales)
        ])

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        # Skip routing (like DRP). Apply per-scale FFN refinement to cluster tokens.
        refined_cluster_feats = []
        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]  # [B, K_lvl, C]
            # Pre-norm residual FFN
            refined = cf + self.cluster_ffn[lvl](self.cluster_ffn_norm[lvl](cf))
            refined_cluster_feats.append(refined)

        point_message = self._cluster_to_points(
            point_feats, refined_cluster_feats, cluster_ids_list, point_mask)
        point_message = self.message_norm(point_message)
        point_message = point_message.masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': point_message}


class C2F_ClusterAttn_CTF_HCG(C2F_ClusterAttn_CTF):
    """M81 Cluster Token FFN × Hierarchical Composition Gather.

    组合 CTF (per-scale FFN 精炼 cluster token, M41=0.4995) 与 HCG (正确多尺度交付,
    M65=0.5002). 两轴独立有效但从未正交:
      - CTF 提升 token 源质量 (per-token FFN, 恢复 mean-pool 丢失的非线性交互);
      - HCG 修复 _cluster_to_points 粗尺度交付缺陷 (逐级组合 点→l0→l1→l2 映射),
        让每个点收到自己真正的多尺度 context.
    假设: 0.5012 champion 的瓶颈在 readback/融合 (CTF 分析结论), HCG 修 readback +
    CTF 提 token 源 = 双短板同补 → 破 0.51 候选.

    实现: 继承 CTF (获得 cluster_ffn 精炼逻辑), 覆写 _cluster_to_points 为 HCG
    的 composed gather 版 (从 M78/reag_hcg 逐字复制). 零新增参数.
    """

    def _cluster_to_points(self, point_feats, cluster_feats_list,
                           cluster_ids_list, point_mask):
        B, N, C = point_feats.shape
        num_scales = self.num_scales

        composed_ids = []
        for b in range(B):
            ids_l0 = cluster_ids_list[0][b].long()
            ids_l0 = ids_l0.clamp(min=0, max=cluster_feats_list[0].shape[1] - 1)
            level_ids = [ids_l0]
            for lvl in range(1, num_scales):
                parent_ids = cluster_ids_list[lvl][b].long()
                parent_ids = parent_ids.clamp(
                    min=0, max=cluster_feats_list[lvl].shape[1] - 1)
                level_ids.append(parent_ids.gather(0, level_ids[-1]))
            composed_ids.append(level_ids)

        scale_msgs = []
        for lvl in range(num_scales):
            cf = cluster_feats_list[lvl]
            msg = torch.zeros(B, N, C, device=point_feats.device, dtype=point_feats.dtype)
            for b in range(B):
                ids_b = composed_ids[b][lvl]
                n_valid = min(ids_b.shape[0], N)
                msg[b, :n_valid] = cf[b, ids_b[:n_valid]]
            scale_msgs.append(msg)

        stack = torch.stack(scale_msgs, dim=-1)
        global_mean = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)
        gate_in = torch.cat([point_feats, global_mean], dim=-1)
        lw = torch.softmax(self.level_gate(gate_in), dim=-1)
        fused = (stack * lw.unsqueeze(-2)).sum(dim=-1)
        fused = self.point_out_proj(self.dropout(fused))
        return fused.masked_fill(point_mask.unsqueeze(-1), 0)


class C2F_ClusterAttn_CTF_HCG_CCL(C2F_ClusterAttn_CTF_HCG):
    """M112 Cluster Token FFN × HCG × Cluster Contrastive Loss.

    在 CTF_HCG 基础上增加 Cluster Contrastive Loss (CCL):
      - 对 FFN 精炼后的多尺度 cluster token 计算 InfoNCE 对比损失
      - finest scale (256) 作为 anchors, middle scale (64) 作为 positives
      - 通过 feature similarity 自动匹配 fine→mid 的 parent 关系
    假设: 对比损失迫使不同尺度的 cluster token 学到一致的结构表征,
    提升 FFN 精炼后 token 的判别力, 突破 CTF_HCG 的性能天花板.
    """

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None,
                 per_layer_topk_list=None, dropout=0.0,
                 ccl_temperature=0.07, ccl_weight=0.1):
        super().__init__(d_model=d_model, nhead=nhead,
                         cluster_layer_nums=cluster_layer_nums,
                         per_layer_topk_list=per_layer_topk_list,
                         dropout=dropout)
        self.ccl_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Linear(d_model, 128)
        )
        self.ccl_temperature = ccl_temperature
        self.ccl_weight = ccl_weight

    def _contrastive_loss(self, cluster_feats_list):
        """InfoNCE between cluster tokens across scales at same spatial location."""
        # Use finest scale (256) as anchors, middle scale (64) as positive pairs
        fine_feats = cluster_feats_list[0]  # [B, 256, C]
        mid_feats = cluster_feats_list[1]   # [B, 64, C]

        # Project to lower dim
        fine_proj = self.ccl_proj(fine_feats)  # [B, 256, 128]
        mid_proj = self.ccl_proj(mid_feats)    # [B, 64, 128]

        # Normalize
        fine_proj = F.normalize(fine_proj, dim=-1)
        mid_proj = F.normalize(mid_proj, dim=-1)

        # logits[b, i, j] = fine_proj[b,i] · mid_proj[b,j] / temperature
        logits = torch.bmm(fine_proj, mid_proj.transpose(1, 2)) / self.ccl_temperature

        # Labels: each fine cluster's positive is its parent mid cluster
        # Use feature similarity for soft assignment (stop gradient)
        with torch.no_grad():
            sim = torch.bmm(fine_feats, mid_feats.transpose(1, 2))  # [B, 256, 64]
            labels = sim.argmax(dim=-1)  # [B, 256]

        # InfoNCE: cross-entropy with soft labels
        loss = F.cross_entropy(logits.view(-1, mid_feats.shape[1]), labels.view(-1))
        return loss

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        # Step 1: CTF FFN refinement of cluster tokens
        refined_cluster_feats = []
        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]
            refined = cf + self.cluster_ffn[lvl](self.cluster_ffn_norm[lvl](cf))
            refined_cluster_feats.append(refined)

        # Step 2: Compute contrastive loss on refined features
        ccl_loss = self.ccl_weight * self._contrastive_loss(refined_cluster_feats)

        # Step 3: HCG readback (composed gather)
        point_message = self._cluster_to_points(
            point_feats, refined_cluster_feats, cluster_ids_list, point_mask)
        point_message = self.message_norm(point_message)
        point_message = point_message.masked_fill(point_mask.unsqueeze(-1), 0)

        return {'point': point_message, 'ccl_loss': ccl_loss}
