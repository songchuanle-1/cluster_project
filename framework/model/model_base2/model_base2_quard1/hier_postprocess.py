"""
quard1 点云层级聚类与 Cluster_Attn 工具。

流程概要：
1. PointCloudPartitioner：按几何位置 FPS + 最近邻，得到多尺度「点→簇」划分（每层 batch 内只算一次，由 SharedClusterBank 复用）。
2. SharedClusterBank：缓存划分结果，把当前点特征按簇做 mean 聚合成 cluster token。
3. Cluster_Attn：每个 query 独立选 top-k 簇 → query 读簇 → 点再通过 query 路由读回；同时输出 point/query 残差消息与 cluster-guided matching_masks，
   在 dec.py 里与原始 pred_masks 融合。
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean


def batch2flatten(x, batch_mask):
    # x: [B, N, C]；batch_mask: [B, N]，True 表示 padding
    # 展平并去掉 padding 行，便于按 batch_offsets 做 scatter
    return x.view(-1, x.size(-1))[~batch_mask.view(-1)]


def get_batches(x, batch_offsets):
    # 将扁平点序列 [total_N, C] 按 batch_offsets 还原为 [B, N_max, C]，并生成 padding mask
    B = len(batch_offsets) - 1
    max_len = max(batch_offsets[1:] - batch_offsets[:-1])
    if torch.is_tensor(max_len):
        max_len = max_len.item()
    new_feats = torch.zeros(B, max_len, x.shape[1], device=x.device, dtype=x.dtype)
    mask = torch.ones(B, max_len, dtype=torch.bool, device=x.device)  # True = padding
    for i in range(B):
        start_idx = batch_offsets[i]
        end_idx = batch_offsets[i + 1]
        cur_len = end_idx - start_idx
        new_feats[i, :cur_len] = x[start_idx:end_idx]
        mask[i, :cur_len] = False
    return new_feats, mask


def aggregate_cluster(feats, cluster_ids):
    # feats: [N, C]；cluster_ids: [N]，簇 id 从 0 连续
    # 簇内 mean → 每个簇一个 token
    if cluster_ids.numel() == 0:
        return feats
    num_cluster = int(cluster_ids.max().item()) + 1
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=num_cluster)


class PointCloudPartitioner(nn.Module):
    """按几何坐标做多层 FPS 聚类，记录每层每个场景下「原始点 → 簇 id」。"""

    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        # per_layer_cluster_ids[l][b]：第 l 尺度、第 b 个场景的局部点簇 id
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]

    def partition_points(self, points_pos, fps_pos):
        # 每个点归属最近的 FPS 中心
        dist_matrix = torch.cdist(points_pos, fps_pos) ## 计算点和中心点的距离
        partition_labels = torch.min(dist_matrix, dim=-1)[1] ## 每个点分给最近的中心
        counts = torch.bincount(partition_labels, minlength=fps_pos.shape[0]) ## 统计每个簇里有多少点
        arange_idx = torch.arange(points_pos.shape[0], device=partition_labels.device)
        _, perm = torch.sort(partition_labels) ## 按簇编号排序，便于后面 split 成不同簇的点索引
        idx_sorted = arange_idx[perm]
        subset_idxs = list(torch.split(idx_sorted, counts.tolist())) ## 按簇编号排序，便于后面 split 成不同簇的点索引
        return subset_idxs ## 返回每个簇的点索引 list格式

    def cluster_layer(self, pos, fps_num, device):
        # 一层：FPS 采样中心 → 点划簇 → 簇中心为 pos 的 mean，供下一层更粗尺度使用
        fps_num = min(fps_num, pos.size(0)) ## 簇数不能超过当前层点数
        fps_seed_sp = FurthestPointSampling.apply(pos.unsqueeze(0), fps_num) ## 用 FPS 采样出这一层的簇中心候选
        fps_pos = pos.gather( ## 把所有点划分到最近的中心
            dim=0,
            index=fps_seed_sp.long().squeeze(0).unsqueeze(-1).repeat(1, pos.size(-1)),
        )
        subset_idxs = self.partition_points(pos, fps_pos)
        cluster_ids_scene = torch.full((pos.size(0),), -1, dtype=torch.long, device=device) ## 为len(center)个点分配id 属于哪一个簇
        for cid, idx_local in enumerate(subset_idxs):
            cluster_ids_scene[idx_local.long()] = cid ## 为len(center)个点分配id 属于哪一个簇
        center = aggregate_cluster(pos, cluster_ids_scene) ## 再对每个簇做均值，得到下一层更粗的中心
        return center, cluster_ids_scene

    def forward(self, sp_coords_float, batch_offsets):
        # 每个 forward 清空并重建当前 batch 的层级划分
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]
        device = sp_coords_float.device
        scene_lengths = [] ### 获取每个场景的点数
        for b in range(len(batch_offsets) - 1):
            scene_lengths.append((batch_offsets[b + 1] - batch_offsets[b]).item())
        layer_nums = list(self.cluster_layer_nums)
        # 第一层簇数不能超过最短场景点数
        layer_nums[0] = min(layer_nums[0], min(scene_lengths))

        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            coords_b = sp_coords_float[s:e]
            for l in range(len(layer_nums)):
                # 逐层在「上一层中心」上继续分簇
                coords_b, idx_to_cluster = self.cluster_layer(coords_b, layer_nums[l], device)
                self.per_layer_cluster_ids[l].append(idx_to_cluster)


class SharedClusterBank(nn.Module):
    """
    与 DEC 配合：get_cluster 只做几何划分一次；
    build_cluster_feats 用当前点特征 + 固定划分做各尺度 cluster token。
    """

    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)

    def get_cluster(self, sp_pos, batch_offsets):
        self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        # 返回 list，每项为 [B, M_l, C]，M_l 为该尺度簇数
        per_layer_feats = [[] for _ in range(len(self.cluster_layer_nums))]
        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            feats_b = sp_feats[s:e]
            for l in range(len(self.cluster_layer_nums)):
                feats_b = aggregate_cluster(feats_b, self.partitioner.per_layer_cluster_ids[l][b])
                per_layer_feats[l].append(feats_b)
        return [torch.stack(feats_l) for feats_l in per_layer_feats]


class Cluster_Attn(nn.Module):
    """
    多尺度 cluster 上的 query 路由 + 点侧消息 + 与 mask 对齐的 matching_masks。

    返回 dict：
    - point / query：供 dec 残差写回 inst_feats、query
    - matching_masks：[B, Q, N]，与 Decoder_layer.prediction_head 的 bnm 同形，用于与 pred_masks 融合
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
        self.per_layer_topk_list = list(per_layer_topk_list[: len(self.cluster_layer_nums)])
        if len(self.per_layer_topk_list) < len(self.cluster_layer_nums):
            self.per_layer_topk_list.extend(
                [self.per_layer_topk_list[-1]] * (len(self.cluster_layer_nums) - len(self.per_layer_topk_list))
            )

        # 点侧、簇侧、query 侧注意力投影
        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.query_linear = nn.Linear(d_model, d_model)
        self.query_k_linear = nn.Linear(d_model, d_model)
        self.query_v_linear = nn.Linear(d_model, d_model)
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.query_out_proj = nn.Linear(d_model, d_model)
        # 单独匹配头：生成 cluster-guided mask logits（非归一化 cosine 小偏置）
        self.match_point_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model),
        )
        self.match_query_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Linear(d_model, d_model),
        )
        self.match_query_norm = nn.LayerNorm(d_model)
        self.match_point_norm = nn.LayerNorm(d_model)
        self.match_scale = nn.Parameter(torch.tensor(1.0))
        # 多尺度融合：点分支看 [point, query_mean]；query 分支只看 query
        self.level_gate = nn.Linear(d_model * 2, len(self.cluster_layer_nums))
        self.query_level_gate = nn.Linear(d_model, len(self.cluster_layer_nums))
        self.message_norm = nn.LayerNorm(d_model)
        self.query_message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def select_query_conditioned_clusters(self, query_feats, cluster_feats, topk):
        # query_feats: [B,Q,C]；cluster_feats: [B,M,C]
        # 每个 query 独立 top-k 簇；不足 M 时退化为全簇 + 全局 token
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]
        if topk >= M:
            global_token = cluster_feats.mean(dim=1, keepdim=True).unsqueeze(1).expand(-1, Q, -1, -1)
            return torch.cat([cluster_feats.unsqueeze(1).expand(-1, Q, -1, -1), global_token], dim=2)

        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        scores = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.scale
        topk = min(topk, M)
        mean_scores = scores.mean(dim=1)  # 多头平均，稳定路由
        topk_idx = mean_scores.topk(topk, dim=-1).indices
        expanded_clusters = cluster_feats.unsqueeze(1).expand(-1, Q, -1, -1)
        selected = expanded_clusters.gather(
            2, topk_idx.unsqueeze(-1).expand(-1, -1, -1, cluster_feats.size(-1))
        )
        selected_weight = mean_scores.gather(-1, topk_idx).unsqueeze(-1)
        selected = selected * (1.0 + selected_weight)
        global_token = cluster_feats.mean(dim=1, keepdim=True).unsqueeze(1).expand(-1, Q, -1, -1)
        return torch.cat([selected, global_token], dim=2)

    def attend_query_to_clusters(self, query_feats, selected_cluster_feats):
        # selected: [B,Q,K,C]；query 在 K 个候选簇 token 上做注意力
        B, Q, K, _ = selected_cluster_feats.shape
        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(selected_cluster_feats).view(B, Q, K, self.nhead, self.head_dim).permute(0, 3, 1, 2, 4)
        v = self.v_linear(selected_cluster_feats).view(B, Q, K, self.nhead, self.head_dim).permute(0, 3, 1, 2, 4)

        scores = torch.einsum("bhqd,bhqkd->bhqk", q, k) * self.scale
        attn = torch.softmax(scores, dim=-1)
        context = torch.einsum("bhqk,bhqkd->bhqd", attn, v)
        context = context.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)
        context = self.query_out_proj(self.dropout(context))
        return context

    def route_query_context_to_points(self, point_feats, query_feats, query_context, point_mask):
        # 点不直接 attend 簇，而是 attend query，value 为 query 经簇更新后的 context
        B, N, _ = point_feats.shape
        q = self.q_linear(point_feats).view(B, N, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.query_k_linear(query_feats).view(B, query_feats.size(1), self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.query_v_linear(query_context).view(B, query_context.size(1), self.nhead, self.head_dim).permute(
            0, 2, 1, 3
        )

        scores = torch.einsum("bhnd,bhqd->bhnq", q, k) * self.scale
        attn = torch.softmax(scores, dim=-1)
        context = torch.einsum("bhnq,bhqd->bhnd", attn, v)
        context = context.permute(0, 2, 1, 3).contiguous().view(B, N, self.d_model)
        context = self.point_out_proj(self.dropout(context))
        context = context.masked_fill(point_mask.unsqueeze(-1), 0)
        return context

    def forward(self, point_feats, query, point_mask, cluster_feats_list):
        # point_feats/query: [B,N,C] / [B,Q,C]；cluster_feats_list 与 per_layer_topk_list 对齐
        query_summary = query.mean(dim=1, keepdim=True).expand(-1, point_feats.shape[1], -1)
        gate_input = torch.cat([point_feats, query_summary], dim=-1)

        multi_scale_messages = []
        multi_scale_query_messages = []
        for cluster_feats, topk in zip(cluster_feats_list, self.per_layer_topk_list):
            selected_cluster_feats = self.select_query_conditioned_clusters(query, cluster_feats, topk)
            query_context = self.attend_query_to_clusters(query, selected_cluster_feats)
            point_context = self.route_query_context_to_points(point_feats, query, query_context, point_mask)
            multi_scale_messages.append(point_context)
            multi_scale_query_messages.append(query_context)

        level_weight = torch.softmax(self.level_gate(gate_input), dim=-1)
        query_level_weight = torch.softmax(self.query_level_gate(query), dim=-1)
        final_message = torch.zeros_like(point_feats)
        final_query_message = torch.zeros_like(query)
        for idx, message in enumerate(multi_scale_messages):
            final_message = final_message + message * level_weight[..., idx:idx + 1]
            final_query_message = final_query_message + multi_scale_query_messages[idx] * query_level_weight[..., idx:idx + 1]

        final_message = self.message_norm(final_message)
        final_query_message = self.query_message_norm(final_query_message)
        final_message = final_message.masked_fill(point_mask.unsqueeze(-1), 0)

        # cluster-guided mask 分支：与 decoder 中 einsum('bnd,bmd->bnm') 的 bqn 维一致（此处 d 与 m 同为 N）
        match_query = self.match_query_norm(self.match_query_proj(query + final_query_message))
        match_point = self.match_point_norm(self.match_point_proj(point_feats + final_message))
        matching_masks = self.match_scale * torch.einsum('bqd,bnd->bqn', match_query, match_point)
        matching_masks = matching_masks.masked_fill(point_mask.unsqueeze(1), 0)

        return {'point': final_message, 'query': final_query_message, 'matching_masks': matching_masks}
