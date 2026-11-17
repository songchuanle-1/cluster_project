# Cluster Attention 后续研究与实验设计

本文以当前最佳模型 `model_base1_quard2_c2f_enc_lite_posA` 为起点，目标不是继续堆叠模块，而是回答一个清晰问题：**层次 cluster context 是否能够在语言条件下增强与目标相关的点云特征，并最终提高 3D referring segmentation 性能？**

## 1. 当前结论与需要修正的归因

现有结果已经支持两个结论：

- 层次 cluster 特征回写有潜力。`model_base1` best mIoU 为 `0.489449`，`lite` 为 `0.499236`，`posA` 为 `0.500940`。
- cluster 模块更适合放在语言交互之后，并且只在 encoder 后 1--2 层注入。`posA` 和 `lite_l1` 最好，使用 3--4 层反而下降。

但当前代码还不能证明 C2F routing 本身有效，原因如下。

### 1.1 路由结果没有参与最终点特征增强

`hier_postprocess.py` 中每层会计算 query 到 cluster 的 attention、top-k 和 child mask，但 `_qctx` 没有进入返回值。最终的 `_cluster_to_points` 只根据 cluster ID gather 所有 cluster token，完全不使用 `prev_indices`、attention weight 或 candidate mask。

因此当前真实数据流更接近：

```text
point feature -> 多尺度均值聚合 -> cluster token
              -> 按 cluster ID 回写 -> 多尺度 gate -> residual
```

而不是：

```text
query -> coarse-to-fine 路由 -> 选择目标相关 cluster
      -> 目标相关 cluster message -> point feature
```

这也意味着 `query_linear/k_linear/v_linear` 的路由分支很可能得不到来自最终 loss 的有效梯度。`noroute` 与 `lite` 的差距目前不能直接解释为 routing 收益，应通过相同代码路径、相同随机种子的严格实验重新验证。

### 1.2 高层 cluster ID 不能直接索引原始点

当前级联关系是：

```text
原始 superpoint --id0--> 256 cluster
256 cluster      --id1--> 64 cluster
64 cluster       --id2--> 8 cluster
```

但 `_cluster_to_points` 将每一级的 `cluster_ids_list[lvl]` 都当成原始点的 ID 使用。实际上 `id1` 的长度对应 256 个细 cluster，`id2` 的长度对应 64 个中层 cluster，而不是原始 superpoint 数量。

正确的原始点到各层映射应通过复合得到：

```text
point_to_256 = id0
point_to_64  = id1[id0]
point_to_8   = id2[id1[id0]]
```

这项修正应该在所有后续实验之前完成。否则中、粗层 message 会被写到 batch 中前若干个点的位置，而不是对应的真实点。

### 1.3 当前 gate 初始化并不是弱注入

encoder 使用 `sigmoid(cluster_att_gate)`。配置中的 `cluster_att_init=0.1` 对应实际 gate 约为 `0.525`，`init=0` 也对应 `0.5`。两者差别非常小，且都不是接近零的残差初始化。

若要测试稳定的弱注入，建议使用以下任一方式：

- `gate = sigmoid(alpha)`，将 `alpha` 初始化为 `-4`，初始 gate 约为 `0.018`；
- `gate = tanh(alpha)`，将 `alpha=0`，实现严格 zero-init；
- 直接使用 LayerScale，`x = x + gamma * message`，`gamma` 初始化为 `1e-3` 或 `1e-2`。

## 2. 推荐的核心模型：Language-Guided Hierarchical Cluster Refinement

建议把后续主模型建立在 `posA + 后1层注入` 上，并将模块拆成四个可验证部分。

### 2.1 正确的层次 cluster bank

保留 FPS 几何划分，但显式保存原始点到每一级 cluster 的复合映射。每层 token 不只使用均值特征，还加入相对几何描述：

```text
cluster_token_l = MLP([
    mean(feature),
    max(feature),
    center_xyz,
    mean(xyz - center),
    std(xyz - center),
    log(cluster_size)
])
```

第一轮实验只加入 `center_xyz + cluster_size`，控制参数和变量数量。若有效，再加入 max/std。相比 query-conditioned pooling，这种几何增强只计算一次，成本更低，也更贴合“增强点云结构信息”的动机。

### 2.2 语言条件，而不是 decoder query 条件

当前 decoder query 数量多、语义不稳定，容易让不同 query 的路由互相干扰。建议先从语言目标向量构造 routing query：

```text
q_lang = AttentionPool(lang_feats, lang_mask)
```

或者优先使用项目已有的 target/entity token positive map 聚合出目标短语向量。这样模块的语义是明确的：利用 referring expression 选择目标相关空间区域。

后续再比较三种条件：

| 条件源 | 含义 | 推荐级别 |
|---|---|---|
| 无条件 | 纯几何层次上下文 | 必做基线 |
| pooled language / target phrase | 表达式引导的场景区域增强 | 推荐主模型 |
| decoder queries | 每个候选实例独立路由 | 二阶段探索 |

### 2.3 让 attention 真正作用于点 message

最稳妥的实现不是 hard top-k 后只返回 `_qctx`，而是生成每个 cluster 的语言相关性，再广播到所属点：

```text
s_l = cosine(Wq(q_lang), Wk(cluster_token_l)) / temperature
a_l = sigmoid(s_l)                         # 每个 cluster 的相关性
m_l(point) = a_l[point_to_cluster_l] * Wv(cluster_token_l)[point_to_cluster_l]
```

最终进行多尺度融合：

```text
message(point) = sum_l level_gate(point, q_lang)_l * m_l(point)
enhanced_point = point + LayerScale(message(point))
```

这个设计具有三个优点：路由权重直接影响最终输出；所有点仍可获得梯度；推理复杂度约为 `O(sum K_l + N * L)`，不需要 `N x Q` attention。

### 2.4 Soft C2F 优先于 Hard C2F

hard top-k 在早期训练中容易选错父簇，并切断未选区域梯度。建议按顺序实验：

1. `soft-all`：每层对全部 cluster 计算 sigmoid relevance，作为可靠主线。
2. `soft-C2F`：父层概率传播为子层先验，`score_child += beta * log(prob_parent)`。
3. `hard-C2F`：只在模型收敛后或推理阶段做 top-k，用于加速。

推荐论文主方法使用 soft-C2F，hard top-k 作为效率实验。这样既保留层次推理叙事，也避免不可微路由带来的训练不稳定。

## 3. 必做实验：先证明机制，再追求更高 mIoU

所有主对照应使用相同训练 epoch、数据划分、学习率、batch size 和 checkpoint 选择规则。至少运行 3 个随机种子，报告 `mean +/- std`，不要只比较单次 best epoch。

### 阶段 A：修正实现并重新建立基线

| 编号 | 模型 | 目的 |
|---|---|---|
| A0 | `model_base1` | 原始基线 |
| A1 | `posA-l1` 原代码 | 复现实验记录 |
| A2 | A1 + 正确的 point-to-level ID | 测量层级回写修正本身的影响 |
| A3 | A2 - 所有 routing 计算 | 验证当前 routing 是否确实不影响输出 |
| A4 | A2 + zero-init LayerScale | 验证稳定注入策略 |

关键 sanity check：固定模型权重和输入，A2 中打乱或修改 top-k 后输出若完全不变，即可直接证明旧 routing 是无效分支。

### 阶段 B：验证 cluster context 为什么有效

| 编号 | 结构 | 要回答的问题 |
|---|---|---|
| B0 | 无 cluster | cluster 是否必要 |
| B1 | 单尺度 256 | 局部上下文是否有效 |
| B2 | 单尺度 64 | 中尺度是否有效 |
| B3 | 单尺度 8 | 全局上下文是否有效 |
| B4 | 256+64+8，平均融合 | 多尺度本身是否有效 |
| B5 | 256+64+8，learned level gate | 自适应尺度是否有效 |
| B6 | B5 + geometry encoding | 几何统计是否进一步有效 |

cluster 数量只做一组紧凑对照即可：`[128,32,8]`、`[256,64,8]`、`[256,64,16]`。不建议一开始展开大规模网格搜索。

### 阶段 C：证明语言引导有效

| 编号 | 条件与路由 | 核心验证 |
|---|---|---|
| C0 | 无条件多尺度回写 | 纯 cluster context 基线 |
| C1 | pooled-language soft relevance | 语言引导是否有效 |
| C2 | target-phrase soft relevance | 更精确的目标短语是否更好 |
| C3 | C2 + soft-C2F parent prior | 层次路由是否有效 |
| C4 | C3 + hard top-k inference | 精度/速度权衡 |

最关键对照是 C0、C2、C3。只有 `C3 > C2 > C0` 且多种子稳定，才能形成完整证据链：cluster context 有效、语言条件有效、层次路由进一步有效。

### 阶段 D：注入策略消融

固定阶段 C 的最佳模块，仅比较：

- 注入位置：`lia 前` 与 `lia 后(posA)`；
- 注入层数：最后 `1` 层与最后 `2` 层；
- gate：scalar LayerScale 与 per-point language-conditioned gate；
- residual message：`cluster token` 与 `cluster token - point feature`。

最后一项值得重点测试。使用 `cluster - point` 表示同簇上下文相对当前点的增量，通常比直接重复加回 cluster 均值更符合“refinement”含义，并能减少特征过平滑。

## 4. 建议增加的评价与诊断

仅报告 overall mIoU 不足以说明 cluster attention 的机制。建议同时记录：

- `Acc@0.25`、`Acc@0.5` 和 mIoU；
- 按目标大小分组：small / medium / large；
- 按表达式类型分组：attribute、spatial relation、multi-object distractor；
- unique / multiple 类别；
- 参数量、FLOPs、GPU memory、单场景延迟；
- 每层 gate 均值和方差、各尺度 level weight；
- 目标点所在 cluster 的 routing recall@k；
- foreground 与 background 的平均 relevance gap。

特别推荐 `routing recall@k`：根据 GT mask 判断每个 cluster 是否包含目标点，测量 coarse、middle、fine 三层 top-k 是否覆盖目标 cluster。它能直接回答路由到底有没有找到目标区域，而不只是最终 mIoU 是否偶然提高。

还应可视化 20--30 个固定验证样本：原始点云、GT、baseline prediction、cluster relevance、增强后 prediction。样本应覆盖成功、失败、小目标和同类干扰物场景。

## 5. 训练与统计协议

- 先使用一个固定 seed 做 10--15 epoch 快速筛选，只淘汰明显差的变体。
- 入选模型必须完整训练到统一 epoch；不要比较不同训练长度的 best mIoU。
- 最终主表至少使用 3 seeds，并报告最后若干 epoch 的稳定表现或统一 early-stop 规则。
- 同时保存 `best mIoU` 与 `final mIoU`。当前多个实验 best 后明显回落，说明单点 best 有较大方差。
- 每个阶段只改变一个变量。新聚合、新 gate、新路由和新监督不要在同一个实验中同时加入。

建议增加轻量辅助监督，但放在主结构验证之后：将 GT point mask按 cluster 聚合成 cluster foreground ratio，监督语言相关性 `a_l`。可使用 soft BCE：

```text
y_cluster = mean(GT_mask of points in cluster)
L_cluster = BCEWithLogits(score_cluster, y_cluster)
```

先测试 loss weight `0.05` 和 `0.1`。该监督训练时使用、推理时移除，不增加推理成本，并能让“语言选择目标 cluster”的机制更可解释。

## 6. 推荐执行顺序

按收益、可信度和成本综合排序：

1. 修正 point-to-level 复合映射，并写输出不变性/形状单元测试。
2. 删除无效 routing，建立干净的 hierarchical context baseline。
3. 使用 `posA + 最后1层 + zero-init LayerScale` 重跑完整实验。
4. 加入 pooled-language 或 target-phrase soft cluster relevance。
5. 加入 soft-C2F parent prior，并测 routing recall@k。
6. 加入轻量 cluster-level auxiliary loss。
7. 最后再探索 geometry-aware token、hard top-k 加速和 query-conditioned 版本。

暂时不优先继续 `attnpool/qcond/agg`。它们增加了明显计算成本，却没有先解决“路由是否真正作用于输出”和“高层 ID 是否正确回写”这两个基础问题。

## 7. 推荐论文叙事

方法主线可以收敛为：

> Point-wise features have limited receptive fields and are easily confused by spatially adjacent distractors. We construct a hierarchical geometric cluster bank and use referring-language relevance to propagate target-aware context from coarse regions to fine point features.

对应的三项贡献应分别有实验支持：

1. hierarchical cluster bank 提供多尺度几何上下文；
2. language-guided relevance 抑制与表达式无关的 cluster 信息；
3. soft coarse-to-fine propagation 在保持低复杂度的同时提高目标区域选择质量。

在完成修正前，建议把现有 `posA` 结果称为“hierarchical cluster context enhancement”的初步证据，不要直接称为 query-guided C2F routing 的有效性证据。

## 8. 已实现的第一批模型变体

以下四个变体已经实现。它们共享 `model_base1_cluster_research` 中的 cluster 实现，并复用 posA 的 backbone、decoder、loss 和训练设置。除明确列出的实验变量外，其余配置保持一致，默认只在 encoder 最后一层注入 cluster message。

| 实验 | 模型与配置 | 主要改动 | 要验证的问题 |
|---|---|---|---|
| A2 | `model_base1_cluster_fixed_ctx_l1` | 修正原始点到 256/64/8 层的复合映射；无条件多尺度 context；保留 sigmoid gate | 正确的层级回写能否建立可靠的 cluster context baseline |
| A4 | `model_base1_cluster_fixed_ctx_l1_ls` | A2 + `1e-3` zero-near LayerScale | 弱残差注入是否比初始值约 0.525 的 sigmoid gate 更稳定 |
| C1 | `model_base1_cluster_langsoft_l1` | 语言相关性直接乘到各层 cluster message | 语言是否能抑制与表达式无关的 cluster context |
| C3 | `model_base1_cluster_langsoft_c2f_l1` | C1 + 父层概率作为子层 relevance 的可微先验 | coarse-to-fine 层次传播是否提供独立收益 |

### 8.1 共享实现

共享代码目录：

```text
Cluster/framework/model/Quard_model/model_base1_cluster_research/
```

其中：

- `hier_postprocess.py` 实现正确的层级映射、无条件 context、language-soft relevance 和 soft-C2F。
- `dec.py` 实现 posA 注入顺序、最后 N 层控制，以及 sigmoid/LayerScale 两种残差 gate。
- `network.py` 复用现有 posA 的 backbone 与 criterion，只替换研究 decoder。
- 四个模型别名目录分别导出共享的 `Network`，由同名 YAML 自动选择。

### 8.2 配置文件

```text
Cluster/configs/Quard/model_base1_cluster_fixed_ctx_l1.yaml
Cluster/configs/Quard/model_base1_cluster_fixed_ctx_l1_ls.yaml
Cluster/configs/Quard/model_base1_cluster_langsoft_l1.yaml
Cluster/configs/Quard/model_base1_cluster_langsoft_c2f_l1.yaml
```

四个变体均使用：

```yaml
cluster_layer_nums: [256, 64, 8]
cluster_att_num_layers: 1
```

变体参数对照：

| 变体 | `cluster_mode` | `cluster_gate_type` | `cluster_att_init` | `c2f_beta` |
|---|---|---|---:|---:|
| A2 | `context` | `sigmoid` | 0.1 | - |
| A4 | `context` | `layerscale` | 0.001 | - |
| C1 | `language_soft` | `layerscale` | 0.001 | - |
| C3 | `language_soft_c2f` | `layerscale` | 0.001 | 1.0 |

### 8.3 推荐训练顺序

第一轮按以下顺序使用相同 seed 运行：

```text
A2 fixed context
 -> A4 fixed context + LayerScale
 -> C1 language-soft
 -> C3 language-soft + soft-C2F
```

对应命令：

```bash
cd /data/songcl/3dres/Cluster_project2/Cluster

CUDA_VISIBLE_DEVICES=0 python tools/train.py configs/Quard/model_base1_cluster_fixed_ctx_l1.yaml
CUDA_VISIBLE_DEVICES=0 python tools/train.py configs/Quard/model_base1_cluster_fixed_ctx_l1_ls.yaml
CUDA_VISIBLE_DEVICES=0 python tools/train.py configs/Quard/model_base1_cluster_langsoft_l1.yaml
CUDA_VISIBLE_DEVICES=0 python tools/train.py configs/Quard/model_base1_cluster_langsoft_c2f_l1.yaml
```

第一轮统一使用配置中的 seed 1999。只有 C1 或 C3 稳定超过 A4 后，再为入选模型补 seed 1998、2000，最终报告 3 seeds 的 `mean +/- std`。

### 8.4 结果判读

| 对比 | 若前者更好，支持的结论 |
|---|---|
| A2 vs 旧 posA-l1 | 修正层级回写后，多尺度 cluster context 的收益可以被可靠验证 |
| A4 vs A2 | zero-near LayerScale 比较强的初始 sigmoid 注入更稳定 |
| C1 vs A4 | language-guided relevance 能过滤无关 cluster 信息 |
| C3 vs C1 | soft coarse-to-fine 父子传播具有独立贡献 |

理想证据链为：

```text
旧 base1
< A2 corrected hierarchical context
< A4 stable hierarchical context
< C1 language-guided context
< C3 language-guided soft-C2F
```

如果 C1 或 C3 低于 A4，应先记录 foreground/background relevance gap、各尺度 level weight 和 LayerScale 数值，再判断是语言 relevance 没学到，还是 C2F prior 过强。优先尝试 `relevance_temperature` 和 `c2f_beta` 的小范围消融，不立即叠加 attention pooling、query-conditioned aggregation 等高成本模块。
