# 几何层次 Top-k Cluster Attention 文献调研与新设计

## 1. 调研目标

本调研围绕当前项目的核心动机：

> 根据点云几何位置建立 `N -> 256 -> 64 -> 8` 的嵌套层级，在粗层筛选 top-k 相关区域，再逐层将候选范围缩小到 64/256 层，最终以低计算量和低显存方式增强 `inst_feats`。

需要回答四个问题：

1. 粗区域 top-k 再做细粒度 attention 是否有已有理论和实验依据？
2. 点云层级应如何建立，才能保持空间一致性？
3. 不规则 cluster 的 children 数量差异如何避免 padding 和显存爆炸？
4. 256-level context 回写 point 时，如何避免同簇点收到完全相同的更新？

## 2. 下载论文

论文保存在 `docs/papers/cluster_attention/`：

| 论文 | 本地文件 | 与本研究的关系 |
|---|---|---|
| BiFormer: Bi-Level Routing Attention | `BiFormer_2303.08810.pdf` | 与“粗区域 top-k -> 细 token attention”最接近 |
| OctFormer | `OctFormer_2305.03045.pdf` | 固定 token 数窗口、层次几何结构、线性复杂度 |
| Stratified Transformer | `StratifiedTransformer_2203.14508.pdf` | 近处密集、远处稀疏的 key 采样与显存优化 |
| FlatFormer | `FlatFormer_2301.08739.pdf` | 等容量分组，避免不规则窗口 padding |
| Point Transformer V2 | `PointTransformerV2_2210.05666.pdf` | 非重叠 partition pooling 和几何位置编码 |
| DSVT | `DSVT_2301.06051.pdf` | 动态稀疏窗口、固定容量 set 和并行计算 |

## 3. 核心论文结论

### 3.1 BiFormer：你的 top-k 路由思路的直接依据

BiFormer 的 Bi-Level Routing Attention 分为两步：

```text
region-level routing:
    region query/key -> region affinity -> row-wise top-k regions

token-level attention:
    gather tokens from selected regions
    -> token attention only inside routed region union
```

公式：

```text
Qr = mean(Q tokens in each region)
Kr = mean(K tokens in each region)
Ar = Qr Kr^T
Ir = topkIndex(Ar)
Kg,Vg = gather(K,V,Ir)
O = Attention(Q,Kg,Vg)
```

与当前研究的对应关系：

```text
BiFormer region     <-> 8/64-level geometric cluster
BiFormer token      <-> 64/256-level child cluster
region top-k        <-> coarse route8/route64
routed token union  <-> selected parent 的 children
```

重要启示：

- top-k 路由应由 coarse feature 内容决定，不应只使用固定几何邻域。
- coarse routing 的目的不是直接代替细层 attention，而是过滤无关区域。
- 最终细层 attention 必须真实使用 top-k 路由结果，否则不能证明 routing 有效。
- BiFormer 能高效 gather 的前提是每个图像 region 包含相同数量的 token。

不能直接照搬的部分：图像 patch 大小固定，而点云 FPS cluster 的 children 数量不均衡。直接展开 routed cluster 会产生由最大 cluster 决定的巨大候选张量，这正是当前实现 OOM 的主要原因。

### 3.2 OctFormer：固定 token 数比固定空间形状更重要

OctFormer 观察到，固定几何窗口中的点数差异很大，会导致严重 padding 和低 GPU 利用率。其核心选择是：

```text
允许窗口形状不规则
但保证每个 attention window 的 token 数固定
```

论文使用 octree shuffled key 排序，再将连续 token reshape 成固定大小窗口，典型窗口大小为 32。

对本研究的启示：

- 路由后的 candidate 不能使用“每个 selected parent 的全部 children”。
- 应为每个 query 设置固定 candidate budget，例如 16 或 32。
- 不应构造 `[Q, selected_parent_num * max_children, C]`。
- 几何连续排序后固定容量分组，通常比大量 padding 更高效。

### 3.3 FlatFormer：等容量分组优于等空间窗口

FlatFormer 将点按空间窗口坐标和局部坐标排序，然后按固定 group size 切分：

```text
spatial sort -> equal-size groups -> dense group attention
```

论文强调，点云 attention 的实际速度常被 neighbor query、gather 和 padding 主导，而不只是理论 FLOPs。

对本研究的启示：

- FLOPs 下降不代表实际显存和延迟下降。
- candidate children 应在每个 parent 内排序，并截断/采样到固定数量。
- 路由索引最好形成规则的 `[num_query, candidate_budget]`，再使用 batch matmul。
- Python per-query 循环只能用于原型，最终实现要批量化。

### 3.4 DSVT：固定容量 set 与交替连接

DSVT 将稀疏窗口动态划分成固定 token 数的 sets，使不同区域能并行执行标准 attention；并通过 rotated set partition 在连续层之间建立跨 set 连接。

对本研究的启示：

- 固定容量候选是部署友好和低显存的关键。
- 单一层级路由可能形成信息孤岛，需要残差或另一种分组提供补充连接。
- 当前项目可以用 multi-scale residual（8/64/256）保留未进入细层 top-k 的低频上下文，而不必恢复全局 point attention。

### 3.5 Stratified Transformer：近处密集、远处稀疏

Stratified Transformer 为每个 query 密集采样近邻 key，同时稀疏采样远距离 key，从而用较低成本扩大感受野。

对本研究的启示：

- top-k routing 不应完全删除 query 自身的局部区域。
- 每个细层 query 的候选应包含两部分：

```text
local candidates: 自身 parent 下的 children，保证局部连续性
routed candidates: coarse top-k 远端区域的 children，提供长程上下文
```

- 纯内容 top-k 可能跳过附近边界信息；local + routed 更稳健。

### 3.6 Point Transformer V2：非重叠 pooling 与位置编码

PTv2 使用非重叠 partition pooling，并通过记录 partition map 直接 unpool；同时在 attention relation 中加入几何位置编码。

对本研究的启示：

- 当前 `point_to_256/id1/id2` 的非重叠层级映射是合理的。
- 直接 map-unpool 本身是有效且高效的，但只广播同一 context 会产生簇内共享更新。
- attention score 不应只有 feature cosine，建议加入 cluster center 的相对位置编码：

```text
score_ij = semantic_score_ij + lambda * geometry_bias(delta_xyz_ij)
```

## 4. 对当前代码的重新判断

当前 `model_base1_topk_c2f_cosine_l1` 已经实现：

```text
geometry: N -> 256 -> 64 -> 8
routing:  8 top-k -> 64 candidate -> 64 top-k -> 256 candidate
writeback: context256/context64/context8 -> gather to N
```

优点：

- top-k 确实控制下一层候选，不再是无效 routing。
- query 是当前尺度 cluster feature，不是 decoder proposal query。
- Cluster 分支只更新 `inst_feats`。
- 移除 point-to-point attention 后显存明显下降。

当前不足：

1. FPS cluster children 数量不均衡，候选展开仍然依赖最大 children 数。
2. cosine routing 没有位置偏置，可能选择语义相似但空间不合理的区域。
3. 256/64/8 context 直接 gather，同一个 256 cluster 的点收到相同 cluster context。
4. `_children_table` 和分块 gather 仍不是最适合 GPU 的规则张量组织。
5. 路由只含 routed candidates，没有显式保证本地 children 一定保留。
6. 当前 top-k 离散选择没有监督，无法知道 route 是否覆盖目标区域。

## 5. 新主方法：Geometry-Aware Balanced Cluster Routing

建议方法名：

```text
Geometry-Aware Balanced Coarse-to-Fine Cluster Routing
简称 GBC-Routing
```

### 5.1 层级建立

第一阶段保留当前几何层级，避免同时改变太多变量：

```text
N -> 256 -> 64 -> 8
```

继续使用非重叠映射：

```text
point_to_256
child256_to_64
child64_to_8
```

后续把 grid partition 作为独立消融，不与主模型同时改动。

### 5.2 Geometry-aware coarse routing

在 8 层计算全局区域关系：

```text
q_i = normalize(Wq F8_i)
k_j = normalize(Wk F8_j)
semantic_ij = q_i^T k_j
```

加入相对几何：

```text
relative_ij = [dx,dy,dz, distance]
geometry_ij = MLP(relative_ij)
score8_ij = semantic_ij / tau8 + lambda8 * geometry_ij
```

为了控制参数：

```text
Wq,Wk: 256 -> 32，共享于 8/64/256 层
geometry MLP: 4 -> 16 -> 1
V 保持 256 维，不投影
```

### 5.3 Local-preserving top-k routing

每个 query 的候选由两部分组成：

```text
candidate = local_children union routed_children
```

其中：

- `local_children`：query 自身 parent 下的 children，始终保留；
- `routed_children`：coarse top-k 其他 parent 下的 children。

这样结合 Stratified Transformer 的局部密集与远端稀疏思想，避免 coarse routing 错误时彻底丢失局部信息。

### 5.4 Balanced candidate budget

不能展开 selected parent 的全部 children。参考 OctFormer、FlatFormer 和 DSVT，固定每层候选容量：

```text
8-level:   full 8
64-level:  candidate budget B64  = 16
256-level: candidate budget B256 = 24 或 32
```

构建方法：

```text
1. local parent 固定保留 m_local 个 children
2. 每个 routed parent 最多提供 m_route 个 children
3. children 按与 query 的低维 routing score 排序
4. 合并后裁剪到固定 B
```

输出始终是规则张量：

```text
candidate64_indices:  [K64,  B64]
candidate256_indices: [K256, B256]
```

显存不再由最大 cluster size决定。

### 5.5 Cluster attention

只对固定候选进行可微 attention：

```text
A_l = softmax(score_l(selected candidates))
M_l = sum(A_l * V_l)
F'_l = F_l + alpha_l * M_l
```

层级顺序：

```text
F8  -> route8
F64 -> candidates(route8 + local)  -> M64 -> route64
F256-> candidates(route64 + local) -> M256
```

### 5.6 Point-specific inst refinement

不恢复高显存 point-to-point attention，也不直接把相同 context 无条件加给同簇所有点。

先映射多层 context：

```text
c_i = w256*M256[parent256(i)]
    + w64 *M64[parent64(i)]
    + w8  *M8[parent8(i)]
```

然后使用 point-specific scalar gate：

```text
d_i = LN(c_i - f_i)
g_i = sigmoid(a^T d_i + b)
f'_i = f_i + gamma * g_i * d_i
```

这里每个点虽然共享 cluster context，但 `d_i` 和 `g_i` 由自己的 `f_i` 决定，因此同簇点更新不同。

低参数版本：

```text
a: [256]，b: [1]
新增仅 257 参数
```

更低参数消融：

```text
g_i = sigmoid(beta * cosine(f_i,c_i) + bias)
```

只增加两个标量。

### 5.7 复杂度

固定候选后，attention 主体近似为：

```text
O(8^2 * d_route)
+ O(64 * B64 * d_route)
+ O(256 * B256 * d_route)
+ O(N * C)  # point gate 和 residual
```

不包含：

```text
O(N^2)
O(N * points_per_selected_cluster * C)
```

显存主要与固定的 `B64/B256` 和 point feature `[N,C]` 成线性关系。

## 6. 推荐模型变体

| 编号 | 模型 | 结构 | 研究问题 |
|---|---|---|---|
| R0 | Current-Cosine | 当前 top-k + direct gather | 当前基线 |
| R1 | Balanced-Cosine | 固定 B64/B256，无位置编码 | balanced packing 是否解决效率问题 |
| R2 | Balanced-Local | R1 + local candidates 必保留 | local+routed 是否更稳定 |
| R3 | Geometry-Routing | R2 + relative xyz bias | 几何偏置是否提高路由质量 |
| R4 | Point-Gated | R3 + point-specific scalar gate | 是否减少簇内共享更新/过平滑 |
| R5 | Bottleneck-QK | R4 + shared 256->32 Q/K | 可学习路由是否优于原始 cosine |

推荐执行顺序：

```text
R0 -> R1 -> R2 -> R4 -> R3 -> R5
```

先解决固定容量和点级差异，再增加位置编码与可学习投影。

## 7. 推荐默认超参数

```yaml
cluster_layer_nums: [256, 64, 8]
route_topk_8: 3
route_topk_64: 4
candidate_budget_64: 16
candidate_budget_256: 24
local_budget_64: 4
local_budget_256: 4
route_dim: 32
route_temperature_init: 0.5
cluster_att_num_layers: 1
cluster_att_init: 0.001
```

粗层 `top-k=3` 比当前 4 更能体现稀疏性；local candidates 提供保底，因此不需要用较大 coarse top-k 弥补路由错误。

## 8. 必做路由诊断

最终论文不能只报告 mIoU，还要证明 routing 确实工作：

1. `routing recall@k`：GT target 所在 cluster 是否被 top-k route 覆盖。
2. 8/64 层 route entropy。
3. local 与 routed candidates 的平均 attention 权重。
4. 每层实际 candidate 数和 padding 比例。
5. route 前后目标 cluster 排名变化。
6. point gate 在目标点、背景点、边界点上的分布。
7. cluster 内 pairwise cosine，监测过平滑。
8. 实测峰值显存、训练迭代时间、推理延迟。

## 9. 最终研究判断

你的原始方向具有明确文献依据，最接近 BiFormer 的 bi-level routing attention；其点云创新空间在于：

```text
几何嵌套 cluster
+ coarse-to-fine content routing
+ fixed-budget balanced children packing
+ local-preserving sparse candidates
+ point-specific gated inst refinement
```

真正应强调的贡献不是普通的“多尺度 cluster mean”，而是：

> 利用几何层级先在粗尺度定位相关区域，再以固定候选预算逐层细化注意力范围，并通过点相关门控将路由后的 cluster context 回写到 instance features。

其中 fixed-budget packing 和 point-specific refinement 是把 BiFormer 思想可靠迁移到不规则点云的关键，也是当前代码下一步最需要实现的部分。

## 10. 已实现代码（2026-07-12）

### R1 Balanced

- 模型：`Cluster/framework/model/Quard_model/model_base1_gbcr_balanced_l1/`
- 配置：`Cluster/configs/Quard/model_base1_gbcr_balanced_l1.yaml`
- 结构：固定 `B64=16`、`B256=24` 候选预算。
- 模块参数：518；含 encoder LayerScale：519。
- `12000x256` Cluster 分支前向反向峰值增量：约 126.85 MB。

### R2 Local

- 模型：`Cluster/framework/model/Quard_model/model_base1_gbcr_local_l1/`
- 配置：`Cluster/configs/Quard/model_base1_gbcr_local_l1.yaml`
- 结构：R1 + own parent 必须进入 routed parents + query token 必须进入固定候选。
- 模块参数：518；含 encoder LayerScale：519。
- `12000x256` Cluster 分支前向反向峰值增量：约 118.73 MB。

### R4 PointGate

- 模型：`Cluster/framework/model/Quard_model/model_base1_gbcr_pointgate_l1/`
- 配置：`Cluster/configs/Quard/model_base1_gbcr_pointgate_l1.yaml`
- 结构：R2 + `sigmoid(Linear(LN(context-point)))` point-specific gate。
- 模块参数：775；含 encoder LayerScale：776。
- `12000x256` Cluster 分支前向反向峰值增量：约 130.77 MB。

三个版本均通过 Python/YAML、CUDA forward/backward、路由 shape、local-parent insertion、point-specific update、独立模型解析和无跨模型目录引用检查。

### Performance-first Adaptive 版本

- 模型：`Cluster/framework/model/Quard_model/model_base1_gbcr_adaptive_l1/`
- 配置：`Cluster/configs/Quard/model_base1_gbcr_adaptive_l1.yaml`
- 结构：64层 `local4+routed12`，256层 `local4+routed20`，共享 `256->32` Q/K，point-specific 三尺度融合，identity-init PointGate。
- 路由：`8 top-3 -> 64 top-6 -> 256 top-8`。
- 模块参数：17,224；含 encoder LayerScale：17,225。
- `12000x256` Cluster 分支前向反向峰值增量：约 137.73 MB。
- point-scale cosine 作为无梯度路由信号，scale bias/temperature、context value、共享 Q/K 和 PointGate 保持可训练。
