"""
quard2_c2f_enc_lite_attnpool: Attention Pooling 替代 scatter_mean.

在 lite 基础上，将 SharedClusterBank 中的 scatter_mean 聚合替换为
可学习 attention pooling，让每个 cluster token 关注簇内最重要的点。

改动:
  1. PointCloudPartitioner 存储每簇的点索引列表 (同 qcond)
  2. SharedClusterBank 新增 attn_pool_q (可学习 cluster query) + attn_pool_proj
  3. build_cluster_feats 中用 cross-attention 替代 scatter_mean

动机:
  scatter_mean 对所有点一视同仁，丢失了簇内结构。
  attention pooling 让 cluster token 自适应关注重要子区域。

计算量: 每簇 ~16 个点做 attention → ~40M FLOPs/层 (+210%)
参数量: +262K (+99%)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean, scatter_max, scatter_sum


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
# PointCloudPartitioner — 存储 cluster_point_lists
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
# SharedClusterBank — Attention Pooling 替代 scatter_mean
# ============================================================================
class SharedClusterBank(nn.Module):
    """几何划分一次，用 attention pooling 聚合 cluster token"""

    def __init__(self, cluster_layer_nums=None, d_model=256):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.d_model = d_model
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)

        # ★ Attention pooling 模块 (content-adaptive: query 从 cluster mean feat 生成)
        # 替代 per-index ParameterList, 现在用 Linear 投影 cluster 均值 → query
        self.attn_pool_query_gen = nn.ModuleList([
            nn.Linear(d_model, d_model) for _ in cluster_layer_nums
        ])
        self.attn_pool_proj = nn.ModuleList([
            nn.Linear(d_model, d_model) for _ in cluster_layer_nums
        ])
        self.attn_pool_out = nn.ModuleList([
            nn.Linear(d_model, d_model) for _ in cluster_layer_nums
        ])

    def get_cluster(self, sp_pos, batch_offsets):
        self.cluster_ids_list, self.child_cluster_maps = self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        """
        Attention pooling (仅 lvl=0, 级联时沿用 scatter_mean).
        Content-adaptive: query 从 cluster mean feat 生成 (替代 per-index 参数).
        """
        device = sp_feats.device
        B = len(batch_offsets) - 1
        cluster_feats_list = []
        current_feats = sp_feats

        for lvl in range(len(self.cluster_layer_nums)):
            ids_list = self.cluster_ids_list[lvl]
            remapped_ids = []
            cum = 0; per_batch_K = []
            for b in range(B):
                ids_b = ids_list[b]
                remapped_ids.append(ids_b + cum)
                Kb = int(ids_b.max().item()) + 1 if ids_b.numel() > 0 else 0
                cum += Kb; per_batch_K.append(Kb)
            flat_ids = torch.cat(remapped_ids, dim=0)
            total_K = cum

            if lvl == 0:
                # ★ lvl=0: attention pooling (content-adaptive query from cluster mean)
                padded_batches = []
                for b in range(B):
                    Kb = per_batch_K[b]; s_b = batch_offsets[b].item(); e_b = batch_offsets[b + 1].item()
                    batch_feats = current_feats[s_b:e_b]; batch_ids = ids_list[b]
                    valid = batch_ids >= 0; batch_ids_c = batch_ids.clamp(min=0)

                    # Content-adaptive: 从 cluster mean feat 生成 per-cluster query
                    cluster_mean = aggregate_cluster(batch_feats, batch_ids_c)  # [Kb, C]
                    q_per_cluster = self.attn_pool_query_gen[lvl](cluster_mean)  # [Kb, C]
                    q_per = q_per_cluster[batch_ids_c]  # [N, C] per-point query

                    k = self.attn_pool_proj[lvl](batch_feats)
                    scores = (q_per * k).sum(-1) / (self.d_model ** 0.5)
                    scores = scores.masked_fill(~valid, -1e9)
                    attn = scatter_softmax_raw(scores, batch_ids_c)
                    agg_b = scatter_sum(batch_feats * attn.unsqueeze(-1), batch_ids_c, dim=0, dim_size=Kb)
                    padded_batches.append(self.attn_pool_out[lvl](agg_b))
            else:
                # lvl>0: scatter_mean (级联)
                agg_feats = aggregate_cluster(current_feats, flat_ids)
                padded_batches = [agg_feats[off:off+Kb] for off, Kb in zip(
                    torch.cumsum(torch.tensor([0]+per_batch_K[:-1], device=device), dim=0), per_batch_K)]

            max_K = max(cf.shape[0] for cf in padded_batches)
            cf_list = [F.pad(cf, (0,0,0,max_K-cf.shape[0])) if cf.shape[0]<max_K else cf for cf in padded_batches]
            cluster_feats_list.append(torch.stack(cf_list, dim=0))
            current_feats = torch.cat(padded_batches, dim=0)

        return cluster_feats_list


# ============================================================================
# scatter_softmax_raw: per-segment softmax (无 dimension 参数)
# ============================================================================
def scatter_softmax_raw(src, index):
    """对每个 segment 做 softmax. src: [N], index: [N]"""
    src_max = scatter_max(src, index)[0]         # [K]
    src_max_pt = src_max[index]                   # [N]
    out = torch.exp(src - src_max_pt)
    out_sum = scatter_sum(out, index)             # [K]
    out_sum_pt = out_sum[index]                   # [N]
    return out / (out_sum_pt + 1e-8)


# ============================================================================
# C2F_ClusterAttn_Lite — 同 lite，不变
# ============================================================================
class C2F_ClusterAttn_Lite(nn.Module):
    """
    轻量版 Coarse-to-Fine Cluster Attention.
    与 lite 完全相同，区别在 SharedClusterBank 的聚合方式。
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

        self.query_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

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

    def _child_mask(self, parent_indices, child_mapping, num_children, B, Q, device):
        mask = torch.zeros(B, Q, num_children, dtype=torch.bool, device=device)
        for bb in range(B):
            mapping = child_mapping[bb]
            for qq in range(Q):
                for pid in parent_indices[bb, qq].tolist():
                    for cc in mapping.get(int(pid), []):
                        if cc < num_children:
                            mask[bb, qq, int(cc)] = True
        return mask

    def _cluster_to_points(self, point_feats, cluster_feats_list,
                           cluster_ids_list, point_mask):
        B, N, C = point_feats.shape
        scale_msgs = []

        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]
            msg = torch.zeros(B, N, C, device=point_feats.device, dtype=point_feats.dtype)
            for b in range(B):
                ids_b = cluster_ids_list[lvl][b].long()
                n_valid = ids_b.shape[0]
                ids_b = ids_b.clamp(min=0, max=cf.shape[1] - 1)
                msg[b, :n_valid] = cf[b, ids_b]
            scale_msgs.append(msg)

        stack = torch.stack(scale_msgs, dim=-1)
        global_mean = point_feats.mean(dim=1, keepdim=True).expand_as(point_feats)
        gate_in = torch.cat([point_feats, global_mean], dim=-1)
        lw = torch.softmax(self.level_gate(gate_in), dim=-1)

        fused = (stack * lw.unsqueeze(-2)).sum(dim=-1)
        fused = self.point_out_proj(self.dropout(fused))
        return fused.masked_fill(point_mask.unsqueeze(-1), 0)

    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        B, Q, _ = query.shape
        num_scales = self.num_scales

        prev_indices = None

        for lvl in reversed(range(num_scales)):
            cf = cluster_feats_list[lvl]
            topk = min(self.per_layer_topk_list[lvl], cf.shape[1])

            if lvl == num_scales - 1:
                _qctx, scores = self._scale_attn(query, cf)
                prev_indices = scores.topk(topk, dim=-1).indices
            else:
                cmask = self._child_mask(prev_indices, child_cluster_maps[lvl],
                                         cf.shape[1], B, Q, cf.device)
                if cmask.any():
                    _qctx, scores = self._scale_attn(query, cf, candidate_mask=cmask)
                    ms = scores.masked_fill(~cmask, -1e9)
                else:
                    _qctx, scores = self._scale_attn(query, cf)
                    ms = scores
                prev_indices = ms.topk(topk, dim=-1).indices

        fm = self._cluster_to_points(point_feats, cluster_feats_list,
                                     cluster_ids_list, point_mask)
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)

        return {'point': fm}


Cluster_Attn = C2F_ClusterAttn_Lite
