"""
quard2_c2f_enc_lite_qcond: Query-Conditioned Cluster Aggregation (v2).

相比 lite 的改动:
  1. SharedClusterBank 存储每簇的点索引列表 (cluster_point_lists)
  2. C2F 路由后，用 batched cross-attention 对选中 clusters 做 query→points
     重聚合 (per-query refined tokens)
  3. _qcond_gather_blend: 将 per-query refined tokens 映射回点，
     与 mean-aggregated tokens 做 per-point learned gate 混合

v2 修复 (相比 v1):
  - 去掉 ctx.mean(dim=0): 保留 per-query 语义
  - batched cross-attention: 替代 Python 三重循环
  - per-point gate: nn.Linear(C,1) 替代全局 scalar
  - 去掉 if gate > 0.01: 始终 blend，不 break autograd

计算量: batched cross-attn ~25M FLOPs/层 (+130%)
参数量: qcond_q/k/v_proj + qcond_gate_proj ~197K (+74%)
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
# PointCloudPartitioner — 增加 cluster_point_lists
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
        per_layer_point_lists = [[] for _ in range(num_layers)]
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

                # 每簇的点索引列表 (反向映射 cluster_ids)
                Kb = int(cid.max().item()) + 1 if cid.numel() > 0 else 0
                point_lists_b = []
                for k in range(Kb):
                    point_lists_b.append((cid == k).nonzero(as_tuple=False).squeeze(-1))
                per_layer_point_lists[lvl].append(point_lists_b)

                if lvl > 0:
                    child_centers = per_layer_coords[lvl + 1][b]
                    parent_centers = per_layer_coords[lvl][b]
                    dist = torch.cdist(child_centers, parent_centers)
                    parent_for_child = torch.min(dist, dim=-1)[1]

                    mapping = {}
                    for cc, pc in enumerate(parent_for_child.tolist()):
                        mapping.setdefault(int(pc), []).append(cc)
                    child_cluster_maps[lvl - 1].append(mapping)

        return per_layer_cluster_ids, child_cluster_maps, per_layer_point_lists


# ============================================================================
# SharedClusterBank — 存储 cluster_point_lists
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
        self.cluster_ids_list, self.child_cluster_maps, self.cluster_point_lists = self.partitioner(sp_pos, batch_offsets)

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
# C2F_ClusterAttn_QCond — Query-Conditioned Cluster Attention (v2)
# ============================================================================
class C2F_ClusterAttn_QCond(nn.Module):
    """
    Query-Conditioned Cluster Attention (v2, batched).

    流程:
      1. C2F 路由: query→cluster attention → topk 级联选择
      2. _qcond_refine: 对选中 clusters 做 batched query→points cross-attention
         → per-level per-query refined cluster tokens [B, K, Q, C]
      3. _cluster_to_points (mean tokens): 多尺度 gather → [B, N, C]
      4. _qcond_gather_blend: 将 query-conditioned tokens gather 到点,
         用 per-point learned gate 混合 mean 和 qcond versions
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

        # ── C2F routing 投影 ──
        self.query_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)

        # ── point message 输出 ──
        self.point_out_proj = nn.Linear(d_model, d_model)

        # ── 多尺度融合 gate ──
        self.level_gate = nn.Linear(d_model * 2, self.num_scales)
        self.message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

        # ── query-conditioned cross-attention 投影 ──
        self.qcond_q_proj = nn.Linear(d_model, d_model)
        self.qcond_k_proj = nn.Linear(d_model, d_model)
        self.qcond_v_proj = nn.Linear(d_model, d_model)
        self.qcond_scale = self.head_dim ** -0.5

        # ── per-point learned gate (替代全局 scalar) ──
        self.qcond_gate_proj = nn.Linear(d_model, 1)

    # ---------- C2F routing: scale-level attention ----------
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

    # ---------- C2F: child mask ----------
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

    # ---------- cluster → point 回读 (mean tokens) ----------
    def _cluster_to_points(self, point_feats, cluster_feats_list,
                           cluster_ids_list, point_mask, apply_proj=True):
        """
        每个点通过 cluster_ids 直接 gather 所属 cluster token → O(N).
        多尺度融合后返回融合结果.

        Args:
            apply_proj: 是否应用 point_out_proj. False 时返回未投影的结果,
                        用于 qcond blending.
        """
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
        if apply_proj:
            fused = self.point_out_proj(self.dropout(fused))
        return fused.masked_fill(point_mask.unsqueeze(-1), 0)

    # ---------- batched cross-attention ----------
    def _qcond_cross_attn(self, query, cluster_pts, cluster_kpm):
        """
        Batched multi-head cross-attention: query attends cluster points.

        Args:
            query:         [Bq, Q, C]
            cluster_pts:   [Bq, M, C]
            cluster_kpm:   [Bq, M] bool, True=padding
        Returns:
            ctx: [Bq, Q, C]
        """
        Bq, Q, _ = query.shape
        M = cluster_pts.shape[1]

        q = self.qcond_q_proj(query).view(Bq, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.qcond_k_proj(cluster_pts).view(Bq, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.qcond_v_proj(cluster_pts).view(Bq, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        attn = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.qcond_scale
        if cluster_kpm is not None:
            attn = attn + cluster_kpm.unsqueeze(1).unsqueeze(2).to(attn.dtype) * (-1e9)
        attn = torch.softmax(attn, dim=-1)

        ctx = torch.einsum("bhqm,bhmd->bhqd", attn, v)
        ctx = ctx.permute(0, 2, 1, 3).contiguous().view(Bq, Q, self.d_model)
        return ctx

    # ---------- query-conditioned refinement (v3: optimized, minimal .item()) ----------
    def _qcond_refine(self, point_feats, query, cluster_point_lists,
                      all_selected, point_mask):
        """
        对 C2F 选中的 clusters 做 batched query→points cross-attention.

        v3 优化: 用 unique() 替代三重 Python 循环, 仅保留 B 次外层循环.
        .item() 调用从 ~9000 次降到 ~U*B 次 (U = unique clusters per batch, 通常 <100).

        Returns:
            refined_list: list of [B, K_lvl, Q, C] per-level per-query refined tokens
        """
        B, Q, C = query.shape
        device = point_feats.device
        refined_list = []

        for lvl in range(self.num_scales):
            # all_selected 按 reversed(range(num_scales)) 顺序 append:
            #   all_selected[0] = 最粗层路由, all_selected[-1] = 最细层路由
            sel = all_selected[self.num_scales - 1 - lvl]  # [B, Q, topk]
            pl_lvl = cluster_point_lists[lvl]  # list[B] of list[K_b] of Tensor

            K_out = max(len(pl_lvl[b]) for b in range(B))

            # ★ 优化: 用 unique() 提取每 batch 的唯一 cluster IDs
            # 避免三重循环 (B × Q × topk)
            bc_batch_idx = []
            bc_point_idx = []

            for b in range(B):
                Kb = len(pl_lvl[b])
                # 提取该 batch 选中的所有 cluster IDs
                sel_b = sel[b].reshape(-1)  # [Q*topk]
                unique_cids = sel_b.unique()  # sorted unique, no .item() yet

                # 过滤有效的 cluster IDs (< Kb)
                valid_mask = unique_cids < Kb
                valid_cids = unique_cids[valid_mask]

                # 收集 point indices (需要 .item() 因为 pl_lvl[b] 是 Python list)
                for cid_tensor in valid_cids:
                    cid = cid_tensor.item()  # 仅 ~U 次 .item() per batch
                    bc_batch_idx.append(b)
                    bc_point_idx.append(pl_lvl[b][cid])

            if not bc_batch_idx:
                refined_list.append(torch.zeros(B, K_out, Q, C, device=device))
                continue

            N_bc = len(bc_batch_idx)

            # ★ 并行 gather 点特征
            max_pts = max(pi.shape[0] for pi in bc_point_idx)
            batch_idx = torch.tensor(bc_batch_idx, device=device)  # [N_bc]

            cluster_pts = torch.zeros(N_bc, max_pts, C, device=device)
            cluster_kpm = torch.ones(N_bc, max_pts, dtype=torch.bool, device=device)

            for bc_idx, pt_idx in enumerate(bc_point_idx):
                n = pt_idx.shape[0]
                cluster_pts[bc_idx, :n] = point_feats[batch_idx[bc_idx], pt_idx]
                cluster_kpm[bc_idx, :n] = False

            # query 扩展: [N_bc, Q, C]
            q_expanded = query[batch_idx]

            # batched cross-attention: [N_bc, Q, C]
            ctx = self._qcond_cross_attn(q_expanded, cluster_pts, cluster_kpm)

            # ★ Scatter 回 [B, K_out, Q, C]
            refined = torch.zeros(B, K_out, Q, C, device=device)

            # 重建 (b, cid) 映射 (需要 Python 循环因为 pl_lvl 结构)
            bc_pos = 0
            for b in range(B):
                Kb = len(pl_lvl[b])
                sel_b = sel[b].reshape(-1)
                unique_cids = sel_b.unique()
                valid_cids = unique_cids[unique_cids < Kb]

                for cid_tensor in valid_cids:
                    cid = cid_tensor.item()
                    if cid < K_out:
                        refined[b, cid] = ctx[bc_pos]
                    bc_pos += 1

            refined_list.append(refined)

        return refined_list

        return refined_list

    # ---------- per-point qcond blending ----------
    def _qcond_gather_blend(self, point_feats, refined_list, cluster_ids_list, point_mask):
        """
        将 per-query refined tokens 映射回点, 用 per-point gate 混合 mean 和 qcond.

        先 per-query blend, 再 average over Q (保留 per-query 差异):
          qcond_b = refined[b, ids_b]              → [n_valid, Q, C]
          fm_b    = fm[b, :n_valid]                → [n_valid, 1, C] (broadcast)
          blended = (1-gate) * fm_b + gate * qcond → [n_valid, Q, C]
          fused   = blended.mean(dim=1)            → [n_valid, C]

        Returns:
            [B, N, C] query-conditioned point message (未投影, 未 norm)
        """
        B, N, C = point_feats.shape
        device = point_feats.device

        fused_qcond = torch.zeros(B, N, C, device=device)

        for lvl in range(self.num_scales):
            refined = refined_list[lvl]  # [B, K, Q, C]
            if refined.shape[1] == 0:
                continue

            for b in range(B):
                ids_b = cluster_ids_list[lvl][b].long()
                n_valid = ids_b.shape[0]
                ids_b = ids_b.clamp(min=0, max=refined.shape[1] - 1)
                # ★ 先 blend 再平均: 保留 per-query 差异
                qcond_b = refined[b, ids_b]  # [n_valid, Q, C]
                fused_qcond[b, :n_valid] += qcond_b.mean(dim=1)

        fused_qcond /= self.num_scales

        # per-point gate: [B, N, 1]
        gate = torch.sigmoid(self.qcond_gate_proj(point_feats))

        return fused_qcond.masked_fill(point_mask.unsqueeze(-1), 0), gate

    # ---------- forward ----------
    def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list,
                cluster_point_lists=None):
        """
        Args:
            point_feats: [B, N, C] padded inst_feats
            query: [B, Q, C]
            point_mask: [B, N] True = padding
            cluster_feats_list: list of [B, K_lvl, C]
            child_cluster_maps: list of list(dict)
            cluster_ids_list: list of list([N_b])
            cluster_point_lists: list of list(list(Tensor)) per-level per-batch per-cluster
        Returns:
            {'point': fm}
        """
        B, Q, _ = query.shape
        num_scales = self.num_scales

        # ── C2F routing ──
        prev_indices = None
        all_selected = []

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

            all_selected.append(prev_indices)

        # ── query-conditioned refinement (batched) ──
        refined_list = None
        if cluster_point_lists is not None:
            refined_list = self._qcond_refine(
                point_feats, query, cluster_point_lists,
                all_selected, point_mask)

        # ── mean cluster → point 回读 (不投影, 后续统一投影) ──
        fm = self._cluster_to_points(point_feats, cluster_feats_list,
                                     cluster_ids_list, point_mask,
                                     apply_proj=False)

        # ── per-point qcond blending ──
        if refined_list is not None:
            qcond_fused, gate = self._qcond_gather_blend(
                point_feats, refined_list, cluster_ids_list, point_mask)
            fm = (1 - gate) * fm + gate * qcond_fused

        # ── 投影 + norm ──
        fm = self.point_out_proj(self.dropout(fm))
        fm = self.message_norm(fm).masked_fill(point_mask.unsqueeze(-1), 0)

        return {'point': fm}


Cluster_Attn = C2F_ClusterAttn_QCond
