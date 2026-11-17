# model_base1_quard2_c2f_enc_lite_posA 模型结构

本文档描述 `model_base1_quard2_c2f_enc_lite_posA` 的网络结构、C2F Encoder Lite 模块、posA 注入位置、张量流、预测头和训练损失。内容以当前项目代码的真实执行路径为准，并单独标出设计意图与实际实现之间的差异。

## 1. 模型定位

该模型用于 ScanRefer 3D Referring Expression Segmentation。输入是一段自然语言描述和对应场景点云，输出被描述目标的点级分割 mask。

模型建立在 `model_base1` 上，主要增加层次化 cluster context：

```text
model_base1
  -> hierarchical cluster bank
  -> coarse-to-fine query-cluster routing
  -> cluster message 回写 superpoint feature
  -> 只在 encoder 后两层注入
  -> posA 调整 cluster 模块在 encoder layer 内的位置
```

当前配置的重要参数：

| 参数 | 数值 | 含义 |
|---|---:|---|
| `num_layer` | 6 | Encoder/Decoder 迭代层数 |
| `d_model` | 256 | 点、语言和 query 的统一特征维度 |
| `nhead` | 8 | attention head 数 |
| `hidden_dim` | 1024 | FFN 隐藏维度 |
| `fps_num` | 256 | query seed 的 FPS 数量 |
| `sampling_module.num_proposal` | 128 | 初始 query 数量 |
| `cluster_layer_nums` | `[256,64,8]` | 细、中、粗三层 cluster 数量 |
| `per_layer_topk_list` | `[32,16,8]` | 细、中、粗层 routing top-k |
| `cluster_att_num_layers` | 2 | 仅在第 5、6 个 encoder layer 使用 cluster 模块 |
| `cluster_att_init` | 0.1 | sigmoid gate 的参数初值 |

## 2. 整体结构

```text
点云输入
  |
  v
Sparse 3D U-Net Backbone
  |
  v
Point Feature --scatter_mean--> Superpoint Feature [sum(N_b), 32]
  |                                      |
  |                                      +--> Superpoint XYZ
  v
Linear + LayerNorm + ReLU
  |
  v
Instance Feature I0 [B, N, 256]

语言 token
  |
  v
Frozen RoBERTa [B, L, 768]
  |
  v
Linear + LayerNorm
  |
  v
Language Feature T0 [B, L, 256]

I0 + T0
  |
  +--> FPS seed + SamplingModule --> Query Q0 [B, 128, 256]
  |
  v
6 x [Encoder Layer -> Decoder Layer -> Iterative Prediction]
  |
  v
Query mask / score / indication prediction
  |
  v
选择目标 query，并映射回原始点
```

## 3. 点云与语言编码

### 3.1 点云分支

原始点特征先经过 sparse convolution 和 U-Net：

```text
voxelization
 -> SubMConv3d
 -> Sparse U-Net
 -> BatchNorm + ReLU
 -> voxel-to-point mapping
 -> superpoint scatter_mean
```

得到：

```text
sp_feats: [sum(N_b), 32]
sp_pos:   [sum(N_b), 3]
```

DEC 中使用输入投影：

```text
I0 = ReLU(LayerNorm(Linear(sp_feats)))
I0: [B, N, 256]
```

若存在 2D 特征，则将 1024 维 2D 特征映射到 256 维，并与 3D instance feature 相加后归一化。

### 3.2 语言分支

语言由冻结的 RoBERTa 编码：

```text
tokens -> RoBERTa -> [B, L, 768]
       -> Linear(768, 256) -> LayerNorm
       -> T0 [B, L, 256]
```

### 3.3 Query 初始化

先从 superpoint 坐标中 FPS 采样 256 个 seed，再通过空间相关的 self-attention 增强 seed feature。SamplingModule 根据点特征和语言特征从 seed 中选择 128 个 proposal：

```text
Superpoint Feature
 -> FPS 256 seeds
 -> SCG spatial self-attention
 -> language-guided SamplingModule
 -> 128 sampled seeds
 -> 3-layer MLP query generator
 -> Q0 [B, 128, 256]
```

## 4. 六层迭代式 Encoder-Decoder

DEC 包含 6 个 encoder layer 和 6 个 decoder layer，按层交替运行：

```text
for layer i = 0 ... 5:
    T_i, I_i = Encoder_i(T_{i-1}, I_{i-1}, Q_{i-1})
    Q_i, prediction_i = Decoder_i(T_i, I_i, Q_{i-1})
```

每层都会产生 auxiliary prediction，最终第 6 层产生主预测。

cluster attention 共享同一套参数，但只有最后两个 encoder layer 启用：

```text
Encoder 1: no cluster
Encoder 2: no cluster
Encoder 3: no cluster
Encoder 4: no cluster
Encoder 5: cluster enabled
Encoder 6: cluster enabled
```

## 5. posA Encoder Layer

### 5.1 模块组成

每个 encoder layer 包含：

| 模块 | Query | Key/Value | 更新对象 |
|---|---|---|---|
| LLA | language | language | `lang_feats` |
| LIA | language | instance | `lang_feats` |
| Cluster Attention | decoder query | cluster token | `inst_feats` |
| ILA | instance | language | `inst_feats` |
| Language FFN | language | - | `lang_feats` |

### 5.2 posA 的执行顺序

```text
输入: T, I, Q

T1 = LLA(T)                         language self-attention
T2 = LIA(query=T1, key/value=I)     language reads instance context

if current layer is one of the last two layers:
    C = BuildHierarchicalCluster(I)
    M = C2FClusterAttention(I, Q, C)
    I1 = I + sigmoid(alpha) * M
else:
    I1 = I

I2 = ILA(query=I1, key/value=T2)    instance reads updated language
T3 = FFN(T2)

输出: T3, I2
```

公式表示：

```text
T'  = LIA(LLA(T), I)
I'  = I + sigmoid(alpha) * ClusterMessage(I, Q)
I'' = ILA(I', T')
T'' = FFN(T')
```

### 5.3 posA 与原 lite 的区别

原始 `c2f_enc_lite`：

```text
LLA -> Cluster -> LIA -> ILA -> FFN
```

posA：

```text
LLA -> LIA -> Cluster -> ILA -> FFN
```

两者最重要的实际差异是：

- 原 lite 中，LIA 的 language query 读取已经经过 cluster 增强的 instance feature。
- posA 中，LIA 先读取未经 cluster 增强的 instance feature；之后 cluster 增强 instance feature，再由 ILA 使用更新后的语言增强 instance feature。

需要注意：LIA 的输出是 `lang_feats`，不是 `inst_feats`。因此当前代码中的 posA 并不是“先将 inst feature language 化，再做 cluster”，而是“先更新语言，再做 instance cluster enhancement，最后执行 language-to-instance 写回”。

## 6. Hierarchical Cluster Bank

### 6.1 几何层次划分

cluster bank 只根据 superpoint XYZ 构建几何层次：

```text
N superpoints
  |
  | FPS + nearest assignment
  v
256 fine clusters
  |
  | FPS + nearest assignment
  v
64 middle clusters
  |
  | FPS + nearest assignment
  v
8 coarse clusters
```

每一级使用 FPS 选取中心，再将输入点或下一级 cluster center 分配给最近中心。

### 6.2 Cluster Token 聚合

cluster feature 使用级联 `scatter_mean` 构建：

```text
C_256 = scatter_mean(I, id_256)
C_64  = scatter_mean(C_256, id_64)
C_8   = scatter_mean(C_64, id_8)
```

张量形状近似为：

```text
C_256: [B, 256, 256]
C_64:  [B,  64, 256]
C_8:   [B,   8, 256]
```

不足 cluster 数量的 batch 会补零到同一长度。

### 6.3 共享方式

几何划分在一次 DEC forward 开始时计算一次。最后两个 encoder layer 共享同一个 cluster attention 模块，但会使用各层当前的 `inst_feats` 重新聚合 cluster token：

```text
geometry assignment: shared and fixed within one forward
cluster features: rebuilt from current instance features at each enabled layer
cluster attention parameters: shared across enabled layers
cluster residual gate: each enabled encoder layer owns an independent scalar
```

## 7. C2F Cluster Attention Lite

### 7.1 模块输入与输出

`C2F_ClusterAttn_Lite` 接收以下输入：

| 输入 | 典型形状 | 作用 |
|---|---|---|
| `point_feats` | `[B,N,256]` | 当前 encoder layer 的 instance/superpoint feature |
| `query` | `[B,Q,256]` | 当前 decoder query，初始 `Q=128` |
| `point_mask` | `[B,N]` | padding mask，`True` 表示无效点 |
| `cluster_feats_list` | `[C_256,C_64,C_8]` | 三个尺度的 cluster token |
| `child_cluster_maps` | 两层 parent-to-child 字典 | coarse-to-fine 候选展开关系 |
| `cluster_ids_list` | 每层 cluster assignment | 将 cluster token gather 回点 |

三个尺度的 token 形状近似为：

```text
C_256: [B, 256, 256]   fine/local scale
C_64:  [B,  64, 256]   middle scale
C_8:   [B,   8, 256]   coarse/global scale
```

模块只返回点特征 message：

```text
output = {'point': M}
M: [B,N,256]
```

Lite 版本不会直接返回或修改 query。query 只被设计用于选择相关 cluster 路径。

### 7.2 多头 Query-to-Cluster Attention

模型维度为 `d_model=256`，使用 `nhead=8`：

```text
d_head = 256 / 8 = 32
scale  = 1 / sqrt(32)
```

对于第 `l` 个尺度的 cluster token `C_l`：

```text
Q_l = W_q(query)       [B,Q,256]
K_l = W_k(C_l)         [B,K_l,256]
V_l = W_v(C_l)         [B,K_l,256]
```

拆分多头后：

```text
Q_l: [B,8,Q,32]
K_l: [B,8,K_l,32]
V_l: [B,8,K_l,32]
```

attention score 为：

```text
S_l[b,h,q,k] = <Q_l[b,h,q], K_l[b,h,k]> / sqrt(32)
S_l: [B,8,Q,K_l]
```

若已有父层候选约束，不属于候选集合的 cluster score 加上 `-1e9`：

```text
S_l = S_l + (~candidate_mask) * (-1e9)
candidate_mask: [B,Q,K_l]
```

随后计算：

```text
A_l   = softmax(S_l, dim=cluster)
CTX_l = A_l @ V_l
CTX_l: [B,Q,256]
```

用于 top-k 排序的是 8 个 head 的平均 score：

```text
mean_score_l = mean(S_l, dim=head)
mean_score_l: [B,Q,K_l]
```

因此每个 query 都有自己的 cluster 排名，而不是整个场景共享一条 routing path。

### 7.3 父子层次关系

三层 cluster 级联构造：

```text
superpoint -> 256 fine -> 64 middle -> 8 coarse
```

为了支持反向的 coarse-to-fine 查询，需要保存：

```text
coarse cluster id -> belonging middle cluster ids
middle cluster id -> belonging fine cluster ids
```

概念上：

```text
children_64(p_8)   = {k_64  | parent(k_64)  = p_8}
children_256(p_64) = {k_256 | parent(k_256) = p_64}
```

`_child_mask` 对每个 batch、每个 query 和每个已选 parent 遍历 children：

```text
parent_indices: [B,Q,K_parent]
        |
        v
child_mask:     [B,Q,K_child]
```

不同 query 因而可以从同一个粗场景中展开不同的细粒度空间区域。

### 7.4 Coarse-to-Fine Routing 过程

代码按 `8 -> 64 -> 256` 遍历。配置的 `per_layer_topk_list=[32,16,8]` 按 `[256,64,8]` 存储。

#### 第一步：8 个 coarse cluster

```text
输入: C_8 [B,8,256]
候选约束: 无
attention score: [B,8 heads,Q,8]
top-k: 8
输出: [B,Q,8] coarse indices
```

coarse 层总共只有 8 个 cluster，因此 top-8 会选择全部 cluster，只改变排序，不产生剪枝。

#### 第二步：64 个 middle cluster

```text
8 coarse indices/query
 -> coarse-to-middle children
 -> candidate_mask_64 [B,Q,64]
 -> masked query-cluster attention
 -> top-16 middle indices [B,Q,16]
```

若整个 `candidate_mask` 没有任何 `True`，代码退化为对全部 64 个 cluster 做 attention。这个 fallback 使用全局 `cmask.any()`，并非逐 batch 或逐 query 判断。

#### 第三步：256 个 fine cluster

```text
16 middle indices/query
 -> middle-to-fine children
 -> candidate_mask_256 [B,Q,256]
 -> masked query-cluster attention
 -> top-32 fine indices [B,Q,32]
```

完整设计路径：

```text
Q
|
+-- attend C_8 --------------------------> top-8 coarse
                                              |
                                              v
                                     expand middle children
                                              |
+-- masked attend C_64 -------------------> top-16 middle
                                              |
                                              v
                                       expand fine children
                                              |
+-- masked attend C_256 ------------------> top-32 fine
```

### 7.5 Lite 与原始重型回读的区别

早期 C2F 使用 query 作为中介，将 query-selected cluster context 再传播到所有点，包含 `N x Q` point-query attention，复杂度近似：

```text
O(B * N * Q * C)
```

Lite 版本进行两项约束：

1. 不更新 decoder query，只增强 `inst_feats`。
2. 不做 point-query 全 attention，按 cluster assignment 直接 gather token。

cluster-to-point 回读的理论复杂度接近：

```text
O(B * N * L * C), L=3
```

query-to-cluster routing 的复杂度约为：

```text
O(B * Q * C * (8 + candidate_64 + candidate_256))
```

### 7.6 Cluster-to-Point 直接回写

每个尺度先建立与 padded point tensor 相同形状的 message：

```text
M_l = zeros([B,N,256])
```

对 batch `b` 中的有效点 `p`：

```text
M_256[b,p] = C_256[b, id_256[b,p]]
M_64[b,p]  = C_64[b,  id_64[b,p]]
M_8[b,p]   = C_8[b,   id_8[b,p]]
```

三个尺度堆叠为：

```text
M_stack: [B,N,256,3]
```

其直观作用是：

- `M_256` 提供局部邻域上下文；
- `M_64` 提供中尺度区域上下文；
- `M_8` 提供粗粒度场景上下文。

这是一种 hierarchical feature broadcasting：同一 cluster 内的点接收相同 token，再由后续模块继续区分。

### 7.7 Per-Point Multi-Scale Level Gate

不同点需要的上下文尺度不同，因此模型为每个点预测三个融合权重。

```text
G   = mean(I, dim=point)              [B,1,256]
G   = expand(G)                       [B,N,256]
Z_p = concat(I_p, G_p)                [B,N,512]
w_p = softmax(W_level Z_p)            [B,N,3]
```

三个权重满足：

```text
w_p,256 + w_p,64 + w_p,8 = 1
```

融合 message：

```text
M_p = w_p,256 * M_256[p]
    + w_p,64  * M_64[p]
    + w_p,8   * M_8[p]

M_p = Linear_256_to_256(Dropout(M_p))
M_p = LayerNorm(M_p)
M_p[padding] = 0
```

当前 `global_mean` 直接对 padded 长度求均值，没有使用 `point_mask` 排除补零位置，因此不同有效点数量的样本可能出现不同程度的均值缩放。

### 7.8 Encoder-Level Residual Gate

cluster message 使用残差方式注入：

```text
gamma_l = sigmoid(alpha_l)
I_enhanced = I + gamma_l * M
```

最后两个 encoder layer 各有独立标量 `alpha_l`，但共享 cluster attention 和 level gate 参数。

当前配置：

```text
alpha_l = 0.1
gamma_l = sigmoid(0.1) ~= 0.525
```

所以训练开始时已经注入约一半强度的归一化 cluster message，并不是接近零的 residual initialization。

### 7.9 完整伪代码

```text
function C2F_CLUSTER_ATTN_LITE(I, Q, point_mask, cluster_bank):
    C_256 = scatter_mean(I, id0)
    C_64  = scatter_mean(C_256, id1)
    C_8   = scatter_mean(C_64, id2)

    selected = None
    for level in [8, 64, 256]:
        if selected is None:
            candidate_mask = None
        else:
            candidate_mask = expand_children(selected)

        context, scores = multihead_cluster_attention(
            query=Q,
            key_value=C_level,
            candidate_mask=candidate_mask
        )
        selected = topk(mean_head(scores), k_level)

    M_256 = gather(C_256, point_to_256)
    M_64  = gather(C_64, point_to_64)
    M_8   = gather(C_8, point_to_8)

    level_weight = softmax(
        Linear(concat(I, global_mean(I)))
    )
    M = weighted_sum([M_256, M_64, M_8], level_weight)
    M = LayerNorm(Linear(M))
    return M
```

Encoder layer 再执行：

```text
I = I + sigmoid(alpha_layer) * M
```

### 7.10 当前实现中的关键断点

设计上，C2F routing 应决定哪些 cluster message 被回写到点。但当前代码：

```text
_qctx, scores = _scale_attn(...)
prev_indices = topk(scores)
```

`_qctx` 被丢弃，最终 `prev_indices` 也没有传入 `_cluster_to_points`。回写函数只接收：

```text
point_feats
cluster_feats_list
cluster_ids_list
point_mask
```

因此当前输出满足：

```text
M = f(point_feats, all_cluster_tokens, cluster_ids)
```

而不是：

```text
M = f(point_feats, query_selected_cluster_tokens, routing_weights)
```

直接结果：

- 修改 `per_layer_topk_list` 理论上不会改变返回的 point message；
- query-to-cluster 的 `_qctx` 不参与 loss，Q/K/V routing 投影缺少有效输出梯度路径；
- 当前实际是无条件多尺度 hierarchical cluster context，而不是有效的 query-conditioned C2F enhancement；
- routing attention 仍消耗计算和显存，但没有参与最终预测。

### 7.11 当前层级 ID 回写限制

级联聚合的 ID 含义：

```text
id0: original point -> 256
id1: 256 -> 64
id2: 64 -> 8
```

原实现对三个 ID 都执行类似 `C_l[id_l]` 的直接回写。但只有 `id0` 的长度等于原始点数，`id1` 和 `id2` 分别对应 256 和 64 个下层 cluster。

正确的 point-to-level assignment 应先复合：

```text
point_to_256 = id0
point_to_64  = id1[id0]
point_to_8   = id2[id1[id0]]
```

然后才能将三个尺度的 token 对齐到每个原始点。该修正是后续 `model_base1_cluster_research` 变体建立可靠 baseline 的第一步。
## 8. Decoder Layer 与预测头

每个 decoder layer 按以下顺序更新 query：

```text
Q1 = QIA(query=Q, key/value=instance)
Q2 = QLA(query=Q1, key/value=language)
Q3 = QQA self-attention(Q2)
Q4 = LayerNorm(Q2 + Q3)
Q5 = FFN(Q4)
```

随后产生三类输出。

### 8.1 Mask prediction

query 与 instance feature 做点积：

```text
pred_masks = einsum(query, instance_feature)
pred_masks: [B, Q, N]
```

### 8.2 Query score

```text
pred_scores = MLP(LayerNorm(query))
pred_scores: [B, Q, 1]
```

### 8.3 Indication prediction

```text
pred_indis = MLP(query)
pred_indis: [B, Q, 2]
```

推理时 `task_type=res`，使用 indication 中目标类别概率最高的 query，其 mask 作为最终 superpoint mask，再映射回原始点。

## 9. 损失函数

主损失由以下部分组成：

```text
L = 1.0 * L_mask_bce
  + 1.0 * L_mask_dice
  + 0.5 * L_score
  + 5.0 * L_sample
  + 0.1 * L_indication
  + 0.1 * L_semantic_align
```

具体包括：

| 损失 | 作用 |
|---|---|
| `mask_bce_loss` | point/superpoint mask 二分类 |
| `mask_dice_loss` | 优化预测 mask 与 GT 的区域重叠 |
| `score_loss` | query mask 质量或匹配分数 |
| `sample_loss` | 监督 language-guided seed sampling |
| `indi_loss` | 判断 query 是否对应目标 |
| `sem_loss` | query 与语言 token 的 contrastive semantic alignment |

前 5 个 decoder layer 还会产生 auxiliary loss，并按层递增加权：

```text
layer_i_weight = (i + 1) / 6
```

## 10. 设计意图与当前真实实现

为了准确理解现有实验，必须区分以下两条路径。

### 10.1 设计意图

```text
decoder query
 -> coarse-to-fine cluster selection
 -> query-relevant cluster context
 -> point feature enhancement
```

### 10.2 当前真实执行路径

当前代码虽然计算了每层 attention、candidate mask 和 top-k，但得到的 `_qctx` 与最终 `prev_indices` 没有参与 `_cluster_to_points`。最终 point message 直接由全部 cluster token 和 cluster ID gather 得到：

```text
decoder query -> C2F score/top-k -> result discarded

instance feature
 -> hierarchical scatter_mean
 -> all cluster tokens gather to points
 -> per-point level gate
 -> residual enhancement
```

因此当前结果主要证明的是：

```text
hierarchical cluster context + multi-scale point broadcast
```

而不能单独证明：

```text
query-guided coarse-to-fine routing
```

此外，当前 `cluster_ids_list` 中高层 ID 分别对应“256 cluster 到 64 cluster”和“64 cluster 到 8 cluster”的映射，原实现将它们直接当成原始点 ID 回写。严格的原始点到各层映射应为：

```text
point_to_256 = id0
point_to_64  = id1[id0]
point_to_8   = id2[id1[id0]]
```

该问题已在后续研究变体 `model_base1_cluster_research` 中修正，但本文档描述的 posA 原模型仍保留原实现。

## 11. 模型特点总结

该模型可以概括为：

```text
Sparse 3D U-Net point encoding
+ frozen RoBERTa language encoding
+ language-guided query sampling
+ 6-layer iterative language-instance-query interaction
+ late-stage hierarchical cluster context enhancement
+ per-point multi-scale fusion
+ mask/score/indication multi-task prediction
```

相比原始 base1，它的核心变化是给 instance feature 增加层次化空间上下文；相比早期 C2F Encoder，它通过直接 cluster-to-point gather、不修改 decoder query、仅在后两层注入来降低计算量并减少对原 decoder 更新路径的干扰；相比普通 lite，posA 将 cluster enhancement 从 LIA 前移动到 LIA 后、ILA 前。

## 12. 相关文件

- 配置：`Cluster/configs/Quard/model_base1_quard2_c2f_enc_lite_posA.yaml`
- 整体网络：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA/network.py`
- Encoder/Decoder：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA/dec.py`
- C2F Encoder Lite：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA/hier_postprocess.py`
- 损失函数：`Cluster/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA/loss.py`
