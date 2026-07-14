import torch
import torch.nn as nn
import torch.nn.functional as F
from functools import partial

from timm.models.layers import DropPath, to_2tuple, trunc_normal_
from timm.models.registry import register_model
from timm.models.vision_transformer import _cfg
import math
from ..functions.quadtree_attention import score_computation_op, value_aggregation_op
from einops.einops import rearrange


class QTAttA(nn.Module):
    """四叉树注意力（版本 A）

    主要特点：
    - 多头注意力（multi-head），在最粗层做 full attention；
    - 在更细层级仅在上一层选中的 top-k 位置对应的 2x2 子块上继续注意力计算；
    - 通过自定义 CUDA/算子 `score_computation_op` 与 `value_aggregation_op` 做稀疏注意力。
    """

    def __init__(
        self,
        nhead,                      # 注意力头数
        dim,                        # 通道维度（总维度），每个头的维度 = dim // nhead
        topks=[32, 32, 32, 32],     # 各个尺度使用的 top-k 大小
        scale=None,
        use_dropout=False,
        attention_dropout=0.1,
    ):
        super().__init__()
        self.use_dropout = use_dropout
        self.topks = topks
        self.nhead = nhead
        self.dim = dim

    def process_coarse_level(self, query, key, value, topk):
        """在最粗尺度上做完整注意力，并选出 top-k key 位置。

        Args:
            query/key/value: [B, C, H, W]
            topk: 每个 query 位置选取的 top-k key 数量。
        Returns:
            A: 注意力权重 [B, L_q, L_k, nhead]
            message: 聚合后的值 [B, L_q, nhead, D]
            topk_score: 每个 query 对应 top-k 的注意力分数
            topk_idx: 每个 query 对应 top-k 的 key 索引（一维索引形式）
        """
        bs, c, h, w = key.shape
        # 每个头的维度 D
        cur_dim = key.shape[1] // self.nhead

        # 将 (B, C, H, W) 展平为 (B, H*W, C) 再 reshape 成 (B, H*W, nhead, D)
        key = rearrange(key, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]
        value = rearrange(value, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]
        query = rearrange(query, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, L, H, D]

        # 使用爱因斯坦求和约定计算 QK^T，得到注意力 logits
        #  (L 表示 query 序列长度，S 表示 key 序列长度，H 表示 head 数)
        QK = torch.einsum("nlhd,nshd->nlsh", query, key)
        # softmax 温度 1/sqrt(D)
        softmax_temp = 1.0 / cur_dim ** 0.5  # sqrt(D)
        # 在 "L_k" 维度上（dim=-2）做 softmax，得到注意力分布
        A = torch.softmax(softmax_temp * QK, dim=-2) #### 计算qk之间的注意力分布

        # 选取每个 query 对应的 top-k key 索引和分数
        topk_score, topk_idx = torch.topk(A, dim=-2, k=topk, largest=True)  ### 每个query对应topk个 key的位置和分数
        # 创建与 A 相同形状的 mask，全 1  topk_idx: [B, L_q, topk, Hh]
        mask = torch.ones_like(A)
        # 将 top-k 位置置为 0（scatter 到 mask 上），后续只在非 top-k 上聚合
        mask = mask.scatter(dim=-2, index=topk_idx, src=torch.zeros_like(topk_idx).float())
        ### 生成出来一个mask 便于知道哪些位置是topk 哪些不是topk   topk设为0  
        # 在被保留的位置上（非 top-k）聚合 value，得到 coarse level 的 message
        message = torch.einsum("nlsh,nshd->nlhd", A * mask, value)  # [B, L_q, nhead, D]
        ### message 聚合的是非topk位置的value
        return A, message, topk_score, topk_idx

    def process_fine_level(self, query, key, value, topk_score, topk_pos, topk_prev, topk, final=False):
        """在更细一级的尺度上进行四叉树注意力。

        思路：
        - 上一层已经得到若干 top-k 空间位置（topk_pos），在当前更细分辨率上，每个 coarse 位置对应 2x2 的子块；
        - 只在这些 2x2 子块内做注意力，从而大大减少计算量；
        - 如果不是最终层（final=False），再次从这些位置中选出新的 top-k，继续向下递归；
          否则直接聚合为最终 message。
        """
        bs, c, h, w = key.shape

        # 单头维度 D
        cur_dim = key.shape[1] // self.nhead
        # 将 key/value 展平到 (B, H*W, nhead, D)
        key = rearrange(key, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]
        value = rearrange(value, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]

        # 当前 finer level 的 query 是更高分辨率的特征，将每个 coarse 位置对应的 2x2 patch 展开成 4 个子节点
        # 先 reshape 为 [B, C, H/2, 2, W/2, 2]，再把 (2,2) 合并到一个长度为 4 的维度上
        query = query.view(bs, c, h // 2, 2, w // 2, 2)
        query = rearrange(query, "b c h t1 w t2-> b (h w) (t1 t2) c ").view(bs, -1, 4, self.nhead, cur_dim)
        ## 先按照粗特征的空间位置，把每个位置的4个子块展开成一个维度，再reshape成(B, L, 4, H, D)
        # 将上一层的 topk 空间坐标放大 2 倍（因为当前尺度的 H、W 是上一层的 2 倍），并生成 2x2 子块的 1D 索引
        idx_gather = []
        topk_pos = topk_pos * 2  ## 假如之前是(0,1),(1,1) 现在变成(0,2),(2,2)
        ###[2, B, L, topk, Hh]
        for x in [0, 1]:
            for y in [0, 1]:
                # (row + x, col + y) -> 一维索引 row*w + 
                ### [][]
                ### [][]  这四个坐标的绝对位置
                idx = (topk_pos[0] + x) * w + topk_pos[1] + y  # convert to index  idx: [B, L, K, Hh]
                idx_gather.append(idx)

        # 将 4 个偏移堆叠在一个新维度上：得到 [B, L, K, 4, nhead]
        idx = torch.stack(idx_gather, dim=3)  

        # ------------------------- 计算局部注意力分数 -------------------------
        # 注：使用自定义算子 score_computation_op，避免显式 gather，大幅节省显存/时间
        # query: [B, N, 4, H, D]
        # key:   [B, 4N, H, D]
        # idx:   [B, N, K, 4, H]
        # QK:    [B, N, 4, 4K, H]
        QK = score_computation_op(query, key.contiguous(), idx.view(bs, -1, topk_prev * 4, self.nhead))
        # 将维度中的 (4K) 拆成 (K, 4)，便于和父节点/子节点关系对应
        QK = rearrange(QK, "n l w (k f) h -> n l w k f h", k=topk_prev, f=4)
        softmax_temp = 1.0 / cur_dim ** 0.5  # sqrt(D)
        # 在 "父节点索引" 维度（-2）上做 softmax，得到 finer level 的注意力 A
        A = torch.softmax(softmax_temp * QK, dim=-2)  # [B, N, 4, K, 4, H]

        # ------------------------- 分数重分配（Score redistribution） -------------------------
        # topk_score 来自上一层父节点，对应 coarse 级别的注意力权重
        topk_score = topk_score.unsqueeze(-2).unsqueeze(2)
        # 将 finer level 的注意力按父节点权重重新加权，然后合并父子维度 -> [B, N, 4, topk_prev*4, H]
        A = (A * topk_score).reshape(bs, -1, 4, topk_prev * 4, self.nhead)
        # idx 同样 reshape 成 [B, N, 4, topk_prev*4, H]，以便与 A 对齐使用
        idx = idx.view(bs, -1, 1, topk_prev * 4, self.nhead).repeat(1, 1, 4, 1, 1)  # [B, N, 4, K*4, H]
        # [B, L, K, 4, nhead]
        # 在 4*topk_prev 的候选中再次选出新的 top-k（更细一层的 active 节点）
        topk_score, topk_idx = torch.topk(A, dim=-2, k=topk, largest=True)

        # ------------------------- 聚合 value，得到 finer level 的 message -------------------------
        if not final:
            # 非最终层：只在「非 top-k」位置上聚合，保留剩余空间给更细一层
            mask = torch.ones_like(A)
            mask = mask.scatter(dim=-2, index=topk_idx, src=torch.zeros_like(topk_idx).float())
            message = value_aggregation_op(A * mask, value.contiguous(), idx)
        else:
            # 最终层：在所有位置上聚合，得到最终 message
            message = value_aggregation_op(A, value.contiguous(), idx)

        # 如果不是最终层，还需要把新的 topk_idx/topk_score 转回空间坐标，用于下一层
        if not final:
            # 根据 topk_idx 从 idx 中取出真实的一维索引
            topk_idx = torch.gather(idx, index=topk_idx, dim=-2)
            # 将 (H/2, W/2, 2, 2) 还原回 (H, W) 网格
            topk_idx = rearrange(topk_idx, "b (h w) (t1 t2) k nh -> b (h t1 w t2) k nh", h=h // 2, t1=2)  # reshape back
            topk_score = rearrange(
                topk_score, "b (h w) (t1 t2) k nh -> b (h t1 w t2) k nh", h=h // 2, t1=2
            )  # reshape back

        return A, message, topk_score, topk_idx

    def forward(self, queries, keys, values, q_mask=None, kv_mask=None):
        """多头四叉树注意力（版本 A）

        Args:
            queries: Query 金字塔，list，元素形状 [B, C, H, W]，从低分辨率到高分辨率
            keys:    Key 金字塔，同上
            values:  Value 金字塔，同上
        Returns:
            final_message: 最终聚合后的 message，形状约为 [B, H_final*W_final, nhead, D]
        """

        # 批大小
        bs = queries[0].shape[0]
        # 存储每个尺度的 message
        messages = []
        # 最粗尺度使用的 top-k
        topk = self.topks[0]

        # 从粗到细遍历（因为金字塔一般从高分辨率到低分辨率存放，这里 reversed）
        for i, (query, key, value) in enumerate(zip(reversed(queries), reversed(keys), reversed(values))):
            bs, c, h, w = key.shape
            if i == 0:
                # 第 0 层：最粗尺度，做 full attention
                A, message, topk_score, topk_idx = self.process_coarse_level(
                    query, key, value, topk
                )  # Full attention for coarest level
            else:
                # 之后的层：只在上一层选中的 top-k 节点的四叉树子节点中做注意力
                topk_prev = topk
                topk = self.topks[i]
                # 是否到达最细层
                final = True if i == len(queries) - 1 else False
                A, message, topk_score, topk_idx = self.process_fine_level(
                    query, key, value, topk_score, topk_pos, topk_prev, topk, final
                )  # Quadtree attention

            messages.append(message)
            if topk_idx is not None:
                # 一维索引 -> (row, col) 坐标，用于下一层 finer level
                topk_pos = torch.stack([topk_idx // w, topk_idx % w])  # convert to coordinate

        # ------------------------- 融合各尺度 message -------------------------
        final_message = 0
        for i, m in enumerate(messages):
            if i == 0:
                # 最粗层 message 直接作为初始值
                final_message = m
            else:
                # 其他层：将上一层结果视作 coarse 特征，与当前 finer 特征相加并上采样
                final_message = final_message.unsqueeze(2) + m
                # 使用 einops 将 2x2 子块折叠回更细的空间网格
                final_message = rearrange(
                    final_message, "b (H W) (t1 t2) h d -> b (H t1 W t2) h d", t1=2, t2=2, H=queries[-i].shape[2]
                )

        return final_message


class QTAttB(nn.Module):
    """四叉树注意力（版本 B）

    与 QTAttA 的主要差异：
    - 在多尺度 message 融合时，引入可学习的尺度权重 `weight`；
    - 可选的局部增强位置编码（LEPE），通过 depthwise Conv2d 提供局部位置信息。
    """

    def __init__(self, nhead, dim, scale, topks=[32, 32, 32, 32], use_dropout=False, attention_dropout=0.1, lepe=False):
        super().__init__()
        self.use_dropout = use_dropout
        self.topks = topks
        self.nhead = nhead
        self.dim = dim
        self.lepe = lepe
        if lepe:  # locally enhanced position encoding（局部增强位置编码）
            # 为每个尺度定一个 depthwise conv，用于提取本地位置偏置
            self.get_vs = nn.ModuleList(
                [
                    nn.Conv2d(dim * nhead, dim * nhead, kernel_size=3, stride=1, padding=1, groups=dim * nhead)
                    for _ in range(scale)
                ]
            )
        # 可学习的尺度权重向量，长度等于尺度数 `scale`
        self.register_parameter("weight", nn.Parameter(torch.randn(scale)))

    def process_coarse_level(self, query, key, value, topk):
        """最粗尺度上的 full attention，与 QTAttA 类似，但不做 mask。"""
        bs, c, h, w = key.shape

        cur_dim = key.shape[1] // self.nhead
        # 展平空间维度 -> [B, H*W, nhead, D]
        key = rearrange(key, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]
        value = rearrange(value, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]
        query = rearrange(query, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)
        # 计算 QK^T
        QK = torch.einsum("nlhd,nshd->nlsh", query, key)
        softmax_temp = 1.0 / cur_dim ** 0.5  # sqrt(D)

        A = torch.softmax(softmax_temp * QK, dim=-2)
        # 选取 top-k 位置（供 finer level 使用）
        topk_score, topk_idx = torch.topk(A, dim=-2, k=topk, largest=True)

        # 直接在所有位置上聚合 value 得到 message
        message = torch.einsum("nlsh,nshd->nlhd", A, value)  # [B, L_q, nhead, D]

        return A, message, topk_score, topk_idx

    def process_fine_level(self, query, key, value, topk_score, topk_pos, topk_prev, topk, final=False):
        """更细尺度上的四叉树注意力（版本 B）。

        与 QTAttA 的不同点在于：没有进行上一层分数的显式重分配，仅用当前 A 计算 message。
        """
        bs, c, h, w = key.shape

        cur_dim = key.shape[1] // self.nhead
        key = rearrange(key, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]
        value = rearrange(value, "b c h w -> b (h w) c").view(bs, -1, self.nhead, cur_dim)  # [B, S, H, D]

        # 将 finer level 的 query 拆成每个 coarse 位置下的 4 个子节点
        query = query.view(bs, c, h // 2, 2, w // 2, 2)
        query = rearrange(query, "b c h t1 w t2-> b (h w) (t1 t2) c ").view(bs, -1, 4, self.nhead, cur_dim)

        # 将上一层的 topk 坐标扩展到当前尺度，并为每个 coarse 位置生成 2x2 子节点索引
        topk_pos = topk_pos * 2
        idx_gather = []
        for x in [0, 1]:
            for y in [0, 1]:
                idx = (topk_pos[0] + x) * w + topk_pos[1] + y  # convert to index
                idx_gather.append(idx)
        idx = torch.stack(idx_gather, dim=3)  # [B, L, K, 4, H]

        # 使用 score_computation_op 计算局部注意力分数
        # query: [B, N, 4, H, D]
        # key:   [B, 4N, H, D]
        # idx:   [B, N, K, 4, H]
        # QK:    [B, N, 4, 4K, H]
        QK = score_computation_op(query, key.contiguous(), idx.view(bs, -1, topk_prev * 4, self.nhead))
        softmax_temp = 1.0 / cur_dim ** 0.5  # sqrt(D)
        A = torch.softmax(softmax_temp * QK, dim=-2)  # [B, N, 4, 4K, H]
        # 将 4K 合并成单一维度，方便后续 top-k
        A = A.reshape(bs, -1, 4, topk_prev * 4, self.nhead)
        # idx 同样 reshape 并在第 2 维复制 4 次，与 A 对齐
        idx = idx.view(bs, -1, 1, topk_prev * 4, self.nhead).repeat(1, 1, 4, 1, 1)  # [B, N, 4, K*4, H]

        # 在 4*topk_prev 的候选中选出新的 top-k
        topk_score, topk_idx = torch.topk(A, dim=-2, k=topk, largest=True)
        # 直接在这些局部区域上聚合 value 得到 message
        message = value_aggregation_op(A, value.contiguous(), idx)
        # 更新 topk_idx/topk_score：从一维索引还原到空间网格 (H,W)
        topk_idx = torch.gather(idx, index=topk_idx, dim=-2)
        topk_idx = rearrange(topk_idx, "b (h w) (t1 t2) k nh -> b (h t1 w t2) k nh", h=h // 2, t1=2)  # reshape back
        topk_score = rearrange(topk_score, "b (h w) (t1 t2) k nh -> b (h t1 w t2) k nh", h=h // 2, t1=2)  # reshape back

        return A, message, topk_score, topk_idx

    def forward(self, queries, keys, values, q_mask=None, kv_mask=None):
        """多头四叉树注意力（版本 B），支持多尺度加权与 LEPE。

        Args:
            queries: Query 金字塔，list，元素 [B, C, H, W]
            keys:    Key 金字塔
            values:  Value 金字塔
        Returns:
            final_message: 聚合后的多尺度 message，形状约为 [B, H_final*W_final, nhead, D]
        """

        bs = queries[0].shape[0]

        messages = []        # 保存每个尺度的 message
        topk = self.topks[0]  # 最粗尺度的 top-k
        # 同样从最粗尺度开始遍历
        for i, (query, key, value) in enumerate(zip(reversed(queries), reversed(keys), reversed(values))):
            bs, c, h, w = key.shape
            if i == 0:  # Full attention for the coarest level
                A, message, topk_score, topk_idx = self.process_coarse_level(query, key, value, topk)
            else:
                topk_prev = topk
                topk = self.topks[i]
                final = True if i == len(queries) - 1 else False
                A, message, topk_score, topk_idx = self.process_fine_level(
                    query, key, value, topk_score, topk_pos, topk_prev, topk, final
                )

            messages.append(message)
            # 将一维索引转换为坐标，用于下一层 finer level
            topk_pos = torch.stack([topk_idx // w, topk_idx % w])  # convert to coordinate

        # ------------------------- 多尺度 message 融合 -------------------------
        final_message = 0

        # 对可学习权重做 softmax，得到各尺度的融合权重
        weight = torch.softmax(self.weight, dim=0)
        for i, m in enumerate(messages):
            if self.lepe:
                # 取出对应尺度的 value 特征，做 depthwise conv 得到局部位置编码 lepe
                H, W = values[-(i + 1)].shape[-2:]
                lepe = self.get_vs[i](values[-(i + 1)])

            if i == 0:
                # 最粗尺度初始化 final_message
                if self.lepe:
                    # [B, C, H, W] -> [B, H*W, nhead, D]
                    lepe = rearrange(lepe, "b (hd d) H W -> b (H W) hd d", hd=self.nhead)
                    final_message = (m + lepe) * weight[i]
                else:
                    final_message = m * weight[i]
            else:
                # 细尺度：在上一层 message 基础上叠加，并把 2x2 子块折叠成更细网格
                if self.lepe:
                    # [B, C, H*2, W*2] -> [B, H*W, 4, nhead, D]
                    lepe = rearrange(lepe, "b (hd d) (H t1) (W t2) -> b (H W) (t1 t2) hd d", hd=self.nhead, t1=2, t2=2)
                    final_message = final_message.unsqueeze(2) + (m + lepe) * weight[i]
                else:
                    final_message = final_message.unsqueeze(2) + m * weight[i]

                # 把 [B, H*W, 4, nhead, D] 折叠到更细级别的空间尺寸上
                final_message = rearrange(
                    final_message, "b (H W) (t1 t2) h d -> b (H t1 W t2) h d", t1=2, t2=2, H=queries[-i].shape[2]
                )
        return final_message
