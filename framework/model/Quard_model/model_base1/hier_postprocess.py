import torch
from pointnet2.pointnet2_utils import FurthestPointSampling
import torch
import torch.nn as nn
from torch_scatter import scatter_mean
import score_computation_cuda
import value_aggregation_cuda
from torch.autograd import Function

class ScoreComputation(Function):
    @staticmethod
    def forward(ctx, query, key, index):
        x = score_computation_cuda.score_forward(query, key, index)
        ctx.save_for_backward(query, key, index)
        return x[0]

    @staticmethod
    def backward(ctx, grad_output):
        input1, input2, index = ctx.saved_tensors
        grad_output = grad_output.contiguous()
        x = score_computation_cuda.score_backward(grad_output, input1, input2, index)
        return x[0], x[1], None


score_computation_op = ScoreComputation.apply





class value_aggregation(Function):
    @staticmethod
    def forward(ctx, score, value, index):
        ctx.save_for_backward(score, value, index)
        f = score.shape[2]
        b, N, _, H = score.shape
        D = value.shape[-1]
        # value [b, M, H, D]
        output = score.new_zeros([b, N, H, D]).contiguous()  # b, 4N, H, D
        value_aggregation_cuda.value_aggregation_forward(score, value, index, output)
        return output

    @staticmethod
    def backward(ctx, grad_output):
        score, value, index = ctx.saved_tensors
        grad_output = grad_output.contiguous()

        grad_score = score.new_zeros(score.shape).contiguous()
        grad_value = value.new_zeros(value.shape).contiguous()

        value_aggregation_cuda.value_aggregation_backward(grad_output, score, value, index, grad_score, grad_value)

        return grad_score, grad_value, None


value_aggregation_op = value_aggregation.apply




def batch2flatten(x, batch_mask):
    return x.view(-1,x.size(-1))[~batch_mask.view(-1)]



def get_batches(x, batch_offsets,off =0):
    B = len(batch_offsets) - 1
    max_len = max(batch_offsets[1:] - batch_offsets[:-1])
    if torch.is_tensor(max_len):
        max_len = max_len.item()
    
    if off !=0:
        new_feats = torch.zeros(B, max_len, x.shape[1],dtype=torch.int32).to(x.device)
    else:
        new_feats = torch.zeros(B, max_len, x.shape[1]).to(x.device)
    mask = torch.ones(B, max_len, dtype=torch.bool).to(x.device)
    for i in range(B):
        start_idx = batch_offsets[i]
        end_idx = batch_offsets[i + 1]
        cur_len = end_idx - start_idx
        padded_feats = torch.cat([x[start_idx:end_idx], torch.zeros(max_len - cur_len, x.shape[1]).to(x.device)], dim=0)
        new_feats[i] = padded_feats
        mask[i, :cur_len] = False
    mask.detach()
    return new_feats, mask

def aggregate_cluster(feats, cluster_ids):
    """按 cluster_id 对特征做平均聚合。

    Args:
        feats: [N, C]
        cluster_ids: [N], 每个元素为簇 id，范围 [0, K-1]
    Returns:
        [K, C]
    """
    if cluster_ids.numel() == 0:
        return feats
    K = int(cluster_ids.max().item()) + 1
    return scatter_mean(feats, cluster_ids, dim=0, dim_size=K)


class Cluster_Attn(nn.Module):

    def __init__(self, d_model=256, nhead=8, cluster_layer_nums=[256,64,8], per_layer_topk_list=[4,4,4,4], dropout=0.0):
        super().__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.head_dim = d_model // nhead
        self.cluster_layer_nums = cluster_layer_nums
        self.per_layer_topk_list = per_layer_topk_list
        ### 注册点云划分器
        self.partitioner = PointCloudPartitioner(cluster_layer_nums=cluster_layer_nums)

        self.register_parameter("weight", nn.Parameter(torch.randn(len(per_layer_topk_list))))


        ###   先共享一组权重qkv
        self.q_linear = nn.Linear(d_model, d_model)
        self.k_linear = nn.Linear(d_model, d_model)
        self.v_linear = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(d_model) 
        self.scale = self.head_dim ** -0.5


    def get_cluster(self, sp_pos, batch_offsets):
        self.partitioner(sp_pos, batch_offsets)



    def get_gather_indices(self, mask):
        """
        mask: (B, H, N, M)  True表示需要选择
        """
        num_valid = mask.sum(dim=-1)  # (B, H, N)
        K = num_valid.max().item()    # 获取整个 batch 中最大的 K
        vals, indices = torch.topk(mask.int(), k=K, dim=-1, sorted=True)
        top_k_mask = vals.bool()
        indices = indices.permute(0,2,3,1).contiguous()
        return indices, top_k_mask
    

    def gather_values(self, tensor, indices, top_k_mask):
        """
        执行具体的 gather 操作
        tensor: (B, H, M, C)
        indices: (B, H, N, K)
        """
        B, H, N, K = indices.shape
        C = tensor.shape[-1]

        tensor_flat = tensor.flatten(0, 1)          # 扁平化处理 (节省显存并适配 gather)
        indices_flat = indices.flatten(0, 1).reshape(B*H, N*K)          # indices: (B*H, N*K)
        indices_expanded = indices_flat.unsqueeze(-1).expand(-1, -1, C)        # 扩展 indices 以匹配 C 维度
        gathered_flat = torch.gather(tensor_flat, 1, indices_expanded)         # Gather
        gathered = gathered_flat.view(B, H, N, K, C)         # 恢复形状
        gathered = gathered * top_k_mask.unsqueeze(-1).type_as(gathered)         # Masking padding (将无效位置置0)
        return gathered

    def process_coarse_level(self, query, key, value, topk):
        """最粗尺度上的 full attention，与 QTAttA 类似，但不做 mask。"""
        bs, n, c = key.shape
        x = query
        query = self.q_linear(query).view(bs, -1, self.nhead, self.head_dim).permute(0,2,1,3)  # [B, S, H, D]
        key = self.k_linear(key).view(bs, -1, self.nhead, self.head_dim).permute(0,2,1,3) # [B, S, H, D]
        value = self.v_linear(value).view(bs, -1, self.nhead, self.head_dim).permute(0,2,1,3)  # [B, S, H, D]

        QK = torch.einsum("nhld,nhsd->nhls", query, key) ### 计算注意力分数

        A = torch.softmax(self.scale * QK, dim=-1) ## bs,h,l,s
        topk_score, topk_idx = torch.topk(A, dim=-1, k=topk, largest=True)  # 选取 top-k 位置（供更精细化的层去使用）

        # 直接在所有位置上聚合 value 得到 message
        output = torch.einsum("nhls,nhsd->nhld", A, value)  # [B, nhead, L_q, D]
        output = output.permute(0, 2, 1, 3).contiguous().view(bs, n, c)  # [B, L_q, C]

        output = self.dropout(output) + x
        if self.norm is not None: output = self.norm(output)

        
        return A, output, topk_idx


    def process_fine_level(self, query, key, value, topk_idx, topk, cluster_ids, sp_feats_batch_masks=None):
        """
        Inputs:
            query: [B, N2, C]
            key:   [B, N2, C]
            value: [B, N2, C]
            topk_idx: [B, H, N1, K]  来自上一层的 topk 索引
            topk: int  本层的 topk 数量       
            cluster_ids: [B, N2]  当前的值属于上一层的哪个簇   [1,63,0,....,]  总共长度256  里边的值是n1内的值
        Returns:
            A: [B, H, N2, K]
            message: [B, H, N2, D]
            topk_idx: [B, H, N2, K]  最终返回本层的 topk 索引 供下一层使用
        """
        B, N, C = key.shape
        x = query
        # 统一成多头形式
        q = self.q_linear(query).view(B, N, self.nhead, self.head_dim)  # [B, N, H, D]
        k = self.k_linear(key).view(B, N, self.nhead, self.head_dim) # [B, N, H, D]
        v = self.v_linear(value).view(B, N, self.nhead, self.head_dim)  # [B, N, H, D]


        _, _, _, K_last = topk_idx.shape #N_last 更粗层的数量

        # 1. 根据 L2 簇 id，找到对应的 L3 父簇在 topk_idx 中的位置
        c_ids_expanded = cluster_ids.unsqueeze(1).expand(-1, self.nhead, -1) # [B, H, N_ben]
        gather_idx = c_ids_expanded.unsqueeze(-1).expand(-1, -1, -1, K_last)

        topk_parent = torch.gather(topk_idx, 2, gather_idx)


        # 2. 为所有 L2 簇 准备父簇 id，比较是否在上面的 topk 集合中
        topk_parent_exp = topk_parent.unsqueeze(3)  # [B, H, N_ben, 1, K_parent]
        cluster_ids_exp = cluster_ids.unsqueeze(1).unsqueeze(2).unsqueeze(-1)  # [B, 1, 1, N_ben, 1]
        
        # 使用any减少维度
        mask_big = (topk_parent_exp == cluster_ids_exp).any(dim=-1)  # [B, H, N_ben, N_ben]
        mask_mask = mask_big
        if sp_feats_batch_masks is not None:
            mask_mask = mask_big & (~sp_feats_batch_masks.unsqueeze(1).unsqueeze(-1)) & (~sp_feats_batch_masks.unsqueeze(1).unsqueeze(1)) # 屏蔽 padding 位置
            
            
        # 1. 获取索引和 mask (只计算一次)
        indices, top_k_mask = self.get_gather_indices(mask_mask)


        # 2. Attention Score
        attn_mask = torch.zeros_like(top_k_mask, dtype=torch.float)
        attn_mask.masked_fill_(~top_k_mask, float("-inf"))
        if sp_feats_batch_masks is not None:
            att_mask2 = (sp_feats_batch_masks.unsqueeze(1).unsqueeze(-1))
            attn_mask.masked_fill_(att_mask2, float("-inf"))

        attn_mask = attn_mask.permute(0,2,3,1).contiguous()  # b n k h
 

        # 3. Gather key 和 value
        QK = score_computation_op(q, k, indices)  # [b, n, k, h]
        QK += attn_mask

        A = torch.softmax(self.scale * QK, dim=-2)  # [b, n, k, h]
        
        QKV = value_aggregation_op(A, v, indices).view(B, N, C)  # [B, L_q, C]


        QKV = self.dropout(QKV) + x
        if self.norm is not None: QKV = self.norm(QKV)


        if sp_feats_batch_masks is not None:
            topk_idx = None
        else:
            topk_score, inner_idx = torch.topk(A, dim=-2, k=topk, largest=True) # 5. 选取 top-k 索引供下一层使用
            topk_idx = torch.gather(indices, -2, inner_idx).permute(0,3,1,2)    
        
        return A, QKV, topk_idx


        
    def forward_att(self, per_layer_cluster_ids, per_layer_feats, sp_feats_batch_masks):
        """前向计算。

        Args:
            feat_l1: [N, C]，点 / 超点特征。
            cluster2_ids: [N]，第一层子集 id（例如 256）。
            cluster3_ids: [N]，第二层子集 id（例如 64 或 16）。
        Returns:
            out: [N, C]，增强后的特征。
        """
        
        messages = []
        messages_gather = []
        A, message,topk_idx = self.process_coarse_level(
                                per_layer_feats[len(per_layer_feats)-1], 
                                per_layer_feats[len(per_layer_feats)-1], 
                                per_layer_feats[len(per_layer_feats)-1],
                                self.per_layer_topk_list[len(per_layer_feats)-1],
                                )
        ### 将粗特征进一步高分辨率化
        last_message = torch.gather(
                message,
                1,
                per_layer_cluster_ids[-1].unsqueeze(-1).expand(-1, -1, message.size(-1))
            )

        messages.append(message)
        messages_gather.append(message)

        
        for i in range(len(per_layer_feats)-2, -1, -1):
            A, message, topk_idx = self.process_fine_level(
                per_layer_feats[i], 
                per_layer_feats[i], 
                per_layer_feats[i], 
                topk_idx, 
                self.per_layer_topk_list[i], 
                per_layer_cluster_ids[i],
                sp_feats_batch_masks if i==0 else None
            )
            messages.append(message)

            ###### 利用per_layer_cluster_ids将message映射回原始点云的分辨率
            messages_gather_new = []
            f = per_layer_cluster_ids[i].unsqueeze(-1)
            for j in range(len(messages_gather)):
                last_message = torch.gather(
                        messages_gather[j],
                        1,
                        f.expand(-1, -1, messages_gather[j].size(-1))
                    )
                messages_gather_new.append(last_message)
            messages_gather_new.append(message)
            messages_gather = messages_gather_new
        
        weight = torch.softmax(self.weight, dim=0)
        for i, m in enumerate(messages_gather):
            messages_gather[i] = m * weight[i]
            messages_gather[i] = messages_gather[i].unsqueeze(1)
        final_message = torch.sum(torch.cat(messages_gather, dim=1), dim=1)


        return final_message


    def forward(self, sp_feats, batch_offsets, batch_mask):
        """
        Args:
            sp_feats: [N_sp, C]
            sp_coords_float: [N_sp, 3]
            batch_offsets: [B+1]
        Returns:
            sp_feats_new: [N_sp, C]
        """
        sp_feats = batch2flatten(sp_feats, batch_mask)

        # 按层收集每个 batch 的结果：外层为层数，内层为 batch 项
        per_layer_feats = [[] for _ in range(len(self.cluster_layer_nums)+1)]

        ## 对每个batch的scene单独处理
        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            feats_b = sp_feats[s:e]          # [Ni, C]  ## 特征信息

            for l in range(len(self.cluster_layer_nums)):
                feats_b = aggregate_cluster(feats_b, self.partitioner.per_layer_cluster_ids[l][b]) 
                per_layer_feats[l+1].append(feats_b)


        for i in range(len(self.cluster_layer_nums)):
            per_layer_feats[i+1] = torch.stack(per_layer_feats[i+1])

        sp_feats_batch, sp_feats_batch_mask = get_batches(sp_feats, batch_offsets)
        per_layer_feats[0] = sp_feats_batch
            
        messages = self.forward_att(self.partitioner.per_layer_cluster_ids_batch, per_layer_feats, sp_feats_batch_mask)

        return messages

class PointCloudPartitioner(nn.Module):
    """
    点云划分器：基于FPS采样结果，将点云划分为互不相交的子集，并为每个子集聚合特征。
    """
    
    def __init__(self, cluster_layer_nums=[256,64,8]):
        super().__init__()
        self.cluster_layer_nums = cluster_layer_nums

        self.per_layer_coords = [[] for _ in range(len(self.cluster_layer_nums)+1)]
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]
        self.per_layer_cluster_ids_batch = [[] for _ in range(len(self.cluster_layer_nums))]
    
    def partition_points(self, points_pos: torch.Tensor, fps_pos: torch.Tensor):
        """
        执行划分并聚合特征。
        Args:
            points_pos:   [M, 3] 原始点坐标
            fps_pos:        [K, 3] FPS采样点（种子点）
            
        Returns:
            subset_idxs:    List[Tensor], 第 k 个子集在原始 coords_i 中的索引 [N_k]
        """
        M, _ = points_pos.shape
        K = fps_pos.shape[0]
        dist_matrix = torch.cdist(points_pos, fps_pos)  ### [M, K]
        min_distances, partition_labels = torch.min(dist_matrix, dim=-1)  ## [M]
        counts = torch.bincount(partition_labels, minlength=K)  # 1) 计算每个簇的数量 # [K]
        arange_idx = torch.arange(M, device=partition_labels.device) # 2) 按标签排序，得到同簇元素在一起的索引序列
        labels_sorted, perm = torch.sort(partition_labels)  # labels_sorted 仅用于调试/检查
        idx_sorted = arange_idx[perm]                       # [M]
        subset_idxs = list(torch.split(idx_sorted, counts.tolist()))
        return subset_idxs

    
    def cluster_layer(self, pos, fps_num, device):
        """
        ## Input pos: [N, 3]
        ## Output center: [K3, 3]  cluster_ids_scene: [N]
        """
        fps_num = min(fps_num, pos.size(0))
        fps_seed_sp = FurthestPointSampling.apply(pos.unsqueeze(0), fps_num)  # [1, K3]
        fps_pos = pos.gather(
            dim=0,
            index=fps_seed_sp.long().squeeze(0).unsqueeze(-1).repeat(1, pos.size(-1)),
        )

        subset_idxs = self.partition_points(pos, fps_pos)

        cluster_ids_scene = torch.full((pos.size(0),), -1, dtype=torch.long, device=device)

        for cid, idx_local in enumerate(subset_idxs):
            cluster_ids_scene[idx_local.long()] = cid ## 为len(center)个点分配id 属于哪一个簇
        
        center = aggregate_cluster(pos, cluster_ids_scene) 
        return center, cluster_ids_scene


    def forward(self,sp_coords_float, batch_offsets):
        self.per_layer_coords = [[] for _ in range(len(self.cluster_layer_nums)+1)]
        self.per_layer_cluster_ids = [[] for _ in range(len(self.cluster_layer_nums))]
        self.per_layer_cluster_ids_batch = [[] for _ in range(len(self.cluster_layer_nums))]
        device = sp_coords_float.device

        ##
        lenss = []
        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            lens = e - s
            lenss.append(lens)
        min_len = min(lenss)
        self.cluster_layer_nums[0] = min(self.cluster_layer_nums[0], min_len) 
        for b in range(len(batch_offsets) - 1):
            s = batch_offsets[b].item()
            e = batch_offsets[b + 1].item()
            coords_b = sp_coords_float[s:e]  # [Ni, 3]  ## 位置信息
            for l in range(len(self.cluster_layer_nums)):
                coords_b, idx_to_cluster = self.cluster_layer(coords_b, self.cluster_layer_nums[l], device)
                self.per_layer_cluster_ids[l].append(idx_to_cluster)
                self.per_layer_coords[l+1].append(coords_b)

        for i in range(len(self.cluster_layer_nums)):
            self.per_layer_coords[i+1] = torch.stack(self.per_layer_coords[i+1])
            if i == 0:
                per_layer_cluster_ids0_batch, _ = get_batches(torch.cat(self.per_layer_cluster_ids[i], dim=0).unsqueeze(-1), batch_offsets, off=-1)
                self.per_layer_cluster_ids_batch[i] = per_layer_cluster_ids0_batch.squeeze(-1)            
            else:
                self.per_layer_cluster_ids_batch[i] =  torch.stack(self.per_layer_cluster_ids[i])  ### 由于 同一个batch中最细化层级的点数并不是一致
        sp_coords_batch, _ = get_batches(sp_coords_float, batch_offsets)
        self.per_layer_coords[0] = sp_coords_batch


