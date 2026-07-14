import torch
import torch.nn as nn
from pointnet2.pointnet2_utils import FurthestPointSampling
from torch_scatter import scatter_mean


def batch2flatten(x, batch_mask):
    # x: [B, N, C]
    # batch_mask: [B, N]，True 表示 padding 位置
    # 这里把 batch 形式压平，并去掉 padding 点
    return x.view(-1, x.size(-1))[~batch_mask.view(-1)]


def get_batches(x, batch_offsets):
    # 根据 batch_offsets 把扁平点特征重新还原成 [B, N_max, C]
    B = len(batch_offsets) - 1
    # 取当前 batch 内最长场景的点数，作为 padding 后的统一长度
    max_len = max(batch_offsets[1:] - batch_offsets[:-1])
    if torch.is_tensor(max_len):
        max_len = max_len.item()
    # new_feats 存放 padding 后的特征
    new_feats = torch.zeros(B, max_len, x.shape[1], device=x.device, dtype=x.dtype)
    # mask=True 表示该位置是 padding
    mask = torch.ones(B, max_len, dtype=torch.bool, device=x.device)
    for i in range(B):
        start_idx = batch_offsets[i]
        end_idx = batch_offsets[i + 1]
        cur_len = end_idx - start_idx
        # 把当前场景真实点特征写回去
        new_feats[i, :cur_len] = x[start_idx:end_idx]
        # 真实点位置标成 False
        mask[i, :cur_len] = False
    return new_feats, mask


def aggregate_cluster(feats, cluster_ids):
    # feats: [N, C]
    # cluster_ids: [N]，每个点属于哪个簇
    if cluster_ids.numel() == 0:
        return feats
    # 簇编号默认从 0 开始连续编号
    num_cluster = int(cluster_ids.max().item()) + 1
    # 用均值把簇内点聚合成一个 cluster token
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=num_cluster)


class PointCloudPartitioner(nn.Module):
    def __init__(self, cluster_layer_nums=None):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        # 每一层目标簇数，例如 [256, 64, 8]
        self.cluster_layer_nums = list(cluster_layer_nums)
        # 保存每一层、每个场景里的点到簇映射
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]

    def partition_points(self, points_pos, fps_pos):
        # 计算每个点到每个 FPS 中心的距离
        dist_matrix = torch.cdist(points_pos, fps_pos)
        # 每个点分给最近的中心
        partition_labels = torch.min(dist_matrix, dim=-1)[1]
        # 统计每个簇里有多少点
        counts = torch.bincount(partition_labels, minlength=fps_pos.shape[0])
        arange_idx = torch.arange(points_pos.shape[0], device=partition_labels.device)
        # 按簇编号排序，便于后面 split 成不同簇的点索引
        _, perm = torch.sort(partition_labels)
        idx_sorted = arange_idx[perm]
        subset_idxs = list(torch.split(idx_sorted, counts.tolist()))
        return subset_idxs

    def cluster_layer(self, pos, fps_num, device):
        # 簇数不能超过当前层点数
        fps_num = min(fps_num, pos.size(0))
        # 用 FPS 采样出这一层的簇中心候选
        fps_seed_sp = FurthestPointSampling.apply(pos.unsqueeze(0), fps_num)
        fps_pos = pos.gather(
            dim=0,
            index=fps_seed_sp.long().squeeze(0).unsqueeze(-1).repeat(1, pos.size(-1)),
        )
        # 把所有点划分到最近的中心
        subset_idxs = self.partition_points(pos, fps_pos)
        cluster_ids_scene = torch.full((pos.size(0),), -1, dtype=torch.long, device=device)
        for cid, idx_local in enumerate(subset_idxs):
            cluster_ids_scene[idx_local.long()] = cid
        # 再对每个簇做均值，得到下一层更粗的中心
        center = aggregate_cluster(pos, cluster_ids_scene)
        return center, cluster_ids_scene

    def forward(self, sp_coords_float, batch_offsets):
        # 每次 forward 都重新记录当前 batch 的层级簇划分
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]
        device = sp_coords_float.device
        scene_lengths = []
        for b in range(len(batch_offsets) - 1):
            scene_lengths.append((batch_offsets[b + 1] - batch_offsets[b]).item())
        layer_nums = list(self.cluster_layer_nums)
        # 第一层簇数不能大于当前 batch 中最短场景的点数
        layer_nums[0] = min(layer_nums[0], min(scene_lengths))

        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            coords_b = sp_coords_float[s:e]
            for l in range(len(layer_nums)):
                # 分层构簇：
                # 上一层输出的粗中心，继续作为下一层的输入
                coords_b, idx_to_cluster = self.cluster_layer(coords_b, layer_nums[l], device)
                self.per_layer_cluster_ids[l].append(idx_to_cluster)


class Cluster_Attn(nn.Module):
    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=None, per_layer_topk_list=None, dropout=0.0):
        super().__init__()
        if cluster_layer_nums is None:
            cluster_layer_nums = [256, 64, 8]
        if per_layer_topk_list is None:
            per_layer_topk_list = [32, 16, 8]
        # 多头维度必须能整除
        assert d_model % nhead == 0
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        # 标准 attention 缩放因子
        self.scale = self.head_dim ** -0.5
        self.cluster_layer_nums = list(cluster_layer_nums)
        # 每个尺度保留多少个 query 相关簇
        self.per_layer_topk_list = list(per_layer_topk_list[: len(self.cluster_layer_nums)])
        if len(self.per_layer_topk_list) < len(self.cluster_layer_nums):
            self.per_layer_topk_list.extend(
                [self.per_layer_topk_list[-1]] * (len(self.cluster_layer_nums) - len(self.per_layer_topk_list))
            )
        # 负责几何层面的层级构簇
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=self.cluster_layer_nums)

        # 点到 query / cluster 的投影
        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.query_linear = nn.Linear(d_model, d_model)
        self.query_k_linear = nn.Linear(d_model, d_model)
        self.query_v_linear = nn.Linear(d_model, d_model)
        # 点分支和 query 分支各自的输出投影
        self.point_out_proj = nn.Linear(d_model, d_model)
        self.query_out_proj = nn.Linear(d_model, d_model)
        # 多尺度融合权重
        self.level_gate = nn.Linear(d_model * 2, len(self.cluster_layer_nums))
        self.query_level_gate = nn.Linear(d_model, len(self.cluster_layer_nums))
        # 融合后做一次归一化，避免分支幅值过大
        self.message_norm = nn.LayerNorm(d_model)
        self.query_message_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def get_cluster(self, sp_pos, batch_offsets):
        # 仅根据空间位置做一次层级划分，供后续所有层复用
        self.partitioner(sp_pos, batch_offsets)

    def build_cluster_feats(self, sp_feats, batch_offsets):
        # 构造每个尺度的 cluster token
        per_layer_feats = [[] for _ in range(len(self.cluster_layer_nums))]
        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            feats_b = sp_feats[s:e]
            for l in range(len(self.cluster_layer_nums)):
                # 复用预先算好的层级划分，把点 token 聚合成 cluster token
                feats_b = aggregate_cluster(feats_b, self.partitioner.per_layer_cluster_ids[l][b])
                per_layer_feats[l].append(feats_b)
        return [torch.stack(feats_l) for feats_l in per_layer_feats]

    def select_query_conditioned_clusters(self, query_feats, cluster_feats, topk):
        # query_feats: [B, Q, C]
        # cluster_feats: [B, M, C]
        B, Q, _ = query_feats.shape
        M = cluster_feats.shape[1]
        if topk >= M:
            # 如果 topk 大于当前簇数，就直接保留全部簇，再额外拼一个全局 token
            global_token = cluster_feats.mean(dim=1, keepdim=True).unsqueeze(1).expand(-1, Q, -1, -1)
            return torch.cat([cluster_feats.unsqueeze(1).expand(-1, Q, -1, -1), global_token], dim=2)

        # 把 query 和 cluster 投到多头空间
        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(cluster_feats).view(B, M, self.nhead, self.head_dim).permute(0, 2, 1, 3)

        # 计算每个 query 对所有簇的相关性
        scores = torch.einsum("bhqd,bhmd->bhqm", q, k) * self.scale
        topk = min(topk, M)
        # 先对 head 求平均，得到更稳定的 query-wise 路由分数
        mean_scores = scores.mean(dim=1)
        # 每个 query 都独立选自己的 top-k cluster
        topk_idx = mean_scores.topk(topk, dim=-1).indices
        expanded_clusters = cluster_feats.unsqueeze(1).expand(-1, Q, -1, -1)
        # 每个 query 拿到自己专属的 top-k cluster token
        selected = expanded_clusters.gather(
            2, topk_idx.unsqueeze(-1).expand(-1, -1, -1, cluster_feats.size(-1))
        )
        # 用 query 对 cluster 的分数对选中 token 做轻量增强
        selected_weight = mean_scores.gather(-1, topk_idx).unsqueeze(-1)
        selected = selected * (1.0 + selected_weight)
        # 再额外补一个全局 token，避免只看局部簇时丢掉全局上下文
        global_token = cluster_feats.mean(dim=1, keepdim=True).unsqueeze(1).expand(-1, Q, -1, -1)
        return torch.cat([selected, global_token], dim=2)

    def attend_query_to_clusters(self, query_feats, selected_cluster_feats):
        # query 先从自己选中的 cluster 集合里读信息
        B, Q, K, _ = selected_cluster_feats.shape
        q = self.query_linear(query_feats).view(B, Q, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.k_linear(selected_cluster_feats).view(B, Q, K, self.nhead, self.head_dim).permute(0, 3, 1, 2, 4)
        v = self.v_linear(selected_cluster_feats).view(B, Q, K, self.nhead, self.head_dim).permute(0, 3, 1, 2, 4)

        # 每个 query 只在自己的 top-k cluster 集合内部做注意力
        scores = torch.einsum("bhqd,bhqkd->bhqk", q, k) * self.scale
        attn = torch.softmax(scores, dim=-1)
        context = torch.einsum("bhqk,bhqkd->bhqd", attn, v)
        context = context.permute(0, 2, 1, 3).contiguous().view(B, Q, self.d_model)
        context = self.query_out_proj(self.dropout(context))
        return context

    def route_query_context_to_points(self, point_feats, query_feats, query_context, point_mask):
        # 点不直接读 cluster，而是读“已经被 cluster 更新过的 query”
        B, N, _ = point_feats.shape
        q = self.q_linear(point_feats).view(B, N, self.nhead, self.head_dim).permute(0, 2, 1, 3)
        k = self.query_k_linear(query_feats).view(B, query_feats.size(1), self.nhead, self.head_dim).permute(0, 2, 1, 3)
        v = self.query_v_linear(query_context).view(B, query_context.size(1), self.nhead, self.head_dim).permute(
            0, 2, 1, 3
        )

        # 点通过 query 路由，决定应该吸收哪个 query 的信息
        scores = torch.einsum("bhnd,bhqd->bhnq", q, k) * self.scale
        attn = torch.softmax(scores, dim=-1)
        context = torch.einsum("bhnq,bhqd->bhnd", attn, v)
        context = context.permute(0, 2, 1, 3).contiguous().view(B, N, self.d_model)
        context = self.point_out_proj(self.dropout(context))
        # padding 点不参与更新
        context = context.masked_fill(point_mask.unsqueeze(-1), 0)
        return context

    def forward(self, sp_feats, query, batch_offsets, batch_mask):
        # 先把 padding 后的点特征还原成扁平形式
        sp_feats_flat = batch2flatten(sp_feats, batch_mask)
        # 再恢复成 batch 形式，方便做 attention
        point_feats, point_mask = get_batches(sp_feats_flat, batch_offsets)
        # 生成每个尺度的 cluster token
        cluster_feats_list = self.build_cluster_feats(sp_feats_flat, batch_offsets)
        # 用 query 均值作为点分支多尺度融合时的辅助条件
        query_summary = query.mean(dim=1, keepdim=True).expand(-1, point_feats.shape[1], -1)
        gate_input = torch.cat([point_feats, query_summary], dim=-1)

        multi_scale_messages = []
        multi_scale_query_messages = []
        for cluster_feats, topk in zip(cluster_feats_list, self.per_layer_topk_list):
            # 每个尺度都执行同一套流程：
            # 1. query 选 cluster
            # 2. cluster 更新 query
            # 3. point 再从 query 读回信息
            selected_cluster_feats = self.select_query_conditioned_clusters(query, cluster_feats, topk)
            query_context = self.attend_query_to_clusters(query, selected_cluster_feats)
            point_context = self.route_query_context_to_points(point_feats, query, query_context, point_mask)
            multi_scale_messages.append(point_context)
            multi_scale_query_messages.append(query_context)

        # 点分支和 query 分支分别学习自己的多尺度融合权重
        level_weight = torch.softmax(self.level_gate(gate_input), dim=-1)
        query_level_weight = torch.softmax(self.query_level_gate(query), dim=-1)
        final_message = torch.zeros_like(point_feats)
        final_query_message = torch.zeros_like(query)
        for idx, message in enumerate(multi_scale_messages):
            # 点 token 融合各尺度返回的信息
            final_message = final_message + message * level_weight[..., idx:idx + 1]
            # query token 也同步融合各尺度信息
            final_query_message = final_query_message + multi_scale_query_messages[idx] * query_level_weight[..., idx:idx + 1]

        # 在回到 DEC 之前做归一化，便于后面通过 gate 稳定叠加
        final_message = self.message_norm(final_message)
        final_query_message = self.query_message_norm(final_query_message)
        # padding 点保持为 0，避免污染后续计算
        final_message = final_message.masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': final_message, 'query': final_query_message}
