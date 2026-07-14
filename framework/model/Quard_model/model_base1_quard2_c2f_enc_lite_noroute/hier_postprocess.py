"""
quard2_c2f_enc_lite_noroute: 纯多尺度 gather，去掉 C2F 路由.

相比 c2f_enc_lite 的改动:
  - 去掉 _scale_attn (query→cluster attention)
  - 去掉 _child_mask (父子级联候选)
  - 去掉 query_linear, k_linear, v_linear (路由相关投影)
  - forward 只做 _cluster_to_points (纯多尺度 gather 融合)

动机:
  nomask (并行多尺度, 无 query 路由) = 0.4997
  lite (C2F 路由 + 多尺度 gather)    = 0.4992
  两者几乎一样，说明 C2F 路由本身没带来多少增益.
  去掉路由可大幅简化代码，减少 ~195K 参数.
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
# PointCloudPartitioner — 同 lite
# ============================================================================
class PointCloudPartitioner(nn.Module):
    """FPS 多层几何划分，记录每层点→簇映射"""

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
        # ★ noroute: 不需要父子映射，但仍保留接口以兼容 SharedClusterBank
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
                    # 保留父子映射构建（兼容接口），但 noroute 不使用
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
# SharedClusterBank — 同 lite
# ============================================================================
class SharedClusterBank(nn.Module):
    """几何划分一次，用当前特征聚合 cluster token"""

    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)

    def get_cluster(self, sp_pos, batch_offsets):
        self.cluster_ids_list, self.child_cluster_maps = self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        """级联聚合：lvl0从原始点聚合成256token/batch，lvl1从256聚合成64/batch，lvl2从64聚合成8/batch"""
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
            total_K = cum
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
# MultiScale_Gather — 纯多尺度 gather，无 query 路由
# ============================================================================
class MultiScale_Gather(nn.Module):
    """
    纯多尺度 Cluster Attention (无 query 路由).

    相比 lite 的改动:
      - 去掉 _scale_attn (query→cluster attention)
      - 去掉 _child_mask (父子级联候选)
      - 去掉 query_linear, k_linear, v_linear
      - forward 只做 _cluster_to_points

    本质: 每个点通过 cluster_ids 直接 gather 所属 cluster token，多尺度融合.
    减少参数: ~195K (query_linear + k_linear + v_linear)
    """

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None,
                 per_layer_topk_list=None, dropout=0.0):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.num_scales = len(cluster_layer_nums)

        self.d_model = d_model

        # ★ 去掉 query_linear, k_linear, v_linear (不再需要路由)

        # ── point message 输出 ──
        self.point_out_proj = nn.Linear(d_model, d_model)

        # ── 多尺度融合 gate (per-point, 基于 [local_feat, global_mean]) ──
        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    # ---------- 多尺度 cluster → point 回读 ----------
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
            query: [B, Q, C]  (不使用，保留接口兼容)
            point_mask: [B, N]  True = padding
            cluster_feats_list: list of [B, K_lvl, C]
            child_cluster_maps: list of list(dict)  (不使用，保留接口兼容)
            cluster_ids_list: list of list([N_b])  每级每个点的 cluster id
        Returns:
            {'point': fm}  仅返回 point message
        """
        # ★ 纯多尺度 gather，不做任何 query routing
        fm = self._cluster_to_points(point_feats, cluster_feats_list,
                                     cluster_ids_list, point_mask)
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)

        return {'point': fm}


Cluster_Attn = MultiScale_Gather
